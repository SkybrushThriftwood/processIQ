"""CSV export functionality for ProcessIQ analysis results."""

import csv
import io
import logging

from processiq.models.insight import AnalysisInsight, Recommendation

logger = logging.getLogger(__name__)


def export_insight_csv(insight: AnalysisInsight) -> bytes:
    """Export AnalysisInsight to CSV format.

    Args:
        insight: LLM-generated analysis insight.

    Returns:
        CSV content as bytes (UTF-8 encoded).
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Summary
    writer.writerow(["ProcessIQ Analysis Report"])
    writer.writerow(["Summary", insight.process_summary])
    writer.writerow([])

    # Issues
    writer.writerow(["ISSUES"])
    writer.writerow(["Title", "Severity", "Description", "Affected Steps", "Root Cause"])
    for issue in insight.issues:
        writer.writerow([
            issue.title,
            issue.severity,
            issue.description,
            "; ".join(issue.affected_steps),
            issue.root_cause_hypothesis,
        ])
    writer.writerow([])

    # Recommendations
    writer.writerow(["RECOMMENDATIONS"])
    writer.writerow([
        "Title",
        "Addresses Issue",
        "Feasibility",
        "Description",
        "Expected Benefit",
        "Risks",
        "Next Steps",
    ])
    for rec in insight.recommendations:
        writer.writerow([
            rec.title,
            rec.addresses_issue,
            rec.feasibility,
            rec.description,
            rec.expected_benefit,
            "; ".join(rec.risks),
            "; ".join(rec.concrete_next_steps),
        ])
    writer.writerow([])

    # Core value work
    if insight.not_problems:
        writer.writerow(["CORE VALUE WORK"])
        writer.writerow(["Step", "Why Not a Problem"])
        for np in insight.not_problems:
            writer.writerow([np.step_name, np.why_not_a_problem])
        writer.writerow([])

    # Patterns
    if insight.patterns:
        writer.writerow(["PATTERNS"])
        for pattern in insight.patterns:
            writer.writerow([pattern])

    logger.info("Exported insight analysis to CSV")
    return output.getvalue().encode("utf-8")


def export_recommendations_csv(recommendations: list[Recommendation]) -> bytes:
    """Export insight recommendations to CSV (project management tool compatible).

    Args:
        recommendations: List of LLM-generated recommendations.

    Returns:
        CSV content as bytes (UTF-8 encoded).
    """
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Title",
        "Addresses Issue",
        "Feasibility",
        "Description",
        "Expected Benefit",
        "Risks",
        "Next Steps",
    ])

    for rec in recommendations:
        writer.writerow([
            rec.title,
            rec.addresses_issue,
            rec.feasibility,
            rec.description,
            rec.expected_benefit,
            "; ".join(rec.risks),
            "; ".join(rec.concrete_next_steps),
        ])

    logger.info("Exported %d recommendations to CSV", len(recommendations))
    return output.getvalue().encode("utf-8")
