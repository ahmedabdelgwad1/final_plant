from infrastructure.agents import (
    vision_agent,
    retriever_agent,
    response_agent,
    evidence_agent,
    plantnet_agent,
    verify_agent,
)
from domain.models import State
from langgraph.graph import StateGraph, START, END


def build_workflow():
    graph = StateGraph(State)

    graph.add_node("vision_agent", vision_agent)
    graph.add_node("retriever_agent", retriever_agent)
    graph.add_node("response_agent", response_agent)
    graph.add_node("evidence_agent", evidence_agent)
    graph.add_node("plantnet_agent", plantnet_agent)
    graph.add_node("verify_agent", verify_agent)

    graph.add_edge(START, "vision_agent")
    graph.add_edge("vision_agent", "retriever_agent")
    graph.add_edge("retriever_agent", "evidence_agent")
    graph.add_edge("evidence_agent", "plantnet_agent")
    graph.add_edge("plantnet_agent", "verify_agent")
    graph.add_edge("verify_agent", "response_agent")
    graph.add_edge("response_agent", END)

    return graph.compile()


app_workflow = build_workflow()


class Workflow:
    def run(self, initial_state: State):
        result = app_workflow.invoke(initial_state)
        return result

