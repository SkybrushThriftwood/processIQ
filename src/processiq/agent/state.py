"""LangGraph agent state definition for ProcessIQ.

Uses TypedDict for better performance in state passing between nodes.
"""

from typing import Annotated, Any

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from processiq.models import (
    AnalysisInsight,
    AnalysisResult,
    BusinessProfile,
    Constraints,
    ProcessData,
)


class AgentState(TypedDict, total=False):
    """State passed between LangGraph nodes.

    Using TypedDict (not Pydantic) for LangGraph performance.
    Fields marked total=False are optional.
    """

    # Input data
    process: ProcessData
    constraints: Constraints | None
    profile: BusinessProfile | None

    # Analysis results
    analysis_result: AnalysisResult | None  # Legacy fallback
    analysis_insight: AnalysisInsight | None  # LLM-based analysis output (preferred)

    # Confidence and data quality
    confidence_score: float
    data_gaps: list[str]

    # Agent reasoning and decisions
    messages: Annotated[list[Any], add_messages]  # Conversation history
    reasoning_trace: list[str]  # Log of agent decisions
    current_phase: str  # Current execution phase

    # Control flow
    needs_clarification: bool
    clarification_questions: list[str]
    user_response: str | None

    # Error handling
    error: str | None

    # LLM configuration (passed from UI)
    analysis_mode: str | None
    llm_provider: str | None


# Initial state factory
def create_initial_state(
    process: ProcessData,
    constraints: Constraints | None = None,
    profile: BusinessProfile | None = None,
    analysis_mode: str | None = None,
    llm_provider: str | None = None,
) -> AgentState:
    """Create initial agent state with required fields."""
    return AgentState(
        process=process,
        constraints=constraints,
        profile=profile,
        analysis_result=None,
        analysis_insight=None,
        confidence_score=0.0,
        data_gaps=[],
        messages=[],
        reasoning_trace=[],
        current_phase="initialization",
        needs_clarification=False,
        clarification_questions=[],
        user_response=None,
        error=None,
        analysis_mode=analysis_mode,
        llm_provider=llm_provider,
    )
