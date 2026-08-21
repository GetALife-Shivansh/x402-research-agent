import logging
import traceback
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from orchestrator.graph import graph
from orchestrator.payments.ledger import ledger_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

app = FastAPI(
    title="x402 Research Orchestrator API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class ResearchRequest(BaseModel):
    query: str

@app.post("/research")
async def research(
    req: ResearchRequest
):
    task_id = str(uuid.uuid4())

    state = {
        "task_id": task_id,
        "query": req.query,
        "plan": None,
        "subtask_results": [],
        "review_feedback": None,
        "retry_count": {},
        "final_report": "",
        "total_cost_usdc": 0.0,
    }

    config = {
        "configurable": {
            "thread_id": task_id
        }
    }

    try:
        result = graph.invoke(
            state,
            config=config
        )

        summary = ledger_summary(task_id)

        return {
            "task_id": task_id,
            "report_markdown": result.get("final_report", ""),
            "reliability_summary": result.get("reliability_summary"),
            "plan": result.get("plan"),
            "payments": summary,
        }
    except Exception as e:
        logger.error(f"Error during graph execution: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Orchestrator error: {str(e)}"
        )

@app.get("/health")
async def health():
    return {
        "status": "ok"
    }

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
