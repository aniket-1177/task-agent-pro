from fastapi import FastAPI
from pydantic import BaseModel
from app.agent.graph import create_graph
from app.db.session import init_db

app = FastAPI()

# Startup event to create DB tables
@app.on_event("startup")
async def startup_event():
    await init_db()

class AgentRequest(BaseModel):
    prompt: str
    mode: str = "auto"

@app.post("/agent/run")
async def run_agent(request: AgentRequest):
    graph = create_graph()
    
    # Initial state
    initial_state = {
        "input_text": request.prompt,
        "mode": request.mode,
        "tasks_to_commit": []
    }
    
    # Execute the graph
    result = await graph.ainvoke(initial_state)
    
    return {
        "classification": result["classification"],
        "message": f"Agent classified this as: {result['classification']}"
    }