"""Tests for processiq.models.analysis."""

import pytest
from pydantic import ValidationError

from processiq.models import (
    AnalysisResult,
    Bottleneck,
    ROIEstimate,
    SeverityLevel,
    Suggestion,
    SuggestionType,
)


class TestSeverityLevel:
    def test_values(self):
        assert SeverityLevel.LOW.value == "low"
        assert SeverityLevel.MEDIUM.value == "medium"
        assert SeverityLevel.HIGH.value == "high"
        assert SeverityLevel.CRITICAL.value == "critical"

    def test_member_count(self):
        assert len(SeverityLevel) == 4


class TestSuggestionType:
    def test_values(self):
        assert SuggestionType.AUTOMATION.value == "automation"
        assert SuggestionType.ELIMINATION.value == "elimination"
        assert SuggestionType.PARALLELIZATION.value == "parallelization"

    def test_member_count(self):
        assert len(SuggestionType) == 7


class TestBottleneck:
    def test_valid_creation(self):
        b = Bottleneck(
            step_name="Approval",
            severity=SeverityLevel.HIGH,
            impact_score=0.8,
            reason="Takes too long",
        )
        assert b.step_name == "Approval"
        assert b.impact_score == 0.8

    def test_impact_score_upper_bound(self):
        with pytest.raises(ValidationError):
            Bottleneck(
                step_name="X",
                severity=SeverityLevel.LOW,
                impact_score=1.5,
                reason="test",
            )

    def test_impact_score_lower_bound(self):
        with pytest.raises(ValidationError):
            Bottleneck(
                step_name="X",
                severity=SeverityLevel.LOW,
                impact_score=-0.1,
                reason="test",
            )

    def test_defaults(self):
        b = Bottleneck(
            step_name="X",
            severity=SeverityLevel.LOW,
            impact_score=0.5,
            reason="test",
        )
        assert b.downstream_impact == []
        assert b.metrics == {}


class TestROIEstimate:
    def test_expected_value_pert(self):
        roi = ROIEstimate(
            pessimistic=100.0,
            likely=200.0,
            optimistic=400.0,
            assumptions=["test"],
            confidence=0.7,
        )
        # PERT: (100 + 4*200 + 400) / 6 = 1300/6 ≈ 216.67
        assert roi.expected_value == pytest.approx(1300 / 6)

    def test_expected_value_symmetric(self):
        roi = ROIEstimate(
            pessimistic=200.0,
            likely=200.0,
            optimistic=200.0,
            assumptions=["test"],
            confidence=0.7,
        )
        assert roi.expected_value == pytest.approx(200.0)

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            ROIEstimate(
                pessimistic=0,
                likely=0,
                optimistic=0,
                assumptions=["test"],
                confidence=1.5,
            )

    def test_payback_months_default(self):
        roi = ROIEstimate(
            pessimistic=0,
            likely=0,
            optimistic=0,
            assumptions=["test"],
            confidence=0.5,
        )
        assert roi.payback_months is None

    def test_assumptions_required(self):
        with pytest.raises(ValidationError):
            ROIEstimate(
                pessimistic=0,
                likely=0,
                optimistic=0,
                assumptions=[],
                confidence=0.5,
            )


class TestSuggestion:
    def test_creation_with_defaults(self):
        s = Suggestion(
            id="s1",
            bottleneck_step="Review",
            suggestion_type=SuggestionType.AUTOMATION,
            title="Automate review",
            description="Use automated checks",
        )
        assert s.implementation_steps == []
        assert s.estimated_cost == 0.0
        assert s.roi is None
        assert s.reasoning == ""
        assert s.alternatives_considered == []


class TestAnalysisResult:
    def test_defaults(self):
        r = AnalysisResult(
            process_name="Test",
            overall_confidence=0.7,
        )
        assert r.bottlenecks == []
        assert r.suggestions == []
        assert r.data_gaps == []
        assert r.summary == ""
