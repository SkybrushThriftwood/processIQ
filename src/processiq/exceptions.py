"""Custom exceptions for ProcessIQ.

Exception hierarchy:
- ProcessIQError (base)
  - ConfigurationError: Invalid or missing configuration
  - InsufficientDataError: Missing required data for analysis
  - ConstraintConflictError: Suggestions conflict with constraints
  - ExtractionError: Failed to extract/parse data from input
  - ValidationError: Data validation failed
"""


class ProcessIQError(Exception):
    """Base exception for all ProcessIQ errors."""

    def __init__(self, message: str, user_message: str | None = None) -> None:
        """Initialize with technical message and optional user-friendly message.

        Args:
            message: Technical error message for logging/debugging.
            user_message: Human-readable message for UI display.
                         If None, uses the technical message.
        """
        super().__init__(message)
        self.user_message = user_message or message


class ConfigurationError(ProcessIQError):
    """Raised when configuration is invalid or missing.

    Example: Missing API key, unsupported LLM provider.
    """

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        user_message: str | None = None,
    ) -> None:
        super().__init__(message, user_message)
        self.config_key = config_key


class InsufficientDataError(ProcessIQError):
    """Raised when required data is missing for analysis.

    Example: ROI calculation requires cost data but none was provided.
    """

    def __init__(
        self,
        message: str,
        missing_fields: list[str] | None = None,
        user_message: str | None = None,
    ) -> None:
        super().__init__(message, user_message)
        self.missing_fields = missing_fields or []


class ConstraintConflictError(ProcessIQError):
    """Raised when a suggestion conflicts with specified constraints.

    Example: Suggestion requires hiring but cannot_hire constraint is set.
    """

    def __init__(
        self,
        message: str,
        constraint_name: str | None = None,
        suggestion_id: str | None = None,
        user_message: str | None = None,
    ) -> None:
        super().__init__(message, user_message)
        self.constraint_name = constraint_name
        self.suggestion_id = suggestion_id


class ExtractionError(ProcessIQError):
    """Raised when data extraction from input fails.

    Example: CSV parsing failed, Excel file is corrupted, LLM extraction failed.
    """

    def __init__(
        self,
        message: str,
        source: str | None = None,
        user_message: str | None = None,
    ) -> None:
        super().__init__(message, user_message)
        self.source = source


class ValidationError(ProcessIQError):
    """Raised when data validation fails.

    Example: Negative time values, missing required columns.
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: str | None = None,
        user_message: str | None = None,
    ) -> None:
        super().__init__(message, user_message)
        self.field = field
        self.value = value
