"""Constraints input component for ProcessIQ UI.

Collects business constraints that limit optimization suggestions:
- Budget limits
- Hiring restrictions
- Compliance requirements
- Timeline constraints
- Priority trade-offs
"""

import contextlib
import logging

import streamlit as st

from processiq.models import Constraints, Priority
from processiq.ui.state import get_constraints, set_constraints

logger = logging.getLogger(__name__)

# User-friendly labels for priorities
PRIORITY_LABELS = {
    Priority.COST_REDUCTION: "Cost Reduction",
    Priority.TIME_REDUCTION: "Time Reduction",
    Priority.QUALITY_IMPROVEMENT: "Quality Improvement",
    Priority.COMPLIANCE: "Compliance",
}


def render_constraints_input() -> None:
    """Render the constraints input section."""
    st.markdown("### Constraints")
    st.markdown(
        "*Define the boundaries for recommendations. "
        "Suggestions that violate constraints will be filtered or flagged.*"
    )

    # Get current constraints or defaults
    current = get_constraints()

    col1, col2 = st.columns(2)

    with col1:
        # Budget limit
        has_budget = st.checkbox(
            "Has budget limit",
            value=current.budget_limit is not None if current else False,
            key="has_budget_limit",
        )

        budget_limit = None
        if has_budget:
            budget_limit = st.number_input(
                "Budget Limit ($)",
                min_value=0,
                value=int(current.budget_limit)
                if current and current.budget_limit
                else 10000,
                step=1000,
                key="budget_limit",
                help="Maximum budget for implementation",
            )

        # Hiring constraint
        cannot_hire = st.checkbox(
            "Cannot hire new staff",
            value=current.cannot_hire if current else False,
            key="cannot_hire",
            help="Check if hiring is not an option",
        )

        # Audit trail requirement
        must_maintain_audit = st.checkbox(
            "Must maintain audit trail",
            value=current.must_maintain_audit_trail if current else False,
            key="must_maintain_audit",
            help="Required for compliance in regulated industries",
        )

    with col2:
        # Timeline constraint
        has_timeline = st.checkbox(
            "Has timeline constraint",
            value=current.max_implementation_weeks is not None if current else False,
            key="has_timeline",
        )

        max_weeks = None
        if has_timeline:
            max_weeks = st.number_input(
                "Max Implementation (weeks)",
                min_value=1,
                max_value=52,
                value=current.max_implementation_weeks
                if current and current.max_implementation_weeks
                else 8,
                key="max_weeks",
                help="Maximum time for implementation",
            )

        # Error rate tolerance
        max_error_increase = st.number_input(
            "Max Error Rate Increase (%)",
            min_value=0.0,
            max_value=100.0,
            value=current.max_error_rate_increase_pct if current else 0.0,
            step=1.0,
            key="max_error_increase",
            help="Maximum acceptable increase in error rate from changes",
        )

    # Priority selection
    st.markdown("#### Optimization Priority")
    st.markdown("*What matters most? This affects how recommendations are ranked.*")

    priority_options = list(PRIORITY_LABELS.keys())

    current_priority_index = 0
    if current and current.priority:
        with contextlib.suppress(ValueError):
            current_priority_index = priority_options.index(current.priority)

    selected_priority = st.radio(
        "Primary goal",
        options=priority_options,
        format_func=lambda x: PRIORITY_LABELS[x],
        index=current_priority_index,
        key="priority",
        horizontal=True,
    )

    # Custom constraints (free text)
    st.markdown("#### Additional Constraints")
    custom_text = st.text_area(
        "Other constraints (one per line)",
        value="\n".join(current.custom_constraints)
        if current and current.custom_constraints
        else "",
        key="custom_constraints",
        placeholder="e.g., Cannot change vendor systems\nMust complete before Q4",
        height=100,
    )

    custom_constraints = [
        line.strip() for line in custom_text.split("\n") if line.strip()
    ]

    # Build and save constraints
    constraints = Constraints(
        budget_limit=float(budget_limit) if budget_limit else None,
        cannot_hire=cannot_hire,
        max_error_rate_increase_pct=max_error_increase,
        must_maintain_audit_trail=must_maintain_audit,
        max_implementation_weeks=max_weeks,
        priority=selected_priority,
        custom_constraints=custom_constraints,
    )

    set_constraints(constraints)

    # Show summary
    _render_constraints_summary(constraints)


def _render_constraints_summary(constraints: Constraints) -> None:
    """Render a summary of active constraints."""
    active = []

    if constraints.budget_limit:
        active.append(f"Budget: ${constraints.budget_limit:,.0f}")

    if constraints.cannot_hire:
        active.append("No hiring")

    if constraints.must_maintain_audit_trail:
        active.append("Audit trail required")

    if constraints.max_implementation_weeks:
        active.append(f"Timeline: {constraints.max_implementation_weeks} weeks")

    if constraints.max_error_rate_increase_pct > 0:
        active.append(f"Max error increase: {constraints.max_error_rate_increase_pct}%")

    if constraints.custom_constraints:
        active.append(f"+{len(constraints.custom_constraints)} custom")

    if active:
        st.markdown(
            f"**Active constraints:** {' | '.join(active)} | "
            f"**Priority:** {PRIORITY_LABELS[constraints.priority]}"
        )
