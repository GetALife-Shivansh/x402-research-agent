from typing import List, Literal

from pydantic import BaseModel, Field


class Subtask(BaseModel):
    id: str
    question: str

    specialist_chain: List[
        Literal[
            "search",
            "enrich",
            "factcheck",
            "summarize"
        ]
    ] = Field(
        default_factory=lambda: [
            "search",
            "enrich",
            "factcheck",
            "summarize"
        ]
    )


class ResearchPlan(BaseModel):
    reasoning: str
    subtasks: List[Subtask]


class ReviewResult(BaseModel):
    approved: bool
    quality_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Quality score from 0.0 (poor) to 1.0 (excellent). Must be a decimal between 0 and 1, not a 1-10 scale."
    )
    feedback: str
