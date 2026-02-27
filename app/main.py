from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from app.agent.graph import create_graph
from app.db.session import init_db, async_session 
from app.db.models import Task

app = FastAPI()

# Startup event to create DB tables
@app.on_event("startup")
async def startup_event():
    await init_db()

class AgentRequest(BaseModel):
    prompt: str
    mode: str = "auto"

# @app.post("/agent/run")
# async def run_agent(request: AgentRequest):
#     graph = create_graph()
    
#     # Initial state
#     initial_state = {
#         "input_text": request.prompt,
#         "mode": request.mode,
#         "tasks_to_commit": []
#     }
    
#     # Execute the graph
#     result = await graph.ainvoke(initial_state)
    
#     return {
#         "classification": result["classification"],
#         "message": f"Agent classified this as: {result['classification']}"
#     }

# Store the compiled graph globally
agent_executor = create_graph()

@app.post("/agent/run")
async def run_agent(request: AgentRequest):
    # Use a thread_id to track this specific conversation
    config = {"configurable": {"thread_id": "user_1"}} 
    
    initial_state = {
        "input_text": request.prompt,
        "mode": request.mode,
    }
    
    # Run until the interrupt
    async for event in agent_executor.astream(initial_state, config):
        pass # The graph will stop at the interrupt_before
    
    # Get current state to show the user the draft
    state = await agent_executor.aget_state(config)
    
    return {
        "thread_id": "user_1",
        "status": "pending_approval",
        "plan": state.values.get("roadmap_draft")
    }

@app.post("/agent/approve")
async def approve_plan(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    
    # Resume execution (this will move into the Executor node)
    await agent_executor.ainvoke(None, config)
    
    return {"message": "Plan approved and saved to database."}


@app.get("/tasks")
async def get_tasks():
    async with async_session() as session:
        result = await session.execute(select(Task))
        tasks = result.scalars().all()
        return tasks