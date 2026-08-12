from langgraph.types import Send

from orchestrator.payments.ledger import record_payment
from orchestrator.payments.x402_client import call_paid_service
from orchestrator.state import OrchestratorState
from orchestrator.tracing import traced_node



def fan_out_to_researchers(state: OrchestratorState):

    done_ids = {
        r["id"]
        for r in state.get(
            "subtask_results",
            []
        )
    }

    pending = [
        st
        for st in state["plan"]["subtasks"]
        if st["id"] not in done_ids
    ]

    return [
        Send(
            "researcher",
            {
                "subtask": st,
                "task_id": state["task_id"]
            }
        )
        for st in pending
    ]



@traced_node("researcher")
def researcher_node(payload: dict) -> dict:

    subtask = payload["subtask"]

    task_id = payload["task_id"]

    question = subtask["question"]


    # 1) Paid search
    search_res, pay_search = call_paid_service(
        "search",
        {
            "query": question,
            "max_results": 3
        }
    )

    sources = [
        r["source"]
        for r in search_res["results"]
    ]

    context = "\n".join(
        f"- {r['content'][:400]} "
        f"(source: {r['source']})"
        for r in search_res["results"]
    )

    record_payment(
        task_id,
        "search",
        pay_search
    )


    # 2) Paid enrichment
    enrich_res, pay_enrich = call_paid_service(
        "enrich",
        {
            "question": question,
            "context": context
        }
    )

    record_payment(
        task_id,
        "enrich",
        pay_enrich
    )


    # 3) Paid fact-check
    factcheck_res, pay_fc = call_paid_service(
        "factcheck",
        {
            "question": question,
            "claims": enrich_res.get(
                "key_facts",
                []
            ),
            "context": context,
        }
    )

    record_payment(
        task_id,
        "factcheck",
        pay_fc
    )


    # 4) Paid citation-aware synthesis
    summarize_res, pay_sum = call_paid_service(
        "summarize",
        {
            "question": question,
            "context": context,
            "key_facts": enrich_res.get(
                "key_facts",
                []
            ),
            "factcheck_notes": factcheck_res.get(
                "notes",
                ""
            ),
            "sources": sources,
        }
    )

    record_payment(
        task_id,
        "summarize",
        pay_sum
    )


    total_cost = sum(
        p["amount_usdc"]
        for p in (
            pay_search,
            pay_enrich,
            pay_fc,
            pay_sum
        )
    )


    return {
        "subtask_results": [
            {
                "id": subtask["id"],
                "specialist": "research_chain",
                "description": question,
                "output": summarize_res["answer"],
                "sources": sources,
                "payment_tx": [
                    pay_search["tx"],
                    pay_enrich["tx"],
                    pay_fc["tx"],
                    pay_sum["tx"],
                ],
                "cost_usdc": total_cost,
            }
        ],
        "total_cost_usdc": total_cost,
    }
