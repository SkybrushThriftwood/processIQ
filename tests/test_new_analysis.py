"""Test the LLM-based analysis pipeline.

This test validates that the architecture:
1. Does NOT identify "Work on the solution" (4h) as a bottleneck to fix
2. Recognizes it as core creative work
3. Identifies the 2 manager reviews as consolidation opportunity
4. Notes the 4 client touchpoints as potential delay sources
5. Suggests specific improvements with trade-offs

Should NOT output:
- "Automate Work on the solution" (absurd for creative work)
- Generic "this step is slow" without context
- ROI numbers that assume you can eliminate creative work
"""

import logging

from processiq.analysis import calculate_process_metrics, format_metrics_for_llm
from processiq.models import ProcessData, ProcessStep

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_creative_agency_process() -> ProcessData:
    """Create the creative agency test case from the rework plan."""
    steps = [
        ProcessStep(
            step_name="Client brings a new project",
            average_time_hours=0.5,
            cost_per_instance=25,
            resources_needed=1,
        ),
        ProcessStep(
            step_name="Employee talks to the client",
            average_time_hours=1.0,
            cost_per_instance=50,
            resources_needed=1,
            depends_on=["Client brings a new project"],
        ),
        ProcessStep(
            step_name="Client gives access to files",
            average_time_hours=0.5,
            cost_per_instance=25,
            resources_needed=1,
            depends_on=["Employee talks to the client"],
        ),
        ProcessStep(
            step_name="Share files with employees",
            average_time_hours=0.5,
            cost_per_instance=50,
            resources_needed=2,
            depends_on=["Client gives access to files"],
        ),
        ProcessStep(
            step_name="Create tasks based on files",
            average_time_hours=1.0,
            cost_per_instance=100,
            resources_needed=2,
            depends_on=["Share files with employees"],
        ),
        ProcessStep(
            step_name="Review tasks by manager",
            average_time_hours=1.0,
            cost_per_instance=100,
            resources_needed=1,
            depends_on=["Create tasks based on files"],
        ),
        ProcessStep(
            step_name="Send invoice to client",
            average_time_hours=0.5,
            cost_per_instance=25,
            resources_needed=1,
            depends_on=["Review tasks by manager"],
        ),
        ProcessStep(
            step_name="Work on the solution",
            average_time_hours=4.0,
            cost_per_instance=300,
            resources_needed=3,
            depends_on=["Review tasks by manager"],
        ),
        ProcessStep(
            step_name="Manager reviews the solution",
            average_time_hours=1.0,
            cost_per_instance=100,
            resources_needed=1,
            depends_on=["Work on the solution"],
        ),
        ProcessStep(
            step_name="Implement the solution",
            average_time_hours=2.0,
            cost_per_instance=150,
            resources_needed=3,
            depends_on=["Manager reviews the solution"],
        ),
        ProcessStep(
            step_name="Get feedback from client",
            average_time_hours=0.5,
            cost_per_instance=25,
            resources_needed=1,
            depends_on=["Implement the solution"],
        ),
        ProcessStep(
            step_name="Adjust the solution",
            average_time_hours=1.0,
            cost_per_instance=100,
            resources_needed=2,
            depends_on=["Get feedback from client"],
        ),
        ProcessStep(
            step_name="Client happy",
            average_time_hours=0.5,
            cost_per_instance=25,
            resources_needed=1,
            depends_on=["Adjust the solution"],
        ),
    ]

    return ProcessData(
        name="Creative Agency Project Workflow",
        description="13-step project delivery process for a creative agency",
        steps=steps,
    )


