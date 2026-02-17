"""Tests for processiq.models.memory."""

from datetime import UTC, datetime

from processiq.models import (
    AnalysisMemory,
    BusinessProfile,
    CompanySize,
    Industry,
    RegulatoryEnvironment,
    RevenueRange,
)


class TestEnums:
    def test_industry_values(self):
        assert Industry.FINANCIAL_SERVICES.value == "financial_services"
        assert Industry.HEALTHCARE.value == "healthcare"
        assert Industry.OTHER.value == "other"
        assert len(Industry) == 8

    def test_company_size_values(self):
        assert CompanySize.STARTUP.value == "startup"
        assert CompanySize.ENTERPRISE.value == "enterprise"
        assert len(CompanySize) == 4

    def test_revenue_range_values(self):
        assert RevenueRange.UNDER_100K.value == "under_100k"
        assert RevenueRange.OVER_100M.value == "over_100m"
        assert RevenueRange.PREFER_NOT_TO_SAY.value == "prefer_not_to_say"
        assert len(RevenueRange) == 8

    def test_regulatory_environment_values(self):
        assert RegulatoryEnvironment.MINIMAL.value == "minimal"
        assert RegulatoryEnvironment.HIGHLY_REGULATED.value == "highly_regulated"
        assert len(RegulatoryEnvironment) == 4


class TestBusinessProfile:
    def test_defaults(self):
        p = BusinessProfile()
        assert p.industry is None
        assert p.custom_industry == ""
        assert p.company_size is None
        assert p.annual_revenue == RevenueRange.PREFER_NOT_TO_SAY
        assert p.regulatory_environment == RegulatoryEnvironment.MODERATE
        assert p.typical_constraints == []
        assert p.preferred_frameworks == []
        assert p.previous_improvements == []
        assert p.rejected_approaches == []
        assert p.notes == ""

    def test_with_all_fields(self, full_profile):
        assert full_profile.industry == Industry.FINANCIAL_SERVICES
        assert full_profile.company_size == CompanySize.ENTERPRISE
        assert full_profile.annual_revenue == RevenueRange.FROM_20M_TO_100M
        assert full_profile.regulatory_environment == RegulatoryEnvironment.HIGHLY_REGULATED
        assert len(full_profile.typical_constraints) == 2
        assert len(full_profile.rejected_approaches) == 1


class TestAnalysisMemory:
    def test_timestamp_auto_set(self):
        before = datetime.now(UTC)
        mem = AnalysisMemory(id="test-1", process_name="Test Process")
        after = datetime.now(UTC)
        assert before <= mem.timestamp <= after

    def test_acceptance_rate_no_suggestions(self):
        mem = AnalysisMemory(id="test-1", process_name="Test")
        assert mem.acceptance_rate == 0.0

    def test_acceptance_rate_all_accepted(self):
        mem = AnalysisMemory(
            id="test-1",
            process_name="Test",
            suggestions_accepted=["s1", "s2", "s3"],
            suggestions_rejected=[],
        )
        assert mem.acceptance_rate == 1.0

    def test_acceptance_rate_mixed(self):
        mem = AnalysisMemory(
            id="test-1",
            process_name="Test",
            suggestions_accepted=["s1", "s2"],
            suggestions_rejected=["s3"],
        )
        # 2 / (2+1) = 0.6667
        assert mem.acceptance_rate == pytest.approx(2 / 3)

    def test_defaults(self):
        mem = AnalysisMemory(id="test-1", process_name="Test")
        assert mem.bottlenecks_found == []
        assert mem.suggestions_offered == []
        assert mem.suggestions_accepted == []
        assert mem.suggestions_rejected == []
        assert mem.rejection_reasons == []
        assert mem.outcome_notes == ""


# Need pytest for approx
import pytest  # noqa: E402
