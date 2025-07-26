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
from app.models.user import User
from app.schemas.activity import ExtendedStartActivityInput, ExtendedStartActivityResponse
from app.memory.store import InMemoryStore
from app.agent.tools.activity_tools import create_activity as create_activity_tool
from app.agent.evaluator_agent import evaluate_performance_tool
from app.agent.tools.evaluation_tools import evaluate_user_performance, get_evaluation_history, analyze_learning_progress
from app.models.activity import Activity
from app.models.activity_category import ActivityCategory
from app.models.activity_sub_category import ActivitySubCategory
from sqlalchemy.orm import joinedload
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

tools = [create_activity_tool, evaluate_performance_tool, evaluate_user_performance, get_evaluation_history, analyze_learning_progress]
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
    logger.debug(f"Chat completion - temp:{temperature}, max_tokens:{max_tokens}, json_mode:{json_mode}")
    
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
            logger.debug("Chat completion successful (JSON)")
            return result
        except json.JSONDecodeError:
            result = {"response": {"text": content}}
            logger.debug("Chat completion successful (TEXT)")
            return result
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise

async def activity_crud(
    state: dict,
    config: dict
) -> dict:
    logger.debug("Activity CRUD operation started")
    
    try:
        operation = state.get("operation")
        payload = state.get("payload", {})
        
        method_map = {
            "create": ("post", ""),
            "list":   ("get",  ""),
            "list-activities": ("get", ""),
            "edit":   ("put",  f"/{payload.get('id')}"),
            "delete": ("delete", f"/{payload.get('id')}")
        }
        method, path = method_map[operation]
        url = f"{ACTIVITY_SERVICE_URL}{path}/" if path == "" else f"{ACTIVITY_SERVICE_URL}{path}"
        logger.debug(f"Activity CRUD - {method} {url}")

        # Prepare headers
        headers = {}
        if payload.get("token"):
            headers["Authorization"] = f"Bearer {payload['token']}"

        # For GET, use query params; for others, use JSON body
        if method == "get":
            # Only include valid query params
            query_params = {k: v for k, v in payload.items() if k in {"category_name", "subcategory_name", "activity_name", "skip", "limit"} and v is not None}
            async with httpx.AsyncClient() as client_http:
                resp = await client_http.request(method, url, params=query_params, headers=headers, timeout=10)
        else:
            async with httpx.AsyncClient() as client_http:
                resp = await client_http.request(method, url, json=payload, headers=headers, timeout=10)

        resp.raise_for_status()
        result = resp.json()
        logger.debug(f"Activity CRUD successful - status:{resp.status_code}")
        return {"result": result}
    except Exception as e:
        logger.error(f"Activity CRUD failed: {e}")
        raise