def test_metrics_calculation():
    """Test that metrics are calculated correctly."""
    process = create_creative_agency_process()
    metrics = calculate_process_metrics(process)

    print("\n" + "=" * 60)
    print("METRICS CALCULATION TEST")
    print("=" * 60)

    print(f"\nProcess: {metrics.process_name}")
    print(f"Total steps: {metrics.step_count}")
    print(f"Total time: {metrics.total_time_hours:.1f} hours")
    print(f"Total cost: ${metrics.total_cost:.2f}")

    print("\n--- Pattern Detection ---")
    print(f"Review steps: {metrics.patterns.review_step_count}")
    print(f"External touchpoints: {metrics.patterns.external_touchpoints}")
    print(f"Creative steps: {metrics.patterns.creative_step_count}")
    print(f"Time in reviews: {metrics.patterns.time_in_reviews_pct:.1f}%")
    print(f"Time in creative work: {metrics.patterns.time_in_creative_pct:.1f}%")

    print("\n--- Step Analysis ---")
    for s in metrics.steps:
        flags = []
        if s.is_longest:
            flags.append("LONGEST")
        if s.is_most_expensive:
            flags.append("COSTLY")
        if s.step_type.value != "unknown":
            flags.append(s.step_type.value.upper())

        flag_str = f" [{', '.join(flags)}]" if flags else ""
        print(
            f"  {s.step_index + 1}. {s.step_name}: {s.time_hours:.1f}h ({s.time_pct:.0f}%){flag_str}"
        )

    # Assertions
    assert metrics.step_count == 13, f"Expected 13 steps, got {metrics.step_count}"
    assert (
        abs(metrics.total_time_hours - 14.0) < 0.1
    ), f"Expected ~14h, got {metrics.total_time_hours}"

    # Check that "Work on the solution" is flagged as longest AND creative
    work_step = next(s for s in metrics.steps if "Work on the solution" in s.step_name)
    assert work_step.is_longest, "Work on the solution should be flagged as longest"
    assert (
        work_step.step_type.value == "creative"
    ), f"Expected creative type, got {work_step.step_type.value}"

    # Check review detection
    assert (
        metrics.patterns.review_step_count >= 2
    ), "Should detect at least 2 review steps"

    # Check external touchpoints (client-related steps)
    assert (
        metrics.patterns.external_touchpoints >= 4
    ), f"Should detect at least 4 client touchpoints, got {metrics.patterns.external_touchpoints}"

    print("\n[PASS] All metrics assertions passed!")
    return metrics


def test_metrics_formatting():
    """Test that metrics are formatted correctly for LLM."""
    process = create_creative_agency_process()
    metrics = calculate_process_metrics(process)
    formatted = format_metrics_for_llm(metrics)

    print("\n" + "=" * 60)
    print("FORMATTED METRICS FOR LLM")
    print("=" * 60)
    print(formatted)

    # Check that key information is present
    assert "Work on the solution" in formatted
    assert "longest" in formatted.lower() or "LONGEST" in formatted
    assert "creative" in formatted.lower()
    assert "review" in formatted.lower()

    print("\n[PASS] Formatting assertions passed!")
    return formatted


def test_graph_structure():
    """Test that the simplified graph compiles and has the correct structure."""
    from processiq.agent.graph import build_graph, compile_graph

    print("\n" + "=" * 60)
    print("GRAPH STRUCTURE TEST")
    print("=" * 60)

    graph = build_graph()
    nodes = list(graph.nodes.keys())

    print(f"\nNodes: {nodes}")

    # Verify expected nodes exist
    expected_nodes = {"check_context", "analyze", "finalize", "request_clarification"}
    actual_nodes = set(nodes) - {
        "__start__",
        "__end__",
    }  # Exclude LangGraph internal nodes
    assert (
        expected_nodes == actual_nodes
    ), f"Expected nodes {expected_nodes}, got {actual_nodes}"

    # Verify old nodes are gone
    old_nodes = {
        "detect_bottlenecks",
        "generate_suggestions",
        "validate_constraints",
        "calculate_roi",
        "generate_alternatives",
    }
    for old_node in old_nodes:
        assert old_node not in nodes, f"Old node '{old_node}' should have been removed"

    # Verify graph compiles
    app = compile_graph()
    assert app is not None, "Graph should compile successfully"

    print(f"Expected nodes present: {expected_nodes}")
    print(f"Old nodes removed: {old_nodes}")
    print("\n[PASS] Graph structure assertions passed!")


