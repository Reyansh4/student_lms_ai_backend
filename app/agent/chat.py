import json
import logging
from typing import Any, Dict
import httpx

from uuid import UUID
from langgraph.graph import StateGraph
from openai import AsyncAzureOpenAI
from sqlalchemy.orm import joinedload

from app.core.azure_config import load_azure_config
from app.core.config import settings
from app.models.activity import Activity
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.activity import ExtendedStartActivityInput, ExtendedStartActivityResponse

# Configure logging
logger = logging.getLogger(__name__)

# Load Azure configuration and create OpenAI client
azure_config = load_azure_config()
client = AsyncAzureOpenAI(
    api_key=azure_config.api_key,
    azure_endpoint=azure_config.endpoint,
    api_version=azure_config.api_version
)

# Base URL for your Activity service
ACTIVITY_SERVICE_URL = settings.ACTIVITY_SERVICE_URL

# Initialize LangGraph workflow
workflow = StateGraph(dict)

# Optional Langfuse tracing
try:
    from langfuse import Langfuse
    langfuse = Langfuse()
    logger.info("Langfuse tracing initialized")
except ImportError:
    logger.warning("Langfuse not installed. Tracing disabled")
    langfuse = None

def trace_function(func_name, input_data, output_data=None, error=None):
    if not langfuse:
        return
    with langfuse.trace(name=func_name) as trace:
        trace.input = input_data
        if output_data:
            trace.output = output_data
        if error:
            trace.error = str(error)

