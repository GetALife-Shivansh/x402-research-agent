from typing import TypedDict, Annotated, List, Optional
import operator


class SubtaskResult(TypedDict):
    id: str
    specialist: str
    description: str
    output: str
    sources: List[str]
    payment_tx: List[Optional[str]]
    cost_usdc: float


class OrchestratorState(TypedDict):
    task_id: str
    query: str
    plan: Optional[dict]
    subtask_results: Annotated[List[SubtaskResult], operator.add]
    review_feedback: Optional[str]
    retry_count: dict
    final_report: str
    reliability_summary: Optional[dict]
    total_cost_usdc: Annotated[float, operator.add]
