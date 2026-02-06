"""Process data models for ProcessIQ."""

from pydantic import BaseModel, Field, field_validator


class ProcessStep(BaseModel):
    """A single step in a business process."""

    step_name: str = Field(..., min_length=1, description="Name of the process step")
    average_time_hours: float = Field(
        ..., ge=0, description="Average time to complete in hours"
    )
    resources_needed: int = Field(
        ..., ge=1, description="Number of people/systems involved"
    )
    error_rate_pct: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Percentage of times this step fails/needs rework",
    )
    cost_per_instance: float = Field(
        default=0.0, ge=0, description="Cost in dollars per execution"
    )
    estimated_fields: list[str] = Field(
        default_factory=list,
        description="Field names estimated by AI (e.g., ['cost_per_instance', 'error_rate_pct'])",
    )
    depends_on: list[str] = Field(
        default_factory=list, description="Steps that must complete before this one"
    )

    @field_validator("depends_on", mode="before")
    @classmethod
    def parse_depends_on(cls, v: str | list[str] | None) -> list[str]:
        """Parse depends_on from semicolon or comma-separated string or list."""
        if v is None:
            return []
        if isinstance(v, str):
            # Try semicolon first, then comma
            if ";" in v:
                return [s.strip() for s in v.split(";") if s.strip()]
            return [s.strip() for s in v.split(",") if s.strip()]
        return v


class ProcessData(BaseModel):
    """Complete process data for analysis."""

    name: str = Field(
        ..., min_length=1, description="Name of the process being analyzed"
    )
    description: str = Field(
        default="", description="Optional description of the process"
    )
    steps: list[ProcessStep] = Field(
        ..., min_length=1, description="List of process steps"
    )

    @property
    def total_time_hours(self) -> float:
        """Calculate total process time (sum of all steps)."""
        return sum(step.average_time_hours for step in self.steps)

    @property
    def total_cost(self) -> float:
        """Calculate total process cost (sum of all steps)."""
        return sum(step.cost_per_instance for step in self.steps)

    @property
    def step_names(self) -> list[str]:
        """Get list of all step names."""
        return [step.step_name for step in self.steps]

    def get_step(self, name: str) -> ProcessStep | None:
        """Get a step by name."""
        for step in self.steps:
            if step.step_name == name:
                return step
        return None
