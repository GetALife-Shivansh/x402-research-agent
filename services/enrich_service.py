from dotenv import load_dotenv
load_dotenv()

import json
import os
import re

from fastapi import FastAPI, Depends
from langchain_groq import ChatGroq
from x402_middleware import require_payment
from llm_retry import invoke_with_retry


app = FastAPI(title="Paid Data Enrichment Service")


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=os.environ.get("GROQ_API_KEY_ENRICH", "dummy_key")
)


PRICE = "1000"


PROMPT = """Extract the key facts, figures, names, and dates relevant to the question below, \
from the given context only. Respond ONLY with JSON, no prose:
{{"key_facts": ["fact 1", "fact 2", ...], "entities": ["entity 1", ...]}}

Question: {question}
Context:
{context}"""


def _parse(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)

    if not m:
        return {
            "key_facts": [],
            "entities": []
        }

    try:
        return json.loads(m.group())

    except Exception:
        return {
            "key_facts": [],
            "entities": []
        }


@app.post("/enrich")
def enrich(
    payload: dict,
    payment=Depends(
        require_payment(
            price_atomic=PRICE,
            pay_to=os.environ.get("X402_PAY_TO_ENRICH", "0x0"),
            resource="/enrich",
            description="Structured fact & entity extraction from research context",
        )
    )
):

    resp = invoke_with_retry(llm, 
        PROMPT.format(
            question=payload["question"],
            context=payload["context"]
        )
    )

    data = _parse(resp.content)

    return {
        **data,
        "payment": payment
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "enrich"
    }
