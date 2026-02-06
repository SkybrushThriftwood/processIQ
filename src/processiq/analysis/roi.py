"""ROI calculation algorithms for ProcessIQ.

Pure algorithmic logic - no LLM calls. Calculates return on investment
for improvement suggestions with pessimistic/likely/optimistic ranges.
"""

import logging
from dataclasses import dataclass

from processiq.models import (
    Bottleneck,
    ProcessData,
    ROIEstimate,
    Suggestion,
    SuggestionType,
)

logger = logging.getLogger(__name__)

# Default improvement factors by suggestion type
DEFAULT_IMPROVEMENT_FACTORS: dict[SuggestionType, dict[str, float]] = {
    SuggestionType.AUTOMATION: {
        "time_reduction_pct": 0.70,  # 70% time reduction typical
        "error_reduction_pct": 0.80,  # 80% error reduction
        "cost_multiplier": 0.3,  # Ongoing cost is 30% of original
    },
    SuggestionType.PROCESS_REDESIGN: {
        "time_reduction_pct": 0.40,
        "error_reduction_pct": 0.30,
        "cost_multiplier": 0.7,
    },
    SuggestionType.RESOURCE_REALLOCATION: {
        "time_reduction_pct": 0.25,
        "error_reduction_pct": 0.15,
        "cost_multiplier": 0.9,
    },
    SuggestionType.TRAINING: {
        "time_reduction_pct": 0.15,
        "error_reduction_pct": 0.40,
        "cost_multiplier": 0.95,
    },
    SuggestionType.TOOL_UPGRADE: {
        "time_reduction_pct": 0.35,
        "error_reduction_pct": 0.25,
        "cost_multiplier": 0.6,
    },
    SuggestionType.ELIMINATION: {
        "time_reduction_pct": 1.0,  # 100% - step is removed
        "error_reduction_pct": 1.0,
        "cost_multiplier": 0.0,
    },
    SuggestionType.PARALLELIZATION: {
        "time_reduction_pct": 0.50,
        "error_reduction_pct": 0.0,  # No error impact
        "cost_multiplier": 1.1,  # Slightly higher cost (coordination)
    },
}


@dataclass
class ROIInputs:
    """Inputs for ROI calculation."""

    current_time_hours: float
    current_cost_per_instance: float
    current_error_rate_pct: float
    executions_per_year: int
    implementation_cost: float
    improvement_factors: dict[str, float]


def calculate_roi(
    suggestion: Suggestion,
    bottleneck: Bottleneck,
    process: ProcessData,
    executions_per_year: int = 1000,
    confidence: float = 0.7,
) -> ROIEstimate:
    """Calculate ROI estimate for a suggestion.

    Args:
        suggestion: The improvement suggestion.
        bottleneck: The bottleneck being addressed.
        process: The full process data.
        executions_per_year: How many times this process runs per year.
        confidence: Base confidence level for the estimate.

    Returns:
        ROI estimate with ranges and assumptions.
    """
    logger.info("Calculating ROI for suggestion: %s", suggestion.title)

    step = process.get_step(bottleneck.step_name)
    if step is None:
        logger.error("Step %s not found in process", bottleneck.step_name)
        return _empty_roi_estimate()

    factors = DEFAULT_IMPROVEMENT_FACTORS.get(
        suggestion.suggestion_type,
        DEFAULT_IMPROVEMENT_FACTORS[SuggestionType.PROCESS_REDESIGN],
    )

    inputs = ROIInputs(
        current_time_hours=step.average_time_hours,
        current_cost_per_instance=step.cost_per_instance,
        current_error_rate_pct=step.error_rate_pct,
        executions_per_year=executions_per_year,
        implementation_cost=suggestion.estimated_cost,
        improvement_factors=factors,
    )

    # Calculate savings scenarios
    likely_savings = _calculate_annual_savings(inputs, scenario="likely")
    pessimistic_savings = _calculate_annual_savings(inputs, scenario="pessimistic")
    optimistic_savings = _calculate_annual_savings(inputs, scenario="optimistic")

    # Calculate payback period based on likely scenario
    payback_months = None
    if likely_savings > 0 and inputs.implementation_cost > 0:
        payback_months = (inputs.implementation_cost / likely_savings) * 12

    # Build assumptions list
    assumptions = _build_assumptions(inputs, suggestion, executions_per_year)

    roi = ROIEstimate(
        pessimistic=pessimistic_savings,
        likely=likely_savings,
        optimistic=optimistic_savings,
        assumptions=assumptions,
        confidence=confidence,
        payback_months=payback_months,
    )

    logger.debug(
        "ROI calculated: pessimistic=$%.0f, likely=$%.0f, optimistic=$%.0f",
        pessimistic_savings,
        likely_savings,
        optimistic_savings,
    )

    return roi