async def classify_intent(state: dict, config: dict) -> dict:
    logger.debug("Classify intent started")
    
    prompt_text = state.get("prompt", "")
    
    # First, check for spelling mistakes in the prompt
    spell_check_prompt = f"""
    Check the following text for actual spelling mistakes (not capitalization differences). 
    Focus on educational terms, subjects, and activity-related words.
    
    IMPORTANT: Do NOT flag capitalization differences as spelling errors. 
    "Test" vs "test" or "Physics" vs "physics" are NOT spelling errors.
    Only flag actual misspellings like "phisics" vs "physics" or "creat" vs "create".
    
    Text: "{prompt_text}"
    
    Return JSON with:
    - has_spelling_errors: boolean (true only for actual misspellings, not capitalization)
    - corrected_text: string (original text if no errors)
    - suggestions: array of corrected words with their original misspellings
    
    Examples:
    - "creat a math quiz" → {{"has_spelling_errors": true, "corrected_text": "create a math quiz", "suggestions": [{{"original": "creat", "corrected": "create"}}]}}
    - "start a phisics experiment" → {{"has_spelling_errors": true, "corrected_text": "start a physics experiment", "suggestions": [{{"original": "phisics", "corrected": "physics"}}]}}
    - "Test paper in Physics" → {{"has_spelling_errors": false, "corrected_text": "Test paper in Physics", "suggestions": []}}
    - "hello there" → {{"has_spelling_errors": false, "corrected_text": "hello there", "suggestions": []}}
    """
    
    try:
        spell_check_result = await chat_completion(
            {"prompt": spell_check_prompt}, {}, json_mode=True
        )
        spell_check_data = spell_check_result.get("response", {})
        
        has_spelling_errors = spell_check_data.get("has_spelling_errors", False)
        corrected_text = spell_check_data.get("corrected_text", prompt_text)
        suggestions = spell_check_data.get("suggestions", [])
        
        # If there are spelling errors, proceed with corrected text automatically
        if has_spelling_errors and suggestions:
            # Check if the corrections are just capitalization differences
            only_capitalization_changes = all(
                s['original'].lower() == s['corrected'].lower() 
                for s in suggestions
            )
            
            if only_capitalization_changes:
                # If only capitalization changed, proceed with corrected text without asking
                logger.info(f"Only capitalization changes detected, proceeding with corrected text: {corrected_text}")
            else:
                # Real spelling errors detected, but proceed automatically with corrected text
                suggestions_text = ", ".join([f"'{s['original']}' → '{s['corrected']}'" for s in suggestions])
                logger.info(f"Spelling corrections applied automatically: {suggestions_text}")
                logger.info(f"Proceeding with corrected text: {corrected_text}")
                # Continue with the corrected text instead of asking user to confirm
            
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
        "- evaluate-performance: User wants to evaluate performance, progress, quiz results, or asks 'how am I doing', 'evaluate my quiz', 'show my progress', etc.\n"
        "Return JSON with 'intent' and 'confidence'.\n"
        f"User input: '{corrected_text}'"
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
    valid_intents = {"create-activity","edit-activity","delete-activity","list-activities","start-activity","generate-activity","greetings","capabilities","evaluate-performance"}
    if intent not in valid_intents:
        intent="unknown"
    
    confidence = result.get("confidence", 0.0)
    operation = intent.replace("-activity","") if intent.endswith("-activity") else intent
    
    logger.debug(f"Intent classified: {intent} (confidence: {confidence})")
    
    # CRITICAL: Preserve the original state while adding classification results
    output = {
        **state,  # Keep all original state (including 'db', 'prompt', 'details', 'token')
        "intent": intent, 
        "confidence": confidence, 
        "operation": operation,
        "corrected_text": corrected_text
    }
    
    return output

async def greet_user(state: dict, config: dict) -> dict:
    logger.debug("Greet user handler")
    result = {
        "message": "Hi! I'm **Leena AI**, your learning assistant—how can I help you today?",
        "activity_id": ""
    }
    return result

async def describe_capabilities(state: dict, config: dict) -> dict:
    logger.debug("Describe capabilities handler")
    result = {
        "message": (
            "I can help you:\n"
            "- create new activities\n"
            "- start or match existing activities\n"
            "- teach topics step-by-step\n"
            "- generate tests and evaluate answers\n"
            "…and more, just ask!"
        ),
        "activity_id": ""
    }
    return result

async def spell_correction_handler(state: dict, config: dict) -> dict:
    logger.debug("Spell correction handler")
    spell_correction_message = state.get("spell_correction_message", "I noticed some spelling issues. Please rephrase your request.")
    result = {
        "message": spell_correction_message,
        "activity_id": ""
    }
    return result

