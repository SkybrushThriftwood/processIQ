"""Standalone demo of the feedback loop mechanism.

Shows what the LLM actually receives when feedback is present.
No API key or running app required.

Usage:
    uv run python scripts/demo_feedback_loop.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from processiq.agent.nodes import _format_feedback_history
from processiq.prompts import get_analysis_prompt

# ---------------------------------------------------------------------------
# Step 1: Simulate user feedback from a previous analysis run
# ---------------------------------------------------------------------------

feedback: dict[str, dict[str, object]] = {
    "Automate Email Processing": {
        "vote": "down",
        "reason": "We already use an automation tool for this, it didn't help",
        "timestamp": "2026-02-17T10:00:00+00:00",
    },
    "Hire Additional Dispatch Staff": {
        "vote": "down",
        "reason": "We have a hiring freeze until Q3",
        "timestamp": "2026-02-17T10:01:00+00:00",
    },
    "Introduce Digital Driver Briefing": {
        "vote": "up",
        "reason": None,
        "timestamp": "2026-02-17T10:02:00+00:00",
    },
}

# ---------------------------------------------------------------------------
# Step 2: Show what _format_feedback_history produces
# ---------------------------------------------------------------------------

print("=" * 70)
print("FEEDBACK HISTORY (what the agent formats before calling the LLM)")
print("=" * 70)

formatted = _format_feedback_history(feedback)
print(formatted)
print()

# ---------------------------------------------------------------------------
# Step 3: Show a fragment of the actual prompt the LLM receives
# ---------------------------------------------------------------------------

sample_metrics = """\
Process: Driving Service Dispatch
Steps: 8  |  Total cycle time: ~18 hours  |  Value-add time: ~3 hours

BOTTLENECK: Weekly Roster Planning — 5 hours per cycle, 27% of total time
DELAY: Email Order Receipt — 90 min idle wait despite only 5 min active work
DELAY: Invoice Processing — 2 hour idle wait, 10 min active work
"""

prompt = get_analysis_prompt(
    metrics_text=sample_metrics,
    business_context="Driving service, 60 drivers, 4 office staff",
    constraints_summary="No new hires until Q3; budget: operational savings only",
    feedback_history=formatted,
)

# Print only the feedback section of the prompt so the output stays readable
feedback_start = prompt.find("## Previous Feedback")
if feedback_start != -1:
    print("=" * 70)
    print("PROMPT SECTION INJECTED INTO LLM (feedback_history block)")
    print("=" * 70)
    print(prompt[feedback_start : feedback_start + 800])
    print()
else:
    print("[feedback_history section not found in prompt — check analyze.j2]")

# ---------------------------------------------------------------------------
# Step 4: Demonstrate empty feedback (baseline)
# ---------------------------------------------------------------------------

print("=" * 70)
print("WITHOUT FEEDBACK (baseline — no feedback_history injected)")
print("=" * 70)
formatted_empty = _format_feedback_history({})
print(repr(formatted_empty))  # Should be None
print("Result: LLM receives no feedback section. All recommendations fair game.")
print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("The feedback loop works as follows:")
print("  1. User clicks 'Helpful' or 'Not useful' on each recommendation")
print("  2. Feedback stored in session_state['recommendation_feedback']")
print("  3. On re-analysis, _format_feedback_history() converts dict -> text")
print("  4. Text injected into analyze.j2 as {{ feedback_history }}")
print("  5. LLM instruction: REJECT listed items, lean toward accepted types")
print()
print("This session run demonstrated:")
for title, f in feedback.items():
    vote = "ACCEPTED" if f["vote"] == "up" else "REJECTED"
    reason = f" (reason: {f['reason']})" if f.get("reason") else ""
    print(f"  [{vote}] {title}{reason}")
