"""Export section component for ProcessIQ UI.

Provides export options for analysis results:
- CSV export (for Jira/Asana import)
- Summary text export
- Markdown export
"""

import logging
from datetime import UTC, datetime

import streamlit as st

from processiq.export import (
    export_analysis_csv,
    export_suggestions_csv,
    export_summary_markdown,
    export_summary_text,
)
from processiq.ui.state import get_analysis_result

logger = logging.getLogger(__name__)


def render_export_section() -> None:
    """Render the export section."""
    result = get_analysis_result()

    if not result:
        return

    st.markdown("### Export & Next Steps")

    # Export buttons
    col1, col2, col3 = st.columns(3)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M")
    process_slug = result.process_name.lower().replace(" ", "_")[:20]

    with col1:
        # CSV Export
        csv_data = export_analysis_csv(result)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"processiq_{process_slug}_{timestamp}.csv",
            mime="text/csv",
            help="Download results as CSV (compatible with Jira, Asana, Excel)",
        )

    with col2:
        # Text Summary Export
        text_data = export_summary_text(result)
        st.download_button(
            label="Download Summary",
            data=text_data,
            file_name=f"processiq_{process_slug}_{timestamp}.txt",
            mime="text/plain",
            help="Download as formatted text (for email, documents)",
        )

    with col3:
        # Markdown Export
        md_data = export_summary_markdown(result)
        st.download_button(
            label="Download Markdown",
            data=md_data,
            file_name=f"processiq_{process_slug}_{timestamp}.md",
            mime="text/markdown",
            help="Download as Markdown (for documentation, GitHub)",
        )

    # Suggestions-only CSV (for task import)
    if result.suggestions:
        st.markdown("")
        csv_suggestions = export_suggestions_csv(result.suggestions)
        st.download_button(
            label="Download Recommendations Only (CSV)",
            data=csv_suggestions,
            file_name=f"processiq_recommendations_{process_slug}_{timestamp}.csv",
            mime="text/csv",
            help="Just the recommendations - ready for project management tool import",
            type="secondary",
        )

    # Next steps section
    st.markdown("---")
    st.markdown("#### If This Were a Real Engagement...")

    st.markdown(
        """
        The next steps would typically include:

        1. **Validate assumptions** - Review the assumptions listed under each ROI estimate with stakeholders who have operational knowledge

        2. **Prioritize recommendations** - Based on your constraints and strategic priorities, select which recommendations to pursue first

        3. **Develop implementation plans** - For selected recommendations, create detailed project plans with timelines, resource requirements, and success metrics

        4. **Establish baselines** - Measure current performance metrics before implementing changes so you can track improvement

        5. **Plan for change management** - Consider training, communication, and support needs for affected teams
        """
    )

    # Quick copy of summary
    with st.expander("Quick Copy Summary", expanded=False):
        st.text_area(
            "Copy this summary:",
            value=export_summary_text(result),
            height=300,
            key="quick_copy_summary",
            label_visibility="collapsed",
        )