async def start_activity_tool(state: dict, config: dict) -> dict:
    logger.debug("Start activity tool handler")
    
    prompt = state.get("prompt", "")
    details = state.get("details", {})
    token = details.get("token")
    db = state.get("db")
    
    # Get user information from state
    details = state.get("details", {})
    user_id = details.get("user_id")
    if not user_id:
        user_id = state.get("user_id")
    if not user_id:
        # Fetch the first user from the database
        from app.models.user import User
        db_session = state.get("db")
        if db_session:
            first_user = db_session.query(User).order_by(User.created_at).first()
            if first_user:
                user_id = str(first_user.id)
            else:
                raise ValueError("No users found in the database to use as created_by.")
        else:
            raise ValueError("Database session not available to fetch a user.")
    
    # Check if user provided a specific activity ID
    if "activity_id" in state and state["activity_id"]:
        activity_id = state["activity_id"]
        logger.info(f"Using provided activity ID: {activity_id}")
        
        activity_payload = {
            "activity_id": str(activity_id),
            "activity_name": None,
            "category_name": None,
            "subcategory_name": None,
            "created_by": user_id
        }
        
        logger.info(f"Using activity ID for direct lookup: {activity_payload}")
        
        # Skip the extraction and fuzzy matching logic
        goto_http_request = True
    else:
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
                "activity_id": None,
                "created_by": user_id
            }
            
            print(f"Extracted data: {extracted_data}")
            print(f"Activity payload: {activity_payload}")
            
            # Try to find exact match in database first
            if activity_payload["activity_name"] and db:
                print(f"=== DATABASE LOOKUP DEBUG ===")
                
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
                    
                print(f"=== END DATABASE LOOKUP DEBUG ===")
            
        except Exception as e:
            logger.warning(f"Failed to extract structured data: {e}")
            # Fallback: use the entire prompt as activity name
            activity_payload = {
                "activity_name": prompt,
                "category_name": None,
                "subcategory_name": None,
                "activity_id": None,
                "created_by": user_id
            }
            logger.info(f"Using fallback payload: {activity_payload}")
    
    try:
        # Instead of making HTTP calls, use the internal agent router
        # Import the start_activity_handler function from the agent module
        from app.agent.start_activity import start_activity_handler
        
        logger.debug(f"Calling internal start_activity_handler with payload: {activity_payload}")
        
        # Call the internal start_activity_handler function
        # Convert the payload to user_input format
        user_input = prompt  # Use the original prompt as user input
        result = await start_activity_handler(user_input, db)
        
        logger.debug(f"Internal start_activity_handler result: {result}")
        
        # Extract activity_id if present in the result
        activity_id = ""
        if isinstance(result, dict):
            if "activity_id" in result:
                activity_id = result["activity_id"]
            elif "suggestions" in result and result["suggestions"]:
                # If there are suggestions, use the first one's activity_id
                activity_id = result["suggestions"][0].get("activity_id", "")
        
        return {
            **result,
            "activity_id": activity_id
        }
        
    except Exception as e:
        logger.error(f"Start activity failed: {e}")
        raise

async def route_activity(state: dict, config: dict) -> dict:
    logger.debug("Route activity handler")
    operation = state.get("operation")
    
    if operation == "list-activities":
        # Extract filters from the user's prompt
        prompt = state.get("prompt", "")
        filters = await extract_list_filters(prompt)
        logger.debug(f"Extracted filters: {filters}")
        
        # Combine the filters with the existing payload
        payload = {**state.get("details", {}), **filters}
        logger.debug(f"Combined payload: {payload}")
        
        # Create new state with the extracted filters
        filtered_state = {
            "operation": operation,
            "payload": payload
        }
        
        result = await activity_crud(filtered_state, config)
        return result.get("result", {})
    elif operation == "unknown":
        result = {"error": "Could not determine intent, please rephrase."}
        return result
    else:
        # For other operations (edit, delete), use the original state
        result = await activity_crud(state, config)
        return result.get("result", {})

async def extract_list_filters(prompt: str) -> dict:
    """Extract activity listing filters from user prompt"""
    extraction_prompt = f"""
    Extract activity listing filters from this user request. Return JSON with these fields:
    - activity_name: The activity name/title to filter (or null)
    - category_name: The subject/category to filter (or null)
    - subcategory_name: The specific topic/subcategory to filter (or null)

    User request: "{prompt}"

    Examples:
    - "Show me all activities" → {{"activity_name": null, "category_name": null, "subcategory_name": null}}
    - "List math quizzes for trigonometry" → {{"activity_name": "quiz", "category_name": "math", "subcategory_name": "trigonometry"}}
    - "Get activities for algebra" → {{"activity_name": null, "category_name": null, "subcategory_name": "algebra"}}
    - "Show all physics activities" → {{"activity_name": null, "category_name": "physics", "subcategory_name": null}}
    - "List all activities" → {{"activity_name": null, "category_name": null, "subcategory_name": null}}
    """
    
    try:
        result = await chat_completion({"prompt": extraction_prompt}, {}, json_mode=True)
        return result.get("response", {})
    except Exception as e:
        logger.warning(f"Failed to extract list filters: {e}")
        return {}

