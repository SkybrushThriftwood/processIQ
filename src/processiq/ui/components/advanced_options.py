"""Advanced options panel for ProcessIQ UI.

Consolidates constraints, business context, and settings into a
collapsed sidebar panel. Hidden by default for the chat-first experience.
"""

import contextlib
import logging

import streamlit as st

from processiq.config import (
    ANALYSIS_MODE_BALANCED,
    ANALYSIS_MODE_COST,
    ANALYSIS_MODE_DEEP,
)
from processiq.models import (
    BusinessProfile,
    CompanySize,
    Constraints,
    Industry,
    Priority,
    RegulatoryEnvironment,
)

logger = logging.getLogger(__name__)

# User-friendly labels
PRIORITY_LABELS = {
    Priority.COST_REDUCTION: "Cost Reduction",
    Priority.TIME_REDUCTION: "Time Reduction",
    Priority.QUALITY_IMPROVEMENT: "Quality Improvement",
    Priority.COMPLIANCE: "Compliance",
}

INDUSTRY_LABELS = {
    Industry.FINANCIAL_SERVICES: "Financial Services",
    Industry.HEALTHCARE: "Healthcare",
    Industry.MANUFACTURING: "Manufacturing",
    Industry.RETAIL: "Retail",
    Industry.TECHNOLOGY: "Technology",
    Industry.GOVERNMENT: "Government",
    Industry.EDUCATION: "Education",
    Industry.OTHER: "Other",
}

COMPANY_SIZE_LABELS = {
    CompanySize.STARTUP: "Startup (< 50)",
    CompanySize.SMALL: "Small (50-200)",
    CompanySize.MID_MARKET: "Mid-Market (200-1000)",
    CompanySize.ENTERPRISE: "Enterprise (> 1000)",
}

REGULATORY_LABELS = {
    RegulatoryEnvironment.MINIMAL: "Minimal",
    RegulatoryEnvironment.MODERATE: "Moderate",
    RegulatoryEnvironment.STRICT: "Strict",
    RegulatoryEnvironment.HIGHLY_REGULATED: "Highly Regulated",
}

# Analysis mode options with user-friendly labels and descriptions
ANALYSIS_MODE_OPTIONS = {
    ANALYSIS_MODE_COST: {
        "label": "Cost-Optimized",
        "description": "Faster responses, lower API costs. Best for testing and iteration.",
    },
    ANALYSIS_MODE_BALANCED: {
        "label": "Balanced (Recommended)",
        "description": "Fast extraction, thorough analysis. Good balance of speed and quality.",
    },
    ANALYSIS_MODE_DEEP: {
        "label": "Deep Analysis",
        "description": "Best models everywhere. Most thorough but slower and higher cost.",
    },
}


def render_advanced_options(
    constraints: Constraints | None = None,
    profile: BusinessProfile | None = None,
    analysis_mode: str = ANALYSIS_MODE_BALANCED,
    llm_provider: str = "openai",
) -> tuple[Constraints | None, BusinessProfile | None, str, str]:
    """Render the advanced options panel in the sidebar.

    Args:
        constraints: Current constraints or None for defaults.
        profile: Current business profile or None for defaults.
        analysis_mode: Current analysis mode preset.
        llm_provider: Current LLM provider.

    Returns:
        Tuple of (updated_constraints, updated_profile, analysis_mode, llm_provider).
    """
    updated_constraints = constraints
    updated_profile = profile

    # LLM Provider selector
    provider_options = ["openai", "anthropic", "ollama"]
    provider_labels = {
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "ollama": "Ollama (local)",
    }
    current_provider_idx = (
        provider_options.index(llm_provider) if llm_provider in provider_options else 0
    )

    st.markdown("**LLM Provider**")
    new_provider = st.radio(
        "LLM Provider",
        options=provider_options,
        index=current_provider_idx,
        format_func=lambda x: provider_labels[x],
        label_visibility="collapsed",
        key="llm_provider_radio",
    )

    is_ollama = new_provider == "ollama"
    if is_ollama:
        st.caption("Local model: all modes use qwen3:8b")

    st.divider()

    # Analysis mode selector
    st.markdown("**Analysis Mode**")
    mode_options = list(ANALYSIS_MODE_OPTIONS.keys())
    current_index = (
        mode_options.index(analysis_mode) if analysis_mode in mode_options else 1
    )

    new_analysis_mode = st.radio(
        "Analysis Mode",
        options=mode_options,
        index=current_index,
        format_func=lambda x: ANALYSIS_MODE_OPTIONS[x]["label"],
        label_visibility="collapsed",
        key="analysis_mode_radio",
        disabled=is_ollama,
    )

    # Show description of selected mode
    if not is_ollama:
        st.caption(ANALYSIS_MODE_OPTIONS[new_analysis_mode]["description"])

    st.divider()

    # Constraints section
    with st.expander("Constraints", expanded=False):
        updated_constraints = _render_constraints_compact(constraints)

    # Business context section
    with st.expander("Business Context", expanded=False):
        updated_profile = _render_context_compact(profile)

    return updated_constraints, updated_profile, new_analysis_mode, new_provider


