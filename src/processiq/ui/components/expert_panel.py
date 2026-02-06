"""Expert mode panel for ProcessIQ UI.

Shows persistent data view with editing capabilities when expert mode is enabled.
Displays:
- Current ProcessData in editable table
- Confidence scores per field
- Reasoning trace (if available)
- Quick edit controls
"""

import logging
from collections.abc import Callable
from typing import Any

import pandas as pd
import streamlit as st

from processiq.analysis import calculate_confidence
from processiq.models import ProcessData, ProcessStep
from processiq.ui.styles import COLORS, get_confidence_color

logger = logging.getLogger(__name__)


def render_expert_panel(
    process_data: ProcessData | None,
    constraints: Any | None = None,
    profile: Any | None = None,
    analysis_result: Any | None = None,
    reasoning_trace: list[str] | None = None,
    on_data_change: Callable[[ProcessData], None] | None = None,
) -> ProcessData | None:
    """Render the expert mode panel.

    Args:
        process_data: Current process data (can be None).
        constraints: Current constraints.
        profile: Current business profile.
        analysis_result: Analysis results if available.
        reasoning_trace: Reasoning trace from analysis.
        on_data_change: Callback when data is edited.

    Returns:
        Updated ProcessData if edited, otherwise original.
    """
    st.markdown(
        f"""
        <div style="
            padding: 0.75rem;
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 0.375rem;
            margin-bottom: 1rem;
        ">
            <div style="
                font-size: 0.875rem;
                font-weight: 600;
                color: {COLORS['text']};
                margin-bottom: 0.25rem;
            ">
                Expert Mode
            </div>
            <div style="font-size: 0.75rem; color: {COLORS['text_muted']};">
                View and edit extracted data directly
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Tab layout for different sections
    if process_data:
        tab_data, tab_confidence, tab_trace = st.tabs(
            ["Process Data", "Confidence", "Reasoning"]
        )

        with tab_data:
            updated_data = _render_data_editor(process_data)
            if updated_data != process_data and on_data_change:
                on_data_change(updated_data)
            process_data = updated_data

        with tab_confidence:
            _render_confidence_details(process_data, constraints, profile)

        with tab_trace:
            _render_reasoning_trace(reasoning_trace, analysis_result)
    else:
        st.info(
            "No process data extracted yet. Describe your process or upload a file."
        )

    return process_data


def _render_data_editor(process_data: ProcessData) -> ProcessData:
    """Render editable data table for process steps.

    Returns:
        Updated ProcessData (may be same object if no changes).
    """
    st.markdown("##### Process Steps")

    # Process metadata
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input(
            "Process Name",
            value=process_data.name,
            key="expert_process_name",
            label_visibility="collapsed",
        )
    with col2:
        st.markdown(
            f"<span style='color: {COLORS['text_muted']}; font-size: 0.75rem;'>"
            f"{len(process_data.steps)} steps | {process_data.total_time_hours:.1f}h total | "
            f"${process_data.total_cost:,.0f} total cost"
            f"</span>",
            unsafe_allow_html=True,
        )

    # Build editable dataframe
    rows = []
    for step in process_data.steps:
        rows.append(
            {
                "Step": step.step_name,
                "Time (h)": step.average_time_hours,
                "Resources": step.resources_needed,
                "Problem %": step.error_rate_pct,
                "Cost ($)": step.cost_per_instance,
                "Depends On": "; ".join(step.depends_on) if step.depends_on else "",
            }
        )

    df = pd.DataFrame(rows)

    # Use st.data_editor for in-place editing
    edited_df = st.data_editor(
        df,
        width="stretch",
        hide_index=True,
        num_rows="dynamic",
        key="expert_step_editor",
        column_config={
            "Step": st.column_config.TextColumn("Step", width="medium", required=True),
            "Time (h)": st.column_config.NumberColumn(
                "Time (h)", min_value=0.0, max_value=1000.0, step=0.25, format="%.2f"
            ),
            "Resources": st.column_config.NumberColumn(
                "Resources", min_value=1, max_value=100, step=1
            ),
            "Problem %": st.column_config.NumberColumn(
                "Problem %",
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                format="%.1f",
                help="How often does this step need rework or hit issues? (0-100%)",
            ),
            "Cost ($)": st.column_config.NumberColumn(
                "Cost ($)",
                min_value=0.0,
                step=10.0,
                format="$%.2f",
                help="Total cost per execution — labor, computing, materials, etc.",
            ),
            "Depends On": st.column_config.TextColumn(
                "Depends On", width="medium", help="Semicolon-separated step names"
            ),
        },
    )

    # Check if data changed
    if not df.equals(edited_df) or new_name != process_data.name:
        # Rebuild ProcessData from edited dataframe
        try:
            new_steps = []
            for _, row in edited_df.iterrows():
                step_name = str(row["Step"]).strip()
                if not step_name:
                    continue

                depends_on_str = str(row.get("Depends On", "") or "")
                depends_on = [s.strip() for s in depends_on_str.split(";") if s.strip()]

                new_steps.append(
                    ProcessStep(
                        step_name=step_name,
                        average_time_hours=float(row.get("Time (h)", 0) or 0),
                        resources_needed=int(row.get("Resources", 1) or 1),
                        error_rate_pct=float(row.get("Problem %", 0) or 0),
                        cost_per_instance=float(row.get("Cost ($)", 0) or 0),
                        depends_on=depends_on,
                    )
                )

            if new_steps:
                return ProcessData(
                    name=new_name or process_data.name,
                    description=process_data.description,
                    steps=new_steps,
                )
        except Exception as e:
            logger.warning("Failed to update process data from editor: %s", e)
            st.error(f"Invalid data: {e}")

    return process_data


def _render_confidence_details(
    process_data: ProcessData,
    constraints: Any | None,
    profile: Any | None,
) -> None:
    """Render detailed confidence breakdown per field."""
    st.markdown("##### Data Completeness")

    confidence_result = calculate_confidence(
        process=process_data,
        constraints=constraints,
        profile=profile,
    )

    # Overall score
    color = get_confidence_color(confidence_result.score)
    st.markdown(
        f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
        ">
            <div style="
                font-size: 1.5rem;
                font-weight: 600;
                color: {color};
            ">
                {confidence_result.score * 100:.0f}%
            </div>
            <div style="font-size: 0.875rem; color: {COLORS['text_muted']};">
                {confidence_result.level.replace('_', ' ').title()}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Breakdown by category
    breakdown = confidence_result.breakdown

    col1, col2, col3 = st.columns(3)

    with col1:
        process_score = breakdown.get("process_completeness", 0)
        st.markdown(
            f"<div style='font-size: 0.75rem; color: {COLORS['text_muted']};'>Process</div>",
            unsafe_allow_html=True,
        )
        st.progress(process_score)

    with col2:
        constraints_score = breakdown.get("constraints_completeness", 0)
        st.markdown(
            f"<div style='font-size: 0.75rem; color: {COLORS['text_muted']};'>Constraints</div>",
            unsafe_allow_html=True,
        )
        st.progress(constraints_score)

    with col3:
        profile_score = breakdown.get("profile_completeness", 0)
        st.markdown(
            f"<div style='font-size: 0.75rem; color: {COLORS['text_muted']};'>Context</div>",
            unsafe_allow_html=True,
        )
        st.progress(profile_score)

    # Per-step confidence indicators
    st.markdown("##### Field Coverage by Step")

    step_coverage = []
    for step in process_data.steps:
        filled_fields = 0
        total_fields = 5  # time, resources, error_rate, cost, depends_on

        if step.average_time_hours > 0:
            filled_fields += 1
        if step.resources_needed > 0:
            filled_fields += 1
        if step.error_rate_pct > 0:
            filled_fields += 1
        if step.cost_per_instance > 0:
            filled_fields += 1
        if step.depends_on:
            filled_fields += 1

        step_coverage.append(
            {
                "Step": step.step_name,
                "Coverage": f"{filled_fields}/{total_fields}",
                "Score": filled_fields / total_fields,
            }
        )

    coverage_df = pd.DataFrame(step_coverage)
    st.dataframe(
        coverage_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Score", min_value=0, max_value=1, format="%.0f%%"
            ),
        },
    )

    # Data gaps
    if confidence_result.data_gaps:
        with st.expander("Missing Data", expanded=False):
            for gap in confidence_result.data_gaps:
                st.markdown(f"- {gap}")


def _render_reasoning_trace(
    reasoning_trace: list[str] | None,
    analysis_result: Any | None,
) -> None:
    """Render reasoning trace from analysis."""
    st.markdown("##### Analysis Reasoning")

    if reasoning_trace:
        for i, step in enumerate(reasoning_trace, 1):
            st.markdown(
                f"""
                <div style="
                    padding: 0.5rem;
                    background: {COLORS['surface']};
                    border-left: 2px solid {COLORS['primary']};
                    margin-bottom: 0.5rem;
                    font-size: 0.875rem;
                ">
                    <span style="color: {COLORS['text_muted']};">{i}.</span> {step}
                </div>
                """,
                unsafe_allow_html=True,
            )
    elif analysis_result:
        st.info("Analysis complete. Reasoning trace not available.")
    else:
        st.info("Run analysis to see reasoning trace.")

    # Show analysis metadata if available
    if analysis_result:
        with st.expander("Analysis Metadata", expanded=False):
            st.markdown(f"**Bottlenecks found:** {len(analysis_result.bottlenecks)}")
            st.markdown(
                f"**Suggestions generated:** {len(analysis_result.suggestions)}"
            )
            if analysis_result.summary:
                st.markdown("**Summary:**")
                st.markdown(analysis_result.summary)


def render_expert_panel_compact(
    process_data: ProcessData | None,
    confidence: float | None = None,
) -> None:
    """Render a compact version of expert panel for sidebar.

    Shows summary info without editing capability.
    """
    if not process_data:
        st.info("No data yet")
        return

    # Quick stats
    st.markdown(
        f"""
        <div style="font-size: 0.875rem; margin-bottom: 0.5rem;">
            <strong>{process_data.name}</strong>
        </div>
        <div style="font-size: 0.75rem; color: {COLORS['text_muted']};">
            {len(process_data.steps)} steps |
            {process_data.total_time_hours:.1f}h |
            ${process_data.total_cost:,.0f}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if confidence is not None:
        color = get_confidence_color(confidence)
        st.markdown(
            f"""
            <div style="
                margin-top: 0.5rem;
                font-size: 0.75rem;
                color: {color};
            ">
                Confidence: {confidence * 100:.0f}%
            </div>
            """,
            unsafe_allow_html=True,
        )

    # List steps
    with st.expander("Steps", expanded=False):
        for step in process_data.steps:
            st.markdown(f"- {step.step_name}")
