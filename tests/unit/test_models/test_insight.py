"""Tests for processiq.models.insight."""

import pytest
from pydantic import ValidationError

from processiq.models import (
    AnalysisInsight,
    AnalysisRequest,
    Issue,
    NotAProblem,
    Recommendation,
)


class TestIssue:
    def test_valid_creation(self):
        issue = Issue(
            title="Slow approval",
            description="Takes 3 days on average",
            severity="high",
        )
        assert issue.title == "Slow approval"
        assert issue.severity == "high"

    def test_defaults(self):
        issue = Issue(
            title="Test",
            description="Desc",
            severity="low",
        )
        assert issue.affected_steps == []
        assert issue.root_cause_hypothesis == ""
        assert issue.evidence == []

    def test_severity_must_be_literal(self):
        with pytest.raises(ValidationError):
            Issue(
                title="Test",
                description="Desc",
                severity="critical",  # not in Literal["high", "medium", "low"]
            )

    def test_title_max_length(self):
        with pytest.raises(ValidationError):
            Issue(
                title="x" * 101,
                description="Desc",
                severity="low",
            )

    def test_title_min_length(self):
        with pytest.raises(ValidationError):
            Issue(
                title="",
                description="Desc",
                severity="low",
            )


class TestRecommendation:
    def test_valid_creation(self):
        rec = Recommendation(
            title="Automate step",
            addresses_issue="Slow approval",
            description="Use workflow tool",
            expected_benefit="2 hours saved",
            feasibility="easy",
        )
        assert rec.feasibility == "easy"

    def test_feasibility_must_be_literal(self):
        with pytest.raises(ValidationError):
            Recommendation(
                title="Test",
                addresses_issue="Issue",
                description="Desc",
                expected_benefit="Benefit",
                feasibility="impossible",
            )

    def test_defaults(self):
        rec = Recommendation(
            title="Test",
            addresses_issue="Issue",
            description="Desc",
            expected_benefit="Benefit",
            feasibility="moderate",
        )
        assert rec.risks == []
        assert rec.affected_steps == []
        assert rec.prerequisites == []
        assert rec.plain_explanation == ""
        assert rec.concrete_next_steps == []


class TestNotAProblem:
    def test_creation(self):
        nap = NotAProblem(
            step_name="Design",
            why_not_a_problem="Core creative work",
        )
        assert nap.step_name == "Design"
        assert nap.appears_problematic_because == ""


class TestAnalysisInsight:
    def test_defaults(self):
        insight = AnalysisInsight(
            process_summary="Simple process",
        )
        assert insight.patterns == []
        assert insight.issues == []
        assert insight.recommendations == []
        assert insight.not_problems == []
        assert insight.follow_up_questions == []
        assert insight.confidence_notes == ""
        assert insight.reasoning == ""

    def test_with_full_data(self, sample_insight):
        assert len(sample_insight.issues) == 1
        assert len(sample_insight.recommendations) == 1
        assert len(sample_insight.not_problems) == 1
        assert len(sample_insight.patterns) == 2


class TestAnalysisRequest:
    def test_defaults(self):
        req = AnalysisRequest(metrics_text="some metrics")
        assert req.industry is None
        assert req.constraints_summary is None
        assert req.user_concerns is None

    def test_with_all_fields(self):
        req = AnalysisRequest(
            metrics_text="metrics",
            industry="technology",
            constraints_summary="budget: $10k",
            user_concerns="Too slow",
        )
        assert req.industry == "technology"
