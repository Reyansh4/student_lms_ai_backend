import json
from app.core.logger import get_logger
from typing import Any, Dict
import httpx

from uuid import UUID
from langgraph.graph import StateGraph
from openai import AsyncAzureOpenAI
from sqlalchemy.orm import joinedload
from langfuse import Langfuse
from app.core.azure_config import load_azure_config
from app.core.config import settings
from app.models.activity import Activity
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.activity import ExtendedStartActivityInput, ExtendedStartActivityResponse
from app.memory.store import InMemoryStore
from app.tools.swagger_loader import get_openapi_spec, clear_openapi_spec_cache
from app.tools.swagger_connectors import register_swagger_tools
from app.agent.tools.activity_tools import create_activity as create_activity_tool
# Configure logging
logger = get_logger(__name__)

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
store = InMemoryStore()
# langfuse_client = Langfuse()
# assert langfuse_client.auth_check(), "Langfuse authentication failed"
# logger.info("Langfuse tracing initialized")
# Optional Langfuse tracing

tools = [create_activity_tool]
# Note: We're not using bound_llm since AsyncAzureOpenAI doesn't support bind_tools
# The create_activity_tool will be called directly in the create_activity_handler
# def trace_function(func_name, input_data, output_data=None, error=None):
#     if not langfuse_client:
#         return
#     with langfuse_client.trace(name=func_name) as trace:
#         trace.input = input_data
#         if output_data:
#             trace.output = output_data
#         if error:
#             trace.error = str(error)

