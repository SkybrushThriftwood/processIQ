"""Tests for processiq.analysis.confidence."""

import pytest

from processiq.analysis.confidence import (
    WEIGHT_CONSTRAINTS,
    WEIGHT_PROCESS,
    WEIGHT_PROFILE,
    ConfidenceResult,
    calculate_confidence,
    identify_critical_gaps,
)
from processiq.models import (
    BusinessProfile,
    CompanySize,
    Constraints,
    Industry,
    Priority,
    ProcessData,
    ProcessStep,
)


class TestConfidenceWeights:
    def test_weights_sum_to_one(self):
        total = WEIGHT_PROCESS + WEIGHT_CONSTRAINTS + WEIGHT_PROFILE
        assert total == pytest.approx(1.0)


class TestConfidenceResult:
    def test_level_high(self):
        r = ConfidenceResult(score=0.85)
        assert r.level == "high"

    def test_level_moderate(self):
        r = ConfidenceResult(score=0.65)
        assert r.level == "moderate"

    def test_level_low(self):
        r = ConfidenceResult(score=0.45)
        assert r.level == "low"

    def test_level_very_low(self):
        r = ConfidenceResult(score=0.3)
        assert r.level == "very low"

    def test_level_boundary_high(self):
        r = ConfidenceResult(score=0.8)
        assert r.level == "high"

    def test_level_boundary_moderate(self):
        r = ConfidenceResult(score=0.6)
        assert r.level == "moderate"

    def test_level_boundary_low(self):
        r = ConfidenceResult(score=0.4)
        assert r.level == "low"

    def test_is_sufficient_above_threshold(self, monkeypatch):
        from processiq import config

        monkeypatch.setattr(config.settings, "confidence_threshold", 0.6)
        r = ConfidenceResult(score=0.7)
        assert r.is_sufficient is True

    def test_is_sufficient_below_threshold(self, monkeypatch):
        from processiq import config

        monkeypatch.setattr(config.settings, "confidence_threshold", 0.6)
        r = ConfidenceResult(score=0.5)
        assert r.is_sufficient is False

    def test_is_sufficient_at_threshold(self, monkeypatch):
        from processiq import config

        monkeypatch.setattr(config.settings, "confidence_threshold", 0.6)
        r = ConfidenceResult(score=0.6)
        assert r.is_sufficient is True


class TestCalculateConfidence:
    def test_full_data_higher_score(self, simple_process, strict_constraints, full_profile):
        result = calculate_confidence(simple_process, strict_constraints, full_profile)
        assert result.score > 0.5

    def test_minimal_data_lower_score(self, single_step_process):
        result = calculate_confidence(single_step_process)
        # No constraints, no profile, minimal process
        assert result.score < 0.5

    def test_no_constraints_partial_score(self, simple_process):
        result = calculate_confidence(simple_process, constraints=None)
        # Constraints component should be 0.3 (partial)
        assert result.breakdown["constraints_completeness"] == 0.3

    def test_no_profile_minimal_score(self, simple_process):
        result = calculate_confidence(simple_process, profile=None)
        assert result.breakdown["profile_completeness"] == 0.2

    def test_constraints_increase_score(self, simple_process, strict_constraints):
        without = calculate_confidence(simple_process)
        with_c = calculate_confidence(simple_process, constraints=strict_constraints)
        assert with_c.score > without.score

    def test_profile_increases_score(self, simple_process, full_profile):
        without = calculate_confidence(simple_process)
        with_p = calculate_confidence(simple_process, profile=full_profile)
        assert with_p.score > without.score

    def test_data_gaps_populated(self, single_step_process):
        result = calculate_confidence(single_step_process)
        # Should have gaps for: no constraints, no profile, missing cost/error data
        assert len(result.data_gaps) > 0

    def test_suggestions_populated(self, single_step_process):
        result = calculate_confidence(single_step_process)
        assert len(result.suggestions_for_improvement) > 0

    def test_breakdown_has_all_components(self, simple_process):
        result = calculate_confidence(simple_process)
        assert "process_completeness" in result.breakdown
        assert "constraints_completeness" in result.breakdown
        assert "profile_completeness" in result.breakdown

    def test_score_between_0_and_1(self, creative_agency_process, strict_constraints, full_profile):
        result = calculate_confidence(
            creative_agency_process, strict_constraints, full_profile
        )
        assert 0.0 <= result.score <= 1.0

    def test_missing_cost_reduces_score(self):
        """Steps with zero cost reduce process completeness."""
        with_cost = ProcessData(
            name="With Cost",
            steps=[
                ProcessStep(
                    step_name="Step",
                    average_time_hours=1.0,
                    resources_needed=1,
                    cost_per_instance=50.0,
                ),
            ],
        )
        without_cost = ProcessData(
            name="No Cost",
            steps=[
                ProcessStep(
                    step_name="Step",
                    average_time_hours=1.0,
                    resources_needed=1,
                    cost_per_instance=0.0,
                ),
            ],
        )
        r1 = calculate_confidence(with_cost)
        r2 = calculate_confidence(without_cost)
        assert r1.breakdown["process_completeness"] > r2.breakdown["process_completeness"]


class TestIdentifyCriticalGaps:
    def test_critical_gaps_ordered_first(self):
        result = ConfidenceResult(
            score=0.5,
            data_gaps=[
                "No dependencies defined between steps",
                "cost for 'Step A'",
                "No business profile provided",
                "time for 'Step B'",
            ],
        )
        gaps = identify_critical_gaps(result)
        # "cost" and "time" gaps should come before "No dependencies"
        cost_idx = next(i for i, g in enumerate(gaps) if "cost" in g.lower())
        time_idx = next(i for i, g in enumerate(gaps) if "time" in g.lower())
        dep_idx = next(i for i, g in enumerate(gaps) if "dependencies" in g.lower())
        assert cost_idx < dep_idx
        assert time_idx < dep_idx

    def test_empty_gaps(self):
        result = ConfidenceResult(score=0.9, data_gaps=[])
        gaps = identify_critical_gaps(result)
        assert gaps == []

    def test_preserves_all_gaps(self):
        result = ConfidenceResult(
            score=0.5,
            data_gaps=["gap1", "cost gap", "gap2"],
        )
        gaps = identify_critical_gaps(result)
        assert len(gaps) == 3
