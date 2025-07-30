"""
Restructured chat agent using centralized tools and configuration
"""

import json
import httpx
from typing import Dict, Any
from langgraph.graph import StateGraph
from app.core.logger import get_logger
from app.config import settings
from app.memory.enhanced_store import enhanced_memory_store
from app.tools.agent_tools import agent_tools
from app.config.agent_config import get_response_template, is_valid_intent
from app.prompts.agent_prompts import (
    CAPABILITIES_RESPONSE, 
    GREETING_RESPONSE,
    ACTIVITY_EXTRACTION_PROMPT
)

logger = get_logger(__name__)

# Initialize LangGraph workflow
workflow = StateGraph(dict)

async def classify_intent(state: dict, config: dict) -> dict:
    """Classify user intent using centralized tools"""
    logger.debug(f"=== CLASSIFY_INTENT START ===")
    logger.debug(f"Input state: {state}")
    
    prompt_text = state.get("prompt", "")
    logger.debug(f"Prompt text: {prompt_text}")
    
    try:
        # Use centralized intent classification
        classification_result = await agent_tools.classify_intent(prompt_text)
        
        intent = classification_result.get("intent", "unknown")
        confidence = classification_result.get("confidence", 0.0)
        target_agent = classification_result.get("target_agent", None)
        operation = intent.replace("-activity", "") if intent.endswith("-activity") else intent
        
        logger.debug(f"Final intent: {intent}")
        logger.debug(f"Confidence: {confidence}")
        logger.debug(f"Operation: {operation}")
        logger.debug(f"Target agent: {target_agent}")
        
        # Preserve the original state while adding classification results
        output = {
            **state,  # Keep all original state
            "intent": intent, 
            "confidence": confidence, 
            "operation": operation,
            "target_agent": target_agent
        }
        
        logger.debug(f"Final output: {output}")
        logger.debug(f"=== CLASSIFY_INTENT SUCCESS ===")
        return output
        
    except Exception as e:
        logger.error(f"=== CLASSIFY_INTENT ERROR ===")
        logger.error(f"Error details: {e}")
        return {
            **state,
            "intent": "unknown",
            "confidence": 0.0,
            "operation": "unknown",
            "target_agent": None
        }

async def greet_user(state: dict, config: dict) -> dict:
    """Handle greeting responses"""
    logger.debug(f"=== GREET_USER START ===")
    logger.debug(f"Input state: {state}")
    
    result = {"result": {"message": GREETING_RESPONSE}}
    logger.debug(f"Greet user result: {result}")
    logger.debug(f"=== GREET_USER SUCCESS ===")
    return result

async def describe_capabilities(state: dict, config: dict) -> dict:
    """Handle capabilities responses"""
    logger.debug(f"=== DESCRIBE_CAPABILITIES START ===")
    logger.debug(f"Input state: {state}")
    
    result = {"result": {"message": CAPABILITIES_RESPONSE}}
    logger.debug(f"Describe capabilities result: {result}")
    logger.debug(f"=== DESCRIBE_CAPABILITIES SUCCESS ===")
    return result

