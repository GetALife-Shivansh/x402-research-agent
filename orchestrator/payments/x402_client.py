"""Client-side x402 payment flow: calls a paid endpoint, and if it gets a 402
back, signs an EIP-3009 transferWithAuthorization for the exact amount
requested, attaches it as X-PAYMENT, and retries.
"""

from dotenv import load_dotenv
load_dotenv()

import base64
import json
import os
import secrets
import time

import httpx
from eth_account import Account
from eth_account.messages import encode_typed_data


SERVICE_URLS = {
    "search": os.environ.get(
        "SEARCH_SERVICE_URL",
        "http://localhost:8001/search"
    ),
    "enrich": os.environ.get(
        "ENRICH_SERVICE_URL",
        "http://localhost:8004/enrich"
    ),
    "factcheck": os.environ.get(
        "FACTCHECK_SERVICE_URL",
        "http://localhost:8003/factcheck"
    ),
    "summarize": os.environ.get(
        "SUMMARIZE_SERVICE_URL",
        "http://localhost:8002/summarize"
    ),
    "report": os.environ.get(
        "REPORT_SERVICE_URL",
        "http://localhost:8005/report"
    ),
}


CHAIN_IDS = {
    "base-sepolia": 84532,
    "base": 8453
}


_private_key = (
    os.environ.get("X402_PAYER_PRIVATE_KEY")
    or ("0x" + secrets.token_hex(32))
)

_account = Account.from_key(_private_key)



def _sign_payment(requirements: dict) -> dict:

    network = requirements["network"]

    valid_after = 0

    valid_before = (
        int(time.time())
        + requirements.get(
            "maxTimeoutSeconds",
            60
        )
    )

    nonce = "0x" + secrets.token_hex(32)

    value = int(
        requirements["maxAmountRequired"]
    )


    domain = {
        "name": requirements.get(
            "extra",
            {}
        ).get(
            "name",
            "USDC"
        ),
        "version": requirements.get(
            "extra",
            {}
        ).get(
            "version",
            "2"
        ),
        "chainId": CHAIN_IDS.get(
            network,
            84532
        ),
        "verifyingContract": requirements["asset"],
    }


    message_types = {
        "TransferWithAuthorization": [
            {
                "name": "from",
                "type": "address"
            },
            {
                "name": "to",
                "type": "address"
            },
            {
                "name": "value",
                "type": "uint256"
            },
            {
                "name": "validAfter",
                "type": "uint256"
            },
            {
                "name": "validBefore",
                "type": "uint256"
            },
            {
                "name": "nonce",
                "type": "bytes32"
            },
        ]
    }


    message = {
        "from": _account.address,
        "to": requirements["payTo"],
        "value": value,
        "validAfter": valid_after,
        "validBefore": valid_before,
        "nonce": nonce,
    }


    signable = encode_typed_data(
        domain_data=domain,
        message_types=message_types,
        message_data=message
    )

    signed = _account.sign_message(
        signable
    )


    return {
        "x402Version": 1,
        "scheme": "exact",
        "network": network,
        "payload": {
            "signature": signed.signature.hex(),
            "authorization": {
                "from": _account.address,
                "to": requirements["payTo"],
                "value": str(value),
                "validAfter": str(valid_after),
                "validBefore": str(valid_before),
                "nonce": nonce,
            },
        },
    }



def call_paid_service(
    service: str,
    json_body: dict,
    timeout: float = 60.0
):
    """
    Full 402 -> sign -> retry flow.
    Returns (response_json, payment_receipt).
    """

    url = SERVICE_URLS[service]


    with httpx.Client(timeout=timeout) as client:

        first = client.post(
            url,
            json=json_body
        )


        if first.status_code != 402:

            first.raise_for_status()

            body = first.json()

            return (
                body,
                body.get(
                    "payment",
                    {
                        "tx": None,
                        "amount_usdc": 0.0,
                        "network": "n/a"
                    }
                )
            )


        requirements = first.json()["detail"]["accepts"][0]


        payment_payload = _sign_payment(
            requirements
        )


        header_value = base64.b64encode(
            json.dumps(payment_payload).encode()
        ).decode()


        second = client.post(
            url,
            json=json_body,
            headers={
                "X-PAYMENT": header_value
            }
        )


        second.raise_for_status()

        body = second.json()


        return (
            body,
            body.get(
                "payment",
                {
                    "tx": None,
                    "amount_usdc": 0.0,
                    "network": requirements["network"]
                }
            )
        )
