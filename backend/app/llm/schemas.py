"""The LLM's structured output contract. No field here can express a risk score or
classification - those are produced by `scoring_service` and are never rewritten by the model;
the schema simply has no place to put one.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class IndicatorExplanation(BaseModel):
    indicator_code: str = Field(
        description="Exactly one of the indicator codes given in the evidence"
    )
    explanation: str = Field(
        description="One or two sentences explaining why this indicator is relevant here"
    )
    source_numbers: list[int] = Field(
        default_factory=list,
        description="Numbers of the [Source N] context blocks that support this explanation",
    )


class SecurityReportLLMOutput(BaseModel):
    summary: str = Field(
        description="2-4 sentence plain-language summary of what the evidence shows. Must not "
        "state a risk score, percentage, or classification label - those are given, not decided, "
        "by this model."
    )
    indicator_explanations: list[IndicatorExplanation] = Field(default_factory=list)
    recommendations: list[str] = Field(
        default_factory=list,
        description="Concrete, actionable next steps for the person who submitted this URL",
    )
