"""
Defines the core ChatAgent using LangGraph flows and Azure OpenAI.
"""
import json
import httpx
import logging
from typing import Any, Dict
from langgraph.graph import StateGraph
from openai import AsyncAzureOpenAI
from app.core.azure_config import load_azure_config
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Load Azure configuration
azure_config = load_azure_config()

# Create Azure OpenAI client
client = AsyncAzureOpenAI(
    api_key=azure_config.api_key,
    azure_endpoint=azure_config.endpoint,
    api_version=azure_config.api_version
)

# Base URL for the Activity CRUD API
ACTIVITY_SERVICE_URL = settings.ACTIVITY_SERVICE_URL

# Initialize the LangGraph workflow
workflow = StateGraph(dict)

# Langfuse tracing setup
try:
    from langfuse import Langfuse
    langfuse = Langfuse()
    logger.info("Langfuse tracing initialized")
except ImportError:
    logger.warning("Langfuse not installed. Tracing disabled")
    langfuse = None

def trace_function(func_name, input_data, output_data=None, error=None):
    """Helper for Langfuse tracing"""
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
    """
    Azure OpenAI chat completion tool using new client.
    """
    try:
        logger.info(f"Chat completion request: {state.get('prompt', '')[:50]}...")
        prompt = state.get("prompt", "")
        messages = state.get("messages", [{"role": "user", "content": prompt}])
        
        # Add system message for JSON responses
        if json_mode:
            system_msg = {
                "role": "system",
                "content": "You MUST respond with valid JSON ONLY. Do not include any other text outside the JSON structure."
            }
            messages = [system_msg] + messages
        
        params = {
            "model": azure_config.deployment,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Enable JSON mode if requested
        if json_mode:
            params["response_format"] = {"type": "json_object"}
        
        response = await client.chat.completions.create(**params)
        
        content = response.choices[0].message.content.strip()
        logger.debug(f"Chat completion response: {content[:200]}...")
        
        try:
            result = {"response": json.loads(content)}
            trace_function("chat_completion", {"prompt": prompt, "json_mode": json_mode}, result)
            return result
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON response: {content[:200]}...")
            result = {"response": {"text": content}}
            trace_function("chat_completion", {"prompt": prompt, "json_mode": json_mode}, result)
            return result
            
    except Exception as e:
        logger.error(f"Chat completion failed: {str(e)}")
        trace_function("chat_completion", state, error=e)
        raise

async def activity_crud(
    state: dict,
    config: dict
) -> dict:
    """
    Performs CRUD operations for student activities.
    """
    try:
        operation = state.get("operation")
        payload = state.get("payload", {})
        logger.info(f"Activity CRUD operation: {operation}")
        
        method_map = {
            "create": ("post", "/activities"),
            "list":   ("get",  "/activities"),
            "edit":   ("put",  f"/activities/{payload.get('id')}"),
            "delete": ("delete", f"/activities/{payload.get('id')}")
        }
        
        if operation not in method_map:
            error_msg = f"Unsupported operation: {operation}"
            logger.error(error_msg)
            trace_function("activity_crud", state, error=error_msg)
            raise ValueError(error_msg)
        
        method, path = method_map[operation]
        url = f"{ACTIVITY_SERVICE_URL}{path}"

        async with httpx.AsyncClient() as http_client:
            logger.debug(f"HTTP {method.upper()} to {url}")
            resp = await http_client.request(
                method,
                url,
                json=payload if method != 'get' else None,
                timeout=10
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"CRUD operation successful: {operation}")
            
            trace_function("activity_crud", {
                "operation": operation,
                "url": url,
                "payload": payload
            }, {"result": result})
            
            return {"result": result}
            
    except Exception as e:
        logger.error(f"CRUD operation failed: {str(e)}")
        trace_function("activity_crud", state, error=e)
        raise

async def classify_intent(state: dict, config: dict) -> dict:
    """
    Classifies user intent using chat_completion tool.
    """
    try:
        prompt_text = state.get("prompt", "")
        logger.info(f"Classifying intent for: {prompt_text[:50]}...")
        
        # Enhanced prompt with examples and strict format
        classification_prompt = (
            "Classify the user's intent into one of these categories:\n"
            "- create-activity: User wants to create a new activity\n"
            "- edit-activity: User wants to modify an existing activity\n"
            "- delete-activity: User wants to remove an activity\n"
            "- list-activities: User wants to view activities\n\n"
            "Return JSON with exactly these keys:\n"
            "- intent: one of the category names above\n"
            "- confidence: float between 0.0 and 1.0\n\n"
            "If uncertain, use 'unknown' as intent.\n\n"
            f"User input: '{prompt_text}'"
        )
        
        classification = await chat_completion(
            {"prompt": classification_prompt},
            {},
            json_mode=True  # Force JSON response
        )
        
        result = classification.get("response", {})
        
        # Handle non-JSON responses
        if "text" in result:
            logger.warning(f"Unexpected text response for intent classification: {result['text']}")
            # Try to extract intent from text
            text = result["text"].lower()
            intent = "unknown"
            if "create" in text:
                intent = "create-activity"
            elif "edit" in text or "update" in text:
                intent = "edit-activity"
            elif "delete" in text or "remove" in text:
                intent = "delete-activity"
            elif "list" in text or "show" in text or "view" in text:
                intent = "list-activities"
            result = {"intent": intent, "confidence": 0.5}
        
        intent = result.get("intent", "unknown").lower()
        confidence = result.get("confidence", 0.0)
        
        # Validate intent
        valid_intents = {"create-activity", "edit-activity", "delete-activity", "list-activities"}
        if intent not in valid_intents:
            logger.warning(f"Invalid intent '{intent}' detected, falling back to 'unknown'")
            intent = "unknown"
        
        logger.info(f"Intent classified: {intent} (confidence: {confidence})")
        
        output = {
            "intent": intent,
            "confidence": confidence,
            "operation": intent.replace("-activity", "") if intent != "unknown" else "unknown"
        }
        
        trace_function("classify_intent", {"prompt": prompt_text}, output)
        return output
        
    except Exception as e:
        logger.error(f"Intent classification failed: {str(e)}")
        trace_function("classify_intent", state, error=e)
        # Fallback to unknown intent
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "operation": "unknown"
        }

