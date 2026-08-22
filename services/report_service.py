from dotenv import load_dotenv
load_dotenv()

import os

from fastapi import FastAPI, Depends
from langchain_groq import ChatGroq
from x402_middleware import require_payment
from llm_retry import invoke_with_retry


app = FastAPI(title="Paid Report Generation Service")


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.3,
    api_key=os.environ.get("GROQ_API_KEY_REPORT", "dummy_key")
)


PRICE = "3000"


PROMPT = """You are a senior research writer. Using the findings below, write a well-structured \
markdown report answering the original question. Use headings, and reuse the [n] citation \
markers exactly as given in each section — do not renumber them, and do not write your own \
sources section (it is appended automatically by the caller).

Original question: {query}

Findings:
{sections}"""


@app.post("/report")
def report(
    payload: dict,
    payment=Depends(
        require_payment(
            price_atomic=PRICE,
            pay_to=os.environ.get("X402_PAY_TO_REPORT", "0x0"),
            resource="/report",
            description="Final cited report compilation",
        )
    )
):

    sections_text = "\n\n".join(
        f"### {s['question']}\n{s['answer']}"
        for s in payload["sections"]
    )

    resp = invoke_with_retry(llm, 
        PROMPT.format(
            query=payload["query"],
            sections=sections_text
        )
    )

    return {
        "report_markdown": resp.content.strip(),
        "payment": payment
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "report"
    }
