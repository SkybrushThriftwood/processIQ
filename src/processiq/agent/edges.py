"""Conditional edge functions for LangGraph routing.

These functions determine which node to execute next based on state.
"""

import logging
from typing import Literal

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
