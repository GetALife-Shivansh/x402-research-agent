from dotenv import load_dotenv
load_dotenv()

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, Depends
from langchain_groq import ChatGroq
from tavily import TavilyClient
from x402_middleware import require_payment
from llm_retry import invoke_with_retry

app = FastAPI(title="Paid Fact-Check & Truthfulness Service")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=os.environ["GROQ_API_KEY_FACTCHECK"]
)

tavily = TavilyClient(
    api_key=os.environ["TAVILY_API_KEY"]
)

PRICE = "1500"

PROMPT = """You are a rigorous, highly skeptical evidence-based fact verification system.
Your job is to critically evaluate whether the given target claim is factually true or false.

STRICT SCORING RULES:
1. If the claim makes assertions that are unsubstantiated, speculative, exaggerated, unverified, or factually incorrect (e.g. claiming major industrial chip exports for a country that has no active commercial fabrication export market), give it a LOW truthfulness_score (between 0.00 and 0.35) and set status to "Very Likely False" or "Probably False" / "Disputed".
2. Do NOT give high scores (0.7-1.0) unless there is concrete, verified, official web evidence directly confirming the specific claim.
3. If fresh web search fails to confirm the specific assertion, assign a low score (e.g., 0.1 - 0.4) and mark it as "Disputed" or "Unconfirmed / Unsupported".

Respond ONLY with JSON matching this structure:
{{
  "verdict": "confirmed" | "partially confirmed" | "unconfirmed" | "disputed",
  "truthfulness_score": 0.0 - 1.0,
  "evidence_confidence": "Low" | "Medium" | "High",
  "status": "Strongly Supported" | "Probably True" | "Disputed" | "Probably False" | "Very Likely False",
  "summary": "1-2 sentence overview of the evidence balance and why the score was assigned",
  "supporting_evidence": [
    {{
      "explanation": "Short explanation of supporting proof",
      "source": "Source / Organization Name",
      "citation": "URL or citation title",
      "strength": "Strong" | "Moderate" | "Weak",
      "date": "Optional date or N/A"
    }}
  ],
  "contradicting_evidence": [
    {{
      "explanation": "Short explanation of contradicting or weakening proof",
      "source": "Source / Organization Name",
      "citation": "URL or citation title",
      "strength": "Strong" | "Moderate" | "Weak",
      "date": "Optional date or N/A"
    }}
  ]
}}

Question: {question}
Claim: {claims}
Original Context: {context}
Supporting Search Context: {supporting_search}
Contradicting Search Context: {contradicting_search}"""

def _parse(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)

    if not m:
        return {
            "verdict": "unconfirmed",
            "truthfulness_score": 0.5,
            "evidence_confidence": "Low",
            "status": "Disputed",
            "summary": "Parse error during verification",
            "supporting_evidence": [],
            "contradicting_evidence": []
        }

    try:
        return json.loads(m.group())

    except Exception:
        return {
            "verdict": "unconfirmed",
            "truthfulness_score": 0.5,
            "evidence_confidence": "Low",
            "status": "Disputed",
            "summary": "Parse error during verification",
            "supporting_evidence": [],
            "contradicting_evidence": []
        }

@app.post("/factcheck")
def factcheck(
    payload: dict,
    payment=Depends(
        require_payment(
            price_atomic=PRICE,
            pay_to=os.environ["X402_PAY_TO_FACTCHECK"],
            resource="/factcheck",
            description="Truthfulness & evidence verification audit",
        )
    )
):
    question = payload.get("question", "")
    claims = payload.get("claims", [])
    claim_text = " ".join(claims) if isinstance(claims, list) else str(claims)

    # Active search for supporting and disconfirming evidence in parallel
    def _search_support():
        try:
            return tavily.search(f"{question} {claim_text}", max_results=3, search_depth="basic")
        except Exception:
            return {}

    def _search_contra():
        try:
            return tavily.search(f"{claim_text} false inaccurate myth controversy criticism debate opposition", max_results=3, search_depth="basic")
        except Exception:
            return {}

    with ThreadPoolExecutor(max_workers=2) as executor:
        f_supp = executor.submit(_search_support)
        f_contra = executor.submit(_search_contra)
        support_hits = f_supp.result()
        contra_hits = f_contra.result()

    supporting_search = "\n".join(
        f"[{r.get('title', 'Source')}]: {r.get('content', '')[:300]} (URL: {r.get('url', '')})"
        for r in support_hits.get("results", [])
    )

    contradicting_search = "\n".join(
        f"[{r.get('title', 'Source')}]: {r.get('content', '')[:300]} (URL: {r.get('url', '')})"
        for r in contra_hits.get("results", [])
    )

    resp = invoke_with_retry(llm, 
        PROMPT.format(
            question=question,
            claims=claim_text,
            context=payload.get("context", ""),
            supporting_search=supporting_search or "No direct supporting sources found.",
            contradicting_search=contradicting_search or "No disconfirming evidence found.",
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