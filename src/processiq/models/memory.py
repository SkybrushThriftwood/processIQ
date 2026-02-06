"""Memory models for ProcessIQ (Phase 2 ready)."""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class Industry(str, Enum):
    """Industry classification options."""

    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    TECHNOLOGY = "technology"
    GOVERNMENT = "government"
    EDUCATION = "education"
    OTHER = "other"


class CompanySize(str, Enum):
    """Company size classification."""

    STARTUP = "startup"  # < 50 employees
    SMALL = "small"  # 50-200 employees
    MID_MARKET = "mid_market"  # 200-1000 employees
    ENTERPRISE = "enterprise"  # > 1000 employees


class RegulatoryEnvironment(str, Enum):
    """Regulatory strictness level."""

    MINIMAL = "minimal"
    MODERATE = "moderate"
    STRICT = "strict"
    HIGHLY_REGULATED = "highly_regulated"


class BusinessProfile(BaseModel):
    """Semantic memory: Facts about the business (Profile approach).

    Phase 1: Populated from user input at session start.
    Phase 2: Persisted and updated across sessions.
    """

    industry: Industry = Field(..., description="Industry classification")
    custom_industry: str = Field(
        default="", description="User-specified industry when 'Other' is selected"
    )
    company_size: CompanySize = Field(..., description="Company size category")
    regulatory_environment: RegulatoryEnvironment = Field(
        default=RegulatoryEnvironment.MODERATE, description="Regulatory strictness"
    )
    typical_constraints: list[str] = Field(
        default_factory=list, description="Common constraints for this business"
    )
    preferred_frameworks: list[str] = Field(
        default_factory=list,
        description="Frameworks user responds well to (Lean, Six Sigma, etc.)",
    )
    previous_improvements: list[str] = Field(
        default_factory=list, description="Past improvement initiatives"
    )
    rejected_approaches: list[str] = Field(
        default_factory=list, description="Approaches user has rejected before"
    )
    notes: str = Field(default="", description="Additional context about the business")


class AnalysisMemory(BaseModel):
    """Episodic memory: Past analysis experience (Collection approach).

    Phase 1: Not persisted (session only).
    Phase 2: Stored in SQLite, searchable in ChromaDB.
    """

    id: str = Field(..., description="Unique identifier for this analysis")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When analysis was performed",
    )
    process_name: str = Field(..., description="Name of the analyzed process")
    bottlenecks_found: list[str] = Field(
        default_factory=list, description="Bottleneck step names"
    )
    suggestions_offered: list[str] = Field(
        default_factory=list, description="Suggestion IDs offered"
    )
    suggestions_accepted: list[str] = Field(
        default_factory=list, description="Suggestion IDs accepted"
    )
    suggestions_rejected: list[str] = Field(
        default_factory=list, description="Suggestion IDs rejected"
    )
    rejection_reasons: list[str] = Field(
        default_factory=list,
        description="Why suggestions were rejected (critical for learning)",
    )
    outcome_notes: str = Field(default="", description="Post-implementation notes")

    @property
    def acceptance_rate(self) -> float:
        """Calculate suggestion acceptance rate."""
        total = len(self.suggestions_accepted) + len(self.suggestions_rejected)
        if total == 0:
            return 0.0
        return len(self.suggestions_accepted) / total
