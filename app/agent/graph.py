from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes.router import router_node

def create_graph():
    workflow = StateGraph(AgentState)

    # Add the router node
    workflow.add_node("router", router_node)

    # Define the starting point
    workflow.set_entry_point("router")

    # Add conditional logic
    # We will expand these destinations in the next step
    workflow.add_edge("router", END)

    return workflow.compile()