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
        "- generate-activity: User wants to generate any activity (quiz, lesson, assignment, etc.) based on a description (including markdown)\n"
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
    valid_intents = {"create-activity","edit-activity","delete-activity","list-activities","start-activity","generate-activity","greetings","capabilities"}
    if intent not in valid_intents:
        intent="unknown"
    confidence = result.get("confidence", 0.0)
    operation = intent.replace("-activity","") if intent.endswith("-activity") else intent
    
    # CRITICAL: Preserve the original state while adding classification results
    output = {
        **state,  # Keep all original state (including 'db', 'prompt', 'details', 'token')
        "intent": intent, 
        "confidence": confidence, 
        "operation": operation
    }
    
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
    prompt = state.get("prompt", "")
    payload = state.get("details", {})
    token = payload.get("token")  # extract the JWT we stashed earlier
    db = state.get("db")  # get database session

    url = f"{settings.SERVER_HOST}{settings.API_PREFIX}/agent/start-activity"
    headers = {}
    logger.info(f"Token present: {token is not None}")
    logger.info(f"Token length: {len(token) if token else 0}")
    logger.info(f"URL: {url}")
    logger.info(f"Original prompt: {prompt}")
    
    # Use AI to intelligently extract activity details from the prompt
    extraction_prompt = f"""
    Extract activity information from this user request. Return JSON with these fields:
    - activity_name: The specific activity name mentioned (e.g., quiz, test, etc)
    - category_name: The subject/category mentioned (e.g., math, science, physics, history)
    - subcategory_name: The specific topic/subcategory mentioned (e.g., algebra, calculus, refractive index)
    
    User request: "{prompt}"
    
    Examples:
    - "start math quiz" → {{"activity_name": "quiz", "category_name": "math", "subcategory_name": null}}
    - "begin algebra practice" → {{"activity_name": "practice", "category_name": "math", "subcategory_name": "algebra"}}
    - "I want to do physics experiments" → {{"activity_name": "experiments", "category_name": "physics", "subcategory_name": "refractive index"}}
    """
    
    try:
        # Extract structured information from the prompt
        extraction_result = await chat_completion({"prompt": extraction_prompt}, {}, json_mode=True)
        extracted_data = extraction_result.get("response", {})
        
        # Create the payload that the /start-activity endpoint expects
        activity_payload = {
            "activity_name": extracted_data.get("activity_name"),
            "category_name": extracted_data.get("category_name"),
            "subcategory_name": extracted_data.get("subcategory_name"),
            "activity_id": None
        }
        
        print(f"Extracted data: {extracted_data}")
        print(f"Activity payload: {activity_payload}")
        
        # Try to find exact match in database first
        if activity_payload["activity_name"]:
            if not db:
                print("Database session not available, will use HTTP endpoint for fuzzy matching")
            else:
                from app.models.activity import Activity
                from app.models.activity_category import ActivityCategory
                from app.models.activity_sub_category import ActivitySubCategory
                from sqlalchemy.orm import joinedload
                
                print(f"=== DATABASE LOOKUP DEBUG ===")
                print(f"Looking for: activity_name='{activity_payload['activity_name']}', category='{activity_payload['category_name']}', subcategory='{activity_payload['subcategory_name']}'")
                
                # Build query based on available extracted data
                query = db.query(Activity).options(
                    joinedload(Activity.category),
                    joinedload(Activity.sub_category)
                ).filter(Activity.is_active == True)
                
                # Add filters based on extracted data
                if activity_payload["activity_name"]:
                    query = query.filter(Activity.name.ilike(f"%{activity_payload['activity_name']}%"))
                    print(f"Added activity name filter: '%{activity_payload['activity_name']}%'")
                
                # Handle category as foreign key - first find category ID by name
                if activity_payload["category_name"]:
                    category = db.query(ActivityCategory).filter(ActivityCategory.name.ilike(f"%{activity_payload['category_name']}%")).first()
                    if category:
                        query = query.filter(Activity.category_id == category.id)
                        print(f"Filtering by category: {category.name} (ID: {category.id})")
                    else:
                        print(f"No category found matching: {activity_payload['category_name']}")
                
                # Handle subcategory as foreign key - first find subcategory ID by name
                if activity_payload["subcategory_name"]:
                    subcategory = db.query(ActivitySubCategory).filter(ActivitySubCategory.name.ilike(f"%{activity_payload['subcategory_name']}%")).first()
                    if subcategory:
                        query = query.filter(Activity.sub_category_id == subcategory.id)
                        print(f"Filtering by subcategory: {subcategory.name} (ID: {subcategory.id})")
                    else:
                        print(f"No subcategory found matching: {activity_payload['subcategory_name']}")
                
                # Get all matches
                matches = query.all()
                print(f"Found {len(matches)} matches")
                
                # Debug: Show all matches
                for i, match in enumerate(matches):
                    print(f"Match {i+1}: {match.name} (ID: {match.id}, Category: {match.category.name if match.category else 'None'}, SubCategory: {match.sub_category.name if match.sub_category else 'None'})")
                
                if len(matches) == 1:
                    # Single exact match - use it directly
                    exact_match = matches[0]
                    print(f"Found single exact match: {exact_match.name} (ID: {exact_match.id})")
                    activity_payload["activity_id"] = str(exact_match.id)  # Convert UUID to string
                    # Clear other fields since we're using ID for direct lookup
                    activity_payload["activity_name"] = None
                    activity_payload["category_name"] = None
                    activity_payload["subcategory_name"] = None
                else:
                    print("No exact match found, will use fuzzy matching")
                    
                # Debug: Show all activities in database
                all_activities = db.query(Activity).filter(Activity.is_active == True).all()
                print(f"Total active activities in database: {len(all_activities)}")
                for i, act in enumerate(all_activities[:5]):  # Show first 5
                    print(f"Activity {i+1}: {act.name} (Category: {act.category.name if act.category else 'None'}, SubCategory: {act.sub_category.name if act.sub_category else 'None'})")
                
                print(f"=== END DATABASE LOOKUP DEBUG ===")
        
    except Exception as e:
        logger.warning(f"Failed to extract structured data: {e}")
        # Fallback: use the entire prompt as activity name
        activity_payload = {
            "activity_name": prompt,
            "category_name": None,
            "subcategory_name": None,
            "activity_id": None
        }
        logger.info(f"Using fallback payload: {activity_payload}")
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
        logger.info(f"Authorization header set: Bearer {token[:20]}...")
    else:
        logger.error("No token found in payload details")

    try:
        async with httpx.AsyncClient() as client_http:
            resp = await client_http.post(
                url,
                json=activity_payload,
                headers=headers,      # <-- pass the user's token here
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

        if data["status"] == "started":
            final_description = data.get("final_description", "")
            if final_description:
                # Recursively invoke the agent with the final_description as the new prompt
                print(f"Recursively invoking agent with final_description: {final_description}")
                new_state = {
                    "prompt": final_description,
                    "details": payload,
                    "db": db
                }
                result = await agent.ainvoke(new_state)
                # Return the result of the recursive invocation
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

        return {"result": {"message": msg}}
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        return {"result": {"error": f"HTTP error: {e.response.status_code} - {e.response.text}"}}
    except Exception as e:
        logger.error(f"Start activity failed: {str(e)}")
        return {"result": {"error": f"Start activity failed: {str(e)}"}}

async def route_activity(state: dict, config: dict) -> dict:
    op = state.get("operation")
    if op == "unknown":
        return {"result": {"error": "Could not determine intent, please rephrase."}}
    result = await activity_crud({"operation": op, "payload": state.get("details", {})}, {})
    return {"result": result.get("result")}

async def generate_activity_handler(state: dict, config: dict) -> dict:
    prompt = state.get("prompt", "")
    result = await chat_completion({"prompt": prompt}, {}, json_mode=False)
    questions = result.get("response", {}).get("text", result.get("response", ""))
    message = f"{questions}"
    prompt = state.get("prompt", "")
    return {"result": {"message": message}}

# Build workflow
workflow.add_node("classify_intent", classify_intent)
workflow.add_node("greet_user", greet_user)
workflow.add_node("describe_capabilities", describe_capabilities)
workflow.add_node("start_activity_tool", start_activity_tool)
workflow.add_node("route_activity", route_activity)
workflow.add_node("generate_activity_handler", generate_activity_handler)

# Transitions
def route_from_classify_intent(state):
    intent = state.get("intent")
    if intent == "greetings":
        return "greet_user"
    elif intent == "capabilities":
        return "describe_capabilities"
    elif intent == "start-activity":
        return "start_activity_tool"
    elif intent == "generate-activity":
        return "generate_activity_handler"
    elif intent in {"create-activity", "edit-activity", "delete-activity", "list-activities"}:
        return "route_activity"
    else:
        # For unknown intents, route to route_activity which will handle the error
        return "route_activity"

workflow.add_conditional_edges("classify_intent", route_from_classify_intent)

# Finish points
workflow.set_entry_point("classify_intent")
for node in ["greet_user","describe_capabilities","start_activity_tool","route_activity","generate_activity_handler"]:
    workflow.set_finish_point(node)

# Compile agent
agent = workflow.compile()
logger.info("Agent workflow compiled successfully")

async def run_agent(input_data: dict) -> dict:
    trace = None
    if langfuse:
        trace = langfuse.trace(name="run_agent")
        trace.input = input_data
    state = {"prompt": input_data.get("prompt", ""), "details": input_data.get("details", {}), "db": input_data.get("db")}
    result = await agent.ainvoke(state)
    output = {"intent": result.get("intent", "unknown"), "result": result.get("result", {})}
    if trace:
        trace.output = output
        trace.end()
    return output