async def chat_completion(
    state: dict,
    config: dict,
    temperature: float = 0.7,
    max_tokens: int = 512,
    json_mode: bool = False
) -> dict:
    logger.debug(f"=== CHAT_COMPLETION START ===")
    logger.debug(f"Input state: {state}")
    logger.debug(f"Config: {config}")
    logger.debug(f"Temperature: {temperature}, Max tokens: {max_tokens}, JSON mode: {json_mode}")
    
    try:
        prompt = state.get("prompt", "")
        messages = state.get("messages", [{"role": "user", "content": prompt}])
        logger.debug(f"Prompt: {prompt}")
        logger.debug(f"Messages: {messages}")
        
        if json_mode:
            system_msg = {"role": "system", "content": "You MUST respond with valid JSON ONLY."}
            messages = [system_msg] + messages
            logger.debug(f"JSON mode enabled, updated messages: {messages}")
        
        params = {
            "model": azure_config.deployment,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        logger.debug(f"OpenAI params: {params}")
        
        response = await client.chat.completions.create(**params)
        content = response.choices[0].message.content.strip()
        logger.debug(f"OpenAI response content: {content}")
        
        try:
            result = {"response": json.loads(content)}
            logger.debug(f"Parsed JSON response: {result}")
            #trace_function("chat_completion", {"prompt": prompt, "json_mode": json_mode}, result)
            logger.debug(f"=== CHAT_COMPLETION SUCCESS (JSON) ===")
            return result
        except json.JSONDecodeError:
            result = {"response": {"text": content}}
            logger.debug(f"JSON decode failed, using text response: {result}")
            #trace_function("chat_completion", {"prompt": prompt, "json_mode": json_mode}, result)
            logger.debug(f"=== CHAT_COMPLETION SUCCESS (TEXT) ===")
            return result
    except Exception as e:
        logger.error(f"=== CHAT_COMPLETION ERROR ===")
        logger.error(f"Error details: {e}")
        #trace_function("chat_completion", state, error=e)
        logger.error(f"Chat completion failed: {e}")
        raise

async def activity_crud(
    state: dict,
    config: dict
) -> dict:
    logger.debug(f"=== ACTIVITY_CRUD START ===")
    logger.debug(f"Input state: {state}")
    logger.debug(f"Config: {config}")
    
    try:
        operation = state.get("operation")
        payload = state.get("payload", {})
        logger.debug(f"Operation: {operation}")
        logger.debug(f"Payload: {payload}")
        
        method_map = {
            "create": ("post", "/activities"),
            "list":   ("get",  "/activities"),
            "edit":   ("put",  f"/activities/{payload.get('id')}"),
            "delete": ("delete", f"/activities/{payload.get('id')}")
        }
        method, path = method_map[operation]
        url = f"{ACTIVITY_SERVICE_URL}{path}"
        logger.debug(f"HTTP method: {method}")
        logger.debug(f"Path: {path}")
        logger.debug(f"Full URL: {url}")
        
        async with httpx.AsyncClient() as client_http:
            resp = await client_http.request(method, url, json=payload if method != 'get' else None, timeout=10)
            logger.debug(f"HTTP response status: {resp.status_code}")
            logger.debug(f"HTTP response headers: {dict(resp.headers)}")
            resp.raise_for_status()
            result = resp.json()
            logger.debug(f"HTTP response body: {result}")
        
        #trace_function("activity_crud", {"operation": operation, "payload": payload}, {"result": result})
        logger.debug(f"=== ACTIVITY_CRUD SUCCESS ===")
        return {"result": result}
    except Exception as e:
        logger.error(f"=== ACTIVITY_CRUD ERROR ===")
        logger.error(f"Error details: {e}")
        #trace_function("activity_crud", state, error=e)
        logger.error(f"Activity CRUD failed: {e}")
        raise

async def classify_intent(state: dict, config: dict) -> dict:
    logger.debug(f"=== CLASSIFY_INTENT START ===")
    logger.debug(f"Input state: {state}")
    logger.debug(f"Config: {config}")
    
    prompt_text = state.get("prompt", "")
    logger.debug(f"Prompt text: {prompt_text}")
    
    # First, check for spelling mistakes in the prompt
    spell_check_prompt = f"""
    Check the following text for spelling mistakes and suggest corrections. 
    Focus on educational terms, subjects, and activity-related words.
    
    Text: "{prompt_text}"
    
    Return JSON with:
    - has_spelling_errors: boolean
    - corrected_text: string (original text if no errors)
    - suggestions: array of corrected words with their original misspellings
    
    Examples:
    - "creat a math quiz" → {{"has_spelling_errors": true, "corrected_text": "create a math quiz", "suggestions": [{{"original": "creat", "corrected": "create"}}]}}
    - "start a phisics experiment" → {{"has_spelling_errors": true, "corrected_text": "start a physics experiment", "suggestions": [{{"original": "phisics", "corrected": "physics"}}]}}
    - "hello there" → {{"has_spelling_errors": false, "corrected_text": "hello there", "suggestions": []}}
    """
    
    try:
        spell_check_result = await chat_completion({"prompt": spell_check_prompt}, {}, json_mode=True)
        spell_check_data = spell_check_result.get("response", {})
        logger.debug(f"Spell check result: {spell_check_data}")
        
        has_spelling_errors = spell_check_data.get("has_spelling_errors", False)
        corrected_text = spell_check_data.get("corrected_text", prompt_text)
        suggestions = spell_check_data.get("suggestions", [])
        
        # If there are spelling errors, ask user to confirm
        if has_spelling_errors and suggestions:
            suggestions_text = ", ".join([f"'{s['original']}' → '{s['corrected']}'" for s in suggestions])
            spell_correction_message = f"🤔 I noticed some spelling in your request. Did you mean:\n\n**{suggestions_text}**\n\n**Original:** {prompt_text}\n**Corrected:** {corrected_text}\n\nPlease confirm if this is what you meant, or rephrase your request."
            
            # Return early with spell correction request
            output = {
                **state,
                "intent": "spell-correction",
                "confidence": 0.0,
                "operation": "spell-correction",
                "corrected_text": corrected_text,
                "suggestions": suggestions,
                "spell_correction_message": spell_correction_message
            }
            logger.debug(f"Spelling errors detected, returning correction request: {output}")
            return output
            
    except Exception as e:
        logger.warning(f"Spell check failed: {e}, proceeding with original text")
        corrected_text = prompt_text
    
    # Proceed with intent classification using corrected text
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
        f"User input: '{corrected_text}'"
    )
    logger.debug(f"Classification prompt: {classification_prompt}")
    
    classification = await chat_completion({"prompt": classification_prompt}, {}, json_mode=True)
    logger.debug(f"Classification result: {classification}")
    
    result = classification.get("response", {})
    logger.debug(f"Extracted result: {result}")
    
    if "text" in result:
        text = result["text"].lower()
        intent = "unknown"
        if any(w in text for w in ["hello","hi","hey"]): intent="greetings"
        elif "what can you do" in text: intent="capabilities"
        elif "start" in text: intent="start-activity"
        result = {"intent": intent, "confidence": 0.5}
        logger.debug(f"Fallback classification - text: {text}, intent: {intent}")
    
    intent = result.get("intent", "unknown").lower()
    valid_intents = {"create-activity","edit-activity","delete-activity","list-activities","start-activity","generate-activity","greetings","capabilities"}
    if intent not in valid_intents:
        intent="unknown"
        logger.debug(f"Invalid intent '{intent}', setting to 'unknown'")
    
    confidence = result.get("confidence", 0.0)
    operation = intent.replace("-activity","") if intent.endswith("-activity") else intent
    
    logger.debug(f"Final intent: {intent}")
    logger.debug(f"Confidence: {confidence}")
    logger.debug(f"Operation: {operation}")
    
    # CRITICAL: Preserve the original state while adding classification results
    output = {
        **state,  # Keep all original state (including 'db', 'prompt', 'details', 'token')
        "intent": intent, 
        "confidence": confidence, 
        "operation": operation,
        "corrected_text": corrected_text
    }
    
    logger.debug(f"Final output: {output}")
    #trace_function("classify_intent", {"prompt": prompt_text}, output)
    logger.debug(f"=== CLASSIFY_INTENT SUCCESS ===")
    return output

