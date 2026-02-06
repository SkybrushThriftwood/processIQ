"""Clarification form component for ProcessIQ UI.

Renders structured clarifying questions with appropriate input widgets
based on the question's input_type. This provides a form-like experience
rather than chat-style interaction.
"""

import contextlib
import logging
from typing import Any

import streamlit as st

from processiq.models import (
    ClarificationBundle,
    ClarificationResponse,
    ClarifyingQuestion,
)
from processiq.ui.state import (
    add_clarification_response,
    clear_clarification_responses,
    get_pending_clarifications,
    set_pending_clarifications,
)

logger = logging.getLogger(__name__)


def render_clarification_form() -> bool:
    """Render the clarification form if there are pending questions.

    Returns:
        True if clarifications were submitted and analysis can re-run,
        False otherwise.
    """
    bundle = get_pending_clarifications()

    if not bundle or not bundle.questions:
        return False

    st.markdown("### Additional Information Needed")

    # Context explaining why we need this
    if bundle.context:
        st.info(bundle.context)
    else:
        st.info(
            "The analysis could be more accurate with additional information. "
            "Please provide what you can - you may skip questions if unknown."
        )

    # Render each question
    responses: dict[str, Any] = {}

    for question in bundle.questions:
        response = _render_question(question)
        responses[question.id] = response

    st.markdown("---")

    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if bundle.can_proceed_without:
            st.caption(
                "You may proceed without answering all questions, "
                "but results may have lower confidence."
            )

    submitted = False

    with col2:
        if bundle.can_proceed_without and st.button(
            "Skip & Continue", type="secondary"
        ):
            # Clear clarifications and allow re-run
            set_pending_clarifications(None)
            clear_clarification_responses()
            submitted = True

    with col3:
        if st.button("Submit Answers", type="primary"):
            # Store responses
            for question_id, value in responses.items():
                if value is not None and value != "":
                    response = ClarificationResponse(
                        question_id=question_id,
                        value=value,
                        skipped=False,
                    )
                    add_clarification_response(response)

            # Clear pending questions
            set_pending_clarifications(None)
            submitted = True
            logger.info("Clarification responses submitted: %d answers", len(responses))

    return submitted


def _render_question(question: ClarifyingQuestion) -> Any:
    """Render a single clarifying question with appropriate widget.

    Args:
        question: The question to render.

    Returns:
        The user's response value.
    """
    # Show question text
    st.markdown(f"**{question.question}**")

    # Show hint if provided
    if question.hint:
        st.caption(question.hint)

    # Render appropriate widget based on input type
    response: Any = None

    if question.input_type == "text":
        response = st.text_input(
            "Answer",
            value=question.default or "",
            key=f"clarify_{question.id}",
            label_visibility="collapsed",
            placeholder="Enter your answer...",
        )

    elif question.input_type == "number":
        default_val = 0.0
        if question.default:
            with contextlib.suppress(ValueError):
                default_val = float(question.default)

        response = st.number_input(
            "Answer",
            value=default_val,
            key=f"clarify_{question.id}",
            label_visibility="collapsed",
        )

    elif question.input_type == "select":
        options = question.options or []
        if not options:
            # Fall back to text input if no options
            response = st.text_input(
                "Answer",
                value=question.default or "",
                key=f"clarify_{question.id}",
                label_visibility="collapsed",
            )
        else:
            # Add "Skip" option if not required
            if not question.required:
                options = ["(Skip this question)", *list(options)]

            default_index = 0
            if question.default and question.default in options:
                default_index = options.index(question.default)

            selected = st.selectbox(
                "Answer",
                options=options,
                index=default_index,
                key=f"clarify_{question.id}",
                label_visibility="collapsed",
            )

            response = None if selected == "(Skip this question)" else selected

    elif question.input_type == "boolean":
        default_bool = False
        if question.default:
            default_bool = question.default.lower() in ("true", "yes", "1")

        response = st.checkbox(
            "Yes",
            value=default_bool,
            key=f"clarify_{question.id}",
        )

    # Mark required fields
    if question.required:
        st.caption("* Required")

    st.markdown("")  # Spacing

    return response


def create_clarification_bundle_from_gaps(
    data_gaps: list[str],
    confidence_score: float,
) -> ClarificationBundle:
    """Create a clarification bundle from data gaps.

    This is a helper to convert simple data gaps into structured questions.

    Args:
        data_gaps: List of data gap descriptions.
        confidence_score: Current confidence score.

    Returns:
        ClarificationBundle with structured questions.
    """
    questions = []

    for i, gap in enumerate(data_gaps[:5]):  # Limit to 5 questions
        # Parse gap to determine appropriate input type
        input_type = "text"
        options = None
        hint = None

        gap_lower = gap.lower()

        if (
            "error rate" in gap_lower
            or "rate" in gap_lower
            or "percentage" in gap_lower
        ):
            input_type = "number"
            hint = "Enter as a percentage (e.g., 5 for 5%)"
        elif "time" in gap_lower or "hours" in gap_lower or "duration" in gap_lower:
            input_type = "number"
            hint = "Enter time in hours"
        elif "cost" in gap_lower or "budget" in gap_lower:
            input_type = "number"
            hint = "Enter amount in dollars"
        elif (
            "yes or no" in gap_lower or "do you" in gap_lower or "can you" in gap_lower
        ):
            input_type = "boolean"
        elif "which" in gap_lower or "select" in gap_lower:
            input_type = "select"
            # Would need actual options from context

        question = ClarifyingQuestion(
            id=f"gap_{i}",
            question=gap,
            input_type=input_type,
            options=options,
            hint=hint,
            required=False,
        )
        questions.append(question)

    context = ""
    if confidence_score < 0.6:
        context = (
            f"Analysis confidence is currently {confidence_score * 100:.0f}%. "
            "Providing the following information would significantly improve accuracy."
        )
    else:
        context = "The following information would help refine the recommendations."

    return ClarificationBundle(
        questions=questions,
        context=context,
        can_proceed_without=True,
    )
