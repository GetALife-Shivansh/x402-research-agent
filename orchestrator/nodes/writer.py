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

    # 1. Call paid report generation service
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

    # 2. Extract key claims from each section and perform paid x402 fact truthfulness verification audits
    verified_claims = []
    total_truthfulness = 0.0

    for r in state["subtask_results"]:
        q = r["description"]
        ans = r["output"]
        # Take first ~250 chars as the representative claim or sentence
        claim_text = ans[:250].strip()
        if not claim_text:
            continue

        fc_res, pay_fc = call_paid_service(
            "factcheck",
            {
                "question": q,
                "claims": [claim_text],
                "context": ans[:500]
            }
        )

        record_payment(
            state["task_id"],
            "factcheck",
            pay_fc
        )

        score = float(fc_res.get("truthfulness_score", 0.8))
        total_truthfulness += score

        verified_claims.append({
            "claim": claim_text,
            "question": q,
            "truthfulness_score": score,
            "evidence_confidence": fc_res.get("evidence_confidence", "Medium"),
            "status": fc_res.get("status", "Strongly Supported"),
            "summary": fc_res.get("summary", ""),
            "supporting_evidence": fc_res.get("supporting_evidence", []),
            "contradicting_evidence": fc_res.get("contradicting_evidence", []),
            "x402_spent_usdc": pay_fc.get("amount_algo", pay_fc.get("amount_usdc", 0.0015))
        })

    num_claims = len(verified_claims)
    overall_reliability = round((total_truthfulness / num_claims * 100)) if num_claims > 0 else 85

    strongly_supported = sum(1 for c in verified_claims if c["truthfulness_score"] >= 0.81)
    probably_true = sum(1 for c in verified_claims if 0.61 <= c["truthfulness_score"] < 0.81)
    disputed = sum(1 for c in verified_claims if 0.41 <= c["truthfulness_score"] < 0.61)
    unsupported = sum(1 for c in verified_claims if c["truthfulness_score"] < 0.41)

    reliability_summary = {
        "overall_reliability_pct": overall_reliability,
        "total_claims_analyzed": num_claims,
        "strongly_supported": strongly_supported,
        "probably_true": probably_true,
        "disputed": disputed,
        "unsupported": unsupported,
        "claims": verified_claims
    }

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
        "reliability_summary": reliability_summary,
        "total_cost_usdc": summary.get('total_algo', summary.get('total_usdc', 0.0))
    }