async def greet_user(state: dict, config: dict) -> dict:
    logger.debug(f"=== GREET_USER START ===")
    logger.debug(f"Input state: {state}")
    logger.debug(f"Config: {config}")
    
    result = {"result": {"message": "Hi! I'm **Leena AI**, your learning assistant—how can I help you today?"}}
    logger.debug(f"Greet user result: {result}")
    logger.debug(f"=== GREET_USER SUCCESS ===")
    return result

async def describe_capabilities(state: dict, config: dict) -> dict:
    logger.debug(f"=== DESCRIBE_CAPABILITIES START ===")
    logger.debug(f"Input state: {state}")
    logger.debug(f"Config: {config}")
    
    result = {"result": {"message": (
        "I can help you:\n"
        "- create new activities\n"
        "- start or match existing activities\n"
        "- teach topics step-by-step\n"
        "- generate tests and evaluate answers\n"
        "…and more, just ask!"
    )}}
    logger.debug(f"Describe capabilities result: {result}")
    logger.debug(f"=== DESCRIBE_CAPABILITIES SUCCESS ===")
    return result

async def spell_correction_handler(state: dict, config: dict) -> dict:
    logger.debug(f"=== SPELL_CORRECTION_HANDLER START ===")
    logger.debug(f"Input state: {state}")
    logger.debug(f"Config: {config}")
    
    spell_correction_message = state.get("spell_correction_message", "I noticed some spelling issues. Please rephrase your request.")
    
    result = {"result": {"message": spell_correction_message}}
    logger.debug(f"Spell correction handler result: {result}")
    logger.debug(f"=== SPELL_CORRECTION_HANDLER SUCCESS ===")
    return result

