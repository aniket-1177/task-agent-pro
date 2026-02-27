from typing import Dict
from app.agent.state import AgentState
from app.db.session import async_session
from app.db.models import Task, Roadmap, Category, task_dependencies, TaskStatus

async def executor_node(state: AgentState):
    classification = state["classification"]
    user_input = state["input_text"]
    plan = state["roadmap_draft"]   # Now RoadmapPlan Pydantic model
    
    async with async_session() as session:
        async with session.begin():
            if classification == "simple":
                # Create a single task
                new_task = Task(
                    title=user_input[:100], 
                    description=user_input,
                    category=Category.PERSONAL# Default for simple
                )
                session.add(new_task)
            
            else:
                # Complex case - roadmap + multiple tasks with dependencies
                new_roadmap = Roadmap(goal=user_input)
                session.add(new_roadmap)
                await session.flush()  # Get roadmap.id

                # Mapping: LLM integer ID → SQLAlchemy Task instance
                id_mapping: Dict[int, Task] = {}

                # First pass: create all tasks without dependencies
                for idx, task_plan in enumerate(plan.tasks, start=1):  # ← .tasks (Pydantic list)
                    new_task = Task(
                        title=task_plan.title,
                        description=task_plan.description,
                        category=Category[task_plan.category.upper()],
                        priority=task_plan.priority,
                        roadmap_id=new_roadmap.id,
                        status=TaskStatus.PENDING,  # explicit default
                        dependencies=[],
                    )
                    session.add(new_task)
                    effective_id = task_plan.id if task_plan.id is not None else idx
                    id_mapping[effective_id] = new_task
                    # id_mapping[task_plan.id] = new_task

                await session.flush()  # Ensure all tasks have .id populated

                # Second pass: link dependencies using many-to-many
                for task_plan in plan.tasks:
                    if task_plan.dependencies:  # list of int IDs
                        current_task = id_mapping[task_plan.id]
                        for dep_llm_id in task_plan.dependencies:
                            parent_task = id_mapping.get(dep_llm_id)
                            if parent_task:
                                current_task.dependencies.append(parent_task)
                            else:
                                # Optional: log warning or skip
                                print(f"Warning: Dependency ID {dep_llm_id} not found")

            await session.commit()

    return {
        "messages": [("ai", "All tasks (with dependencies) have been saved to the database.")],
        "tasks_to_commit": []  # optional: can populate if needed later
    }