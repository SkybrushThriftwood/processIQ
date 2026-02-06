"""Header component for ProcessIQ UI."""

import streamlit as st


def render_header() -> None:
    """Render the application header.

    Shows app name, subtitle, and brief value proposition.
    Designed to communicate value in under 10 seconds.
    """
    st.title("ProcessIQ")
    st.markdown(
        "*AI-powered process optimization advisor with constraint-aware ROI estimates*"
    )

    st.markdown(
        """
        ProcessIQ analyzes your business processes to identify bottlenecks,
        evaluate constraints, and provide actionable recommendations with
        transparent ROI estimates. Every recommendation shows its assumptions
        and confidence level.
        """
    )

    st.divider()
