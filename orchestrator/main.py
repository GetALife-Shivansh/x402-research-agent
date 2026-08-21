from dotenv import load_dotenv
load_dotenv()

import asyncio
import uuid

from orchestrator.graph import graph



def main():

    query = input(
        "Research question: "
    )


    task_id = str(
        uuid.uuid4()
    )


    state = {
        "task_id": task_id,
        "query": query,
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


    result = asyncio.run(
        graph.ainvoke(
            state,
            config=config
        )
    )


    print(
        "\n" + "=" * 70
    )

    print(
        f"TASK ID: {task_id}"
    )

    print(
        "=" * 70
    )

    print(
        result["final_report"]
    )



if __name__ == "__main__":
    main()
