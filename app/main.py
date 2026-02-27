from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.db.models import Roadmap
from app.agent.utils import sort_tasks_topologically
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
    
@app.get("/roadmaps/{roadmap_id}/tree")
async def get_roadmap_tree(roadmap_id: UUID):
    async with async_session() as session:
        # Load roadmap and tasks + dependencies in a single query
        query = (
            select(Roadmap)
            .options(selectinload(Roadmap.tasks).selectinload(Task.dependencies))
            .where(Roadmap.id == roadmap_id)
        )
        result = await session.execute(query)
        roadmap = result.scalar_one_or_none()

        if not roadmap:
            raise HTTPException(status_code=404, detail="Roadmap not found")

        # Sort the tasks using our utility
        ordered_tasks = sort_tasks_topologically(roadmap.tasks)

        return {
            "goal": roadmap.goal,
            "created_at": roadmap.created_at,
            "timeline": [
                {
                    "id": t.id,
                    "title": t.title,
                    "category": t.category.value,
                    "status": t.status.value,
                    "depends_on": [dep.title for dep in t.dependencies]
                }
                for t in ordered_tasks
            ]
        }