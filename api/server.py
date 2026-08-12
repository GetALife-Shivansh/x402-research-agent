import uuid

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from orchestrator.graph import graph
from orchestrator.payments.ledger import ledger_summary


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

    task_id = str(
        uuid.uuid4()
    )


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


    result = graph.invoke(
        state,
        config=config
    )


    summary = ledger_summary(
        task_id
    )


    return {
        "task_id": task_id,
        "report_markdown": result["final_report"],
        "plan": result["plan"],
        "payments": summary,
    }



@app.get("/health")
async def health():

    return {
        "status": "ok"
    }


@app.get("/")
async def frontend():
    return FileResponse("frontend/index.html")