async def start_activity_tool(state: dict, config: dict) -> dict:
    logger.debug(f"=== START_ACTIVITY_TOOL START ===")
    logger.debug(f"Input state: {state}")
    logger.debug(f"Config: {config}")
    
    prompt = state.get("prompt", "")
    payload = state.get("details", {})
    token = payload.get("token")  # extract the JWT we stashed earlier
    db = state.get("db")  # get database session

    logger.debug(f"Prompt: {prompt}")
    logger.debug(f"Payload: {payload}")
    logger.debug(f"Token present: {token is not None}")
    logger.debug(f"Token length: {len(token) if token else 0}")
    logger.debug(f"Database session present: {db is not None}")

    url = f"{settings.SERVER_HOST}{settings.API_PREFIX}/agent/start-activity"
    headers = {}
    logger.info(f"Token present: {token is not None}")
    logger.info(f"Token length: {len(token) if token else 0}")
    logger.info(f"URL: {url}")
    logger.info(f"Original prompt: {prompt}")
    logger.debug(f"Full URL: {url}")
    logger.debug(f"Headers: {headers}")
    
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
    
    logger.debug(f"Extraction prompt: {extraction_prompt}")
    
    try:
        # Extract structured information from the prompt
        extraction_result = await chat_completion({"prompt": extraction_prompt}, {}, json_mode=True)
        extracted_data = extraction_result.get("response", {})
        
        logger.debug(f"Extraction result: {extraction_result}")
        logger.debug(f"Extracted data: {extracted_data}")
        
        # Create the payload that the /start-activity endpoint expects
        activity_payload = {
            "activity_name": extracted_data.get("activity_name"),
            "category_name": extracted_data.get("category_name"),
            "subcategory_name": extracted_data.get("subcategory_name"),
            "activity_id": None
        }
        
        print(f"Extracted data: {extracted_data}")
        print(f"Activity payload: {activity_payload}")
        logger.debug(f"Activity payload: {activity_payload}")
        
        # Try to find exact match in database first
        if activity_payload["activity_name"]:
            if not db:
                print("Database session not available, will use HTTP endpoint for fuzzy matching")
                logger.debug("Database session not available, will use HTTP endpoint for fuzzy matching")
            else:
                from app.models.activity import Activity
                from app.models.activity_category import ActivityCategory
                from app.models.activity_sub_category import ActivitySubCategory
                from sqlalchemy.orm import joinedload
                
                print(f"=== DATABASE LOOKUP DEBUG ===")
                logger.debug(f"=== DATABASE LOOKUP DEBUG ===")
                print(f"Looking for: activity_name='{activity_payload['activity_name']}', category='{activity_payload['category_name']}', subcategory='{activity_payload['subcategory_name']}'")
                logger.debug(f"Looking for: activity_name='{activity_payload['activity_name']}', category='{activity_payload['category_name']}', subcategory='{activity_payload['subcategory_name']}'")
                
                # Build query based on available extracted data
                query = db.query(Activity).options(
                    joinedload(Activity.category),
                    joinedload(Activity.sub_category)
                ).filter(Activity.is_active == True)
                
                # Add filters based on extracted data
                if activity_payload["activity_name"]:
                    query = query.filter(Activity.name.ilike(f"%{activity_payload['activity_name']}%"))
                    print(f"Added activity name filter: '%{activity_payload['activity_name']}%'")
                    logger.debug(f"Added activity name filter: '%{activity_payload['activity_name']}%'")
                
                # Handle category as foreign key - first find category ID by name
                if activity_payload["category_name"]:
                    category = db.query(ActivityCategory).filter(ActivityCategory.name.ilike(f"%{activity_payload['category_name']}%")).first()
                    if category:
                        query = query.filter(Activity.category_id == category.id)
                        print(f"Filtering by category: {category.name} (ID: {category.id})")
                        logger.debug(f"Filtering by category: {category.name} (ID: {category.id})")
                    else:
                        print(f"No category found matching: {activity_payload['category_name']}")
                        logger.debug(f"No category found matching: {activity_payload['category_name']}")
                
                # Handle subcategory as foreign key - first find subcategory ID by name
                if activity_payload["subcategory_name"]:
                    subcategory = db.query(ActivitySubCategory).filter(ActivitySubCategory.name.ilike(f"%{activity_payload['subcategory_name']}%")).first()
                    if subcategory:
                        query = query.filter(Activity.sub_category_id == subcategory.id)
                        print(f"Filtering by subcategory: {subcategory.name} (ID: {subcategory.id})")
                        logger.debug(f"Filtering by subcategory: {subcategory.name} (ID: {subcategory.id})")
                    else:
                        print(f"No subcategory found matching: {activity_payload['subcategory_name']}")
                        logger.debug(f"No subcategory found matching: {activity_payload['subcategory_name']}")
                
                # Get all matches
                matches = query.all()
                print(f"Found {len(matches)} matches")
                logger.debug(f"Found {len(matches)} matches")
                
                # Debug: Show all matches
                for i, match in enumerate(matches):
                    print(f"Match {i+1}: {match.name} (ID: {match.id}, Category: {match.category.name if match.category else 'None'}, SubCategory: {match.sub_category.name if match.sub_category else 'None'})")
                    logger.debug(f"Match {i+1}: {match.name} (ID: {match.id}, Category: {match.category.name if match.category else 'None'}, SubCategory: {match.sub_category.name if match.sub_category else 'None'})")
                
                if len(matches) == 1:
                    # Single exact match - use it directly
                    exact_match = matches[0]
                    print(f"Found single exact match: {exact_match.name} (ID: {exact_match.id})")
                    logger.debug(f"Found single exact match: {exact_match.name} (ID: {exact_match.id})")
                    activity_payload["activity_id"] = str(exact_match.id)  # Convert UUID to string
                    # Clear other fields since we're using ID for direct lookup
                    activity_payload["activity_name"] = None
                    activity_payload["category_name"] = None
                    activity_payload["subcategory_name"] = None
                else:
                    print("No exact match found, will use fuzzy matching")
                    logger.debug("No exact match found, will use fuzzy matching")
                    
                # Debug: Show all activities in database
                all_activities = db.query(Activity).filter(Activity.is_active == True).all()
                print(f"Total active activities in database: {len(all_activities)}")
                logger.debug(f"Total active activities in database: {len(all_activities)}")
                for i, act in enumerate(all_activities[:5]):  # Show first 5
                    print(f"Activity {i+1}: {act.name} (Category: {act.category.name if act.category else 'None'}, SubCategory: {act.sub_category.name if act.sub_category else 'None'})")
                    logger.debug(f"Activity {i+1}: {act.name} (Category: {act.category.name if act.category else 'None'}, SubCategory: {act.sub_category.name if act.sub_category else 'None'})")
                
                print(f"=== END DATABASE LOOKUP DEBUG ===")
                logger.debug(f"=== END DATABASE LOOKUP DEBUG ===")
        
    except Exception as e:
        logger.warning(f"Failed to extract structured data: {e}")
        logger.debug(f"Exception details: {e}")
        # Fallback: use the entire prompt as activity name
        activity_payload = {
            "activity_name": prompt,
            "category_name": None,
            "subcategory_name": None,
            "activity_id": None
        }
        logger.info(f"Using fallback payload: {activity_payload}")
        logger.debug(f"Fallback activity payload: {activity_payload}")
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
        logger.info(f"Authorization header set: Bearer {token[:20]}...")
        logger.debug(f"Authorization header set: Bearer {token[:20]}...")
    else:
        logger.error("No token found in payload details")
        logger.debug("No token found in payload details")

    try:
        logger.debug(f"Making HTTP request to: {url}")
        logger.debug(f"Request payload: {activity_payload}")
        logger.debug(f"Request headers: {headers}")
        
        async with httpx.AsyncClient() as client_http:
            resp = await client_http.post(
                url,
                json=activity_payload,
                headers=headers,      # <-- pass the user's token here
                timeout=10
            )
            logger.debug(f"HTTP response status: {resp.status_code}")
            logger.debug(f"HTTP response headers: {dict(resp.headers)}")
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"HTTP response body: {data}")

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
            logger.debug(f"Multiple activities found, message: {msg}")

        result = {"result": {"message": msg}}
        logger.debug(f"Start activity tool result: {result}")
        logger.debug(f"=== START_ACTIVITY_TOOL SUCCESS ===")
        return result
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        logger.debug(f"HTTP error details: {e}")
        logger.debug(f"HTTP response status: {e.response.status_code}")
        logger.debug(f"HTTP response text: {e.response.text}")
        result = {"result": {"error": f"HTTP error: {e.response.status_code} - {e.response.text}"}}
        logger.debug(f"=== START_ACTIVITY_TOOL HTTP ERROR ===")
        return result
    except Exception as e:
        logger.error(f"Start activity failed: {str(e)}")
        logger.debug(f"Exception details: {e}")
        result = {"result": {"error": f"Start activity failed: {str(e)}"}}
        logger.debug(f"=== START_ACTIVITY_TOOL EXCEPTION ===")
        return result

