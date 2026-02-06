"""Clarification models for ProcessIQ agent interactions."""

from typing import Literal

from pydantic import BaseModel, Field


class ClarifyingQuestion(BaseModel):
    """A structured question the agent needs answered to proceed.

    Enables the UI to render appropriate input widgets based on input_type,
    improving UX compared to free-form text input.
    """

    id: str = Field(..., description="Unique identifier for tracking responses")
    question: str = Field(..., description="The question text to display")
    target_field: str | None = Field(
        default=None,
        description="Path to the model field this fills, e.g., 'steps[2].error_rate_pct'",
    )
    input_type: Literal["text", "number", "select", "boolean"] = Field(
        default="text",
        description="Determines which UI widget to render",
    )
    options: list[str] | None = Field(
        default=None,
        description="Available choices for 'select' input type",
    )
    default: str | None = Field(
        default=None,
        description="Pre-filled suggestion or default value",
    )
    hint: str | None = Field(
        default=None,
        description="Helper text explaining what kind of answer is expected",
    )
    required: bool = Field(
        default=False,
        description="Whether this question must be answered to proceed",
    )


class ClarificationResponse(BaseModel):
    """User's response to a clarifying question."""

    question_id: str = Field(..., description="ID of the question being answered")
    value: str | float | bool | None = Field(..., description="The user's answer")
    skipped: bool = Field(
        default=False, description="Whether user chose to skip this question"
    )


class ClarificationBundle(BaseModel):
    """A set of clarifying questions to present to the user."""

    questions: list[ClarifyingQuestion] = Field(
        default_factory=list,
        description="Questions to ask",
    )
    context: str = Field(
        default="",
        description="Explanation of why these questions are being asked",
    )
    can_proceed_without: bool = Field(
        default=True,
        description="Whether user can skip and proceed with lower confidence",
    )