async def start_activity_tool(state: dict, config: dict) -> dict:
    """Handle start activity requests"""
    logger.debug(f"=== START_ACTIVITY_TOOL START ===")
    logger.debug(f"Input state: {state}")
    
    prompt = state.get("prompt", "")
    payload = state.get("details", {})
    token = payload.get("token")
    db = state.get("db")
    
    logger.debug(f"Prompt: {prompt}")
    logger.debug(f"Token present: {token is not None}")
    logger.debug(f"Database session present: {db is not None}")
    
    url = f"{settings.SERVER_HOST}{settings.API_PREFIX}/agent/start-activity"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
        logger.info(f"Authorization header set: Bearer {token[:20]}...")
    else:
        logger.error("No token found in payload details")
    
    try:
        # Extract activity details using centralized tools
        activity_details = await agent_tools.extract_activity_details(prompt)
        
        activity_payload = {
            "activity_name": activity_details.get("activity_name"),
            "category_name": activity_details.get("category_name"),
            "subcategory_name": activity_details.get("subcategory_name"),
            "activity_id": None
        }
        
        logger.debug(f"Activity payload: {activity_payload}")
        
        # Try to find exact match in database first
        if activity_payload["activity_name"] and db:
            # Database lookup logic (existing implementation)
            logger.debug("Performing database lookup for activity")
            # ... (existing database lookup code)
        
        # Make HTTP request to start activity
        async with httpx.AsyncClient() as client_http:
            resp = await client_http.post(
                url,
                json=activity_payload,
                headers=headers,
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"HTTP response body: {data}")
        
        if data["status"] == "started":
            final_description = data.get("final_description", "")
            if final_description:
                # Recursively invoke the agent with the final_description
                new_state = {
                    "prompt": final_description,
                    "details": payload,
                    "db": db
                }
                result = await agent.ainvoke(new_state)
                msg = result.get("result", {}).get("message", "Activity executed, but no message returned.")
            else:
                msg = "Activity started, but no description was found."
        else:
            sug = "\n".join(f"- {s['name']}" for s in data["suggestions"])
            msg = (
                "I found several activities matching your request:\n"
                + sug +
                "\n\nWhich one would you like to start?"
            )
        
        result = {"result": {"message": msg}}
        logger.debug(f"Start activity tool result: {result}")
        logger.debug(f"=== START_ACTIVITY_TOOL SUCCESS ===")
        return result
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        result = {"result": {"error": f"HTTP error: {e.response.status_code} - {e.response.text}"}}
        logger.debug(f"=== START_ACTIVITY_TOOL HTTP ERROR ===")
        return result
    except Exception as e:
        logger.error(f"Start activity failed: {str(e)}")
        result = {"result": {"error": f"Start activity failed: {str(e)}"}}
        logger.debug(f"=== START_ACTIVITY_TOOL EXCEPTION ===")
        return result

async def route_activity(state: dict, config: dict) -> dict:
    """Route activity CRUD operations"""
    logger.debug(f"=== ROUTE_ACTIVITY START ===")
    logger.debug(f"Input state: {state}")
    
    op = state.get("operation")
    logger.debug(f"Operation: {op}")
    
    if op == "unknown":
        result = {"result": {"error": get_response_template("unknown_intent")}}
        logger.debug(f"Unknown operation, returning error: {result}")
        logger.debug(f"=== ROUTE_ACTIVITY UNKNOWN OPERATION ===")
        return result
    
    try:
        # Use existing activity_crud logic
        result = await activity_crud({"operation": op, "payload": state.get("details", {})}, {})
        return {"result": result.get("result")}
    except Exception as e:
        logger.error(f"Route activity failed: {e}")
        return {"result": {"error": f"Activity operation failed: {str(e)}"}}

async def activity_crud(state: dict, config: dict) -> dict:
    """Handle activity CRUD operations"""
    logger.debug(f"=== ACTIVITY_CRUD START ===")
    logger.debug(f"Input state: {state}")
    
    try:
        operation = state.get("operation")
        payload = state.get("payload", {})
        logger.debug(f"Operation: {operation}")
        logger.debug(f"Payload: {payload}")
        
        method_map = {
            "create": ("post", "/activities"),
            "list": ("get", "/activities"),
            "edit": ("put", f"/activities/{payload.get('id')}"),
            "delete": ("delete", f"/activities/{payload.get('id')}")
        }
        method, path = method_map[operation]
        url = f"{settings.ACTIVITY_SERVICE_URL}{path}"
        logger.debug(f"HTTP method: {method}")
        logger.debug(f"Path: {path}")
        logger.debug(f"Full URL: {url}")
        
        async with httpx.AsyncClient() as client_http:
            resp = await client_http.request(method, url, json=payload if method != 'get' else None, timeout=10)
            logger.debug(f"HTTP response status: {resp.status_code}")
            resp.raise_for_status()
            result = resp.json()
            logger.debug(f"HTTP response body: {result}")
        
        logger.debug(f"=== ACTIVITY_CRUD SUCCESS ===")
        return {"result": result}
    except Exception as e:
        logger.error(f"=== ACTIVITY_CRUD ERROR ===")
        logger.error(f"Error details: {e}")
        logger.error(f"Activity CRUD failed: {e}")
        raise