async def generate_activity_handler(state: dict, config: dict) -> dict:
    logger.debug("Generate activity handler")
    result = {
        "message": "Activity generation feature is coming soon!",
        "activity_id": ""
    }
    return result

async def evaluate_performance_handler(state: dict, config: dict) -> dict:
    logger.debug("Evaluate performance handler")
    
    try:
        # Get user information
        details = state.get("details", {})
        user_id = details.get("user_id")
        if not user_id:
            user_id = state.get("user_id")
        
        if not user_id:
            from app.models.user import User
            db_session = state.get("db")
            if db_session:
                first_user = db_session.query(User).order_by(User.created_at).first()
                if first_user:
                    user_id = str(first_user.id)
                else:
                    return {
                        "message": "❌ No user found. Please log in to evaluate performance.",
                        "activity_id": ""
                    }
            else:
                return {
                    "message": "❌ Database session not available for evaluation.",
                    "activity_id": ""
                }
        
        db = state.get("db")
        if not db:
            return {
                "message": "❌ Database session required for evaluation.",
                "activity_id": ""
            }
        
        prompt = state.get("prompt", "")
        
        # Extract activity information from the prompt
        extraction_prompt = f"""
        Extract evaluation details from this user request. Return JSON with:
        - activity_id: Specific activity ID if mentioned
        - activity_name: Activity name if mentioned
        - evaluation_type: Type of evaluation (quiz, progress, comprehensive, etc.)
        - specific_focus: What specific aspect to evaluate (if mentioned)
        
        User request: "{prompt}"
        
        Examples:
        - "evaluate my quiz" → {{"activity_id": "", "activity_name": "", "evaluation_type": "quiz", "specific_focus": "quiz performance"}}
        - "how am I doing in machine learning" → {{"activity_id": "", "activity_name": "machine learning", "evaluation_type": "comprehensive", "specific_focus": "overall progress"}}
        - "evaluate my progress" → {{"activity_id": "", "activity_name": "", "evaluation_type": "progress", "specific_focus": "learning progress"}}
        """
        
        extraction_result = await chat_completion({"prompt": extraction_prompt}, {}, json_mode=True)
        extracted_data = extraction_result.get("response", {})
        
        # Get current activity if not specified
        activity_id = extracted_data.get("activity_id", "")
        if not activity_id:
            # Try to find the most recent activity for the user
            from app.models.activity_session import ActivitySession
            recent_session = db.query(ActivitySession).filter(
                ActivitySession.user_id == user_id
            ).order_by(ActivitySession.created_at.desc()).first()
            
            if recent_session:
                activity_id = str(recent_session.activity_id)
            else:
                # If no recent activity, create a comprehensive evaluation
                activity_id = "comprehensive"
        
        # Create evaluation agent
        from app.agent.evaluation_agent import EvaluationAgent
        evaluation_agent = EvaluationAgent(db)
        
        # Convert to UUID if it's a valid UUID
        try:
            activity_uuid = UUID(activity_id) if activity_id != "comprehensive" else None
        except ValueError:
            activity_uuid = None
        
        # Run evaluation
        evaluation_result = await evaluation_agent.evaluate(
            user_id=UUID(user_id),
            activity_id=activity_uuid if activity_uuid else UUID("00000000-0000-0000-0000-000000000000"),
            chat_context=prompt,
            triggered_by="chat"
        )
        
        # Format the response for chat
        overall_score = evaluation_result.get("overall_score", 0)
        evaluation_type = evaluation_result.get("evaluation_type", "comprehensive")
        summary = evaluation_result.get("summary", "Evaluation completed successfully.")
        
        # Create a user-friendly message
        if overall_score > 0:
            score_message = f"🎯 **Overall Score: {overall_score:.1f}%**\n\n"
        else:
            score_message = ""
        
        # Get key insights
        strengths = evaluation_result.get("strengths", [])
        recommendations = evaluation_result.get("recommendations", [])
        
        strengths_text = ""
        if strengths:
            strengths_text = "✅ **Your Strengths:**\n" + "\n".join([f"• {strength}" for strength in strengths[:3]]) + "\n\n"
        
        recommendations_text = ""
        if recommendations:
            recommendations_text = "💡 **Recommendations:**\n" + "\n".join([f"• {rec}" for rec in recommendations[:3]]) + "\n\n"
        
        # Combine the message
        full_message = f"{score_message}{summary}\n\n{strengths_text}{recommendations_text}"
        
        # Add follow-up options
        full_message += "🔍 **What would you like to explore further?**\n"
        full_message += "• Detailed quiz analysis\n"
        full_message += "• Learning progress trends\n"
        full_message += "• Specific topic performance\n"
        full_message += "• Personalized study recommendations"
        
        result = {
            "message": full_message,
            "activity_id": activity_id,
            "evaluation_data": {
                "overall_score": overall_score,
                "evaluation_type": evaluation_type,
                "strengths": strengths,
                "recommendations": recommendations,
                "detailed_results": evaluation_result.get("detailed_results", {})
            }
        }
        
        logger.info(f"Evaluation completed for user {user_id} with score {overall_score}")
        return result
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        return {
            "message": f"❌ Evaluation failed: {str(e)}",
            "activity_id": "",
            "error": str(e)
        }

