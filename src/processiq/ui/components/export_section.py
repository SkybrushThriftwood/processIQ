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
    export_insight_csv,
    export_insight_markdown,
    export_insight_text,
    export_recommendations_csv,
)
from processiq.ui.state import get_analysis_insight

logger = logging.getLogger(__name__)


def render_export_section() -> None:
    """Render the export section."""
    insight = get_analysis_insight()

    if not insight:
        return

    st.markdown("### Export & Next Steps")

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M")

    col1, col2, col3 = st.columns(3)

    with col1:
        csv_data = export_insight_csv(insight)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"processiq_analysis_{timestamp}.csv",
            mime="text/csv",
            help="Download results as CSV (compatible with Jira, Asana, Excel)",
        )

    with col2:
        text_data = export_insight_text(insight)
        st.download_button(
            label="Download Summary",
            data=text_data,
            file_name=f"processiq_analysis_{timestamp}.txt",
            mime="text/plain",
            help="Download as formatted text (for email, documents)",
        )

    with col3:
        md_data = export_insight_markdown(insight)
        st.download_button(
            label="Download Markdown",
            data=md_data,
            file_name=f"processiq_analysis_{timestamp}.md",
            mime="text/markdown",
            help="Download as Markdown (for documentation, GitHub)",
        )

    # Recommendations-only CSV
    if insight.recommendations:
        st.markdown("")
        csv_recs = export_recommendations_csv(insight.recommendations)
        st.download_button(
            label="Download Recommendations Only (CSV)",
            data=csv_recs,
            file_name=f"processiq_recommendations_{timestamp}.csv",
            mime="text/csv",
            help="Just the recommendations - ready for project management tool import",
            type="secondary",
        )

    # Next steps
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

    # Quick copy
    with st.expander("Quick Copy Summary", expanded=False):
        st.text_area(
            "Copy this summary:",
            value=export_insight_text(insight),
            height=300,
            key="quick_copy_summary",
            label_visibility="collapsed",
        )
