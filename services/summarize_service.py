from dotenv import load_dotenv
load_dotenv()

import os

from fastapi import FastAPI, Depends
from langchain_groq import ChatGroq
from x402_middleware import require_payment
from llm_retry import invoke_with_retry


app = FastAPI(title="Paid Summarization Service")


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.3,
    api_key=os.environ["GROQ_API_KEY_SUMMARIZE"]
)


PRICE = "1000"


PROMPT = """Write a concise, well-sourced answer (3-5 sentences) to the sub-question below, using \
the context, key facts, and fact-check notes provided. Cite sources inline as [1], [2] etc, \
matching the order of the sources list below.

Sub-question: {question}

Context:
{context}

Key facts: {key_facts}
Fact-check notes: {factcheck_notes}
Sources (in order): {sources}"""


@app.post("/summarize")
def summarize(
    payload: dict,
    payment=Depends(
        require_payment(
            price_atomic=PRICE,
            pay_to=os.environ["X402_PAY_TO_SUMMARIZE"],
            resource="/summarize",
            description="Citation-aware answer synthesis",
        )
    )
):

    resp = invoke_with_retry(llm, 
        PROMPT.format(
            question=payload["question"],
            context=payload["context"],
            key_facts=payload.get("key_facts", []),
            factcheck_notes=payload.get("factcheck_notes", ""),
            sources=payload.get("sources", []),
        )
    )

    return {
        "answer": resp.content.strip(),
        "payment": payment
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "summarize"
    }