async def route_activity(state: dict, config: dict) -> dict:
    """
    Routes to appropriate activity CRUD operation.
    """
    try:
        operation = state.get("operation")
        logger.info(f"Routing activity with operation: {operation}")
        
        # Handle unknown intents gracefully
        if operation == "unknown":
            error_msg = "Could not determine user intent. Please rephrase your request."
            logger.warning(error_msg)
            trace_function("route_activity", state, error=error_msg)
            return {"result": {"error": error_msg}}
        
        if operation not in {"create", "list", "edit", "delete"}:
            error_msg = f"Unsupported intent: {operation}"
            logger.error(error_msg)
            trace_function("route_activity", state, error=error_msg)
            return {"result": {"error": error_msg}}
        
        payload = state.get("details", {})
        logger.info(f"Routing to {operation} with payload")
        
        result = await activity_crud(
            {"operation": operation, "payload": payload},
            {}
        )
        
        output = {"result": result.get("result")}
        trace_function("route_activity", state, output)
        return output
        
    except Exception as e:
        logger.error(f"Routing failed: {str(e)}")
        trace_function("route_activity", state, error=e)
        return {"result": {"error": f"Activity routing failed: {str(e)}"}}

# Define workflow nodes
workflow.add_node("classify_intent", classify_intent)
workflow.add_node("route_activity", route_activity)

# Set up graph transitions
workflow.add_edge("classify_intent", "route_activity")
workflow.set_entry_point("classify_intent")
workflow.set_finish_point("route_activity")

# Compile the graph
agent = workflow.compile()
logger.info("Agent workflow compiled successfully")

# Unified entry point for the agent
async def run_agent(input_data: dict) -> dict:
    """
    Executes the agent workflow with user input.
    Input format: {'prompt': str, 'details': dict}
    Output format: {'intent': str, 'result': dict}
    """
    try:
        logger.info(f"Agent invoked with prompt: {input_data.get('prompt', '')[:50]}...")
        
        # Start Langfuse trace for the full agent run
        if langfuse:
            trace = langfuse.trace(name="run_agent")
            trace.input = input_data
        else:
            trace = None
        
        state = {
            "prompt": input_data.get("prompt", ""),
            "details": input_data.get("details", {})
        }
        
        result = await agent.ainvoke(state)
        output = {
            "intent": result.get("intent", "unknown"),
            "result": result.get("result", {})
        }
        
        # Add error details if present
        if "error" in output.get("result", {}):
            output["error"] = output["result"]["error"]
        
        logger.info(f"Agent completed with intent: {output['intent']}")
        
        if trace:
            trace.output = output
            trace.end()
            
        return output
        
    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}")
        if langfuse:
            trace = langfuse.trace(name="run_agent")
            trace.input = input_data
            trace.error = str(e)
            trace.end()
        return {
            "intent": "error",
            "result": {"error": f"Agent execution failed: {str(e)}"}
        }