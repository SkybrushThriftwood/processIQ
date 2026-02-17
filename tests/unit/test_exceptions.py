"""Tests for processiq.exceptions."""

from processiq.exceptions import (
    ConfigurationError,
    ConstraintConflictError,
    ExtractionError,
    InsufficientDataError,
    ProcessIQError,
    ValidationError,
)


class TestProcessIQError:
    def test_message(self):
        e = ProcessIQError("technical error")
        assert str(e) == "technical error"

    def test_user_message_default(self):
        e = ProcessIQError("technical error")
        assert e.user_message == "technical error"

    def test_user_message_custom(self):
        e = ProcessIQError("technical error", user_message="Something went wrong")
        assert e.user_message == "Something went wrong"


class TestConfigurationError:
    def test_config_key(self):
        e = ConfigurationError("Missing key", config_key="api_key")
        assert e.config_key == "api_key"

    def test_config_key_none(self):
        e = ConfigurationError("Error")
        assert e.config_key is None

    def test_inherits(self):
        assert issubclass(ConfigurationError, ProcessIQError)


class TestInsufficientDataError:
    def test_missing_fields(self):
        e = InsufficientDataError("Not enough data", missing_fields=["cost", "time"])
        assert e.missing_fields == ["cost", "time"]

    def test_missing_fields_default(self):
        e = InsufficientDataError("Error")
        assert e.missing_fields == []

    def test_inherits(self):
        assert issubclass(InsufficientDataError, ProcessIQError)


class TestConstraintConflictError:
    def test_attributes(self):
        e = ConstraintConflictError(
            "Conflict",
            constraint_name="budget",
            suggestion_id="s1",
        )
        assert e.constraint_name == "budget"
        assert e.suggestion_id == "s1"

    def test_inherits(self):
        assert issubclass(ConstraintConflictError, ProcessIQError)


class TestExtractionError:
    def test_source(self):
        e = ExtractionError("Parse failed", source="csv")
        assert e.source == "csv"

    def test_source_none(self):
        e = ExtractionError("Error")
        assert e.source is None

    def test_inherits(self):
        assert issubclass(ExtractionError, ProcessIQError)


class TestValidationError:
    def test_field_and_value(self):
        e = ValidationError("Bad value", field="cost", value="-5")
        assert e.field == "cost"
        assert e.value == "-5"

    def test_defaults(self):
        e = ValidationError("Error")
        assert e.field is None
        assert e.value is None

    def test_inherits(self):
        assert issubclass(ValidationError, ProcessIQError)


class TestExceptionHierarchy:
    def test_all_inherit_from_base(self):
        for exc_class in [
            ConfigurationError,
            InsufficientDataError,
            ConstraintConflictError,
            ExtractionError,
            ValidationError,
        ]:
            assert issubclass(exc_class, ProcessIQError)
            assert issubclass(exc_class, Exception)
