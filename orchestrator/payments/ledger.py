"""
In-memory + append-only JSON-lines log of every autonomous x402 payment
the orchestrator makes, so the final report can show a full audit trail.
"""

import json
import os
import time


LEDGER_PATH = os.environ.get(
    "X402_LEDGER_PATH",
    "payment_ledger.jsonl"
)

_ledger: dict = {}


def record_payment(
    task_id: str,
    service: str,
    payment: dict
) -> dict:

    entry = {
        "task_id": task_id,
        "service": service,
        "tx": payment.get("tx"),
        "network": payment.get("network"),
        "amount_usdc": payment.get(
            "amount_usdc",
            0.0
        ),
        "resource": payment.get("resource"),
        "timestamp": time.time(),
    }

    _ledger.setdefault(
        task_id,
        []
    ).append(entry)


    with open(LEDGER_PATH, "a") as f:
        f.write(
            json.dumps(entry) + "\n"
        )


    return entry



def ledger_summary(task_id: str) -> dict:

    payments = _ledger.get(
        task_id,
        []
    )

    return {
        "payments": payments,
        "count": len(payments),
        "total_usdc": sum(
            p["amount_usdc"]
            for p in payments
        ),
    }
