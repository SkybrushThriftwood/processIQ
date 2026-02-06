"""Privacy notice component for ProcessIQ UI.

Provides transparency about data handling with two tiers:
- Simple version for non-technical users (default)
- Technical details for those who want them (expandable)
"""

import streamlit as st

from processiq.ui.styles import COLORS


def render_privacy_notice(expanded: bool = False) -> None:
    """Render the privacy notice with expandable technical details.

    Args:
        expanded: Whether to show the technical details by default.
    """
    # Simple version - always visible
    st.markdown(
        f"""
        <div style="
            padding: 0.75rem 1rem;
            background: {COLORS['background_alt']};
            border-radius: 0.375rem;
            border-left: 3px solid {COLORS['primary']};
            font-size: 0.875rem;
            color: {COLORS['text']};
        ">
            <strong>Your data stays private.</strong>
            Processing happens in your session only. Documents are not stored.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Technical details - expandable
    with st.expander("Technical details", expanded=expanded):
        st.markdown(
            """
            **How your data is handled:**

            - Documents are processed in-memory and discarded after extraction
            - No data is sent to third parties beyond the LLM API call
            - Session data is stored locally in your browser
            - You can clear all data at any time with the Reset button
            - For enterprise deployments, self-hosted LLM options are available

            **What is sent to the LLM:**

            - Extracted text from your documents (not the raw files)
            - Process descriptions you provide
            - No personal identifiers are included unless you add them

            **Data retention:**

            - Session data: Until you close the browser or click Reset
            - Server-side: None (stateless processing)
            - LLM provider: Subject to their data retention policy
            """
        )


def render_privacy_notice_compact() -> None:
    """Render a compact privacy notice for sidebar use."""
    st.markdown(
        f"""
        <div style="
            font-size: 0.75rem;
            color: {COLORS['text_muted']};
            padding: 0.5rem 0;
        ">
            Your data stays private. Documents are processed in-session and not stored.
            <a href="#" onclick="return false;" style="color: {COLORS['primary']};">Learn more</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_privacy_badge() -> None:
    """Render a small privacy badge for the header area."""
    st.markdown(
        f"""
        <span style="
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.25rem 0.5rem;
            background: {COLORS['background_alt']};
            border: 1px solid {COLORS['border']};
            border-radius: 9999px;
            font-size: 0.75rem;
            color: {COLORS['text_muted']};
        ">
            <span style="color: {COLORS['success']};">&#9679;</span>
            Private
        </span>
        """,
        unsafe_allow_html=True,
    )
