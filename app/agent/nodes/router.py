import json
from langchain_groq import ChatGroq
from app.agent.state import AgentState

llm = ChatGroq(model="llama-3.1-8b-instant")

async def router_node(state: AgentState):
    user_input = state["input_text"]
    mode = state.get("mode", "auto")

    # If user explicitly chose a mode, respect it
    if mode == "todo":
        return {"classification": "simple"}
    if mode == "blueprint":
        return {"classification": "complex"}

    # Otherwise, ask the LLM to decide
    # prompt = f"""
    # Analyze this request: "{user_input}"
    # If it's a single, clear task (e.g., 'Remind me to buy milk'), return 'simple'.
    # If it's a goal requiring multiple steps (e.g., 'Plan a trip to Japan'), return 'complex'.
    # Return ONLY the word 'simple' or 'complex'.
    # """
    prompt = f"""
    Classification Task:
    Input: "{user_input}"
    Rules:
    - If it's a single task, reply: simple
    - If it's a project/multiple steps, reply: complex
    Output only the word. No punctuation.
    """
    
    response = await llm.ainvoke(prompt)
    classification = response.content.strip().lower()
    
    return {"classification": classification}