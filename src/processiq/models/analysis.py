"""Analysis result models for ProcessIQ."""

from enum import Enum

from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    """Bottleneck severity classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SuggestionType(str, Enum):
    """Types of improvement suggestions."""

    AUTOMATION = "automation"
    PROCESS_REDESIGN = "process_redesign"
    RESOURCE_REALLOCATION = "resource_reallocation"
    TRAINING = "training"
    TOOL_UPGRADE = "tool_upgrade"
    ELIMINATION = "elimination"
    PARALLELIZATION = "parallelization"


class Bottleneck(BaseModel):
    """An identified bottleneck in the process."""

    step_name: str = Field(..., description="Name of the bottleneck step")
    severity: SeverityLevel = Field(..., description="Severity of the bottleneck")
    impact_score: float = Field(..., ge=0, le=1, description="Impact score (0-1)")
    reason: str = Field(..., description="Why this is a bottleneck")
    downstream_impact: list[str] = Field(
        default_factory=list, description="Steps affected by this bottleneck"
    )
    metrics: dict[str, float] = Field(
        default_factory=dict, description="Relevant metrics (time, cost, error_rate)"
    )


class ROIEstimate(BaseModel):
    """ROI estimate with ranges and assumptions."""

    pessimistic: float = Field(..., description="Conservative estimate in dollars/year")
    likely: float = Field(..., description="Most likely estimate in dollars/year")
    optimistic: float = Field(..., description="Best-case estimate in dollars/year")
    assumptions: list[str] = Field(
        ..., min_length=1, description="Assumptions behind the estimate"
    )
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    payback_months: float | None = Field(
        default=None, ge=0, description="Estimated payback period"
    )

    @property
    def expected_value(self) -> float:
        """Calculate weighted expected value (PERT-style)."""
        return (self.pessimistic + 4 * self.likely + self.optimistic) / 6


class Suggestion(BaseModel):
    """An improvement suggestion for a bottleneck."""

    id: str = Field(..., description="Unique identifier for the suggestion")
    bottleneck_step: str = Field(..., description="The bottleneck this addresses")
    suggestion_type: SuggestionType = Field(..., description="Type of improvement")
    title: str = Field(..., description="Short title for the suggestion")
    description: str = Field(..., description="Detailed description of the suggestion")
    implementation_steps: list[str] = Field(
        default_factory=list, description="Steps to implement"
    )
    estimated_cost: float = Field(
        default=0.0, ge=0, description="Implementation cost in dollars"
    )
    roi: ROIEstimate | None = Field(
        default=None, description="ROI estimate if calculated"
    )
    reasoning: str = Field(default="", description="Why this suggestion was made")
    alternatives_considered: list[str] = Field(
        default_factory=list, description="Other options that were considered"
    )


class AnalysisResult(BaseModel):
    """Complete analysis output."""

    process_name: str = Field(..., description="Name of the analyzed process")
    bottlenecks: list[Bottleneck] = Field(
        default_factory=list, description="Identified bottlenecks"
    )
    suggestions: list[Suggestion] = Field(
        default_factory=list, description="Improvement suggestions"
    )
    overall_confidence: float = Field(
        ..., ge=0, le=1, description="Overall analysis confidence"
    )
    data_gaps: list[str] = Field(
        default_factory=list, description="Missing data that would improve analysis"
    )
    summary: str = Field(default="", description="Executive summary of findings")
