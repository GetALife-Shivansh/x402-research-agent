"""One-command launcher for all 5 paid x402 microservices."""

from dotenv import load_dotenv
load_dotenv()

import multiprocessing as mp
import os

import uvicorn


SERVICES = [
    (
        "search_service:app",
        int(os.environ.get("SEARCH_SERVICE_PORT", 8001))
    ),
    (
        "summarize_service:app",
        int(os.environ.get("SUMMARIZE_SERVICE_PORT", 8002))
    ),
    (
        "factcheck_service:app",
        int(os.environ.get("FACTCHECK_SERVICE_PORT", 8003))
    ),
    (
        "enrich_service:app",
        int(os.environ.get("ENRICH_SERVICE_PORT", 8004))
    ),
    (
        "report_service:app",
        int(os.environ.get("REPORT_SERVICE_PORT", 8005))
    ),
]


def _run(app_path: str, port: int):
    uvicorn.run(
        app_path,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


if __name__ == "__main__":

    procs = []

    for app_path, port in SERVICES:
        p = mp.Process(
            target=_run,
            args=(app_path, port)
        )
        p.start()
        procs.append(p)


    print("Launched paid x402 services:")

    for app_path, port in SERVICES:
        print(
            f"  - {app_path:<25} http://localhost:{port}"
        )


    for p in procs:
        p.join()