def _calculate_annual_savings(inputs: ROIInputs, scenario: str) -> float:
    """Calculate annual savings for a given scenario.

    Scenarios apply multipliers to the improvement factors:
    - pessimistic: 50% of expected improvement
    - likely: 100% of expected improvement
    - optimistic: 130% of expected improvement
    """
    scenario_multipliers = {
        "pessimistic": 0.5,
        "likely": 1.0,
        "optimistic": 1.3,
    }
    multiplier = scenario_multipliers.get(scenario, 1.0)

    time_reduction = inputs.improvement_factors["time_reduction_pct"] * multiplier
    time_reduction = min(time_reduction, 1.0)  # Cap at 100%

    error_reduction = inputs.improvement_factors["error_reduction_pct"] * multiplier
    error_reduction = min(error_reduction, 1.0)

    # Time savings (assuming hourly cost derived from cost_per_instance / time)
    hourly_rate = (
        inputs.current_cost_per_instance / inputs.current_time_hours
        if inputs.current_time_hours > 0
        else 75.0  # Default hourly rate
    )
    time_saved_hours = inputs.current_time_hours * time_reduction
    time_savings_per_execution = time_saved_hours * hourly_rate

    # Error cost savings (assume each error costs 2x the step cost to fix)
    error_cost_per_execution = (
        inputs.current_cost_per_instance * 2 * (inputs.current_error_rate_pct / 100)
    )
    error_savings_per_execution = error_cost_per_execution * error_reduction

    # Total savings per execution
    savings_per_execution = time_savings_per_execution + error_savings_per_execution

    # Annual savings
    annual_savings = savings_per_execution * inputs.executions_per_year

    # Subtract implementation cost (amortized over 1 year for annual ROI)
    # For ongoing costs, we don't subtract implementation cost here
    # (it's reflected in payback period instead)

    return annual_savings


def _build_assumptions(
    inputs: ROIInputs,
    suggestion: Suggestion,
    executions_per_year: int,
) -> list[str]:
    """Build list of assumptions for the ROI estimate."""
    assumptions = [
        f"Process executes {executions_per_year:,} times per year",
        f"Current step cost: ${inputs.current_cost_per_instance:.2f} per execution",
        f"Current step time: {inputs.current_time_hours:.1f} hours",
    ]

    factors = inputs.improvement_factors
    if factors["time_reduction_pct"] > 0:
        assumptions.append(
            f"Expected time reduction: {factors['time_reduction_pct']*100:.0f}% "
            f"(based on {suggestion.suggestion_type.value})"
        )

    if factors["error_reduction_pct"] > 0 and inputs.current_error_rate_pct > 0:
        assumptions.append(
            f"Expected error reduction: {factors['error_reduction_pct']*100:.0f}%"
        )
        assumptions.append("Error rework cost estimated at 2x step cost")

    if inputs.implementation_cost > 0:
        assumptions.append(f"Implementation cost: ${inputs.implementation_cost:,.0f}")

    return assumptions


def _empty_roi_estimate() -> ROIEstimate:
    """Return an empty ROI estimate for error cases."""
    return ROIEstimate(
        pessimistic=0.0,
        likely=0.0,
        optimistic=0.0,
        assumptions=["Unable to calculate ROI - step not found"],
        confidence=0.0,
        payback_months=None,
    )
