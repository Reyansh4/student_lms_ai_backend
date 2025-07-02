from langgraph.graph import StateGraph
from app.memory.store import InMemoryStore
from app.core.logger import get_logger
from openai import AsyncAzureOpenAI
from app.core.azure_config import load_azure_config
import json

logger = get_logger(__name__)
store = InMemoryStore()

# Load Azure configuration
azure_config = load_azure_config()
client = AsyncAzureOpenAI(
    api_key=azure_config.api_key,
    azure_endpoint=azure_config.endpoint,
    api_version=azure_config.api_version
)

def fetch_history(state: dict, config: dict) -> dict:
    session_id = state.get("session_id")
    history = store.get_history(session_id)
    state["messages"] = [{"role": m.role, "content": m.content} for m in history]
    return state

async def build_eval_prompt(state: dict, config: dict) -> dict:
    messages = state["messages"]
    # Detect activity types in history
    content = []
    for m in messages:
        if "quiz" in m.content.lower() or "test" in m.content.lower():
            metric = (
                "For each quiz or test activity, evaluate the user's answers: "
                "accuracy, completeness, clarity of approach, and common mistakes."
            )
        elif "read" in m.content.lower() or "book" in m.content.lower():
            metric = (
                "For each reading activity, calculate completion percentage "
                "and retention insights."
            )
        else:
            metric = None
        content.append(m.content)
    # Build a single system prompt covering both cases
    system_prompt = (
        "You are an expert tutor. "
        "Based on the conversation below, evaluate the user across all activity types: \n"
        "- Quizzes/Tests: accuracy, approach, completeness, mistakes\n"
        "- Readings: completion percentage, retention insights\n"
        "Respond with JSON: {\n"
        "  \"scores\": { \"accuracy\": int, \"approach\": int, \"completeness\": int, \"mistakes\": int, \"completion\": int, \"retention\": int },\n"
        "  \"summary\": string\n"
        "}\n"
    )
    state["messages"] = [{"role": "system", "content": system_prompt}]
    state["messages"].extend([{"role": m["role"], "content": m["content"]} for m in messages])
    return state

async def llm_json(state: dict, config: dict) -> dict:
    resp = await client.chat.completions.create(
        model=azure_config.deployment,
        messages=state["messages"],
        temperature=0.7
    )
    raw = resp.choices[0].message.content.strip()
    return {"response": json.loads(raw)}

async def format_output(state: dict, config: dict) -> dict:
    eval_json = state.get("response", {})
    msg = (
        f"📊 **Your Performance**\n\n"
        f"- Accuracy: {eval_json['scores']['accuracy']}%\n"
        f"- Approach: {eval_json['scores']['approach']}%\n"
        f"- Completeness: {eval_json['scores']['completeness']}%\n"
        f"- Common Mistakes Score: {eval_json['scores']['mistakes']}%\n"
        f"- Reading Completion: {eval_json['scores']['completion']}%\n"
        f"- Retention: {eval_json['scores']['retention']}%\n\n"
        f"**Summary:** {eval_json['summary']}"
    )
    return {"result": {"message": msg}}

# Assemble evaluator graph
eval_graph = StateGraph(dict)
eval_graph.add_node("fetch_history", fetch_history)
eval_graph.add_node("build_eval_prompt", build_eval_prompt)
eval_graph.add_node("llm_json", llm_json)
eval_graph.add_node("format_output", format_output)

# Define flow
eval_graph.add_edge("fetch_history", "build_eval_prompt")
eval_graph.add_edge("build_eval_prompt", "llm_json")
eval_graph.add_edge("llm_json", "format_output")

eval_graph.set_entry_point("fetch_history")
eval_graph.set_finish_point("format_output")

# Compile into a reusable tool
evaluate_performance_tool = eval_graph.compile()
