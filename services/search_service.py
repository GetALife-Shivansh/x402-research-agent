from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, Depends
from tavily import TavilyClient
from x402_middleware import require_payment

app = FastAPI(title="Paid Search Service")

client = TavilyClient(
    api_key=os.environ["TAVILY_API_KEY"]
)

PRICE = "1000"  # 0.001 USDC


@app.post("/search")
def search(
    payload: dict,
    payment=Depends(
        require_payment(
            price_atomic=PRICE,
            pay_to=os.environ["X402_PAY_TO_SEARCH"],
            resource="/search",
            description="Web search — returns top results with sources",
        )
    )
):
    query = payload["query"]
    max_results = payload.get("max_results", 3)

    res = client.search(
        query,
        max_results=max_results,
        search_depth="advanced"
    )

    results = [
        {
            "content": r["content"],
            "source": r["url"]
        }
        for r in res.get("results", [])
    ]

    return {
        "results": results,
        "payment": payment
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "search"
    }