async def route_activity(state: dict, config: dict) -> dict:
    logger.debug(f"=== ROUTE_ACTIVITY START ===")
    logger.debug(f"Input state: {state}")
    logger.debug(f"Config: {config}")
    
    op = state.get("operation")
    logger.debug(f"Operation: {op}")
    
    if op == "unknown":
        result = {"result": {"error": "Could not determine intent, please rephrase."}}
        logger.debug(f"Unknown operation, returning error: {result}")
        logger.debug(f"=== ROUTE_ACTIVITY UNKNOWN OPERATION ===")
        return result
    
    result = await activity_crud({"operation": op, "payload": state.get("details", {})}, {})
    return {"result": result.get("result")}

async def generate_activity_handler(state: dict, config: dict) -> dict:
    prompt = state.get("prompt", "")
    result = await chat_completion({"prompt": prompt}, {}, json_mode=False)
    questions = result.get("response", {}).get("text", result.get("response", ""))
    message = f"{questions}"
    prompt = state.get("prompt", "")
    return {"result": {"message": message}}

async def create_activity_handler(state: dict, config: dict) -> dict:
    logger.debug(f"=== CREATE_ACTIVITY_HANDLER START ===")
    logger.debug(f"Input state: {state}")
    logger.debug(f"Config: {config}")
    
    prompt = state.get("prompt", "")
    logger.debug(f"Prompt: {prompt}")
    
    # Use AI to extract activity creation details from the prompt
    extraction_prompt = f"""
    Extract activity creation information from this user request. Return JSON with these fields:
    - name: The activity name/title
    - description: A detailed description of the activity
    - category_name: The subject/category (e.g., math, science, physics, history)
    - subcategory_name: The specific topic/subcategory (e.g., algebra, calculus, refractive index)
    - difficulty_level: One of "Beginner", "Intermediate", or "Advanced"
    
    User request: "{prompt}"
    
    Examples:
    - "Create a math quiz about algebra for beginners" → {{"name": "Algebra Quiz", "description": "A quiz covering basic algebra concepts", "category_name": "math", "subcategory_name": "algebra", "difficulty_level": "Beginner"}}
    - "Make a physics experiment on refractive index for advanced students" → {{"name": "Refractive Index Experiment", "description": "Advanced experiment to measure and analyze refractive index", "category_name": "physics", "subcategory_name": "refractive index", "difficulty_level": "Advanced"}}
    """
    
    logger.debug(f"Extraction prompt: {extraction_prompt}")
    
    try:
        # Extract structured information from the prompt
        extraction_result = await chat_completion({"prompt": extraction_prompt}, {}, json_mode=True)
        extracted_data = extraction_result.get("response", {})
        
        logger.debug(f"Extraction result: {extraction_result}")
        logger.debug(f"Extracted data: {extracted_data}")
        
        # Get user information from state
        details = state.get("details", {})
        user_id = details.get("user_id")
        
        # Also check if user_id is directly in the state (from run_agent input)
        if not user_id:
            user_id = state.get("user_id")
        
        # Get database session for looking up category and subcategory IDs
        db = state.get("db")
        if not db:
            raise ValueError("Database session not available")
        
        # Look up category and subcategory IDs by name
        from app.models.activity_category import ActivityCategory
        from app.models.activity_sub_category import ActivitySubCategory
        
        category_name = extracted_data.get("category_name", "General")
        subcategory_name = extracted_data.get("subcategory_name", "General")
        
        # Find category by name using fuzzy matching
        # First try exact match
        category = db.query(ActivityCategory).filter(ActivityCategory.name.ilike(f"%{category_name}%")).first()
        
        # If no exact match, try fuzzy matching with common variations
        if not category:
            # Try different variations of the category name
            variations = [
                category_name.lower(),
                category_name.title(),
                category_name.capitalize(),
                category_name.replace(" ", ""),
                category_name.replace(" ", "_"),
                category_name.replace(" ", "-")
            ]
            
            for variation in variations:
                category = db.query(ActivityCategory).filter(
                    ActivityCategory.name.ilike(f"%{variation}%")
                ).first()
                if category:
                    logger.info(f"Found category '{category.name}' using fuzzy match for '{category_name}'")
                    break
        
        # If still no match, create new category
        if not category:
            category = ActivityCategory(name=category_name)
            db.add(category)
            db.flush()
            logger.info(f"Created new category: {category_name} with ID: {category.id}")
        
        # Find subcategory by name using fuzzy matching
        # First try exact match within the category
        subcategory = db.query(ActivitySubCategory).filter(
            ActivitySubCategory.name.ilike(f"%{subcategory_name}%"),
            ActivitySubCategory.category_id == category.id
        ).first()
        
        # If no exact match, try fuzzy matching with common variations
        if not subcategory:
            # Try different variations of the subcategory name
            variations = [
                subcategory_name.lower(),
                subcategory_name.title(),
                subcategory_name.capitalize(),
                subcategory_name.replace(" ", ""),
                subcategory_name.replace(" ", "_"),
                subcategory_name.replace(" ", "-")
            ]
            
            for variation in variations:
                subcategory = db.query(ActivitySubCategory).filter(
                    ActivitySubCategory.name.ilike(f"%{variation}%"),
                    ActivitySubCategory.category_id == category.id
                ).first()
                if subcategory:
                    logger.info(f"Found subcategory '{subcategory.name}' using fuzzy match for '{subcategory_name}'")
                    break
        
        # If still no match, create new subcategory
        if not subcategory:
            subcategory = ActivitySubCategory(name=subcategory_name, category_id=category.id)
            db.add(subcategory)
            db.flush()
            logger.info(f"Created new subcategory: {subcategory_name} with ID: {subcategory.id}")
        
        # Prepare payload for create_activity tool
        logger.info(f"Extracted data: {extracted_data}")
        activity_payload = {
            "name": extracted_data.get("name", "New Activity"),
            "description": extracted_data.get("description", ""),
            "category_id": str(category.id),
            "sub_category_id": str(subcategory.id),
            "difficulty_level": extracted_data.get("difficulty_level", "Beginner"),
            "created_by": user_id,
            "access_type": "private"  # Always PRIVATE for agent-created activities
        }
        
        logger.info(f"Activity payload: {activity_payload}")
        
        # Call the create_activity tool
        tool_result = await create_activity_tool.ainvoke(activity_payload)
        logger.debug(f"Create activity tool result: {tool_result}")
        
        # Format success message
        message = f"✅ Activity created successfully!\n\n**{tool_result['name']}**\n\n**Description:** {tool_result['description']}\n**Category:** {tool_result['category']}\n**Subcategory:** {tool_result['subcategory']}\n**Difficulty:** {tool_result['difficulty_level']}\n**Access Type:** {tool_result['access_type']}\n\nActivity ID: {tool_result['id']}"
        
        result = {"result": {"message": message}}
        logger.debug(f"Create activity handler result: {result}")
        logger.debug(f"=== CREATE_ACTIVITY_HANDLER SUCCESS ===")
        return result
        
    except Exception as e:
        logger.error(f"=== CREATE_ACTIVITY_HANDLER ERROR ===")
        logger.error(f"Error details: {e}")
        error_message = f"❌ Failed to create activity: {str(e)}"
        result = {"result": {"error": error_message}}
        logger.debug(f"=== CREATE_ACTIVITY_HANDLER EXCEPTION ===")
        return result

