from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from app.agent.state import AgentState

# We define exactly what a "Planned Task" looks like
class TaskPlan(BaseModel):
    id: Optional[int] = Field(description="Unique index for this plan (e.g., 1, 2, 3)")
    title: str = Field(description="Short title of the task")
    description: str = Field(description="Detailed explanation of what to do")
    category: str = Field(description="One of: office, personal, chores, fitness")
    priority: int = Field(description="Priority from 1 (low) to 3 (high)")
    dependencies: List[int] = Field(description="List of IDs this task depends on", default=[])

class RoadmapPlan(BaseModel):
    tasks: List[TaskPlan]

# Using a larger model for planning
planner_llm = ChatGroq(model="llama-3.3-70b-versatile")

async def planner_node(state: AgentState):
    user_input = state["input_text"]
    
    # We use .with_structured_output to force JSON compliance
    structured_llm = planner_llm.with_structured_output(RoadmapPlan)
    
    prompt = f"""
    You are an expert project planner.
    Decompose the following goal into a detailed roadmap.

    Goal: "{user_input}"

    Rules YOU MUST FOLLOW:
    1. Assign EVERY task a unique integer "id" starting from 1 and increasing by 1 (1, 2, 3, ...).
    Do NOT skip numbers. Do NOT reuse numbers.
    2. If a task depends on earlier tasks, list their "id" values in the "dependencies" array.
    3. Respond ONLY with valid JSON — no extra text, no explanations.
    4. Use EXACTLY this structure:
    {{
    "tasks": [
        {{
        "id": 1,
        "title": "Short title",
        "description": "Detailed description",
        "category": "office" | "personal" | "chores" | "fitness" (lowercase),
        "priority": 1 | 2 | 3,
        "dependencies": []   // or [2, 3] etc.
        }},
        ...
    ]
    }}

    Example for a simple goal:
    {{
    "tasks": [
        {{"id": 1, "title": "Research", "description": "...", "category": "personal", "priority": 2, "dependencies": []}},
        {{"id": 2, "title": "Implement", "description": "...", "category": "office", "priority": 3, "dependencies": [1]}}
    ]
    }}
    """
    
    response = await structured_llm.ainvoke(prompt)
    
    # Convert Pydantic model to dict for LangGraph state
    print(type(response), response)  # add temporarily before return
    # return {"roadmap_draft": response.dict()}
    return {"roadmap_draft": response}

