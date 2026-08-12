from orchestrator.llm_client import get_llm, invoke_with_retry
from orchestrator.models import ReviewResult
from orchestrator.state import OrchestratorState
from orchestrator.tracing import traced_node


CRITIC_PROMPT = """You are a research quality reviewer. Each research pass below was produced \
through paid, fact-checked API calls (x402 micropayments) — so only request another paid pass \
if something important is clearly missing. Respond with structured output."""


@traced_node("critic")
def critic_node(state: OrchestratorState) -> dict:

    research_text = "\n\n".join(
        f"Q: {r['description']}\nA: {r['output']}"
        for r in state["subtask_results"]
    )


    llm = get_llm()


    structured = llm.with_structured_output(
        ReviewResult,
        include_raw=True
    )


    raw = invoke_with_retry(
        structured,
        [
            (
                "system",
                CRITIC_PROMPT
            ),
            (
                "human",
                f"Original question: {state['query']}\n\n"
                f"Research gathered:\n{research_text}"
            ),
        ],
    )


    result = raw["parsed"]


    retries = (
        state.get(
            "retry_count",
            {}
        ).get(
            "critic",
            0
        )
    )


    if result.approved or retries >= 1:
        return {
            "review_feedback": None
        }


    new_retry = dict(
        state.get(
            "retry_count",
            {}
        )
    )

    new_retry["critic"] = retries + 1


    return {
        "review_feedback": result.feedback,
        "retry_count": new_retry,
    }
