from typing import Annotated, TypedDict, List, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Standard conversation history
    messages: Annotated[list, add_messages]
    
    # Custom fields for our logic
    input_text: str
    mode: str  # "auto", "todo", or "blueprint"
    classification: str  # "simple" or "complex"
    roadmap_draft: Optional[dict]
    category_hint: Optional[str]
    tasks_to_commit: List[dict]
    is_approved: bool