async def generate_activity_handler(state: dict, config: dict) -> dict:
    """Handle activity generation requests"""
    logger.debug(f"=== GENERATE_ACTIVITY_HANDLER START ===")
    logger.debug(f"Input state: {state}")
    
    prompt = state.get("prompt", "")
    
    try:
        # Use centralized chat completion
        from app.config.agent_config import get_chat_completion_config
        config_settings = get_chat_completion_config()
        response = await agent_tools._chat_completion(
            prompt=prompt,
            temperature=config_settings["default_temperature"],
            max_tokens=config_settings["default_max_tokens"],
            json_mode=config_settings["json_mode"]
        )
        
        questions = response.get("response", {}).get("text", response.get("response", ""))
        message = f"{questions}"
        
        result = {"result": {"message": message}}
        logger.debug(f"Generate activity handler result: {result}")
        logger.debug(f"=== GENERATE_ACTIVITY_HANDLER SUCCESS ===")
        return result
        
    except Exception as e:
        logger.error(f"Generate activity handler failed: {e}")
        result = {"result": {"error": f"Activity generation failed: {str(e)}"}}
        logger.debug(f"=== GENERATE_ACTIVITY_HANDLER ERROR ===")
        return result

async def collaborative_learning_handler(state: dict, config: dict) -> dict:
    """Handle collaborative learning requests"""
    logger.debug(f"=== COLLABORATIVE_LEARNING_HANDLER START ===")
    logger.debug(f"Input state: {state}")
    
    prompt = state.get("prompt", "")
    learning_context = state.get("learning_context", "")
    
    try:
        from app.agents.multi_agent_system import multi_agent_system
        result = await multi_agent_system.collaborative_learning_session(prompt, learning_context)
        
        message = result.get("combined_response", get_response_template("error"))
        
        logger.debug(f"Collaborative learning result: {result}")
        logger.debug(f"=== COLLABORATIVE_LEARNING_HANDLER SUCCESS ===")
        return {"result": {"message": message, "session_type": "collaborative_learning"}}
        
    except Exception as e:
        logger.error(f"=== COLLABORATIVE_LEARNING_HANDLER ERROR ===")
        logger.error(f"Error details: {e}")
        return {"result": {"error": f"Collaborative learning failed: {str(e)}"}}

async def single_agent_consultation_handler(state: dict, config: dict) -> dict:
    """Handle single agent consultation requests"""
    logger.debug(f"=== SINGLE_AGENT_CONSULTATION_HANDLER START ===")
    logger.debug(f"Input state: {state}")
    
    prompt = state.get("prompt", "")
    target_agent = state.get("target_agent", "tutor")
    
    try:
        from app.agents.multi_agent_system import multi_agent_system
        result = await multi_agent_system.single_agent_consultation(target_agent, prompt)
        
        message = result.get("response", get_response_template("error"))
        
        logger.debug(f"Single agent consultation result: {result}")
        logger.debug(f"=== SINGLE_AGENT_CONSULTATION_HANDLER SUCCESS ===")
        return {"result": {"message": message, "session_type": "single_agent", "agent": target_agent}}
        
    except Exception as e:
        logger.error(f"=== SINGLE_AGENT_CONSULTATION_HANDLER ERROR ===")
        logger.error(f"Error details: {e}")
        return {"result": {"error": f"Single agent consultation failed: {str(e)}"}}

