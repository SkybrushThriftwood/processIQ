"""LangGraph node functions for ProcessIQ agent.

Each node represents a step in the analysis pipeline.
Nodes log entry/exit and return state updates.

Architecture:
- Algorithms calculate FACTS (metrics, percentages, dependencies)
- LLM makes JUDGMENTS (what's a problem, what's core value)
- ROI estimates come from LLM recommendations (contextual, not formulaic)
"""

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
    business_context = (
        _format_business_context_for_llm(profile) if profile else None
    )
    constraints_summary = (
        _format_constraints_for_llm(constraints) if constraints else None
    )

    # Format feedback history (if user has rated previous recommendations)
    feedback = state.get("feedback_history", {})
    feedback_text = _format_feedback_history(feedback) if feedback else None

    # Call LLM for analysis
    analysis_mode = state.get("analysis_mode")
    llm_provider = state.get("llm_provider")
    insight = _run_llm_analysis(
        metrics_text=metrics_text,
        business_context=business_context,
        constraints_summary=constraints_summary,
        profile=profile,
        analysis_mode=analysis_mode,
        llm_provider=llm_provider,
        feedback_history=feedback_text,
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


def _format_feedback_history(feedback: dict[str, dict]) -> str | None:
    """Format recommendation feedback into text for the LLM prompt.

    Args:
        feedback: Dict keyed by recommendation title, values have
                  "vote" ("up"/"down") and optional "reason".

    Returns:
        Formatted text for the prompt, or None if no feedback.
    """
    if not feedback:
        return None

    lines = []
    rejected = [(t, f) for t, f in feedback.items() if f["vote"] == "down"]
    accepted = [(t, f) for t, f in feedback.items() if f["vote"] == "up"]

    if rejected:
        lines.append("REJECTED recommendations (do NOT suggest these again):")
        for title, f in rejected:
            reason = f.get("reason")
            if reason:
                lines.append(f'- "{title}" -- Reason: {reason}')
            else:
                lines.append(f'- "{title}" -- (no reason given)')

    if accepted:
        if lines:
            lines.append("")
        lines.append("ACCEPTED recommendations (user found these valuable):")
        for title, _ in accepted:
            lines.append(f'- "{title}"')

    return "\n".join(lines) if lines else None


def _run_llm_analysis(
    metrics_text: str,
    business_context: str | None = None,
    constraints_summary: str | None = None,
    profile: BusinessProfile | None = None,
    analysis_mode: str | None = None,
    llm_provider: str | None = None,
    feedback_history: str | None = None,
) -> AnalysisInsight | None:
    """Run LLM-based process analysis using structured output.

    Uses LangChain's with_structured_output() for guaranteed schema compliance.
    The LLM returns an AnalysisInsight directly via tool calling -- no manual
    JSON parsing needed.

    Returns AnalysisInsight on success, None on failure.
    Retries once on failure.
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

        structured_model = model.with_structured_output(AnalysisInsight)

        system_msg = get_system_prompt(profile=profile)
        user_msg = get_analysis_prompt(
            metrics_text=metrics_text,
            business_context=business_context,
            constraints_summary=constraints_summary,
            feedback_history=feedback_history,
        )

        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=user_msg),
        ]

        # Try up to 2 times (retry once on failure)
        for attempt in range(2):
            logger.debug(
                "Calling LLM for process analysis (attempt %d)...", attempt + 1
            )

            try:
                result = structured_model.invoke(messages)
                insight: AnalysisInsight | None = (
                    result if isinstance(result, AnalysisInsight) else None
                )
            except Exception as e:
                logger.warning(
                    "Structured output failed on attempt %d: %s", attempt + 1, e
                )
                if attempt == 0:
                    continue
                return None

            if insight is None:
                logger.warning("LLM returned None on attempt %d", attempt + 1)
                if attempt == 0:
                    continue
                return None

            logger.info("LLM analysis parsed successfully via structured output")
            return insight

        return None

    except Exception as e:
        logger.error("LLM analysis failed: %s", e)
        return None


def _format_business_context_for_llm(profile: BusinessProfile) -> str:
    """Format the full business profile as readable context for LLM."""
    from processiq.models.memory import RevenueRange

    parts = []

    # Industry
    if profile.industry is not None:
        industry_str = profile.custom_industry or profile.industry.value
        parts.append(f"Industry: {industry_str}")

    # Company size
    if profile.company_size is not None:
        size_labels = {
            "startup": "Startup (under 50 employees)",
            "small": "Small business (50-200 employees)",
            "mid_market": "Mid-market company (200-1000 employees)",
            "enterprise": "Enterprise (over 1000 employees)",
        }
        parts.append(
            f"Company size: {size_labels.get(profile.company_size.value, profile.company_size.value)}"
        )

    # Revenue range (only if provided)
    if profile.annual_revenue != RevenueRange.PREFER_NOT_TO_SAY:
        revenue_labels = {
            "under_100k": "Under $100K/year",
            "100k_to_500k": "$100K - $500K/year",
            "500k_to_1m": "$500K - $1M/year",
            "1m_to_5m": "$1M - $5M/year",
            "5m_to_20m": "$5M - $20M/year",
            "20m_to_100m": "$20M - $100M/year",
            "over_100m": "Over $100M/year",
        }
        parts.append(
            f"Annual revenue: {revenue_labels.get(profile.annual_revenue.value, profile.annual_revenue.value)}"
        )

    # Regulatory environment
    parts.append(f"Regulatory environment: {profile.regulatory_environment.value}")

    # Rejected approaches
    if profile.rejected_approaches:
        parts.append(
            f"Previously rejected approaches (DO NOT suggest): {', '.join(profile.rejected_approaches)}"
        )

    # Free-text notes (most important for context)
    if profile.notes and profile.notes.strip():
        parts.append(f"\nAdditional context from the user:\n{profile.notes.strip()}")

    return "\n".join(parts)


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