async def create_activity_handler(state: dict, config: dict) -> dict:
    logger.debug("Create activity handler")
    
    try:
        prompt = state.get("prompt", "")
        
        # Extract activity details using AI
        extraction_prompt = f"""
        Extract activity creation details from this user request. Return JSON with:
        - name: Activity name
        - description: Brief description
        - category_name: Subject/category (e.g., math, science, history)
        - subcategory_name: Specific topic (e.g., algebra, physics, world war)
        - difficulty_level: Beginner, Intermediate, or Advanced
        - final_description: Detailed activity description
        
        User request: "{prompt}"
        """
        
        extraction_result = await chat_completion({"prompt": extraction_prompt}, {}, json_mode=True)
        extracted_data = extraction_result.get("response", {})
        
        # Get user information
        details = state.get("details", {})
        user_id = details.get("user_id")
        if not user_id:
            user_id = state.get("user_id")
        if not user_id:
            from app.models.user import User
            db_session = state.get("db")
            if db_session:
                first_user = db_session.query(User).order_by(User.created_at).first()
                if first_user:
                    user_id = str(first_user.id)
                else:
                    raise ValueError("No users found in the database")
            else:
                raise ValueError("Database session not available")
        
        db = state.get("db")
        if not db:
            raise ValueError("Database session required for activity creation")
        
        # Find or create category
        category_name = extracted_data.get("category_name", "General")
        category = db.query(ActivityCategory).filter(
            ActivityCategory.name.ilike(f"%{category_name}%")
        ).first()
        
        if not category:
            # Try fuzzy matching with variations
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
            category = ActivityCategory(name=category_name, description=f"Activity of {category_name}")
            db.add(category)
            db.flush()
            logger.info(f"Created new category: {category_name} with ID: {category.id}")
            db.commit()
        
        # Find subcategory by name using fuzzy matching
        subcategory_name = extracted_data.get("subcategory_name", "General")
        subcategory = db.query(ActivitySubCategory).filter(
            ActivitySubCategory.name.ilike(f"%{subcategory_name}%"),
            ActivitySubCategory.category_id == category.id
        ).first()
        
        # If no exact match, try fuzzy matching with common variations
        if not subcategory:
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
            subcategory = ActivitySubCategory(
                name=subcategory_name,
                category_id=category.id,
                description=""
            )
            db.add(subcategory)
            db.flush()
            logger.info(f"Created new subcategory: {subcategory_name} with ID: {subcategory.id}")
            db.commit()
        
        # Prepare payload for create_activity tool
        activity_payload = {
            "name": extracted_data.get("name", "New Activity"),
            "description": extracted_data.get("description", ""),
            "category_id": str(category.id),
            "sub_category_id": str(subcategory.id),
            "difficulty_level": extracted_data.get("difficulty_level", "Beginner"),
            "created_by": user_id,
            "access_type": "private",
            "final_description": extracted_data.get("final_description")
        }

        # Add ai_guide if available
        if "ai_guide" in extracted_data:
            activity_payload["ai_guide"] = extracted_data["ai_guide"]
        
        if not activity_payload.get("final_description"):
            # Generate with AI or set a default
            activity_payload["final_description"] = f"This activity covers {activity_payload['name']} in detail."
        
        logger.info(f"Creating activity: {activity_payload['name']}")
        
        # Call the create_activity tool
        tool_result = await create_activity_tool.ainvoke({"payload": activity_payload})
        
        # Format success message
        message = f"✅ Activity created successfully!\n\n**{tool_result['name']}**\n\n**Description:** {tool_result['description']}\n**Category:** {tool_result['category']}\n**Subcategory:** {tool_result['subcategory']}\n**Difficulty:** {tool_result['difficulty_level']}\n**Access Type:** {tool_result['access_type']}\n\nActivity ID: {tool_result['id']}"
        
        result = {
            "message": message,
            "activity_id": tool_result.get('id', '')
        }
        logger.debug("Create activity handler completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Create activity handler failed: {e}")
        error_message = f"❌ Failed to create activity: {str(e)}"
        result = {
            "error": error_message,
            "activity_id": ""
        }
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
workflow.add_node("evaluate_performance_handler", evaluate_performance_handler)