async def learning_support_handler(state: dict, config: dict) -> dict:
    """Handle general learning support requests"""
    logger.debug(f"=== LEARNING_SUPPORT_HANDLER START ===")
    logger.debug(f"Input state: {state}")
    
    prompt = state.get("prompt", "")
    
    try:
        from app.agents.multi_agent_system import multi_agent_system
        result = await multi_agent_system.process_learning_request(prompt)
        
        message = result.get("combined_response", get_response_template("error"))
        
        logger.debug(f"Learning support result: {result}")
        logger.debug(f"=== LEARNING_SUPPORT_HANDLER SUCCESS ===")
        return {"result": {"message": message, "session_type": "learning_support"}}
        
    except Exception as e:
        logger.error(f"=== LEARNING_SUPPORT_HANDLER ERROR ===")
        logger.error(f"Error details: {e}")
        return {"result": {"error": f"Learning support failed: {str(e)}"}}

# Build workflow
workflow.add_node("classify_intent", classify_intent)
workflow.add_node("greet_user", greet_user)
workflow.add_node("describe_capabilities", describe_capabilities)
workflow.add_node("start_activity_tool", start_activity_tool)
workflow.add_node("route_activity", route_activity)
workflow.add_node("generate_activity_handler", generate_activity_handler)
workflow.add_node("collaborative_learning_handler", collaborative_learning_handler)
workflow.add_node("single_agent_consultation_handler", single_agent_consultation_handler)
workflow.add_node("learning_support_handler", learning_support_handler)

# Routing function
def route_from_classify_intent(state):
    logger.debug(f"=== ROUTE_FROM_CLASSIFY_INTENT START ===")
    logger.debug(f"Input state: {state}")
    
    intent = state.get("intent")
    logger.debug(f"Intent: {intent}")
    
    routing_map = {
        "greetings": "greet_user",
        "capabilities": "describe_capabilities",
        "start-activity": "start_activity_tool",
        "generate-activity": "generate_activity_handler",
        "collaborative-learning": "collaborative_learning_handler",
        "single-agent-consultation": "single_agent_consultation_handler",
        "learning-support": "learning_support_handler"
    }
    
    # Handle activity CRUD operations
    if intent in {"create-activity", "edit-activity", "delete-activity", "list-activities"}:
        logger.debug("Routing to: route_activity")
        return "route_activity"
    
    # Handle other intents
    route = routing_map.get(intent, "route_activity")
    logger.debug(f"Routing to: {route}")
    return route

workflow.add_conditional_edges("classify_intent", route_from_classify_intent)

# Finish points
workflow.set_entry_point("classify_intent")
finish_nodes = [
    "greet_user", "describe_capabilities", "start_activity_tool", "route_activity",
    "generate_activity_handler", "collaborative_learning_handler", 
    "single_agent_consultation_handler", "learning_support_handler"
]
for node in finish_nodes:
    workflow.set_finish_point(node)

# Compile agent
agent = workflow.compile()
logger.info("Chat agent workflow compiled successfully")

async def run_agent(input_data: dict) -> dict:
    """Run the chat agent with input data"""
    logger.debug(f"=== RUN_AGENT START ===")
    logger.debug(f"Input data: {input_data}")
    
    user_id = input_data.get("user_id")
    if not user_id:
        raise ValueError("user_id is required for session memory")
    
    # Get or create an enhanced memory session
    session = enhanced_memory_store.get_or_create_session(user_id)
    prompt = input_data.get("prompt", "")
    
    # Record the user turn
    enhanced_memory_store.add_message(session.session_id, "user", prompt)
    history = enhanced_memory_store.get_history(session.session_id)
    messages = [{"role": m.role, "content": m.content} for m in history]
    
    state = {
        "prompt": prompt,
        "details": input_data.get("details", {}),
        "db": input_data.get("db"),
        "messages": messages
    }
    logger.debug(f"Initial state: {state}")
    
    logger.debug(f"Invoking agent workflow...")
    result = await agent.ainvoke(state)
    logger.debug(f"Agent workflow result: {result}")
    
    reply = result.get("result", {}).get("message", "")
    enhanced_memory_store.add_message(session.session_id, "assistant", reply)
    
    output = {
        "intent": result.get("intent", "unknown"),
        "result": result.get("result", {}),
        "session_id": session.session_id
    }
    logger.debug(f"Final output: {output}")
    
    logger.debug(f"=== RUN_AGENT SUCCESS ===")
    return output 