"""Tests for processiq.ingestion.csv_loader."""

import pytest

from processiq.exceptions import ExtractionError, ValidationError
from processiq.ingestion.csv_loader import (
    _map_columns,
    _normalize_column_name,
    _validate_required_columns,
    load_csv,
    load_csv_from_bytes,
)

# ---------------------------------------------------------------------------
# Column name normalization
# ---------------------------------------------------------------------------


class TestNormalizeColumnName:
    def test_lowercase(self):
        assert _normalize_column_name("Step_Name") == "step_name"

    def test_strips_whitespace(self):
        assert _normalize_column_name("  step_name  ") == "step_name"

    def test_strips_parenthetical_suffix(self):
        assert _normalize_column_name("Time (hours)") == "time"

    def test_strips_dollar_sign(self):
        assert _normalize_column_name("Cost $") == "cost"

    def test_strips_percent(self):
        assert _normalize_column_name("Error Rate %") == "error_rate"

    def test_replaces_spaces_with_underscores(self):
        assert _normalize_column_name("step name") == "step_name"

    def test_replaces_hyphens_with_underscores(self):
        assert _normalize_column_name("step-name") == "step_name"

    def test_strips_trailing_underscores(self):
        assert _normalize_column_name("cost_") == "cost"


# ---------------------------------------------------------------------------
# Column mapping
# ---------------------------------------------------------------------------


class TestMapColumns:
    def test_standard_names_unchanged(self):
        import pandas as pd

        df = pd.DataFrame(columns=["step_name", "average_time_hours", "resources_needed"])
        mapped = _map_columns(df)
        assert list(mapped.columns) == ["step_name", "average_time_hours", "resources_needed"]

    def test_aliases_mapped(self):
        import pandas as pd

        df = pd.DataFrame(columns=["task", "hours", "people"])
        mapped = _map_columns(df)
        assert "step_name" in mapped.columns
        assert "average_time_hours" in mapped.columns
        assert "resources_needed" in mapped.columns


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidateRequiredColumns:
    def test_all_present(self):
        import pandas as pd

        df = pd.DataFrame(columns=["step_name", "average_time_hours", "resources_needed"])
        # Should not raise
        _validate_required_columns(df)

    def test_missing_raises(self):
        import pandas as pd

        df = pd.DataFrame(columns=["step_name"])
        with pytest.raises(ValidationError) as exc_info:
            _validate_required_columns(df)
        assert "Missing required columns" in str(exc_info.value)


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

VALID_CSV = b"""step_name,average_time_hours,resources_needed,cost_per_instance,depends_on
Review document,1.5,2,50,
Approve document,0.5,1,25,Review document
"""

ALIAS_CSV = b"""task,hours,people
Step A,1.0,1
Step B,2.0,2
"""

DOLLAR_CSV = b"""step_name,average_time_hours,resources_needed,cost_per_instance
Step A,1.0,1,$100
Step B,2.0,2,$200
"""

PERCENT_CSV = b"""step_name,average_time_hours,resources_needed,error_rate_pct
Step A,1.0,1,5%
Step B,2.0,2,10%
"""

SEMICOLON_CSV = b"""step_name;average_time_hours;resources_needed
Step A;1.0;1
Step B;2.0;2
"""


class TestLoadCsv:
    def test_load_from_bytes(self):
        result = load_csv(VALID_CSV, process_name="Test")
        assert result.name == "Test"
        assert len(result.steps) == 2
        assert result.steps[0].step_name == "Review document"

    def test_load_from_file_path(self, tmp_path):
        csv_file = tmp_path / "process.csv"
        csv_file.write_bytes(VALID_CSV)
        result = load_csv(str(csv_file), process_name="File Test")
        assert len(result.steps) == 2

    def test_file_not_found(self):
        with pytest.raises(ExtractionError):
            load_csv("/nonexistent/path/file.csv")

    def test_empty_csv(self):
        with pytest.raises((ExtractionError, Exception)):
            load_csv(b"", process_name="Empty")

    def test_headers_only_no_data(self):
        csv_data = b"step_name,average_time_hours,resources_needed\n"
        with pytest.raises(ExtractionError):
            load_csv(csv_data, process_name="No Data")

    def test_with_column_aliases(self):
        result = load_csv(ALIAS_CSV, process_name="Alias Test")
        assert len(result.steps) == 2
        assert result.steps[0].step_name == "Step A"

    def test_dollar_signs_stripped(self):
        result = load_csv(DOLLAR_CSV, process_name="Dollar Test")
        assert result.steps[0].cost_per_instance == 100.0
        assert result.steps[1].cost_per_instance == 200.0

    def test_percent_stripped(self):
        result = load_csv(PERCENT_CSV, process_name="Percent Test")
        assert result.steps[0].error_rate_pct == 5.0
        assert result.steps[1].error_rate_pct == 10.0

    def test_semicolon_delimiter(self):
        result = load_csv(SEMICOLON_CSV, process_name="Semi Test")
        assert len(result.steps) == 2

    def test_depends_on_parsed(self):
        result = load_csv(VALID_CSV, process_name="Deps Test")
        assert result.steps[1].depends_on == ["Review document"]

    def test_all_rows_invalid_raises(self):
        bad_csv = b"""step_name,average_time_hours,resources_needed
,invalid,0
,bad,-1
"""
        with pytest.raises(ValidationError):
            load_csv(bad_csv, process_name="Bad Data")


class TestLoadCsvFromBytes:
    def test_convenience_function(self):
        result = load_csv_from_bytes(VALID_CSV, process_name="Bytes Test")
        assert len(result.steps) == 2
