"""CSV export functionality for ProcessIQ analysis results."""

import csv
import io
import logging

from processiq.models import AnalysisResult, Bottleneck, Suggestion
from processiq.models.insight import AnalysisInsight, Recommendation

logger = logging.getLogger(__name__)


def export_bottlenecks_csv(bottlenecks: list[Bottleneck]) -> bytes:
    """Export bottlenecks to CSV format.

    Args:
        bottlenecks: List of identified bottlenecks.

    Returns:
        CSV content as bytes (UTF-8 encoded).
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "Step Name",
            "Severity",
            "Impact Score",
            "Reason",
            "Downstream Impact",
            "Time (hours)",
            "Error Rate (%)",
            "Cost ($)",
        ]
    )

    # Data rows
    for b in bottlenecks:
        writer.writerow(
            [
                b.step_name,
                b.severity.value,
                f"{b.impact_score:.2f}",
                b.reason,
                "; ".join(b.downstream_impact) if b.downstream_impact else "",
                b.metrics.get("time_hours", ""),
                b.metrics.get("error_rate_pct", ""),
                b.metrics.get("cost", ""),
            ]
        )

    logger.info("Exported %d bottlenecks to CSV", len(bottlenecks))
    return output.getvalue().encode("utf-8")


def export_suggestions_csv(suggestions: list[Suggestion]) -> bytes:
    """Export suggestions to CSV format (Jira/Asana compatible).

    Args:
        suggestions: List of improvement suggestions.

    Returns:
        CSV content as bytes (UTF-8 encoded).
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header (designed for import into project management tools)
    writer.writerow(
        [
            "Title",
            "Description",
            "Type",
            "Target Step",
            "Estimated Cost ($)",
            "ROI Pessimistic ($/year)",
            "ROI Likely ($/year)",
            "ROI Optimistic ($/year)",
            "Confidence (%)",
            "Assumptions",
            "Implementation Steps",
        ]
    )

    # Data rows
    for s in suggestions:
        roi_pessimistic = ""
        roi_likely = ""
        roi_optimistic = ""
        confidence = ""
        assumptions = ""

        if s.roi:
            roi_pessimistic = f"{s.roi.pessimistic:.0f}"
            roi_likely = f"{s.roi.likely:.0f}"
            roi_optimistic = f"{s.roi.optimistic:.0f}"
            confidence = f"{s.roi.confidence * 100:.0f}"
            assumptions = "; ".join(s.roi.assumptions)

        writer.writerow(
            [
                s.title,
                s.description,
                s.suggestion_type.value,
                s.bottleneck_step,
                f"{s.estimated_cost:.0f}",
                roi_pessimistic,
                roi_likely,
                roi_optimistic,
                confidence,
                assumptions,
                "; ".join(s.implementation_steps),
            ]
        )

    logger.info("Exported %d suggestions to CSV", len(suggestions))
    return output.getvalue().encode("utf-8")


def export_analysis_csv(result: AnalysisResult) -> bytes:
    """Export complete analysis result to CSV format.

    Creates a multi-section CSV with bottlenecks and suggestions.

    Args:
        result: Complete analysis result.

    Returns:
        CSV content as bytes (UTF-8 encoded).
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Summary section
    writer.writerow(["ProcessIQ Analysis Results"])
    writer.writerow(["Process", result.process_name])
    writer.writerow(["Overall Confidence", f"{result.overall_confidence * 100:.0f}%"])
    writer.writerow(["Bottlenecks Found", len(result.bottlenecks)])
    writer.writerow(["Suggestions Generated", len(result.suggestions)])
    writer.writerow([])

    # Bottlenecks section
    writer.writerow(["BOTTLENECKS"])
    writer.writerow(
        [
            "Step Name",
            "Severity",
            "Impact Score",
            "Reason",
            "Downstream Impact",
        ]
    )
    for b in result.bottlenecks:
        writer.writerow(
            [
                b.step_name,
                b.severity.value,
                f"{b.impact_score:.2f}",
                b.reason,
                "; ".join(b.downstream_impact) if b.downstream_impact else "",
            ]
        )
    writer.writerow([])

    # Suggestions section
    writer.writerow(["SUGGESTIONS"])
    writer.writerow(
        [
            "Title",
            "Type",
            "Target Step",
            "Cost ($)",
            "ROI Likely ($/year)",
            "Confidence (%)",
        ]
    )
    for s in result.suggestions:
        roi_likely = f"{s.roi.likely:.0f}" if s.roi else ""
        confidence = f"{s.roi.confidence * 100:.0f}" if s.roi else ""
        writer.writerow(
            [
                s.title,
                s.suggestion_type.value,
                s.bottleneck_step,
                f"{s.estimated_cost:.0f}",
                roi_likely,
                confidence,
            ]
        )

    if result.data_gaps:
        writer.writerow([])
        writer.writerow(["DATA GAPS"])
        for gap in result.data_gaps:
            writer.writerow([gap])

    logger.info(
        "Exported complete analysis to CSV for process: %s", result.process_name
    )
    return output.getvalue().encode("utf-8")


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
