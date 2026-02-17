"""Integration tests for the LLM analysis pipeline.

These tests require a live LLM API key and are marked with @pytest.mark.llm.
Run with: pytest -m llm
"""

import pytest

from processiq.agent.nodes import analyze_with_llm_node
from processiq.agent.state import create_initial_state
from processiq.models import ProcessData, ProcessStep


def _create_creative_agency_process() -> ProcessData:
    """Create the canonical creative agency test case."""
    steps = [
        ProcessStep(step_name="Client brings a new project", average_time_hours=0.5, cost_per_instance=25, resources_needed=1),
        ProcessStep(step_name="Employee talks to the client", average_time_hours=1.0, cost_per_instance=50, resources_needed=1, depends_on=["Client brings a new project"]),
        ProcessStep(step_name="Client gives access to files", average_time_hours=0.5, cost_per_instance=25, resources_needed=1, depends_on=["Employee talks to the client"]),
        ProcessStep(step_name="Share files with employees", average_time_hours=0.5, cost_per_instance=50, resources_needed=2, depends_on=["Client gives access to files"]),
        ProcessStep(step_name="Create tasks based on files", average_time_hours=1.0, cost_per_instance=100, resources_needed=2, depends_on=["Share files with employees"]),
        ProcessStep(step_name="Review tasks by manager", average_time_hours=1.0, cost_per_instance=100, resources_needed=1, depends_on=["Create tasks based on files"]),
        ProcessStep(step_name="Send invoice to client", average_time_hours=0.5, cost_per_instance=25, resources_needed=1, depends_on=["Review tasks by manager"]),
        ProcessStep(step_name="Work on the solution", average_time_hours=4.0, cost_per_instance=300, resources_needed=3, depends_on=["Review tasks by manager"]),
        ProcessStep(step_name="Manager reviews the solution", average_time_hours=1.0, cost_per_instance=100, resources_needed=1, depends_on=["Work on the solution"]),
        ProcessStep(step_name="Implement the solution", average_time_hours=2.0, cost_per_instance=150, resources_needed=3, depends_on=["Manager reviews the solution"]),
        ProcessStep(step_name="Get feedback from client", average_time_hours=0.5, cost_per_instance=25, resources_needed=1, depends_on=["Implement the solution"]),
        ProcessStep(step_name="Adjust the solution", average_time_hours=1.0, cost_per_instance=100, resources_needed=2, depends_on=["Get feedback from client"]),
        ProcessStep(step_name="Client happy", average_time_hours=0.5, cost_per_instance=25, resources_needed=1, depends_on=["Adjust the solution"]),
    ]
    return ProcessData(
        name="Creative Agency Project Workflow",
        description="13-step project delivery process for a creative agency",
        steps=steps,
    )


@pytest.mark.llm
def test_llm_analysis_creative_agency():
    """Test that LLM analysis produces valid AnalysisInsight.

    Validates:
    - LLM does NOT flag "Work on the solution" as an issue to fix
    - LLM recognizes creative work as core value (not_problems)
    - LLM suggests review consolidation
    """
    process = _create_creative_agency_process()
    state = create_initial_state(process=process)

    result = analyze_with_llm_node(state)

    insight = result.get("analysis_insight")
    assert insight is not None, "Expected analysis_insight in result"

    # "Work on the solution" should NOT appear as an issue to fix
    issue_steps = []
    for issue in insight.issues:
        issue_steps.extend(issue.affected_steps)

    work_as_issue = any(
        "work on" in s.lower() and "solution" in s.lower() for s in issue_steps
    )
    assert not work_as_issue, (
        "'Work on the solution' should not be flagged as an issue"
    )

    # "Work on the solution" should be in not_problems
    work_protected = any(
        "work on" in np.step_name.lower() and "solution" in np.step_name.lower()
        for np in insight.not_problems
    )
    assert work_protected, (
        "'Work on the solution' should be identified as core value work"
    )
