"""
Shared server-side x402 payment-required middleware for the paid microservices.

Implements the x402 wire protocol:
  1. Client calls endpoint without payment -> server replies 402.
  2. Client sends signed payment in X-PAYMENT header.
  3. Server verifies and settles payment.
"""

from dotenv import load_dotenv
load_dotenv()

import base64
import json
import os
import time
import uuid
from typing import Optional

import requests
from fastapi import Header, HTTPException

X402_VERSION = 1
MOCK_MODE = os.environ.get("X402_MOCK", "true").lower() == "true"
NETWORK = os.environ.get("X402_NETWORK", "base-sepolia")
FACILITATOR_URL = os.environ.get(
    "X402_FACILITATOR_URL",
    "https://x402.org/facilitator"
)

USDC_ADDRESS = os.environ.get(
    "X402_USDC_ADDRESS",
    "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
)


def _payment_requirements(
    price_atomic: str,
    pay_to: str,
    resource: str,
    description: str
) -> dict:
    return {
        "scheme": "exact",
        "network": NETWORK,
        "maxAmountRequired": price_atomic,
        "resource": resource,
        "description": description,
        "mimeType": "application/json",
        "payTo": pay_to,
        "maxTimeoutSeconds": 60,
        "asset": USDC_ADDRESS,
        "extra": {
            "name": "USDC",
            "version": "2"
        },
    }


def _facilitator_verify(payment_payload: dict, requirements: dict) -> dict:
    if MOCK_MODE:
        return {
            "isValid": True,
            "invalidReason": None
        }

    resp = requests.post(
        f"{FACILITATOR_URL}/verify",
        json={
            "x402Version": X402_VERSION,
            "paymentPayload": payment_payload,
            "paymentRequirements": requirements,
        },
        timeout=10,
    )

    resp.raise_for_status()
    return resp.json()


def _facilitator_settle(payment_payload: dict, requirements: dict) -> dict:
    if MOCK_MODE:
        return {
            "success": True,
            "transaction": "0xmock" + uuid.uuid4().hex,
            "network": NETWORK
        }

    resp = requests.post(
        f"{FACILITATOR_URL}/settle",
        json={
            "x402Version": X402_VERSION,
            "paymentPayload": payment_payload,
            "paymentRequirements": requirements,
        },
        timeout=15,
    )

    resp.raise_for_status()
    return resp.json()


def require_payment(
    price_atomic: str,
    pay_to: str,
    resource: str,
    description: str
):
    """
    FastAPI dependency factory.

    Example:
    Depends(
        require_payment(
            "1000",
            pay_to_addr,
            "/search",
            "Web search"
        )
    )
    """

    requirements = _payment_requirements(
        price_atomic,
        pay_to,
        resource,
        description
    )

    def dependency(
        x_payment: Optional[str] = Header(
            default=None,
            alias="X-PAYMENT"
        )
    ):

        if not x_payment:
            raise HTTPException(
                status_code=402,
                detail={
                    "x402Version": X402_VERSION,
                    "error": "X-PAYMENT header is required",
                    "accepts": [requirements],
                },
            )

        try:
            decoded = json.loads(
                base64.b64decode(x_payment)
            )

        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Malformed X-PAYMENT header"
            )


        verification = _facilitator_verify(
            decoded,
            requirements
        )

        if not verification.get("isValid", False):
            raise HTTPException(
                status_code=402,
                detail={
                    "x402Version": X402_VERSION,
                    "error": verification.get(
                        "invalidReason",
                        "payment invalid"
                    ),
                    "accepts": [requirements],
                },
            )


        settlement = _facilitator_settle(
            decoded,
            requirements
        )


        return {
            "tx": settlement.get("transaction"),
            "network": settlement.get(
                "network",
                NETWORK
            ),
            "amount_usdc": int(price_atomic) / 1_000_000,
            "payer": decoded.get(
                "payload",
                {}
            ).get(
                "authorization",
                {}
            ).get(
                "from"
            ),
            "resource": resource,
            "settled_at": time.time(),
        }


    return dependency
