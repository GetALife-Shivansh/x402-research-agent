from orchestrator.payments.ledger import (
    ledger_summary,
    record_payment
)

from orchestrator.payments.x402_client import (
    call_paid_service
)

from orchestrator.state import OrchestratorState
from orchestrator.tracing import traced_node

@traced_node("writer")
def writer_node(state: OrchestratorState) -> dict:

    global_sources = []
    seen = {}

    sections = []

    for r in state["subtask_results"]:

        for src in r["sources"]:

            if src not in seen:
                seen[src] = len(global_sources) + 1
                global_sources.append(src)

        sections.append(
            {
                "question": r["description"],
                "answer": r["output"],
                "sources": r["sources"]
            }
        )

    report_res, pay_report = call_paid_service(
        "report",
        {
            "query": state["query"],
            "sections": sections,
        }
    )

    record_payment(
        state["task_id"],
        "report",
        pay_report
    )

    report = report_res["report_markdown"]

    if global_sources:

        footer = "\n".join(
            f"{i + 1}. [{url}]({url})"
            for i, url in enumerate(global_sources)
        )

        report += (
            "\n\n---\n"
            "**Sources**\n"
            + footer
        )

    summary = ledger_summary(
        state["task_id"]
    )

    ledger_md = "\n".join(
        f"- `{p['service']}` → tx `{p['tx']}` — "
        f"₳{p.get('amount_algo', p.get('amount_usdc', 0.0)):.4f} ALGO "
        f"({p['network']})"
        for p in summary["payments"]
    )

    report += (
        f"\n\n---\n"
        f"**Algorand Autonomous Payment Ledger** — "
        f"{summary['count']} x402 payments, "
        f"total ₳{summary.get('total_algo', summary.get('total_usdc', 0.0)):.4f} ALGO\n"
        f"{ledger_md}"
    )

    return {
        "final_report": report,
        "total_cost_usdc": pay_report.get("amount_algo", pay_report.get("amount_usdc", 0.0))
    }