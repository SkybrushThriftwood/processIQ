"""Tests for processiq.export.csv_export."""

from processiq.export.csv_export import export_insight_csv, export_recommendations_csv


class TestExportInsightCsv:
    def test_returns_bytes(self, sample_insight):
        result = export_insight_csv(sample_insight)
        assert isinstance(result, bytes)

    def test_contains_summary(self, sample_insight):
        result = export_insight_csv(sample_insight).decode("utf-8")
        assert "5-step order process" in result

    def test_contains_issues(self, sample_insight):
        result = export_insight_csv(sample_insight).decode("utf-8")
        assert "Redundant approvals" in result
        assert "ISSUES" in result

    def test_contains_recommendations(self, sample_insight):
        result = export_insight_csv(sample_insight).decode("utf-8")
        assert "Consolidate approvals" in result
        assert "RECOMMENDATIONS" in result

    def test_contains_not_problems(self, sample_insight):
        result = export_insight_csv(sample_insight).decode("utf-8")
        assert "Design solution" in result
        assert "CORE VALUE WORK" in result

    def test_contains_patterns(self, sample_insight):
        result = export_insight_csv(sample_insight).decode("utf-8")
        assert "2 approval steps" in result


class TestExportRecommendationsCsv:
    def test_returns_bytes(self, sample_insight):
        result = export_recommendations_csv(sample_insight.recommendations)
        assert isinstance(result, bytes)

    def test_header_row(self, sample_insight):
        result = export_recommendations_csv(sample_insight.recommendations).decode(
            "utf-8"
        )
        lines = result.strip().split("\n")
        assert "Title" in lines[0]
        assert "Feasibility" in lines[0]

    def test_row_count(self, sample_insight):
        result = export_recommendations_csv(sample_insight.recommendations).decode(
            "utf-8"
        )
        lines = result.strip().split("\n")
        # 1 header + 1 data row
        assert len(lines) == 2

    def test_empty_recommendations(self):
        result = export_recommendations_csv([]).decode("utf-8")
        lines = result.strip().split("\n")
        # Just header
        assert len(lines) == 1
