"""LangGraph graph construction for ProcessIQ agent.

Builds the stateful graph with nodes, edges, and conditional routing.

Graph flow:
    check_context → (sufficient) → analyze → finalize → END
                  → (insufficient) → request_clarification → (loop back)
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from processiq.agent.edges import (
    route_after_clarification,
    route_after_context_check,
)
from processiq.agent.nodes import (
    analyze_with_llm_node,
    check_context_sufficiency,
    finalize_analysis_node,
)
from processiq.agent.state import AgentState
from processiq.config import TASK_CLARIFICATION, settings

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph[AgentState]:
    """Build the ProcessIQ analysis graph.

    Graph structure:
    ```
    START
      │
      ▼
    check_context ──────────────────┐
      │                             │
      │ (sufficient)                │ (insufficient)
      ▼                             ▼
    analyze                 request_clarification
      │                             │
      ▼                             │ (user responds)
    finalize                ────────┘
      │
      ▼
    END
    ```
    """
    logger.info("Building ProcessIQ analysis graph")

    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("check_context", check_context_sufficiency)
    graph.add_node("analyze", analyze_with_llm_node)
    graph.add_node("finalize", finalize_analysis_node)
    graph.add_node("request_clarification", _request_clarification_node)

    # Set entry point
    graph.set_entry_point("check_context")

    # Conditional edges
    graph.add_conditional_edges(
        "check_context",
        route_after_context_check,
        {
            "request_clarification": "request_clarification",
            "analyze": "analyze",
        },
    )

    graph.add_conditional_edges(
        "request_clarification",
        route_after_clarification,
        {
            "check_context": "check_context",
            "analyze": "analyze",
        },
    )

    # Linear edges
    graph.add_edge("analyze", "finalize")
    graph.add_edge("finalize", END)

    logger.info("Graph built successfully")
    return graph


def compile_graph(checkpointer: Any = None) -> Any:
    """Compile the graph for execution.

    Args:
        checkpointer: Optional checkpointer for state persistence.
                     Use MemorySaver for development, SqliteSaver for production.

    Returns:
        Compiled graph ready for invocation.
    """
    graph = build_graph()

    if checkpointer:
        logger.info("Compiling graph with checkpointer")
        return graph.compile(checkpointer=checkpointer)

    logger.info("Compiling graph without checkpointer")
    return graph.compile()


def _generate_llm_clarification_questions(
    confidence: float,
    data_gaps: list[str],
    phase: str,
    partial_results: list[str] | None = None,
) -> list[str] | None:
    """Generate clarification questions using LLM.

    Returns None if LLM is disabled or fails (caller should use fallback).
    """
    if not settings.llm_explanations_enabled:
        return None

    try:
        from processiq.llm import get_chat_model
        from processiq.prompts import get_clarification_prompt, get_system_prompt

        model = get_chat_model(task=TASK_CLARIFICATION)

        system_msg = get_system_prompt()
        user_msg = get_clarification_prompt(
            confidence=confidence,
            phase=phase,
            data_gaps=data_gaps,
            partial_results=partial_results,
        )

        logger.debug("Generating LLM clarification questions")
        response = model.invoke(
            [
                SystemMessage(content=system_msg),
                HumanMessage(content=user_msg),
            ]
        )

        # Parse response into list of questions
        raw_content = (
            response.content if hasattr(response, "content") else str(response)
        )
        content = raw_content if isinstance(raw_content, str) else str(raw_content)

        # Simple parsing: split by numbered lines
        questions: list[str] = []
        for line in content.split("\n"):
            line = line.strip()
            if line and len(line) > 2 and line[0].isdigit() and line[1] in ".):":
                questions.append(line[2:].strip())
            elif line and line.startswith("-"):
                questions.append(line[1:].strip())

        if questions:
            logger.info("LLM generated %d clarification questions", len(questions))
            return questions[:3]
        logger.warning("Could not parse LLM response into questions, using as-is")
        return [content]

    except Exception as e:
        logger.warning("LLM clarification question generation failed: %s", e)
        return None


def _request_clarification_node(state: AgentState) -> dict[str, Any]:
    """Node: Request clarification from user.

    Uses LLM to generate contextual clarification questions when enabled.
    """
    logger.info("Node: request_clarification - awaiting user input")

    confidence = state.get("confidence_score", 0.5)
    data_gaps = state.get("data_gaps", [])
    existing_questions = state.get("clarification_questions", [])

    # Try LLM for better questions
    llm_questions = _generate_llm_clarification_questions(
        confidence=confidence,
        data_gaps=data_gaps,
        phase="initial_analysis",
        partial_results=None,
    )

    used_llm = llm_questions is not None

    # Use LLM questions if available, otherwise fall back to template
    if llm_questions:
        formatted_questions = llm_questions
    elif existing_questions:
        formatted_questions = existing_questions
    else:
        formatted_questions = [f"Please provide: {gap}" for gap in data_gaps[:3]]

    reasoning = f"Requesting clarification: {len(formatted_questions)} questions"
    if used_llm:
        reasoning += " (LLM generated)"

    return {
        "clarification_questions": formatted_questions,
        "reasoning_trace": [*state.get("reasoning_trace", []), reasoning],
        "current_phase": "awaiting_input",
    }
