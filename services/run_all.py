"""One-command launcher for all 5 paid x402 microservices."""

from dotenv import load_dotenv

load_dotenv()

import multiprocessing as mp
import os

import uvicorn


SERVICES = [
    (
        "services.search_service:app",
        int(os.environ.get("SEARCH_SERVICE_PORT", 8001)),
    ),
    (
        "services.summarize_service:app",
        int(os.environ.get("SUMMARIZE_SERVICE_PORT", 8002)),
    ),
    (
        "services.factcheck_service:app",
        int(os.environ.get("FACTCHECK_SERVICE_PORT", 8003)),
    ),
    (
        "services.enrich_service:app",
        int(os.environ.get("ENRICH_SERVICE_PORT", 8004)),
    ),
    (
        "services.report_service:app",
        int(os.environ.get("REPORT_SERVICE_PORT", 8005)),
    ),
]


def _run(app_path: str, port: int):
    uvicorn.run(
        app_path,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


def main():
    processes = []

    print("Starting paid x402 services...")

    for app_path, port in SERVICES:
        process = mp.Process(
            target=_run,
            args=(app_path, port),
        )

        process.start()
        processes.append(process)

    print("\nLaunched paid x402 services:\n")

    for app_path, port in SERVICES:
        print(
            f"  - {app_path:<35} "
            f"http://localhost:{port}"
        )

    print()

    try:
        for process in processes:
            process.join()

    except KeyboardInterrupt:
        print("\nStopping paid x402 services...")

        for process in processes:
            if process.is_alive():
                process.terminate()

        for process in processes:
            process.join(timeout=5)


if __name__ == "__main__":
    main()