# Build workflow
workflow.add_node("classify_intent", classify_intent)
workflow.add_node("greet_user", greet_user)
workflow.add_node("describe_capabilities", describe_capabilities)
workflow.add_node("spell_correction_handler", spell_correction_handler)
workflow.add_node("start_activity_tool", start_activity_tool)
workflow.add_node("route_activity", route_activity)
workflow.add_node("generate_activity_handler", generate_activity_handler)
workflow.add_node("create_activity_handler", create_activity_handler)

# Transitions
def route_from_classify_intent(state):
    logger.debug(f"=== ROUTE_FROM_CLASSIFY_INTENT START ===")
    logger.debug(f"Input state: {state}")
    
    intent = state.get("intent")
    logger.debug(f"Intent: {intent}")
    
    if intent == "greetings":
        logger.debug("Routing to: greet_user")
        return "greet_user"
    elif intent == "capabilities":
        logger.debug("Routing to: describe_capabilities")
        return "describe_capabilities"
    elif intent == "spell-correction":
        logger.debug("Routing to: spell_correction_handler")
        return "spell_correction_handler"
    elif intent == "start-activity":
        logger.debug("Routing to: start_activity_tool")
        return "start_activity_tool"
    elif intent == "generate-activity":
        return "generate_activity_handler"
    elif intent == "create-activity":
        logger.debug("Routing to: create_activity_handler")
        return "create_activity_handler"
    elif intent in {"edit-activity", "delete-activity", "list-activities"}:
        logger.debug("Routing to: route_activity")
        return "route_activity"
    else:
        # For unknown intents, route to route_activity which will handle the error
        logger.debug("Unknown intent, routing to: route_activity")
        return "route_activity"