# Transitions
def route_from_classify_intent(state):
    intent = state.get("intent")
    logger.debug(f"Routing intent: {intent}")
    
    if intent == "greetings":
        return "greet_user"
    elif intent == "capabilities":
        return "describe_capabilities"
    elif intent == "start-activity":
        return "start_activity_tool"
    elif intent == "generate-activity":
        return "generate_activity_handler"
    elif intent == "create-activity":
        return "create_activity_handler"
    elif intent in {"edit-activity", "delete-activity", "list-activities"}:
        return "route_activity"
    elif intent == "evaluate-performance":
        return "evaluate_performance_handler"
    else:
        # For unknown intents, route to route_activity which will handle the error
        return "route_activity"

workflow.add_conditional_edges("classify_intent", route_from_classify_intent)

# Finish points
workflow.set_entry_point("classify_intent")
for node in ["greet_user","describe_capabilities","start_activity_tool","route_activity","generate_activity_handler","create_activity_handler","evaluate_performance_handler"]:
    workflow.set_finish_point(node)

# Compile agent
agent = workflow.compile()
logger.info("Agent workflow compiled successfully")

async def run_agent(input_data: dict) -> dict:
    logger.debug("Run agent started")
    
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
    
    logger.debug("Invoking agent workflow...")
    result = await agent.ainvoke(state)
    
    # Handle the new flattened response structure
    # Handlers now return results directly, not wrapped in a "result" object
    if "result" in result:
        # Some handlers might still return the old format, handle both
        reply = result.get("result", {}).get("message", "")
        result_data = result.get("result", {})
    else:
        # New format: handlers return data directly
        reply = result.get("message", "")
        result_data = result
    
    store.add_message(session.session_id, "assistant", reply)
    
    output = {"intent": result.get("intent", "unknown"), "result": result_data, "session_id": session.session_id}
    logger.debug("Run agent completed successfully")
    
    if trace:
        trace.output = output
        trace.end()
    
    return output
