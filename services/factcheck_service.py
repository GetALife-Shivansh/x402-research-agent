from dotenv import load_dotenv
load_dotenv()

import json
import os
import re

from fastapi import FastAPI, Depends
from langchain_groq import ChatGroq
from tavily import TavilyClient
from x402_middleware import require_payment
from llm_retry import invoke_with_retry


app = FastAPI(title="Paid Fact-Check Service")


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=os.environ["GROQ_API_KEY_FACTCHECK"]
)

tavily = TavilyClient(
    api_key=os.environ["TAVILY_API_KEY"]
)


PRICE = "1500"


PROMPT = """You are a fact-checker. Given a question, claimed facts, the original context, and \
a fresh cross-reference search, judge whether the claims hold up. Respond ONLY with JSON, no prose:
{{"verdict": "confirmed" | "partially confirmed" | "unconfirmed", "confidence": 0.0-1.0, \
"notes": "1-2 sentence explanation"}}

Question: {question}
Claimed facts: {claims}
Original context: {context}
Cross-reference search: {crossref}"""


def _parse(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)

    if not m:
        return {
            "verdict": "unconfirmed",
            "confidence": 0.0,
            "notes": "parse error"
        }

    try:
        return json.loads(m.group())

    except Exception:
        return {
            "verdict": "unconfirmed",
            "confidence": 0.0,
            "notes": "parse error"
        }


@app.post("/factcheck")
def factcheck(
    payload: dict,
    payment=Depends(
        require_payment(
            price_atomic=PRICE,
            pay_to=os.environ["X402_PAY_TO_FACTCHECK"],
            resource="/factcheck",
            description="Cross-referenced fact verification",
        )
    )
):

    crossref_hits = tavily.search(
        payload["question"],
        max_results=2,
        search_depth="basic"
    )

    crossref = "\n".join(
        r["content"][:300]
        for r in crossref_hits.get("results", [])
    )


    resp = invoke_with_retry(llm, 
        PROMPT.format(
            question=payload["question"],
            claims=payload.get("claims", []),
            context=payload["context"],
            crossref=crossref or "No additional cross-reference found.",
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
        "service": "factcheck"
    }
