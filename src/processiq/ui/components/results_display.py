"""Results display component for ProcessIQ UI.

New architecture (Phase 2): Summary-first, details expandable.

Displays analysis results in organized sections:
- Process summary (lead with insight, not data tables)
- Issues identified (with root cause hypotheses)
- Recommendations (linked to specific issues, with trade-offs)
- Core value work (what looks slow but isn't waste)
- Expandable details: patterns, data quality, reasoning trace

Supports both:
- AnalysisInsight (new LLM-based, preferred)
- AnalysisResult (legacy algorithm-based, fallback)
"""

import logging

import streamlit as st

from processiq.models import AnalysisInsight, AnalysisResult, Bottleneck, Suggestion
from processiq.models.insight import Issue, NotAProblem, Recommendation
from processiq.ui.state import (
    get_analysis_insight,
    get_analysis_result,
    get_reasoning_trace,
)
from processiq.ui.styles import COLORS, get_confidence_color, get_severity_color

logger = logging.getLogger(__name__)


def render_results() -> None:
    """Render the analysis results section.

    Prefers AnalysisInsight (new) over AnalysisResult (legacy).
    """
    insight = get_analysis_insight()
    result = get_analysis_result()

    if insight:
        _render_insight_results(insight)
    elif result:
        _render_legacy_results(result)
    else:
        st.info("No analysis results available. Run the analysis first.")


# =============================================================================
# NEW: AnalysisInsight rendering (summary-first, details expandable)
# =============================================================================


def _render_insight_results(insight: AnalysisInsight) -> None:
    """Render new LLM-based analysis insight."""
    # What I Found - lead with summary
    _render_insight_summary(insight)

    # Main opportunities (issues + recommendations together)
    _render_opportunities(insight)

    # Core value work (not problems)
    if insight.not_problems:
        _render_not_problems(insight.not_problems)

    # Expandable sections
    _render_expandable_details(insight)


def _render_insight_summary(insight: AnalysisInsight) -> None:
    """Render the insight summary - lead with what we found."""
    st.markdown("### What I Found")

    # Process summary
    if insight.process_summary:
        st.markdown(insight.process_summary)

    # Quick stats in subtle style
    col1, col2, col3 = st.columns(3)

    with col1:
        issue_count = len(insight.issues)
        high_severity = sum(1 for i in insight.issues if i.severity == "high")
        label = f"{issue_count} issue{'s' if issue_count != 1 else ''}"
        if high_severity:
            label += f" ({high_severity} significant)"
        st.caption(label)

    with col2:
        rec_count = len(insight.recommendations)
        st.caption(f"{rec_count} recommendation{'s' if rec_count != 1 else ''}")

    with col3:
        ok_count = len(insight.not_problems)
        if ok_count:
            st.caption(f"{ok_count} area{'s' if ok_count != 1 else ''} that look fine")

    st.markdown("---")


def _render_opportunities(insight: AnalysisInsight) -> None:
    """Render issues and their linked recommendations together."""
    if not insight.issues and not insight.recommendations:
        st.success("No significant issues identified in this process.")
        return

    st.markdown("### Main Opportunities")

    # Build a map of issue title -> recommendations
    issue_to_recs: dict[str, list[Recommendation]] = {}
    unlinked_recs: list[Recommendation] = []

    for rec in insight.recommendations:
        if rec.addresses_issue:
            if rec.addresses_issue not in issue_to_recs:
                issue_to_recs[rec.addresses_issue] = []
            issue_to_recs[rec.addresses_issue].append(rec)
        else:
            unlinked_recs.append(rec)

    # Render each issue with its recommendations
    for i, issue in enumerate(insight.issues):
        _render_issue_with_recommendations(
            issue=issue,
            index=i + 1,
            recommendations=issue_to_recs.get(issue.title, []),
        )

    # Render any recommendations not linked to issues
    if unlinked_recs:
        st.markdown("#### Additional Recommendations")
        for i, rec in enumerate(unlinked_recs):
            _render_standalone_recommendation(rec, i + 1)


