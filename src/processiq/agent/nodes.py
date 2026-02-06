"""LangGraph node functions for ProcessIQ agent.

Each node represents a step in the analysis pipeline.
Nodes log entry/exit and return state updates.

Architecture:
- Algorithms calculate FACTS (metrics, percentages, dependencies)
- LLM makes JUDGMENTS (what's a problem, what's core value)
- ROI estimates come from LLM recommendations (contextual, not formulaic)
"""

import json
import logging
from typing import Any

from processiq.agent.state import AgentState
from processiq.analysis import (
    ConfidenceResult,
    calculate_confidence,
    calculate_process_metrics,
    format_metrics_for_llm,
    identify_critical_gaps,
)
from processiq.config import TASK_ANALYSIS, settings
from processiq.models import (
    AnalysisInsight,
    BusinessProfile,
    Constraints,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM Helper Functions
# ---------------------------------------------------------------------------


def _get_llm_model(
    task: str | None = None,
    analysis_mode: str | None = None,
    provider: str | None = None,
):
    """Get the LLM model, with lazy import to avoid circular dependencies.

    Args:
        task: Optional task name for task-specific model config.
        analysis_mode: Optional analysis mode preset.
        provider: Optional provider override.
    """
    from processiq.llm import get_chat_model

    return get_chat_model(task=task, analysis_mode=analysis_mode, provider=provider)


# ---------------------------------------------------------------------------
# Graph Nodes
# ---------------------------------------------------------------------------


def check_context_sufficiency(state: AgentState) -> dict[str, Any]:
    """Node: Check if we have sufficient context to proceed.

    Agentic Decision Point #1: Decides whether to ask for more data
    or proceed with analysis.
    """
    logger.info("Node: check_context_sufficiency - START")

    process = state.get("process")
    if process is None:
        raise ValueError("AgentState missing required 'process' field")
    constraints = state.get("constraints")
    profile = state.get("profile")

    confidence_result: ConfidenceResult = calculate_confidence(
        process=process,
        constraints=constraints,
        profile=profile,
    )

    reasoning = f"Context check: confidence={confidence_result.score:.1%} ({confidence_result.level})"

    if not confidence_result.is_sufficient:
        critical_gaps = identify_critical_gaps(confidence_result)
        reasoning += f", identified {len(critical_gaps)} critical gaps"
        logger.info("Context insufficient, needs clarification")

        return {
            "confidence_score": confidence_result.score,
            "data_gaps": confidence_result.data_gaps,
            "needs_clarification": True,
            "clarification_questions": confidence_result.suggestions_for_improvement[
                :3
            ],
            "reasoning_trace": [*state.get("reasoning_trace", []), reasoning],
            "current_phase": "needs_clarification",
        }

    logger.info("Context sufficient, proceeding to analysis")
    return {
        "confidence_score": confidence_result.score,
        "data_gaps": confidence_result.data_gaps,
        "needs_clarification": False,
        "reasoning_trace": [*state.get("reasoning_trace", []), reasoning],
        "current_phase": "analysis",
    }


def analyze_with_llm_node(state: AgentState) -> dict[str, Any]:
    """Node: Analyze process using LLM judgment on pre-calculated metrics.

    Algorithms calculate FACTS (time percentages, dependencies, patterns).
    LLM makes JUDGMENTS (what's a problem vs core value).

    The LLM receives structured metrics and returns AnalysisInsight with:
    - Issues (problems with root cause hypotheses)
    - Recommendations (tied to specific issues)
    - Not-problems (steps that look slow but are core value)
    """
    logger.info("Node: analyze_with_llm - START")

    process = state.get("process")
    if process is None:
        raise ValueError("AgentState missing required 'process' field")

    constraints = state.get("constraints")
    profile = state.get("profile")

    # Calculate metrics (FACTS, not judgments)
    metrics = calculate_process_metrics(process)
    metrics_text = format_metrics_for_llm(metrics)

    logger.debug(
        "Metrics calculated: %d steps, %.1fh total, %d reviews, %d external",
        metrics.step_count,
        metrics.total_time_hours,
        metrics.patterns.review_step_count,
        metrics.patterns.external_touchpoints,
    )

    # Build context for LLM
    industry = (
        profile.custom_industry or profile.industry.value
        if profile and profile.industry
        else None
    )
    constraints_summary = (
        _format_constraints_for_llm(constraints) if constraints else None
    )

    # Call LLM for analysis
    analysis_mode = state.get("analysis_mode")
    llm_provider = state.get("llm_provider")
    insight = _run_llm_analysis(
        metrics_text=metrics_text,
        industry=industry,
        constraints_summary=constraints_summary,
        profile=profile,
        analysis_mode=analysis_mode,
        llm_provider=llm_provider,
    )

    if insight is None:
        logger.warning("LLM analysis failed, no insight produced")
        return {
            "analysis_insight": None,
            "error": "LLM analysis failed. Please try again.",
            "reasoning_trace": [
                *state.get("reasoning_trace", []),
                "LLM analysis failed",
            ],
            "current_phase": "finalization",
        }

    logger.info(
        "LLM analysis complete: %d issues, %d recommendations, %d not-problems",
        len(insight.issues),
        len(insight.recommendations),
        len(insight.not_problems),
    )

    reasoning = (
        f"LLM analysis: {len(insight.issues)} issues identified, "
        f"{len(insight.recommendations)} recommendations, "
        f"{len(insight.not_problems)} steps identified as core value (not waste)"
    )

    return {
        "analysis_insight": insight,
        "reasoning_trace": [*state.get("reasoning_trace", []), reasoning],
        "current_phase": "finalization",
    }


def finalize_analysis_node(state: AgentState) -> dict[str, Any]:
    """Node: Finalize and package the analysis results.

    Passes through the AnalysisInsight from the analyze node.
    Sets the phase to complete.
    """
    logger.info("Node: finalize_analysis - START")

    insight = state.get("analysis_insight")
    confidence = state.get("confidence_score", 0.0)
    error = state.get("error")

    if error:
        reasoning = f"Analysis finalized with error: {error}"
    elif insight:
        reasoning = (
            f"Analysis finalized: {len(insight.issues)} issues, "
            f"{len(insight.recommendations)} recommendations, "
            f"confidence={confidence:.0%}"
        )
    else:
        reasoning = "Analysis finalized with no results"

    logger.info("Analysis finalized (confidence=%.0f%%)", confidence * 100)

    return {
        "reasoning_trace": [*state.get("reasoning_trace", []), reasoning],
        "current_phase": "complete",
    }


# ---------------------------------------------------------------------------
# LLM Analysis Helpers
# ---------------------------------------------------------------------------


def _run_llm_analysis(
    metrics_text: str,
    industry: str | None = None,
    constraints_summary: str | None = None,
    profile: BusinessProfile | None = None,
    analysis_mode: str | None = None,
    llm_provider: str | None = None,
) -> AnalysisInsight | None:
    """Run LLM-based process analysis.

    Returns AnalysisInsight on success, None on failure.
    Retries once if the LLM returns an empty response.
    """
    if not settings.llm_explanations_enabled:
        logger.debug("LLM explanations disabled, skipping LLM analysis")
        return None

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        from processiq.prompts import get_analysis_prompt, get_system_prompt

        model = _get_llm_model(
            task=TASK_ANALYSIS,
            analysis_mode=analysis_mode,
            provider=llm_provider,
        )

        system_msg = get_system_prompt(profile=profile)
        user_msg = get_analysis_prompt(
            metrics_text=metrics_text,
            industry=industry,
            constraints_summary=constraints_summary,
        )

        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=user_msg),
        ]

        # Try up to 2 times (retry once on empty response)
        for attempt in range(2):
            logger.debug(
                "Calling LLM for process analysis (attempt %d)...", attempt + 1
            )

            response = model.invoke(messages)

            raw_content = (
                response.content if hasattr(response, "content") else str(response)
            )
            content_str = (
                raw_content if isinstance(raw_content, str) else str(raw_content)
            )

            if not content_str or not content_str.strip():
                logger.warning(
                    "Empty LLM response on attempt %d. Response object: %s",
                    attempt + 1,
                    type(response).__name__,
                )
                if attempt == 0:
                    continue  # Retry once
                return None

            insight = _parse_analysis_response(content_str)

            if insight:
                logger.info("LLM analysis parsed successfully")
                return insight

            logger.warning(
                "Failed to parse LLM analysis response on attempt %d", attempt + 1
            )
            return None  # Don't retry parse failures — same response would fail again

        return None

    except Exception as e:
        logger.error("LLM analysis failed: %s", e)
        return None


