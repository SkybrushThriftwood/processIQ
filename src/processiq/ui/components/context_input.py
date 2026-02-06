"""Business context input component for ProcessIQ UI.

Collects business context that influences recommendations:
- Industry
- Company size
- Regulatory environment
- Past improvements and rejected approaches
"""

import contextlib
import logging

import streamlit as st

from processiq.models import (
    BusinessProfile,
    CompanySize,
    Industry,
    RegulatoryEnvironment,
)
from processiq.ui.state import get_business_profile, set_business_profile

logger = logging.getLogger(__name__)

# User-friendly labels
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
    CompanySize.STARTUP: "Startup (< 50 employees)",
    CompanySize.SMALL: "Small (50-200 employees)",
    CompanySize.MID_MARKET: "Mid-Market (200-1000 employees)",
    CompanySize.ENTERPRISE: "Enterprise (> 1000 employees)",
}

REGULATORY_LABELS = {
    RegulatoryEnvironment.MINIMAL: "Minimal",
    RegulatoryEnvironment.MODERATE: "Moderate",
    RegulatoryEnvironment.STRICT: "Strict",
    RegulatoryEnvironment.HIGHLY_REGULATED: "Highly Regulated",
}


def render_context_input() -> None:
    """Render the business context input section."""
    st.markdown("### Business Context")
    st.markdown(
        "*Help the advisor understand your business environment. "
        "This improves recommendation relevance.*"
    )

    # Get current profile or create defaults
    current = get_business_profile()

    col1, col2 = st.columns(2)

    with col1:
        # Industry selection
        industry_options = list(INDUSTRY_LABELS.keys())
        current_industry_index = 0
        if current:
            with contextlib.suppress(ValueError):
                current_industry_index = industry_options.index(current.industry)

        industry = st.selectbox(
            "Industry",
            options=industry_options,
            format_func=lambda x: INDUSTRY_LABELS[x],
            index=current_industry_index,
            key="industry",
        )

        # Custom industry text when "Other" is selected
        custom_industry = ""
        if industry == Industry.OTHER:
            custom_industry = st.text_input(
                "Specify your industry",
                value=current.custom_industry if current else "",
                placeholder="e.g., Creative Agency, Logistics, Legal Services...",
                key="custom_industry",
            )

        # Company size
        size_options = list(COMPANY_SIZE_LABELS.keys())
        current_size_index = 0
        if current:
            with contextlib.suppress(ValueError):
                current_size_index = size_options.index(current.company_size)

        company_size = st.selectbox(
            "Company Size",
            options=size_options,
            format_func=lambda x: COMPANY_SIZE_LABELS[x],
            index=current_size_index,
            key="company_size",
        )

    with col2:
        # Regulatory environment
        reg_options = list(REGULATORY_LABELS.keys())
        current_reg_index = 1  # Default to Moderate
        if current:
            with contextlib.suppress(ValueError):
                current_reg_index = reg_options.index(current.regulatory_environment)

        regulatory = st.selectbox(
            "Regulatory Environment",
            options=reg_options,
            format_func=lambda x: REGULATORY_LABELS[x],
            index=current_reg_index,
            key="regulatory",
            help="How strictly regulated is your industry?",
        )

        # Preferred frameworks
        framework_options = [
            "Lean",
            "Six Sigma",
            "Theory of Constraints",
            "Agile",
            "Other",
        ]
        current_frameworks = current.preferred_frameworks if current else []
        preferred_frameworks = st.multiselect(
            "Preferred Frameworks (optional)",
            options=framework_options,
            default=[f for f in current_frameworks if f in framework_options],
            key="frameworks",
            help="Frameworks your organization responds well to",
        )

    # Historical context (collapsed by default since optional)
    with st.expander("Historical Context (optional)", expanded=False):
        st.markdown("*This helps avoid suggestions that have been tried or rejected.*")

        col1, col2 = st.columns(2)

        with col1:
            previous_text = st.text_area(
                "Previous Improvements",
                value="\n".join(current.previous_improvements) if current else "",
                key="previous_improvements",
                placeholder="e.g., Automated routing in 2023\nUpgraded CRM system",
                height=100,
            )
            previous_improvements = [
                line.strip() for line in previous_text.split("\n") if line.strip()
            ]

        with col2:
            rejected_text = st.text_area(
                "Rejected Approaches",
                value="\n".join(current.rejected_approaches) if current else "",
                key="rejected_approaches",
                placeholder="e.g., Offshore processing\nFull automation",
                height=100,
            )
            rejected_approaches = [
                line.strip() for line in rejected_text.split("\n") if line.strip()
            ]

        notes = st.text_area(
            "Additional Notes",
            value=current.notes if current else "",
            key="context_notes",
            placeholder="Any other context that might be relevant...",
            height=68,
        )

    # Build and save business profile
    profile = BusinessProfile(
        industry=industry,
        custom_industry=custom_industry,
        company_size=company_size,
        regulatory_environment=regulatory,
        preferred_frameworks=preferred_frameworks,
        previous_improvements=previous_improvements,
        rejected_approaches=rejected_approaches,
        notes=notes if "notes" in dir() else "",
    )

    set_business_profile(profile)

    # Show summary
    _render_context_summary(profile)


def _render_context_summary(profile: BusinessProfile) -> None:
    """Render a summary of the business context."""
    industry_label = profile.custom_industry or INDUSTRY_LABELS[profile.industry]
    summary_parts = [
        industry_label,
        COMPANY_SIZE_LABELS[profile.company_size].split(" (")[0],  # Just the label
        REGULATORY_LABELS[profile.regulatory_environment] + " regulation",
    ]

    if profile.preferred_frameworks:
        summary_parts.append(f"{len(profile.preferred_frameworks)} framework(s)")

    if profile.rejected_approaches:
        summary_parts.append(
            f"{len(profile.rejected_approaches)} rejected approach(es)"
        )

    st.markdown(f"**Context:** {' | '.join(summary_parts)}")