def _render_issue_with_recommendations(
    issue: Issue,
    index: int,
    recommendations: list[Recommendation],
) -> None:
    """Render an issue card with its linked recommendations."""
    severity_color = get_severity_color(issue.severity)

    # Issue container with colored left border
    st.markdown(
        f"""
        <div style="
            border-left: 4px solid {severity_color};
            padding-left: 1rem;
            margin-bottom: 1.5rem;
        ">
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 0.5rem;
            ">
                <h4 style="margin: 0; font-size: 1.1rem; color: {COLORS['text']};">
                    {index}. {issue.title}
                </h4>
                <span style="
                    display: inline-block;
                    padding: 0.125rem 0.5rem;
                    background: {severity_color}15;
                    color: {severity_color};
                    border-radius: 0.25rem;
                    font-size: 0.75rem;
                    font-weight: 500;
                    text-transform: uppercase;
                ">{issue.severity}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Description
    st.markdown(issue.description)

    # Affected steps
    if issue.affected_steps:
        st.caption(f"Affects: {', '.join(issue.affected_steps)}")

    # Root cause hypothesis (if meaningful)
    if issue.root_cause_hypothesis:
        with st.expander("Why this might be happening", expanded=False):
            st.markdown(issue.root_cause_hypothesis)
            if issue.evidence:
                st.markdown("**Evidence:**")
                for ev in issue.evidence:
                    st.markdown(f"- {ev}")

    # Linked recommendations
    if recommendations:
        st.markdown("**Suggested actions:**")
        for rec in recommendations:
            _render_recommendation_compact(rec)

    st.markdown("")  # Spacing


def _render_recommendation_compact(rec: Recommendation) -> None:
    """Render a recommendation in compact form (within an issue)."""
    # Feasibility indicator
    feasibility_icons = {
        "easy": "Low effort",
        "moderate": "Moderate effort",
        "complex": "High effort",
    }
    feasibility_text = feasibility_icons.get(rec.feasibility, rec.feasibility)

    st.markdown(f"**{rec.title}** ({feasibility_text})")
    st.markdown(rec.description)

    # Expected benefit
    if rec.expected_benefit:
        st.markdown(f"Expected benefit: {rec.expected_benefit}")

    # Progressive disclosure: plain explanation (Layer 2)
    if rec.plain_explanation:
        with st.expander("What this means in practice", expanded=False):
            st.markdown(rec.plain_explanation)

    # Progressive disclosure: concrete next steps (Layer 3)
    if rec.concrete_next_steps:
        with st.expander("How to get started", expanded=False):
            for i, step in enumerate(rec.concrete_next_steps, 1):
                st.markdown(f"{i}. {step}")

    # Trade-offs / risks
    if rec.risks:
        with st.expander("Trade-offs and risks", expanded=False):
            for risk in rec.risks:
                st.markdown(f"- {risk}")

    # Prerequisites
    if rec.prerequisites:
        with st.expander("Prerequisites", expanded=False):
            for prereq in rec.prerequisites:
                st.markdown(f"- {prereq}")


def _render_standalone_recommendation(rec: Recommendation, index: int) -> None:
    """Render a recommendation that isn't linked to a specific issue."""
    st.markdown(f"**{index}. {rec.title}**")
    st.caption(f"Feasibility: {rec.feasibility}")
    st.markdown(rec.description)

    if rec.expected_benefit:
        st.markdown(f"Expected benefit: {rec.expected_benefit}")

    # Progressive disclosure: plain explanation (Layer 2)
    if rec.plain_explanation:
        with st.expander("What this means in practice", expanded=False):
            st.markdown(rec.plain_explanation)

    # Progressive disclosure: concrete next steps (Layer 3)
    if rec.concrete_next_steps:
        with st.expander("How to get started", expanded=False):
            for i, step in enumerate(rec.concrete_next_steps, 1):
                st.markdown(f"{i}. {step}")

    if rec.risks:
        with st.expander("Trade-offs", expanded=False):
            for risk in rec.risks:
                st.markdown(f"- {risk}")

    st.markdown("---")


def _render_not_problems(not_problems: list[NotAProblem]) -> None:
    """Render the 'not problems' section - core value work that looks slow."""
    st.markdown("### Core Value Work")
    st.markdown(
        "_These steps may look like bottlenecks, but they're where real value is created:_"
    )

    for np in not_problems:
        st.markdown(
            f"""
            <div style="
                background: {COLORS['background_alt']};
                border-left: 4px solid {COLORS['success']};
                padding: 0.75rem 1rem;
                margin-bottom: 0.75rem;
                border-radius: 0 0.25rem 0.25rem 0;
            ">
                <strong>{np.step_name}</strong>
                <p style="margin: 0.5rem 0 0 0; color: {COLORS['text']};">
                    {np.why_not_a_problem}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Why it might look problematic
        if np.appears_problematic_because:
            st.caption(f"Why it might look slow: {np.appears_problematic_because}")

    st.markdown("---")


def _render_expandable_details(insight: AnalysisInsight) -> None:
    """Render expandable sections for patterns, data quality, etc."""
    # Patterns detected
    if insight.patterns:
        with st.expander("Patterns Detected", expanded=False):
            for pattern in insight.patterns:
                st.markdown(f"- {pattern}")

    # Follow-up questions (if LLM had any)
    if insight.follow_up_questions:
        with st.expander("Questions to Consider", expanded=False):
            st.markdown("_Answering these would help refine the analysis:_")
            for q in insight.follow_up_questions:
                st.markdown(f"- {q}")

    # Confidence notes / caveats
    if insight.confidence_notes:
        with st.expander("Analysis Caveats", expanded=False):
            st.markdown(insight.confidence_notes)

    # Reasoning trace
    _render_reasoning_trace()


# =============================================================================
# LEGACY: AnalysisResult rendering (kept for backward compatibility)
# =============================================================================


def _render_legacy_results(result: AnalysisResult) -> None:
    """Render legacy algorithm-based analysis results."""
    # Header with overall confidence
    _render_results_header(result)

    # Executive Summary
    _render_executive_summary(result)

    # Bottlenecks
    _render_bottlenecks(result.bottlenecks)

    # Recommendations
    _render_recommendations(result.suggestions)

    # Data gaps (if any)
    if result.data_gaps:
        _render_data_gaps(result.data_gaps)

    # Reasoning trace (collapsed)
    _render_reasoning_trace()


def _render_results_header(result: AnalysisResult) -> None:
    """Render the results header with key metrics."""
    st.markdown("### Analysis Results")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Process", result.process_name)

    with col2:
        st.metric("Bottlenecks", len(result.bottlenecks))

    with col3:
        st.metric("Recommendations", len(result.suggestions))

    with col4:
        # Confidence with color
        color = get_confidence_color(result.overall_confidence)
        st.markdown(
            f"""
            <div>
                <div style="color: #64748b; font-size: 0.875rem;">Confidence</div>
                <div style="color: {color}; font-size: 1.5rem; font-weight: 600;">{result.overall_confidence * 100:.0f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_executive_summary(result: AnalysisResult) -> None:
    """Render the executive summary section."""
    st.markdown("#### Executive Summary")

    if result.summary:
        st.markdown(result.summary)
    else:
        st.info("No summary available.")

    st.markdown("---")


def _render_bottlenecks(bottlenecks: list[Bottleneck]) -> None:
    """Render the bottlenecks section."""
    st.markdown(f"#### Key Bottlenecks ({len(bottlenecks)})")

    if not bottlenecks:
        st.success("No significant bottlenecks identified in this process.")
        return

    for i, bottleneck in enumerate(bottlenecks):
        _render_bottleneck_card(bottleneck, i)

    st.markdown("---")


def _render_bottleneck_card(bottleneck: Bottleneck, index: int) -> None:
    """Render a single bottleneck as a card."""
    severity_color = get_severity_color(bottleneck.severity.value)

    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{index + 1}. {bottleneck.step_name}**")

        with col2:
            # Severity badge
            st.markdown(
                f"""
                <span style="
                    display: inline-block;
                    padding: 0.125rem 0.5rem;
                    background: {severity_color}15;
                    color: {severity_color};
                    border-radius: 0.25rem;
                    font-size: 0.75rem;
                    font-weight: 500;
                    text-transform: uppercase;
                ">{bottleneck.severity.value}</span>
                """,
                unsafe_allow_html=True,
            )

        # Impact and reason
        col1, col2 = st.columns([1, 3])

        with col1:
            st.markdown(f"**Impact:** {bottleneck.impact_score:.2f}")

        with col2:
            st.markdown(bottleneck.reason)

        # Downstream impact
        if bottleneck.downstream_impact:
            st.caption(f"Affects: {', '.join(bottleneck.downstream_impact)}")

        # Metrics
        if bottleneck.metrics:
            metrics_str = " | ".join(
                [
                    f"{k.replace('_', ' ').title()}: {v:.1f}"
                    if isinstance(v, float)
                    else f"{k.replace('_', ' ').title()}: {v}"
                    for k, v in bottleneck.metrics.items()
                ]
            )
            st.caption(metrics_str)

        st.markdown("")  # Spacing


def _render_recommendations(suggestions: list[Suggestion]) -> None:
    """Render the recommendations section."""
    st.markdown(f"#### Recommendations ({len(suggestions)})")

    if not suggestions:
        st.info(
            "No recommendations generated. This may be due to constraint conflicts."
        )
        return

    for i, suggestion in enumerate(suggestions):
        _render_suggestion_card(suggestion, i)


def _render_suggestion_card(suggestion: Suggestion, index: int) -> None:
    """Render a single suggestion as a card."""
    with st.container():
        # Header with title and type
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{index + 1}. {suggestion.title}**")

        with col2:
            st.caption(suggestion.suggestion_type.value.replace("_", " ").title())

        # Description
        st.markdown(suggestion.description)

        # ROI section
        if suggestion.roi:
            roi = suggestion.roi
            confidence_color = get_confidence_color(roi.confidence)

            st.markdown("**ROI Estimate:**")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Pessimistic", f"${roi.pessimistic:,.0f}/yr")

            with col2:
                st.metric("Likely", f"${roi.likely:,.0f}/yr")

            with col3:
                st.metric("Optimistic", f"${roi.optimistic:,.0f}/yr")

            with col4:
                st.markdown(
                    f"""
                    <div>
                        <div style="color: #64748b; font-size: 0.875rem;">Confidence</div>
                        <div style="color: {confidence_color}; font-size: 1.25rem; font-weight: 600;">{roi.confidence * 100:.0f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Assumptions (important for trust)
            if roi.assumptions:
                with st.expander("Assumptions", expanded=False):
                    for assumption in roi.assumptions:
                        st.markdown(f"- {assumption}")

        # Implementation cost
        st.caption(f"Estimated implementation cost: ${suggestion.estimated_cost:,.0f}")

        # Implementation steps (collapsed)
        if suggestion.implementation_steps:
            with st.expander("Implementation Steps", expanded=False):
                for step in suggestion.implementation_steps:
                    st.markdown(f"1. {step}")

        # Reasoning (collapsed)
        if suggestion.reasoning:
            with st.expander("Why this recommendation?", expanded=False):
                st.markdown(suggestion.reasoning)
                if suggestion.alternatives_considered:
                    st.markdown("**Alternatives considered:**")
                    for alt in suggestion.alternatives_considered:
                        st.markdown(f"- {alt}")

        st.markdown("---")


def _render_data_gaps(gaps: list[str]) -> None:
    """Render the data gaps section."""
    with st.expander(f"Data Gaps ({len(gaps)})", expanded=False):
        st.markdown("*The following information would improve analysis accuracy:*")
        for gap in gaps:
            st.markdown(f"- {gap}")


def _render_reasoning_trace() -> None:
    """Render the reasoning trace section (collapsed by default)."""
    trace = get_reasoning_trace()

    if not trace:
        return

    with st.expander("Reasoning Trace (Agent Decisions)", expanded=False):
        st.markdown(
            "*This trace shows the agent's decision-making process for audit and review:*"
        )

        for i, entry in enumerate(trace):
            st.markdown(f"{i + 1}. {entry}")

        # Copy button for portfolio reviewers
        trace_text = "\n".join([f"{i + 1}. {entry}" for i, entry in enumerate(trace)])
        st.text_area(
            "Copy trace:",
            value=trace_text,
            height=100,
            key="trace_copy",
            label_visibility="collapsed",
        )