def _render_constraints_compact(constraints: Constraints | None) -> Constraints:
    """Render constraints in a compact sidebar format."""
    # Budget
    has_budget = st.checkbox(
        "Budget limit",
        value=constraints.budget_limit is not None if constraints else False,
        key="adv_has_budget",
    )
    budget_limit = None
    if has_budget:
        budget_limit = st.number_input(
            "Amount ($)",
            min_value=0,
            value=int(constraints.budget_limit)
            if constraints and constraints.budget_limit
            else 10000,
            step=1000,
            key="adv_budget",
            label_visibility="collapsed",
        )

    # Timeline
    has_timeline = st.checkbox(
        "Timeline limit",
        value=constraints.max_implementation_weeks is not None
        if constraints
        else False,
        key="adv_has_timeline",
    )
    max_weeks = None
    if has_timeline:
        max_weeks = st.number_input(
            "Weeks",
            min_value=1,
            max_value=52,
            value=constraints.max_implementation_weeks
            if constraints and constraints.max_implementation_weeks
            else 8,
            key="adv_weeks",
            label_visibility="collapsed",
        )

    # Quick toggles
    cannot_hire = st.checkbox(
        "Cannot hire",
        value=constraints.cannot_hire if constraints else False,
        key="adv_no_hire",
    )

    must_audit = st.checkbox(
        "Audit trail required",
        value=constraints.must_maintain_audit_trail if constraints else False,
        key="adv_audit",
    )

    # Priority
    priority_options = list(PRIORITY_LABELS.keys())
    current_index = 0
    if constraints and constraints.priority:
        with contextlib.suppress(ValueError):
            current_index = priority_options.index(constraints.priority)

    priority = st.selectbox(
        "Priority",
        options=priority_options,
        format_func=lambda x: PRIORITY_LABELS[x],
        index=current_index,
        key="adv_priority",
    )

    return Constraints(
        budget_limit=float(budget_limit) if budget_limit else None,
        cannot_hire=cannot_hire,
        must_maintain_audit_trail=must_audit,
        max_implementation_weeks=max_weeks,
        priority=priority,
        max_error_rate_increase_pct=constraints.max_error_rate_increase_pct
        if constraints
        else 0.0,
        custom_constraints=constraints.custom_constraints if constraints else [],
    )


def _render_context_compact(profile: BusinessProfile | None) -> BusinessProfile:
    """Render business context in a compact sidebar format."""
    # Industry
    industry_options = list(INDUSTRY_LABELS.keys())
    current_industry = 0
    if profile:
        with contextlib.suppress(ValueError):
            current_industry = industry_options.index(profile.industry)

    industry = st.selectbox(
        "Industry",
        options=industry_options,
        format_func=lambda x: INDUSTRY_LABELS[x],
        index=current_industry,
        key="adv_industry",
    )

    # Custom industry text when "Other" is selected
    custom_industry = ""
    if industry == Industry.OTHER:
        custom_industry = st.text_input(
            "Specify your industry",
            value=getattr(profile, "custom_industry", "") if profile else "",
            placeholder="e.g., Creative Agency, Logistics, Legal Services...",
            key="adv_custom_industry",
        )

    # Company size
    size_options = list(COMPANY_SIZE_LABELS.keys())
    current_size = 0
    if profile:
        with contextlib.suppress(ValueError):
            current_size = size_options.index(profile.company_size)

    company_size = st.selectbox(
        "Company Size",
        options=size_options,
        format_func=lambda x: COMPANY_SIZE_LABELS[x],
        index=current_size,
        key="adv_size",
    )

    # Regulatory
    reg_options = list(REGULATORY_LABELS.keys())
    current_reg = 1  # Moderate default
    if profile:
        with contextlib.suppress(ValueError):
            current_reg = reg_options.index(profile.regulatory_environment)

    regulatory = st.selectbox(
        "Regulation Level",
        options=reg_options,
        format_func=lambda x: REGULATORY_LABELS[x],
        index=current_reg,
        key="adv_regulatory",
    )

    return BusinessProfile(
        industry=industry,
        custom_industry=custom_industry,
        company_size=company_size,
        regulatory_environment=regulatory,
        preferred_frameworks=profile.preferred_frameworks if profile else [],
        previous_improvements=profile.previous_improvements if profile else [],
        rejected_approaches=profile.rejected_approaches if profile else [],
        notes=profile.notes if profile else "",
    )


def render_sidebar_footer() -> None:
    """Render footer items for the sidebar."""
    st.divider()

    if st.button(
        "Reset Conversation",
    ):
        # This triggers a rerun; the main app handles the actual reset
        st.session_state["reset_requested"] = True
        st.rerun()

    st.markdown(
        """
        <div style="font-size: 0.75rem; color: #64748b; text-align: center; margin-top: 1rem;">
        ProcessIQ v0.1
        </div>
        """,
        unsafe_allow_html=True,
    )
