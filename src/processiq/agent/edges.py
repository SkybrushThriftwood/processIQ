"""Conditional edge functions for LangGraph routing.

These functions determine which node to execute next based on state.
"""

import logging
from typing import Literal

from langchain_core.messages import AIMessage

from processiq.agent.state import AgentState

logger = logging.getLogger(__name__)


def route_after_context_check(
    state: AgentState,
) -> Literal["request_clarification", "analyze"]:
    """Route after context sufficiency check.

    If confidence is too low, request clarification from user.
    Otherwise, proceed to LLM analysis.
    """
    needs_clarification = state.get("needs_clarification", False)

    if needs_clarification:
        logger.debug("Routing to: request_clarification")
        return "request_clarification"

    logger.debug("Routing to: analyze")
    return "analyze"


def route_after_clarification(
    state: AgentState,
) -> Literal["check_context", "analyze"]:
    """Route after receiving user clarification.

    If user provided a response, re-check context.
    This creates a loop until confidence is sufficient.
    """
    user_response = state.get("user_response")
    confidence = state.get("confidence_score", 0.0)

    # If user provided response, re-check context
    if user_response:
        logger.debug("User response received, re-checking context")
        return "check_context"

    # If confidence is now sufficient (perhaps user declined to provide more data)
    # proceed anyway with what we have
    if confidence >= 0.4:  # Lower threshold after user interaction
        logger.debug("Proceeding with available data")
        return "analyze"

    logger.debug("Still need more context")
    return "check_context"


def route_after_initial_analysis(
    state: AgentState,
) -> Literal["investigate", "finalize"]:
    """Skip investigation if initial analysis found nothing actionable,
    or if max_cycles is set to 0 (investigation disabled).
    """
    from processiq.config import settings

    insight = state.get("analysis_insight")
    max_cycles = state.get("max_cycles_override") or settings.agent_max_cycles

    if max_cycles == 0:
        logger.debug("Routing: investigation disabled (max_cycles=0)")
        return "finalize"

    if not insight or not insight.issues:
        logger.debug("Routing: no issues found, skipping investigation")
        return "finalize"

    logger.debug(
        "Routing: %d issue(s) found, proceeding to investigation", len(insight.issues)
    )
    return "investigate"


def route_investigation(
    state: AgentState,
) -> Literal["tools", "finalize"]:
    """Route after investigate_node.

    Forward to tools if LLM made tool calls AND we are under the turn limit.
    Otherwise finalize.
    """
    from processiq.config import settings

    messages = state.get("messages", [])
    if not messages:
        return "finalize"

    last = messages[-1]
    cycle_count = state.get("cycle_count", 0)
    max_cycles = state.get("max_cycles_override") or settings.agent_max_cycles

    has_tool_calls = isinstance(last, AIMessage) and bool(
        getattr(last, "tool_calls", [])
    )

    if has_tool_calls and cycle_count < max_cycles:
        logger.debug("Routing to tools (turn %d/%d)", cycle_count, max_cycles)
        return "tools"

    logger.debug(
        "Routing to finalize (turn %d, tool_calls=%s)", cycle_count, has_tool_calls
    )
    return "finalize"
