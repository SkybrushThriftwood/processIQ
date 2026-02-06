"""ProcessIQ - AI-powered process optimization advisor.

Main entry point. Run with: streamlit run app.py
"""

import streamlit as st

from processiq.config import settings
from processiq.logging_config import setup_logging
from processiq.ui import (
    configure_page,
    init_session_state,
    is_reset_requested,
    render_header,
    render_input_area,
    render_main_content,
    render_sidebar,
    reset_conversation,
)


def main() -> None:
    """Main application entry point."""
    # Configure logging
    setup_logging(settings.log_level)

    # Configure page (must be first Streamlit call)
    configure_page()

    # Initialize session state
    init_session_state()

    # Handle reset request
    if is_reset_requested():
        reset_conversation()
        st.rerun()

    # Render UI
    render_header()
    render_sidebar()
    render_main_content()
    render_input_area()


if __name__ == "__main__":
    main()
