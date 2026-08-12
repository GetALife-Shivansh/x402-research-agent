from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from orchestrator.nodes.critic import critic_node
from orchestrator.nodes.researcher import (
    fan_out_to_researchers,
    researcher_node
)
from orchestrator.nodes.supervisor import supervisor_node
from orchestrator.nodes.writer import writer_node
from orchestrator.state import OrchestratorState



def route_after_critic(state: OrchestratorState) -> str:
    return (
        "supervisor"
        if state.get("review_feedback")
        else "writer"
    )



def build_graph():

    builder = StateGraph(
        OrchestratorState
    )


    builder.add_node(
        "supervisor",
        supervisor_node
    )

    builder.add_node(
        "researcher",
        researcher_node
    )

    builder.add_node(
        "critic",
        critic_node
    )

    builder.add_node(
        "writer",
        writer_node
    )


    builder.add_edge(
        START,
        "supervisor"
    )


    builder.add_conditional_edges(
        "supervisor",
        fan_out_to_researchers,
        [
            "researcher"
        ]
    )


    builder.add_edge(
        "researcher",
        "critic"
    )


    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        [
            "supervisor",
            "writer"
        ]
    )


    builder.add_edge(
        "writer",
        END
    )


    return builder.compile(
        checkpointer=MemorySaver()
    )



graph = build_graph()