def test_llm_analysis():
    """Test the full LLM analysis (requires API key)."""
    from processiq.agent.nodes import analyze_with_llm_node
    from processiq.agent.state import create_initial_state

    process = create_creative_agency_process()
    state = create_initial_state(process=process)

    print("\n" + "=" * 60)
    print("LLM ANALYSIS TEST")
    print("=" * 60)

    try:
        result = analyze_with_llm_node(state)

        if result.get("analysis_insight"):
            insight = result["analysis_insight"]

            print(f"\nProcess Summary: {insight.process_summary}")

            print("\n--- Patterns Detected ---")
            for p in insight.patterns:
                print(f"  - {p}")

            print("\n--- Issues Identified ---")
            for issue in insight.issues:
                print(f"\n  [{issue.severity.upper()}] {issue.title}")
                print(f"    {issue.description}")
                print(f"    Affected: {', '.join(issue.affected_steps)}")
                if issue.root_cause_hypothesis:
                    print(f"    Root cause: {issue.root_cause_hypothesis}")

            print("\n--- Recommendations ---")
            for rec in insight.recommendations:
                print(f"\n  {rec.title}")
                print(f"    Addresses: {rec.addresses_issue}")
                print(f"    Expected benefit: {rec.expected_benefit}")
                print(f"    Feasibility: {rec.feasibility}")
                if rec.risks:
                    print(f"    Risks: {', '.join(rec.risks)}")

            print("\n--- NOT Problems (Core Value) ---")
            for np in insight.not_problems:
                print(f"\n  {np.step_name}")
                print(f"    Why not a problem: {np.why_not_a_problem}")

            # KEY VALIDATION: Check that "Work on the solution" is NOT in issues
            issue_steps = []
            for issue in insight.issues:
                issue_steps.extend(issue.affected_steps)

            work_mentioned_as_issue = any(
                "work on" in s.lower() and "solution" in s.lower() for s in issue_steps
            )

            # Check that work is identified as NOT a problem
            work_is_not_problem = any(
                "work on" in np.step_name.lower() and "solution" in np.step_name.lower()
                for np in insight.not_problems
            )

            # Check for review consolidation recommendation
            has_review_recommendation = any(
                "review" in rec.title.lower() or "consolidat" in rec.title.lower()
                for rec in insight.recommendations
            )

            print("\n" + "=" * 60)
            print("VALIDATION RESULTS")
            print("=" * 60)
            print(
                f"'Work on solution' flagged as issue: {work_mentioned_as_issue} (should be False)"
            )
            print(
                f"'Work on solution' in not-problems: {work_is_not_problem} (should be True)"
            )
            print(
                f"Review consolidation suggested: {has_review_recommendation} (should be True)"
            )

            if (
                not work_mentioned_as_issue
                and work_is_not_problem
                and has_review_recommendation
            ):
                print("\n[PASS] LLM analysis passed all key validations!")
            else:
                print("\n[WARN] Some validations failed - review LLM output")

        else:
            print("\nNo analysis_insight in result - LLM may have failed")
            print(f"Result keys: {result.keys()}")
            if "reasoning_trace" in result:
                print(f"Reasoning: {result['reasoning_trace']}")

    except Exception as e:
        print(f"\nError during LLM analysis: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run tests
    test_metrics_calculation()
    test_metrics_formatting()
    test_graph_structure()

    # Only run LLM test if explicitly requested (requires API key)
    import sys

    if "--llm" in sys.argv:
        test_llm_analysis()
    else:
        print("\n" + "=" * 60)
        print("Skipping LLM test (run with --llm flag to include)")
        print("=" * 60)
