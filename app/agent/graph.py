from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver # For local dev, In production, we'd use PostgresSaver
from app.agent.state import AgentState
from app.agent.nodes.router import router_node
from app.agent.nodes.planner import planner_node
from app.agent.nodes.executor import executor_node # Create this file

memory = MemorySaver()

def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("router", router_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)

    workflow.set_entry_point("router")

    # The Logic Gate
    def route_decision(state: AgentState):
        if state["classification"] == "simple":
            return "executor"
        return "planner"

    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "executor": "executor",
            "planner": "planner"
        }
    )

    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", END)

    # return workflow.compile()
    return workflow.compile(checkpointer=memory, interrupt_before=["executor"])