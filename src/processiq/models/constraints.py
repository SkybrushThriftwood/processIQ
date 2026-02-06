"""Constraint models for ProcessIQ."""

from enum import Enum

from pydantic import BaseModel, Field


class Priority(str, Enum):
    """Optimization priority options."""

    COST_REDUCTION = "cost_reduction"
    TIME_REDUCTION = "time_reduction"
    QUALITY_IMPROVEMENT = "quality_improvement"
    COMPLIANCE = "compliance"


class Constraints(BaseModel):
    """Business constraints that limit optimization suggestions."""

    budget_limit: float | None = Field(
        default=None, ge=0, description="Maximum budget in dollars"
    )
    cannot_hire: bool = Field(default=False, description="Cannot add new staff")
    max_error_rate_increase_pct: float = Field(
        default=0.0, ge=0, description="Maximum allowed increase in error rate"
    )
    must_maintain_audit_trail: bool = Field(
        default=False, description="Must preserve audit trail"
    )
    max_implementation_weeks: int | None = Field(
        default=None, ge=1, description="Maximum implementation time in weeks"
    )
    priority: Priority = Field(
        default=Priority.COST_REDUCTION, description="Primary optimization goal"
    )
    custom_constraints: list[str] = Field(
        default_factory=list, description="Additional custom constraints as free text"
    )

    def is_hiring_allowed(self) -> bool:
        """Check if hiring is allowed."""
        return not self.cannot_hire

    def has_budget_limit(self) -> bool:
        """Check if there's a budget constraint."""
        return self.budget_limit is not None


class ConflictResult(BaseModel):
    """Result of checking a suggestion against constraints."""

    is_valid: bool = Field(
        ..., description="Whether the suggestion passes all constraints"
    )
    conflicts: list[str] = Field(
        default_factory=list, description="List of constraint violations"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Non-blocking concerns"
    )

    @property
    def has_conflicts(self) -> bool:
        """Check if there are any conflicts."""
        return len(self.conflicts) > 0
