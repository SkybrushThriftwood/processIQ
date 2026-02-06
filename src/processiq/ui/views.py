"""View rendering functions for ProcessIQ UI.

Contains all Streamlit rendering logic: header, sidebar, chat area, etc.
"""

import streamlit as st

from processiq.ui.components import (
    render_advanced_options,
    render_chat_history,
    render_chat_input,
    render_confirm_buttons,
    render_export_section,
    render_file_uploader,
    render_privacy_notice,
    render_results,
    render_sidebar_footer,
    render_welcome_message,
)
from processiq.ui.handlers import (
    execute_pending_analysis,
    execute_pending_input,
    handle_confirm_button,
    handle_estimate_button,
    handle_file_upload,
    handle_user_input,
)
from processiq.ui.state import (
    ChatState,
    get_analysis_insight,
    get_analysis_mode,
    get_analysis_result,
    get_business_profile,
    get_chat_state,
    get_constraints,
    get_llm_provider,
    get_messages,
    get_process_data,
    has_process_data_gaps,
    is_input_pending,
    set_analysis_mode,
    set_business_profile,
    set_constraints,
    set_llm_provider,
)
from processiq.ui.styles import COLORS, apply_custom_css


def configure_page() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="ProcessIQ",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_custom_css()


def render_header() -> None:
    """Render minimal header for chat-first UI."""
    st.markdown(
        f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1rem;
            border-bottom: 1px solid {COLORS['border']};
            margin-bottom: 1rem;
        ">
            <div>
                <h1 style="margin: 0; font-size: 1.5rem; color: {COLORS['text']};">
                    ProcessIQ
                </h1>
                <p style="margin: 0; font-size: 0.875rem; color: {COLORS['text_muted']};">
                    AI-powered process optimization advisor
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    """Render the sidebar with advanced options."""
    with st.sidebar:
        st.markdown("### Options")

        # Get current values
        constraints = get_constraints()
        profile = get_business_profile()
        analysis_mode = get_analysis_mode()
        llm_provider = get_llm_provider()

        # Render advanced options
        new_constraints, new_profile, new_mode, new_provider = render_advanced_options(
            constraints=constraints,
            profile=profile,
            analysis_mode=analysis_mode,
            llm_provider=llm_provider,
        )

        # Update state if changed
        set_constraints(new_constraints)
        set_business_profile(new_profile)
        set_analysis_mode(new_mode)
        set_llm_provider(new_provider)

        # Privacy notice
        st.divider()
        render_privacy_notice()

        # Footer
        render_sidebar_footer()


def render_chat_area() -> None:
    """Render the main chat area (guided mode - chat only)."""
    current_state = get_chat_state()
    messages = get_messages()

    # Show welcome message if no messages
    if current_state == ChatState.WELCOME and not messages:
        render_welcome_message()
    else:
        # Render message history
        render_chat_history(messages)

    # Handle pending input (deferred processing)
    if is_input_pending():
        # Show progress indicator while processing
        _render_processing_progress()

        # Execute pending input processing
        if execute_pending_input():
            st.rerun()
        return  # Don't render other UI elements while processing

    # Show confirm buttons if in confirming state
    if current_state == ChatState.CONFIRMING and get_process_data():
        show_estimate = has_process_data_gaps()
        confirmed, wants_estimate = render_confirm_buttons(
            show_estimate=show_estimate,
        )
        if confirmed:
            handle_confirm_button()
            st.rerun()
        if wants_estimate:
            handle_estimate_button()
            st.rerun()

    # Show results display if we have analysis (prefer insight over legacy result)
    if current_state == ChatState.RESULTS and (
        get_analysis_insight() or get_analysis_result()
    ):
        st.divider()
        render_results()
        st.divider()
        render_export_section()

    # Handle ANALYZING state
    if current_state == ChatState.ANALYZING:
        # Show progress indicator
        _render_analysis_progress()

        # Execute pending analysis
        if execute_pending_analysis():
            st.rerun()


def _render_processing_progress(
    title: str = "Processing...",
    subtitle: str = "Understanding your input",
) -> None:
    """Render a generic processing progress indicator.

    Args:
        title: Main progress message.
        subtitle: Secondary descriptive text.
    """
    st.markdown(
        f"""
        <div style="
            padding: 1rem;
            background: {COLORS['background_alt']};
            border-radius: 0.375rem;
            margin: 1rem 0;
        ">
            <div style="
                display: flex;
                align-items: center;
                gap: 0.75rem;
                margin-bottom: 0.75rem;
            ">
                <div style="
                    width: 1rem;
                    height: 1rem;
                    border: 2px solid {COLORS['primary']};
                    border-top-color: transparent;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                "></div>
                <span style="font-weight: 500; color: {COLORS['text']};">{title}</span>
            </div>
            <div style="
                font-size: 0.875rem;
                color: {COLORS['text_muted']};
                padding-left: 1.75rem;
            ">
                {subtitle}
            </div>
        </div>
        <style>
            @keyframes spin {{
                to {{ transform: rotate(360deg); }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_analysis_progress() -> None:
    """Render analysis progress with descriptive steps."""
    _render_processing_progress(
        title="Analyzing your process...",
        subtitle="Detecting bottlenecks and generating recommendations",
    )


def render_main_content() -> None:
    """Render main content area."""
    render_chat_area()


def render_input_area() -> None:
    """Render the input area with chat input and file upload."""
    current_state = get_chat_state()

    # Don't show input during analysis or while processing
    if current_state == ChatState.ANALYZING or is_input_pending():
        return

    # File upload
    col1, col2 = st.columns([4, 1])

    with col1:
        user_input = render_chat_input(
            placeholder=_get_input_placeholder(current_state),
            key="chat_input",
        )

    with col2:
        uploaded_file = render_file_uploader(key="file_upload")

    # Handle inputs
    if user_input:
        handle_user_input(user_input)
        st.rerun()

    # handle_file_upload returns True if file was processed, False if skipped
    if uploaded_file and handle_file_upload(uploaded_file):
        st.rerun()


def _get_input_placeholder(state: ChatState) -> str:
    """Get appropriate placeholder text for current state."""
    placeholders = {
        ChatState.WELCOME: "Describe your process or drop a file...",
        ChatState.GATHERING: "Add more details or drop a file...",
        ChatState.CONFIRMING: "Type 'confirm' to analyze, or describe changes...",
        ChatState.CLARIFYING: "Answer the question above...",
        ChatState.RESULTS: "Ask a follow-up question...",
        ChatState.CONTINUING: "Ask anything about the analysis...",
    }
    return placeholders.get(state, "Type a message...")
