"""Session state management for ProcessIQ Streamlit UI.

Centralizes all st.session_state access to ensure consistency
across reruns and provide type hints.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

import streamlit as st

from processiq.config import ANALYSIS_MODE_BALANCED
from processiq.models import (
    AnalysisInsight,
    BusinessProfile,
    ClarificationBundle,
    ClarificationResponse,
    Constraints,
    ProcessData,
)
from processiq.persistence import generate_user_id
from processiq.persistence import get_thread_id as make_thread_id

logger = logging.getLogger(__name__)


class ChatState(str, Enum):
    """Conversation states for the chat-first UI."""

    WELCOME = "welcome"  # Initial state, waiting for first input
    GATHERING = "gathering"  # Collecting process information
    CONFIRMING = "confirming"  # User reviewing extracted data
    ANALYZING = "analyzing"  # Analysis in progress
    CLARIFYING = "clarifying"  # Agent needs more info
    RESULTS = "results"  # Showing analysis results
    CONTINUING = "continuing"  # Follow-up conversation


@dataclass
class LastUploadedFile:
    """Track the last uploaded file to prevent reprocessing."""

    name: str
    size: int


@dataclass
class SessionState:
    """Type-safe representation of session state.

    Used for documentation and IDE support; actual state
    lives in st.session_state.
    """

    # User identification (for persistence)
    user_id: str | None = None  # UUID generated on first visit

    # Chat state
    chat_state: ChatState = ChatState.WELCOME
    messages: list[Any] = field(default_factory=list)  # List of ChatMessage
    thread_id: str | None = None

    # Process data
    process_data: ProcessData | None = None
    constraints: Constraints | None = None
    business_profile: BusinessProfile | None = None

    # Analysis
    analysis_insight: AnalysisInsight | None = None
    confidence: Any | None = None  # ConfidenceResult

    # UI settings
    analysis_mode: str = ANALYSIS_MODE_BALANCED

    # File tracking (prevents infinite rerun loop)
    last_uploaded_file: LastUploadedFile | None = None

    # Control flags
    reset_requested: bool = False


# Session state keys with their defaults
_STATE_DEFAULTS: dict[str, Any] = {
    "user_id": None,  # Generated on first init
    "chat_state": ChatState.WELCOME.value,
    "messages": [],
    "thread_id": None,
    "process_data": None,
    "constraints": None,
    "business_profile": None,
    "analysis_result": None,
    "analysis_insight": None,
    "confidence": None,
    "analysis_mode": ANALYSIS_MODE_BALANCED,
    "llm_provider": "openai",
    "last_uploaded_file": None,
    "reset_requested": False,
    # Analysis pending flag (triggers analysis on next render cycle)
    "analysis_pending": False,
    # Input pending flag (triggers processing on next render cycle)
    "input_pending": False,
    "pending_input_text": None,
    "pending_input_state": None,  # ChatState when input was submitted
    # Partial process data (incomplete/unvalidated data during GATHERING)
    "partial_process": None,
    # Clarification context (user responses to agent questions)
    "clarification_context": "",
    # Structured clarification state
    "pending_clarifications": None,  # ClarificationBundle or None
    "clarification_responses": [],  # list[ClarificationResponse]
    # Reasoning trace (populated by agent, displayed in results)
    "reasoning_trace": [],
    # Data review state
    "data_confirmed": False,
    "confidence_score": None,
    "data_gaps": [],
    # Draft step builder
    "draft_steps": None,  # list[dict] or None
    # File upload key counter (incrementing clears the widget)
    "file_upload_key_counter": 0,
}


def init_session_state() -> None:
    """Initialize session state with default values if not already set.

    Also generates a user_id if one doesn't exist (for persistence).
    """
    for key, default in _STATE_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # Generate user_id if not set (enables persistence)
    if st.session_state.get("user_id") is None:
        st.session_state.user_id = generate_user_id()
        logger.info("Generated new user ID: %s", st.session_state.user_id[:8])

    logger.debug("Session state initialized")


# --- User ID (Persistence) ---


def get_user_id() -> str:
    """Get current user ID.

    Returns:
        User ID string. If not set, generates a new one.
    """
    user_id = st.session_state.get("user_id")
    if user_id is None:
        user_id = generate_user_id()
        st.session_state.user_id = user_id
        logger.info("Generated new user ID: %s", user_id[:8])
    return user_id


def set_user_id(user_id: str) -> None:
    """Set user ID (mainly for testing)."""
    st.session_state.user_id = user_id


# --- Chat State ---


def get_chat_state() -> ChatState:
    """Get current chat state."""
    return ChatState(st.session_state.get("chat_state", ChatState.WELCOME.value))


def set_chat_state(state: ChatState) -> None:
    """Set chat state."""
    st.session_state.chat_state = state.value
    logger.debug("Chat state changed to: %s", state.value)


# --- Messages ---


def get_messages() -> list[Any]:
    """Get all conversation messages."""
    return st.session_state.get("messages", [])


def add_message(message: Any) -> None:
    """Add a message to the conversation."""
    messages = get_messages()
    messages.append(message)
    st.session_state.messages = messages


def clear_messages() -> None:
    """Clear all messages."""
    st.session_state.messages = []


# --- Thread ID ---


def get_thread_id() -> str | None:
    """Get current thread ID."""
    return st.session_state.get("thread_id")


def set_thread_id(thread_id: str | None) -> None:
    """Set thread ID."""
    st.session_state.thread_id = thread_id


def get_or_create_thread_id() -> str:
    """Get current thread ID, or create a new one if none exists.

    The thread ID is composed of user_id:conversation_id format,
    enabling persistence and conversation history per user.

    Returns:
        Thread ID string.
    """
    thread_id = get_thread_id()
    if thread_id is None:
        user_id = get_user_id()
        thread_id = make_thread_id(user_id)
        set_thread_id(thread_id)
        logger.info("Created new thread: %s", thread_id[:16])
    return thread_id


# --- Process Data ---


def get_process_data() -> ProcessData | None:
    """Get current process data."""
    return st.session_state.get("process_data")


def set_process_data(data: ProcessData | None) -> None:
    """Set process data."""
    st.session_state.process_data = data


# --- Constraints ---


def get_constraints() -> Constraints | None:
    """Get current constraints."""
    return st.session_state.get("constraints")


def set_constraints(constraints: Constraints | None) -> None:
    """Set constraints."""
    st.session_state.constraints = constraints


# --- Business Profile ---


def get_business_profile() -> BusinessProfile | None:
    """Get current business profile."""
    return st.session_state.get("business_profile")


def set_business_profile(profile: BusinessProfile | None) -> None:
    """Set business profile."""
    st.session_state.business_profile = profile


# --- Analysis Insight ---


def get_analysis_insight() -> AnalysisInsight | None:
    """Get LLM-based analysis insight."""
    return st.session_state.get("analysis_insight")


def set_analysis_insight(insight: AnalysisInsight | None) -> None:
    """Set new LLM-based analysis insight."""
    st.session_state.analysis_insight = insight


# --- Confidence ---


def get_confidence() -> Any | None:
    """Get confidence result."""
    return st.session_state.get("confidence")


def set_confidence(confidence: Any | None) -> None:
    """Set confidence result."""
    st.session_state.confidence = confidence


# --- UI Settings ---


def get_analysis_mode() -> str:
    """Get selected analysis mode."""
    return st.session_state.get("analysis_mode", ANALYSIS_MODE_BALANCED)


def set_analysis_mode(mode: str) -> None:
    """Set analysis mode."""
    st.session_state.analysis_mode = mode


def get_llm_provider() -> Literal["anthropic", "openai", "ollama"]:
    """Get selected LLM provider.

    Returns one of: 'openai', 'anthropic', 'ollama'.
    """
    provider = st.session_state.get("llm_provider", "openai")
    if provider not in ("openai", "anthropic", "ollama"):
        return "openai"
    return provider


def set_llm_provider(provider: str) -> None:
    """Set LLM provider."""
    st.session_state.llm_provider = provider


# --- File Upload Tracking ---


def get_last_uploaded_file() -> tuple[str, int] | None:
    """Get last uploaded file info (name, size)."""
    data = st.session_state.get("last_uploaded_file")
    if data:
        return (data["name"], data["size"])
    return None


def set_last_uploaded_file(name: str, size: int) -> None:
    """Set last uploaded file info."""
    st.session_state.last_uploaded_file = {"name": name, "size": size}


def is_file_already_processed(name: str, size: int) -> bool:
    """Check if a file with same name and size was already processed."""
    last = get_last_uploaded_file()
    if last is None:
        return False
    return last[0] == name and last[1] == size


def clear_last_uploaded_file() -> None:
    """Clear last uploaded file tracking."""
    st.session_state.last_uploaded_file = None


def has_process_data_gaps() -> bool:
    """Check if current process data has missing values that could be estimated.

    Returns True if there are step-level data gaps (time, cost, error rate)
    that an LLM could reasonably estimate. Does NOT trigger for missing
    constraints or business profile (those aren't estimable).
    """
    confidence = get_confidence()
    if confidence is None:
        return False

    process_gap_keywords = ["time for", "cost for", "error rate for"]
    return any(
        any(kw in gap.lower() for kw in process_gap_keywords)
        for gap in getattr(confidence, "data_gaps", [])
    )


# --- Clarification Context ---


def get_clarification_context() -> str:
    """Get accumulated clarification context from user responses."""
    return st.session_state.get("clarification_context", "")


def add_clarification_context(context: str) -> None:
    """Add to clarification context (accumulates across multiple responses)."""
    existing = get_clarification_context()
    if existing:
        st.session_state.clarification_context = f"{existing}\n{context}"
    else:
        st.session_state.clarification_context = context


def clear_clarification_context() -> None:
    """Clear clarification context."""
    st.session_state.clarification_context = ""


# --- Structured Clarifications ---


def get_pending_clarifications() -> ClarificationBundle | None:
    """Get pending clarification bundle (structured questions for the user)."""
    return st.session_state.get("pending_clarifications")


def set_pending_clarifications(bundle: ClarificationBundle | None) -> None:
    """Set pending clarification bundle."""
    st.session_state.pending_clarifications = bundle


def add_clarification_response(response: ClarificationResponse) -> None:
    """Add a user response to a clarifying question."""
    responses = st.session_state.get("clarification_responses", [])
    responses.append(response)
    st.session_state.clarification_responses = responses


def clear_clarification_responses() -> None:
    """Clear all clarification responses."""
    st.session_state.clarification_responses = []


# --- Analysis Pending ---


def is_analysis_pending() -> bool:
    """Check if analysis is pending (should be triggered on next render)."""
    return st.session_state.get("analysis_pending", False)


def set_analysis_pending(pending: bool) -> None:
    """Set analysis pending flag."""
    st.session_state.analysis_pending = pending


# --- Input Pending ---


def is_input_pending() -> bool:
    """Check if input processing is pending (should be triggered on next render)."""
    return st.session_state.get("input_pending", False)


def get_pending_input() -> tuple[str | None, ChatState | None]:
    """Get pending input text and the state when it was submitted.

    Returns:
        Tuple of (input_text, chat_state) or (None, None) if no pending input.
    """
    if not is_input_pending():
        return None, None
    text = st.session_state.get("pending_input_text")
    state_value = st.session_state.get("pending_input_state")
    state = ChatState(state_value) if state_value else None
    return text, state


def set_input_pending(text: str, state: ChatState) -> None:
    """Set pending input for deferred processing.

    Args:
        text: The user input text to process.
        state: The ChatState when input was submitted.
    """
    st.session_state.input_pending = True
    st.session_state.pending_input_text = text
    st.session_state.pending_input_state = state.value


def clear_input_pending() -> None:
    """Clear pending input flag."""
    st.session_state.input_pending = False
    st.session_state.pending_input_text = None
    st.session_state.pending_input_state = None


# --- Partial Process ---


def get_partial_process() -> dict | None:
    """Get partial process data (incomplete/unvalidated data during GATHERING).

    Returns a dict with whatever we've understood so far:
    - steps: list of partial step dicts
    - name: process name if detected
    - context: additional context provided
    """
    return st.session_state.get("partial_process")


def set_partial_process(data: dict | None) -> None:
    """Set partial process data."""
    st.session_state.partial_process = data


def update_partial_process(updates: dict) -> None:
    """Merge updates into existing partial process data."""
    current = get_partial_process() or {}

    # Merge steps
    if "steps" in updates:
        existing_steps = current.get("steps", [])
        # Simple merge: add new steps
        # TODO: Smarter merging (detect duplicates, update existing steps)
        current["steps"] = existing_steps + updates["steps"]

    # Merge other fields
    for key in ["name", "context", "description"]:
        if updates.get(key):
            current[key] = updates[key]

    set_partial_process(current)


def clear_partial_process() -> None:
    """Clear partial process data."""
    st.session_state.partial_process = None


# --- Data Review ---


def is_data_confirmed() -> bool:
    """Check if user has confirmed the data for analysis."""
    return st.session_state.get("data_confirmed", False)


def set_data_confirmed(confirmed: bool) -> None:
    """Set data confirmed flag."""
    st.session_state.data_confirmed = confirmed


def set_confidence_score(score: float) -> None:
    """Set the confidence score from data quality check."""
    st.session_state.confidence_score = score


def set_data_gaps(gaps: list[str]) -> None:
    """Set the list of data gaps found during quality check."""
    st.session_state.data_gaps = gaps


# --- Draft Step Builder ---


def get_draft_steps() -> list[dict] | None:
    """Get draft steps from the step builder form."""
    return st.session_state.get("draft_steps")


def set_draft_steps(steps: list[dict] | None) -> None:
    """Set draft steps."""
    st.session_state.draft_steps = steps


def add_draft_step(step: dict) -> None:
    """Add a draft step to the builder."""
    steps = get_draft_steps() or []
    steps.append(step)
    st.session_state.draft_steps = steps


def remove_draft_step(index: int) -> None:
    """Remove a draft step by index."""
    steps = get_draft_steps() or []
    if 0 <= index < len(steps):
        steps.pop(index)
        st.session_state.draft_steps = steps


# --- File Upload Key ---


def get_file_upload_key() -> str:
    """Get a unique key for the file uploader widget.

    The key includes a counter that increments on reset,
    which forces Streamlit to create a new widget (clearing the file).
    """
    counter = st.session_state.get("file_upload_key_counter", 0)
    return f"file_upload_{counter}"


# --- Reset ---


def request_reset() -> None:
    """Request a conversation reset."""
    st.session_state.reset_requested = True


def is_reset_requested() -> bool:
    """Check if reset was requested."""
    return st.session_state.get("reset_requested", False)


def reset_conversation() -> None:
    """Reset all conversation state to defaults.

    Creates a new thread_id for the user (keeping the same user_id).
    This starts a fresh conversation while preserving user identity.
    """
    st.session_state.chat_state = ChatState.WELCOME.value
    st.session_state.messages = []
    # Create new thread_id for fresh conversation (preserves user_id)
    user_id = get_user_id()
    st.session_state.thread_id = make_thread_id(user_id)
    st.session_state.process_data = None
    st.session_state.partial_process = None
    st.session_state.analysis_insight = None
    st.session_state.confidence = None
    st.session_state.last_uploaded_file = None
    st.session_state.reset_requested = False
    # Increment file upload key counter to clear the file uploader widget
    st.session_state.file_upload_key_counter = (
        st.session_state.get("file_upload_key_counter", 0) + 1
    )
    st.session_state.analysis_pending = False
    st.session_state.input_pending = False
    st.session_state.pending_input_text = None
    st.session_state.pending_input_state = None
    st.session_state.clarification_context = ""
    st.session_state.pending_clarifications = None
    st.session_state.clarification_responses = []
    st.session_state.data_confirmed = False
    st.session_state.confidence_score = None
    st.session_state.data_gaps = []
    st.session_state.draft_steps = None
    # Note: Keep user_id, constraints, business_profile, analysis_mode
    logger.info("Conversation reset, new thread: %s", st.session_state.thread_id[:16])


def reset_all() -> None:
    """Reset all state to defaults including settings.

    Preserves user_id for persistence continuity.
    """
    # Preserve user_id
    user_id = st.session_state.get("user_id")

    for key in _STATE_DEFAULTS:
        st.session_state[key] = _STATE_DEFAULTS[key]

    # Restore user_id (or generate new if needed)
    if user_id:
        st.session_state.user_id = user_id
    else:
        st.session_state.user_id = generate_user_id()

    logger.info("All state reset to defaults")


# --- Reasoning Trace ---


def get_reasoning_trace() -> list[str]:
    """Get reasoning trace."""
    return st.session_state.get("reasoning_trace", [])


def set_reasoning_trace(trace: list[str]) -> None:
    """Set reasoning trace."""
    st.session_state.reasoning_trace = trace
