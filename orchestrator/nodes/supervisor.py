from orchestrator.llm_client import get_llm, invoke_with_retry
from orchestrator.models import ResearchPlan
from orchestrator.state import OrchestratorState
from orchestrator.tracing import traced_node


SUPERVISOR_PROMPT = """You are a research supervisor. Break the user's query into 2-4 focused, \
non-overlapping sub-questions that together fully answer it. Each will be independently \
researched through a chain of PAID services (search -> enrich -> fact-check -> summarize), so \
avoid redundant or overly narrow sub-questions — every one costs real money.
{feedback_block}
Respond with structured output matching the schema."""


@traced_node("supervisor")
def supervisor_node(state: OrchestratorState) -> dict:

    existing = (
        state["plan"]["subtasks"]
        if state.get("plan")
        else []
    )


    feedback_block = ""

    if state.get("review_feedback"):

        feedback_block = (
            f"\nA prior research pass was reviewed and found incomplete. "
            f"Gap to address: {state['review_feedback']}\n"
            f"Only produce NEW sub-questions that close this specific gap — "
            f"do not repeat already-covered angles."
        )


    llm = get_llm()

    structured = llm.with_structured_output(
        ResearchPlan,
        include_raw=True
    )


    raw = invoke_with_retry(
        structured,
        [
            (
                "system",
                SUPERVISOR_PROMPT.format(
                    feedback_block=feedback_block
                )
            ),
            (
                "human",
                state["query"]
            ),
        ],
    )


    plan = raw["parsed"]


    offset = len(existing)

    new_subtasks = []

    for i, st in enumerate(plan.subtasks):

        d = st.model_dump()

        d["id"] = f"task_{offset + i + 1}"

        new_subtasks.append(d)


    return {
        "plan": {
            "reasoning": plan.reasoning,
            "subtasks": existing + new_subtasks
        },
        "review_feedback": None,
    }
