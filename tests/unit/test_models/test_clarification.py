"""Tests for processiq.models.clarification."""

from processiq.models import (
    ClarificationBundle,
    ClarificationResponse,
    ClarifyingQuestion,
)


class TestClarifyingQuestion:
    def test_defaults(self):
        q = ClarifyingQuestion(id="q1", question="What industry?")
        assert q.input_type == "text"
        assert q.target_field is None
        assert q.options is None
        assert q.default is None
        assert q.hint is None
        assert q.required is False

    def test_select_input_type(self):
        q = ClarifyingQuestion(
            id="q1",
            question="Pick one",
            input_type="select",
            options=["A", "B", "C"],
        )
        assert q.input_type == "select"
        assert q.options == ["A", "B", "C"]

    def test_boolean_input_type(self):
        q = ClarifyingQuestion(
            id="q1",
            question="Is this regulated?",
            input_type="boolean",
        )
        assert q.input_type == "boolean"

    def test_number_input_type(self):
        q = ClarifyingQuestion(
            id="q1",
            question="How many employees?",
            input_type="number",
        )
        assert q.input_type == "number"


class TestClarificationResponse:
    def test_string_value(self):
        r = ClarificationResponse(question_id="q1", value="Technology")
        assert r.value == "Technology"
        assert r.skipped is False

    def test_float_value(self):
        r = ClarificationResponse(question_id="q1", value=42.5)
        assert r.value == 42.5

    def test_bool_value(self):
        r = ClarificationResponse(question_id="q1", value=True)
        assert r.value is True

    def test_none_value(self):
        r = ClarificationResponse(question_id="q1", value=None)
        assert r.value is None

    def test_skipped(self):
        r = ClarificationResponse(question_id="q1", value=None, skipped=True)
        assert r.skipped is True


class TestClarificationBundle:
    def test_defaults(self):
        b = ClarificationBundle()
        assert b.questions == []
        assert b.context == ""
        assert b.can_proceed_without is True

    def test_with_questions(self):
        b = ClarificationBundle(
            questions=[
                ClarifyingQuestion(id="q1", question="What industry?"),
            ],
            context="Need more info",
            can_proceed_without=False,
        )
        assert len(b.questions) == 1
        assert b.can_proceed_without is False
