"""Tests for processiq.agent.edges."""

from processiq.agent.edges import route_after_clarification, route_after_context_check


class TestRouteAfterContextCheck:
    def test_sufficient_routes_to_analyze(self):
        state = {"needs_clarification": False}
        assert route_after_context_check(state) == "analyze"

    def test_insufficient_routes_to_clarification(self):
        state = {"needs_clarification": True}
        assert route_after_context_check(state) == "request_clarification"

    def test_missing_key_defaults_to_analyze(self):
        state = {}
        assert route_after_context_check(state) == "analyze"


class TestRouteAfterClarification:
    def test_with_response_routes_to_check_context(self):
        state = {"user_response": "Some answer", "confidence_score": 0.3}
        assert route_after_clarification(state) == "check_context"

    def test_no_response_high_confidence_routes_to_analyze(self):
        state = {"user_response": None, "confidence_score": 0.5}
        assert route_after_clarification(state) == "analyze"

    def test_no_response_at_threshold_routes_to_analyze(self):
        state = {"user_response": None, "confidence_score": 0.4}
        assert route_after_clarification(state) == "analyze"

    def test_no_response_low_confidence_routes_to_check_context(self):
        state = {"user_response": None, "confidence_score": 0.3}
        assert route_after_clarification(state) == "check_context"

    def test_empty_response_treated_as_no_response(self):
        state = {"user_response": "", "confidence_score": 0.5}
        # Empty string is falsy, so treated as no response
        assert route_after_clarification(state) == "analyze"

    def test_missing_keys_defaults(self):
        state = {}
        # user_response defaults to None (falsy), confidence defaults to 0.0
        assert route_after_clarification(state) == "check_context"
