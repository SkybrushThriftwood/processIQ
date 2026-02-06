"""ProcessIQ LangGraph agent.

The recommended way to interact with the agent is through the interface module:

    from processiq.agent import analyze_process, extract_from_text

For advanced usage (custom checkpointers, testing), use graph.py directly.
"""

from processiq.agent.graph import build_graph, compile_graph
from processiq.agent.interface import (
    AgentResponse,
    analyze_process,
    continue_conversation,
    extract_from_file,
    extract_from_text,
    get_thread_state,
    has_saved_state,
)
from processiq.agent.state import AgentState, create_initial_state

__all__ = [
    # Interface (recommended)
    "AgentResponse",
    "analyze_process",
    "continue_conversation",
    "extract_from_file",
    "extract_from_text",
    "get_thread_state",
    "has_saved_state",
    # Low-level (advanced)
    "AgentState",
    "build_graph",
    "compile_graph",
    "create_initial_state",
]
