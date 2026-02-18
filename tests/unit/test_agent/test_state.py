"""Tests for processiq.agent.state."""

from processiq.agent.state import create_initial_state


class TestCreateInitialState:
    def test_required_fields(self, simple_process):
        state = create_initial_state(process=simple_process)
        assert state["process"] is simple_process

    def test_defaults(self, simple_process):
        state = create_initial_state(process=simple_process)
        assert state["confidence_score"] == 0.0
        assert state["needs_clarification"] is False
        assert state["data_gaps"] == []
        assert state["messages"] == []
        assert state["reasoning_trace"] == []
        assert state["current_phase"] == "initialization"
        assert state["clarification_questions"] == []
        assert state["user_response"] is None
        assert state["error"] is None
        assert state["analysis_insight"] is None
        assert state["constraints"] is None
        assert state["profile"] is None
        assert state["analysis_mode"] is None
        assert state["llm_provider"] is None

    def test_with_optional_fields(
        self, simple_process, strict_constraints, minimal_profile
    ):
        state = create_initial_state(
            process=simple_process,
            constraints=strict_constraints,
            profile=minimal_profile,
            analysis_mode="balanced",
            llm_provider="anthropic",
        )
        assert state["constraints"] is strict_constraints
        assert state["profile"] is minimal_profile
        assert state["analysis_mode"] == "balanced"
        assert state["llm_provider"] == "anthropic"

    def test_preserves_process_data(self, creative_agency_process):
        state = create_initial_state(process=creative_agency_process)
        assert state["process"].name == "Creative Agency Project Workflow"
        assert len(state["process"].steps) == 13