def _parse_analysis_response(content: str) -> AnalysisInsight | None:
    """Parse LLM response into AnalysisInsight model.

    Handles JSON extraction from markdown code blocks if present.
    """
    try:
        logger.debug("LLM response length: %d chars", len(content) if content else 0)

        if not content or not content.strip():
            logger.warning("Empty LLM response")
            return None

        # Extract JSON from markdown code blocks if present
        json_str = content
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                json_str = content[start:end].strip()
                logger.debug("Extracted JSON from ```json block")
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                json_str = content[start:end].strip()
                logger.debug("Extracted JSON from ``` block")

        # Try to find JSON object if not in code block
        if not json_str.strip().startswith("{"):
            first_brace = content.find("{")
            last_brace = content.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str = content[first_brace : last_brace + 1]
                logger.debug("Extracted JSON by finding braces")

        if not json_str.strip().startswith("{"):
            logger.warning(
                "No JSON object found in response. Preview: %s...", content[:200]
            )
            return None

        data = json.loads(json_str)
        return AnalysisInsight(**data)

    except json.JSONDecodeError as e:
        logger.warning("JSON decode error: %s", e)
        logger.debug(
            "Failed JSON (first 300 chars): %s", content[:300] if content else "(empty)"
        )
        return None
    except Exception as e:
        logger.warning("Error parsing analysis response: %s", e)
        return None


def _format_constraints_for_llm(constraints: Constraints) -> str:
    """Format constraints as a readable summary for LLM."""
    parts = []

    if constraints.budget_limit:
        parts.append(f"Budget limit: ${constraints.budget_limit:,.0f}")

    if constraints.cannot_hire:
        parts.append("Cannot hire new staff")

    if constraints.must_maintain_audit_trail:
        parts.append("Must maintain audit trail")

    if constraints.max_implementation_weeks:
        parts.append(
            f"Max implementation time: {constraints.max_implementation_weeks} weeks"
        )

    if constraints.max_error_rate_increase_pct:
        parts.append(
            f"Max acceptable error rate increase: {constraints.max_error_rate_increase_pct}%"
        )

    if constraints.priority:
        parts.append(f"Priority: {constraints.priority.value}")

    return "; ".join(parts) if parts else "No specific constraints"