async def chat_completion(
    state: dict,
    config: dict,
    temperature: float = 0.7,
    max_tokens: int = 512,
    json_mode: bool = False
) -> dict:
    try:
        prompt = state.get("prompt", "")
        messages = state.get("messages", [{"role": "user", "content": prompt}])
        if json_mode:
            system_msg = {"role": "system", "content": "You MUST respond with valid JSON ONLY."}
            messages = [system_msg] + messages
        params = {
            "model": azure_config.deployment,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        response = await client.chat.completions.create(**params)
        content = response.choices[0].message.content.strip()
        try:
            result = {"response": json.loads(content)}
            trace_function("chat_completion", {"prompt": prompt, "json_mode": json_mode}, result)
            return result
        except json.JSONDecodeError:
            result = {"response": {"text": content}}
            trace_function("chat_completion", {"prompt": prompt, "json_mode": json_mode}, result)
            return result
    except Exception as e:
        trace_function("chat_completion", state, error=e)
        logger.error(f"Chat completion failed: {e}")
        raise

async def activity_crud(
    state: dict,
    config: dict
) -> dict:
    try:
        operation = state.get("operation")
        payload = state.get("payload", {})
        method_map = {
            "create": ("post", "/activities"),
            "list":   ("get",  "/activities"),
            "edit":   ("put",  f"/activities/{payload.get('id')}"),
            "delete": ("delete", f"/activities/{payload.get('id')}")
        }
        method, path = method_map[operation]
        url = f"{ACTIVITY_SERVICE_URL}{path}"
        async with httpx.AsyncClient() as client_http:
            resp = await client_http.request(method, url, json=payload if method != 'get' else None, timeout=10)
            resp.raise_for_status()
            result = resp.json()
        trace_function("activity_crud", {"operation": operation, "payload": payload}, {"result": result})
        return {"result": result}
    except Exception as e:
        trace_function("activity_crud", state, error=e)
        logger.error(f"Activity CRUD failed: {e}")
        raise

async def classify_intent(state: dict, config: dict) -> dict:
    prompt_text = state.get("prompt", "")
    classification_prompt = (
        "Classify the user's intent into one of these categories:\n"
        "- create-activity\n"
        "- edit-activity\n"
        "- delete-activity\n"
        "- list-activities\n"
        "- start-activity: User wants to begin an activity\n"
        "- greetings: User is greeting the agent\n"
        "- capabilities: User asks what you can do\n"
        "Return JSON with 'intent' and 'confidence'.\n"
        f"User input: '{prompt_text}'"
    )
    classification = await chat_completion({"prompt": classification_prompt}, {}, json_mode=True)
    result = classification.get("response", {})
    if "text" in result:
        text = result["text"].lower()
        intent = "unknown"
        if any(w in text for w in ["hello","hi","hey"]): intent="greetings"
        elif "what can you do" in text: intent="capabilities"
        elif "start" in text: intent="start-activity"
        result = {"intent": intent, "confidence": 0.5}
    intent = result.get("intent", "unknown").lower()
    valid_intents = {"create-activity","edit-activity","delete-activity","list-activities","start-activity","greetings","capabilities"}
    if intent not in valid_intents:
        intent="unknown"
    confidence = result.get("confidence", 0.0)
    operation = intent.replace("-activity","") if intent.endswith("-activity") else intent
    output = {"intent": intent, "confidence": confidence, "operation": operation}
    trace_function("classify_intent", {"prompt": prompt_text}, output)
    return output

async def greet_user(state: dict, config: dict) -> dict:
    return {"result": {"message": "Hi! I'm **Leena AI**, your learning assistant—how can I help you today?"}}

async def describe_capabilities(state: dict, config: dict) -> dict:
    return {"result": {"message": (
        "I can help you:\n"
        "- create new activities\n"
        "- start or match existing activities\n"
        "- teach topics step-by-step\n"
        "- generate tests and evaluate answers\n"
        "…and more, just ask!"
    )}}

async def start_activity_tool(state: dict, config: dict) -> dict:
    payload = state.get("details", {})
    token   = payload.get("token")  # extract the JWT we stashed earlier

    url = f"{settings.SERVER_HOST}{settings.API_PREFIX}/agent/start-activity"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient() as client_http:
        resp = await client_http.post(
            url,
            json=payload,
            headers=headers,      # <-- pass the user’s token here
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()

    if data["status"] == "started":
        msg = (
            f"Great! I'm Leena AI. I got your input and will start the activity:\n\n"
            f"**{data['final_description']}**\n\n"
            "Shall I begin now?"
        )
    else:
        sug = "\n".join(f"- {s['name']} ({s['score']}%)" for s in data["suggestions"])
        msg = (
            "I found several activities matching your request:\n"
            + sug +
            "\n\nWhich one would you like to start?"
        )

    return {"result": {"message": msg}}

async def route_activity(state: dict, config: dict) -> dict:
    op = state.get("operation")
    if op == "unknown":
        return {"result": {"error": "Could not determine intent, please rephrase."}}
    result = await activity_crud({"operation": op, "payload": state.get("details", {})}, {})
    return {"result": result.get("result")}

# Build workflow
workflow.add_node("classify_intent", classify_intent)
workflow.add_node("greet_user", greet_user)
workflow.add_node("describe_capabilities", describe_capabilities)
workflow.add_node("start_activity_tool", start_activity_tool)
workflow.add_node("route_activity", route_activity)

# Transitions
def route_from_classify_intent(state):
    intent = state.get("intent")
    if intent == "greetings":
        return "greet_user"
    elif intent == "capabilities":
        return "describe_capabilities"
    elif intent == "start-activity":
        return "start_activity_tool"
    elif intent in {"create-activity", "edit-activity", "delete-activity", "list-activities"}:
        return "route_activity"
    else:
        return None  # or END if you want to terminate

workflow.add_conditional_edges("classify_intent", route_from_classify_intent)

# Finish points
workflow.set_entry_point("classify_intent")
for node in ["greet_user","describe_capabilities","start_activity_tool","route_activity"]:
    workflow.set_finish_point(node)

# Compile agent
agent = workflow.compile()
logger.info("Agent workflow compiled successfully")

async def run_agent(input_data: dict) -> dict:
    trace = None
    if langfuse:
        trace = langfuse.trace(name="run_agent")
        trace.input = input_data
    state = {"prompt": input_data.get("prompt", ""), "details": input_data.get("details", {})}
    result = await agent.ainvoke(state)
    output = {"intent": result.get("intent", "unknown"), "result": result.get("result", {})}
    if trace:
        trace.output = output
        trace.end()
    return output