workflow.add_conditional_edges("classify_intent", route_from_classify_intent)

# Finish points
workflow.set_entry_point("classify_intent")
for node in ["greet_user","describe_capabilities","spell_correction_handler","start_activity_tool","route_activity","generate_activity_handler","create_activity_handler"]:
    workflow.set_finish_point(node)

# Compile agent
agent = workflow.compile()
logger.info("Agent workflow compiled successfully")
_lazy_swagger_initialized = False

async def run_agent(input_data: dict) -> dict:
    global _lazy_swagger_initialized
    # Cold-start: register Swagger tools on first agent request
    # print(f"Running agent")
    # print(f"Lazy swagger initialized: {_lazy_swagger_initialized}")
    # if not _lazy_swagger_initialized:
    #     clear_openapi_spec_cache()
    #     spec = get_openapi_spec()
    #     register_swagger_tools(workflow, spec)
    #     _lazy_swagger_initialized = True
    #     logger.info(f"Registered Swagger tools: {list(workflow.nodes.keys())}")
    logger.debug(f"=== RUN_AGENT START ===")
    logger.debug(f"Input data: {input_data}")
    
    trace = None
    # if langfuse:
    #     trace = langfuse.trace(name="run_agent")
    #     trace.input = input_data
    user_id = input_data.get("user_id")
    if not user_id:
        raise ValueError("user_id is required for session memory")
    
    # 1) Get or create an in-memory session
    session = store.get_or_create_session(user_id)
    prompt=input_data.get("prompt", "")
    # 2) Record the user turn
    store.add_message(session.session_id, "user", prompt)
    history = store.get_history(session.session_id)
    messages = [{"role": m.role, "content": m.content} for m in history]
    state = {"prompt":prompt , "details": input_data.get("details", {}), "db": input_data.get("db"), "messages": messages, "user_id": user_id}
    logger.debug(f"Initial state: {state}")
    
    logger.debug(f"Invoking agent workflow...")
    result = await agent.ainvoke(state)
    logger.debug(f"Agent workflow result: {result}")
    reply = result.get("result", {}).get("message", "")
    store.add_message(session.session_id, "assistant", reply)
    
    output = {"intent": result.get("intent", "unknown"), "result": result.get("result", {}),"session_id": session.session_id}
    logger.debug(f"Final output: {output}")
    
    if trace:
        trace.output = output
        trace.end()
        logger.debug("Langfuse trace ended")
    
    logger.debug(f"=== RUN_AGENT SUCCESS ===")
    return output
