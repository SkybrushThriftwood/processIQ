"""Tests for processiq.analysis.metrics."""

import pytest

from processiq.analysis.metrics import (
    StepType,
    _infer_step_type,
    calculate_process_metrics,
    format_metrics_for_llm,
)
from processiq.models import ProcessData

# ---------------------------------------------------------------------------
# Step type inference
# ---------------------------------------------------------------------------


class TestInferStepType:
    def test_review(self):
        assert _infer_step_type("Review tasks by manager") == StepType.REVIEW

    def test_approval(self):
        assert _infer_step_type("Manager approval") == StepType.REVIEW

    def test_external_client(self):
        assert _infer_step_type("Client brings a new project") == StepType.EXTERNAL

    def test_external_feedback(self):
        assert _infer_step_type("Get feedback from client") == StepType.EXTERNAL

    def test_handoff_send(self):
        # "Send invoice to client" matches EXTERNAL ("client") before HANDOFF ("send")
        assert _infer_step_type("Send report to manager") == StepType.HANDOFF

    def test_handoff_share(self):
        assert _infer_step_type("Share files with employees") == StepType.HANDOFF

    def test_creative_solution(self):
        assert _infer_step_type("Work on the solution") == StepType.CREATIVE

    def test_creative_design(self):
        assert _infer_step_type("Design the prototype") == StepType.CREATIVE

    def test_admin_invoice(self):
        assert _infer_step_type("Generate invoice") == StepType.ADMINISTRATIVE

    def test_processing_task(self):
        # "Create tasks" matches CREATIVE ("create") before PROCESSING ("task")
        assert _infer_step_type("Prepare the data") == StepType.PROCESSING

    def test_unknown(self):
        assert _infer_step_type("Xyz blorp") == StepType.UNKNOWN

    def test_case_insensitive(self):
        assert _infer_step_type("REVIEW THE DOCUMENT") == StepType.REVIEW

    def test_priority_order_review_over_external(self):
        # "Review" patterns checked before "external"
        # A step with "review" should be classified as REVIEW even if it also matches external
        assert _infer_step_type("Review client feedback") == StepType.REVIEW


# ---------------------------------------------------------------------------
# Metrics calculation
# ---------------------------------------------------------------------------


class TestCalculateProcessMetrics:
    def test_step_count(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        assert metrics.step_count == 3

    def test_totals(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        assert metrics.total_time_hours == pytest.approx(3.5)
        assert metrics.total_cost == pytest.approx(175.0)

    def test_process_name(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        assert metrics.process_name == "Simple Process"

    def test_time_percentages(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        # Step B: 2h / 3.5h = ~57.1%
        step_b = next(s for s in metrics.steps if s.step_name == "Step B")
        assert step_b.time_pct == pytest.approx(2.0 / 3.5 * 100, rel=0.01)

    def test_cost_percentages(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        # Step B: $100 / $175 = ~57.1%
        step_b = next(s for s in metrics.steps if s.step_name == "Step B")
        assert step_b.cost_pct == pytest.approx(100.0 / 175.0 * 100, rel=0.01)

    def test_longest_flag(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        step_b = next(s for s in metrics.steps if s.step_name == "Step B")
        step_a = next(s for s in metrics.steps if s.step_name == "Step A")
        assert step_b.is_longest is True
        assert step_a.is_longest is False

    def test_most_expensive_flag(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        step_b = next(s for s in metrics.steps if s.step_name == "Step B")
        assert step_b.is_most_expensive is True

    def test_zero_cost_no_division_error(self, zero_cost_process):
        metrics = calculate_process_metrics(zero_cost_process)
        # All cost_pct should be 0, no ZeroDivisionError
        for step in metrics.steps:
            assert step.cost_pct == 0.0

    def test_zero_cost_most_expensive_flag(self, zero_cost_process):
        metrics = calculate_process_metrics(zero_cost_process)
        # When max_cost is 0, no step should be flagged
        for step in metrics.steps:
            assert step.is_most_expensive is False

    def test_dependency_counts(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        step_a = next(s for s in metrics.steps if s.step_name == "Step A")
        step_c = next(s for s in metrics.steps if s.step_name == "Step C")
        # Step A has downstream (B depends on it, C transitively)
        assert step_a.downstream_count >= 2
        # Step C has upstream (depends on B, transitively on A)
        assert step_c.upstream_count >= 2

    def test_data_quality_flags(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        assert metrics.has_all_times is True
        assert metrics.has_all_costs is True
        assert metrics.has_error_rates is False  # No error rates set
        assert metrics.has_dependencies is True

    def test_data_quality_no_dependencies(self, zero_cost_process):
        metrics = calculate_process_metrics(zero_cost_process)
        assert metrics.has_dependencies is False
        assert metrics.has_all_costs is False

    def test_creative_agency_canonical(self, creative_agency_process):
        """Canonical test: creative agency process metrics."""
        metrics = calculate_process_metrics(creative_agency_process)

        assert metrics.step_count == 13
        assert metrics.total_time_hours == pytest.approx(14.0, abs=0.1)

        # "Work on the solution" should be flagged as longest AND creative
        work_step = next(
            s for s in metrics.steps if "Work on the solution" in s.step_name
        )
        assert work_step.is_longest is True
        assert work_step.step_type == StepType.CREATIVE

        # At least 2 review steps
        assert metrics.patterns.review_step_count >= 2

        # At least 4 external touchpoints (client-related)
        assert metrics.patterns.external_touchpoints >= 4

    def test_sequential_chain_length(self, creative_agency_process):
        metrics = calculate_process_metrics(creative_agency_process)
        # The longest chain goes through all 13 steps (minus the branching at invoice)
        assert metrics.patterns.sequential_chain_length >= 10

    def test_empty_process(self):
        """Edge case: ProcessData requires min 1 step, but calculate handles empty."""
        process = ProcessData.__new__(ProcessData)
        object.__setattr__(process, "name", "Empty")
        object.__setattr__(process, "description", "")
        object.__setattr__(process, "steps", [])

        metrics = calculate_process_metrics(process)
        assert metrics.step_count == 0
        assert metrics.total_time_hours == 0
        assert metrics.total_cost == 0


# ---------------------------------------------------------------------------
# Format for LLM
# ---------------------------------------------------------------------------


class TestFormatMetricsForLlm:
    def test_contains_step_names(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        formatted = format_metrics_for_llm(metrics)
        assert "Step A" in formatted
        assert "Step B" in formatted
        assert "Step C" in formatted

    def test_contains_longest_flag(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        formatted = format_metrics_for_llm(metrics)
        assert "longest" in formatted

    def test_contains_costly_flag(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        formatted = format_metrics_for_llm(metrics)
        assert "costly" in formatted

    def test_contains_patterns_section(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        formatted = format_metrics_for_llm(metrics)
        assert "Patterns Detected" in formatted

    def test_contains_data_quality_section(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        formatted = format_metrics_for_llm(metrics)
        assert "Data Quality" in formatted

    def test_contains_process_name(self, simple_process):
        metrics = calculate_process_metrics(simple_process)
        formatted = format_metrics_for_llm(metrics)
        assert "Simple Process" in formatted

    def test_creative_agency_formatting(self, creative_agency_process):
        metrics = calculate_process_metrics(creative_agency_process)
        formatted = format_metrics_for_llm(metrics)
        assert "Work on the solution" in formatted
        assert "creative" in formatted
        assert "review" in formatted
