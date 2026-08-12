import os
import subprocess
import sys
import time


def main():
    processes = []

    try:
        # Start the original x402 service launcher.
        # This launches all five paid services:
        #
        # 8001 search
        # 8002 summarize
        # 8003 factcheck
        # 8004 enrich
        # 8005 report

        print("Starting paid x402 services...")

        services = subprocess.Popen(
            [
                sys.executable,
                "services/run_all.py",
            ]
        )

        processes.append(services)

        # Give the five services time to start.
        time.sleep(5)

        # Railway provides PORT.
        # Locally we use 8000.
        port = int(os.environ.get("PORT", "8000"))

        print(f"Starting main API on port {port}...")

        api = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "api.server:app",
                "--host",
                "0.0.0.0",
                "--port",
                str(port),
            ]
        )

        processes.append(api)

        # Keep the application alive.
        api.wait()

    except KeyboardInterrupt:
        print("\nStopping x402...")

    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()

        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    main()