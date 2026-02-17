"""Tests for processiq.analysis.roi."""

import pytest

from processiq.analysis.roi import (
    DEFAULT_IMPROVEMENT_FACTORS,
    calculate_roi,
)
from processiq.models import (
    Bottleneck,
    ProcessData,
    ProcessStep,
    ROIEstimate,
    SeverityLevel,
    Suggestion,
    SuggestionType,
)


@pytest.fixture
def roi_process() -> ProcessData:
    """Process for ROI tests."""
    return ProcessData(
        name="ROI Test Process",
        steps=[
            ProcessStep(
                step_name="Manual Review",
                average_time_hours=2.0,
                cost_per_instance=100.0,
                error_rate_pct=5.0,
                resources_needed=1,
            ),
            ProcessStep(
                step_name="Data Entry",
                average_time_hours=1.0,
                cost_per_instance=50.0,
                error_rate_pct=10.0,
                resources_needed=1,
            ),
        ],
    )


@pytest.fixture
def review_bottleneck() -> Bottleneck:
    return Bottleneck(
        step_name="Manual Review",
        severity=SeverityLevel.HIGH,
        impact_score=0.8,
        reason="Slow and error-prone",
    )


@pytest.fixture
def automation_suggestion() -> Suggestion:
    return Suggestion(
        id="s1",
        bottleneck_step="Manual Review",
        suggestion_type=SuggestionType.AUTOMATION,
        title="Automate review",
        description="Use automated checks",
        estimated_cost=5000.0,
    )


@pytest.fixture
def elimination_suggestion() -> Suggestion:
    return Suggestion(
        id="s2",
        bottleneck_step="Manual Review",
        suggestion_type=SuggestionType.ELIMINATION,
        title="Eliminate review",
        description="Remove unnecessary step",
        estimated_cost=0.0,
    )


class TestDefaultImprovementFactors:
    def test_all_suggestion_types_covered(self):
        for st in SuggestionType:
            assert st in DEFAULT_IMPROVEMENT_FACTORS, f"Missing factors for {st}"

    def test_elimination_is_100_percent(self):
        factors = DEFAULT_IMPROVEMENT_FACTORS[SuggestionType.ELIMINATION]
        assert factors["time_reduction_pct"] == 1.0
        assert factors["error_reduction_pct"] == 1.0
        assert factors["cost_multiplier"] == 0.0


class TestCalculateRoi:
    def test_automation_positive_savings(
        self, automation_suggestion, review_bottleneck, roi_process
    ):
        roi = calculate_roi(automation_suggestion, review_bottleneck, roi_process)
        assert roi.likely > 0

    def test_pessimistic_less_than_likely(
        self, automation_suggestion, review_bottleneck, roi_process
    ):
        roi = calculate_roi(automation_suggestion, review_bottleneck, roi_process)
        assert roi.pessimistic <= roi.likely

    def test_likely_less_than_optimistic(
        self, automation_suggestion, review_bottleneck, roi_process
    ):
        roi = calculate_roi(automation_suggestion, review_bottleneck, roi_process)
        assert roi.likely <= roi.optimistic

    def test_elimination_higher_savings(
        self, elimination_suggestion, automation_suggestion, review_bottleneck, roi_process
    ):
        roi_elim = calculate_roi(elimination_suggestion, review_bottleneck, roi_process)
        roi_auto = calculate_roi(automation_suggestion, review_bottleneck, roi_process)
        # Elimination should save more (or equal) than automation
        assert roi_elim.likely >= roi_auto.likely

    def test_step_not_found_returns_empty(self, automation_suggestion, roi_process):
        missing_bottleneck = Bottleneck(
            step_name="Nonexistent Step",
            severity=SeverityLevel.LOW,
            impact_score=0.1,
            reason="test",
        )
        roi = calculate_roi(automation_suggestion, missing_bottleneck, roi_process)
        assert roi.likely == 0.0
        assert roi.confidence == 0.0

    def test_payback_months_calculated(
        self, automation_suggestion, review_bottleneck, roi_process
    ):
        roi = calculate_roi(automation_suggestion, review_bottleneck, roi_process)
        # Suggestion has estimated_cost=5000, so payback should be calculated
        assert roi.payback_months is not None
        assert roi.payback_months > 0

    def test_payback_months_none_when_no_cost(
        self, elimination_suggestion, review_bottleneck, roi_process
    ):
        roi = calculate_roi(elimination_suggestion, review_bottleneck, roi_process)
        # estimated_cost=0 means no payback period needed
        assert roi.payback_months is None

    def test_assumptions_populated(
        self, automation_suggestion, review_bottleneck, roi_process
    ):
        roi = calculate_roi(automation_suggestion, review_bottleneck, roi_process)
        assert len(roi.assumptions) >= 3  # At least executions, cost, time

    def test_confidence_passed_through(
        self, automation_suggestion, review_bottleneck, roi_process
    ):
        roi = calculate_roi(
            automation_suggestion, review_bottleneck, roi_process, confidence=0.9
        )
        assert roi.confidence == 0.9

    def test_custom_executions_per_year(
        self, automation_suggestion, review_bottleneck, roi_process
    ):
        roi_low = calculate_roi(
            automation_suggestion, review_bottleneck, roi_process,
            executions_per_year=100,
        )
        roi_high = calculate_roi(
            automation_suggestion, review_bottleneck, roi_process,
            executions_per_year=10000,
        )
        assert roi_high.likely > roi_low.likely

    def test_error_rate_included_in_savings(
        self, review_bottleneck, roi_process
    ):
        """Steps with error rates should include error cost savings."""
        suggestion = Suggestion(
            id="s1",
            bottleneck_step="Data Entry",
            suggestion_type=SuggestionType.TRAINING,
            title="Train staff",
            description="Reduce errors",
            estimated_cost=1000.0,
        )
        bottleneck = Bottleneck(
            step_name="Data Entry",
            severity=SeverityLevel.MEDIUM,
            impact_score=0.5,
            reason="High errors",
        )
        roi = calculate_roi(suggestion, bottleneck, roi_process)
        # Training has error_reduction_pct > 0, and Data Entry has 10% error rate
        assert roi.likely > 0
