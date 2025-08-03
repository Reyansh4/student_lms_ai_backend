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
    logger.info(f"=== CLASSIFY_INTENT START ===")
    logger.info(f"Input state: {state}")
    
    prompt_text = state.get("prompt", "")
    logger.info(f"Prompt text: {prompt_text}")
    
    try:
        # Use centralized intent classification
        classification_result = await agent_tools.classify_intent(prompt_text)
        logger.info(f"Classification result from agent_tools: {classification_result}")
        
        intent = classification_result.get("intent", "unknown")
        confidence = classification_result.get("confidence", 0.0)
        target_agent = classification_result.get("target_agent", None)
        
        logger.info(f"Final intent: {intent}")
        logger.info(f"Confidence: {confidence}")
        logger.info(f"Target agent: {target_agent}")
        
        # Preserve the original state while adding classification results
        output = {
            **state,  # Keep all original state
            "intent": intent, 
            "confidence": confidence, 
            "target_agent": target_agent
        }
        
        logger.info(f"Final output: {output}")
        logger.info(f"=== CLASSIFY_INTENT SUCCESS ===")
        return output
        
    except Exception as e:
        logger.error(f"=== CLASSIFY_INTENT ERROR ===")
        logger.error(f"Error details: {e}")
        return {
            **state,
            "intent": "unknown",
            "confidence": 0.0,
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
    """Handle general learning support requests with comprehensive activity management"""
    logger.info(f"=== LEARNING_SUPPORT_HANDLER START ===")
    logger.info(f"Input state: {state}")
    
    prompt = state.get("prompt", "")
    intent = state.get("intent", "")
    
    logger.info(f"Learning support handler received intent: '{intent}'")
    logger.info(f"Learning support handler received prompt: '{prompt}'")
    
    try:
        # Check if this is an activity-related request
        activity_keywords = ["list activities", "show activities", "find activities", "create activity", "new activity", "start activity", "edit activity", "delete activity", "activity"]
        is_activity_request = any(keyword in prompt.lower() for keyword in activity_keywords) or intent in ["list-activities", "create-activity", "edit-activity", "delete-activity", "start-activity"]
        
        logger.info(f"Is activity request: {is_activity_request}")
        
        if is_activity_request:
            # Step 1: Use LLM to extract detailed information from the prompt
            extraction_prompt = f"""
            Analyze this user prompt: "{prompt}"
            
            Extract the following information and return a JSON object:
            - intent: The specific action (list, create, edit, delete, start, search, filter)
            - category: The main subject category (extract the exact category name mentioned)
            - subcategory: The broader topic within the category (extract the exact subcategory name mentioned)
            - activity_name: The specific activity name if mentioned
            - difficulty_level: Any difficulty level mentioned (beginner, intermediate, advanced)
            - filters: Any additional filters mentioned (by user, by date, by popularity, etc.)
            - description: Any description or requirements mentioned
            
            **Guidelines:**
            - Extract the exact category and subcategory names as mentioned in the prompt
            - Categories are main subjects like Mathematics, Physics, Biology, Chemistry, History, etc.
            - Subcategories are broader topics within each category like Trigonometry, Calculus, Refractive Index, Cell Biology, etc.
            - If no specific subcategory is mentioned, set subcategory to null
            - Preserve the exact spelling and case as mentioned in the prompt
            
            **Examples:**
            - "List all activities of Maths" → {{"intent": "list", "category": "Mathematics", "subcategory": null, "activity_name": null, "difficulty_level": null, "filters": null, "description": null}}
            - "Create a calculus quiz for beginners" → {{"intent": "create", "category": "Mathematics", "subcategory": "Calculus", "activity_name": "calculus quiz", "difficulty_level": "beginner", "filters": null, "description": "quiz for beginners"}}
            - "Start the algebra practice" → {{"intent": "start", "category": "Mathematics", "subcategory": "Algebra", "activity_name": "algebra practice", "difficulty_level": null, "filters": null, "description": null}}
            - "Show me all physics activities about refractive index" → {{"intent": "list", "category": "Physics", "subcategory": "Refractive Index", "activity_name": null, "difficulty_level": null, "filters": null, "description": null}}
            - "Find biology activities in genetics for advanced students" → {{"intent": "list", "category": "Biology", "subcategory": "Genetics", "activity_name": null, "difficulty_level": "advanced", "filters": null, "description": null}}
            - "Create a trigonometry exercise" → {{"intent": "create", "category": "Mathematics", "subcategory": "Trigonometry", "activity_name": "trigonometry exercise", "difficulty_level": null, "filters": null, "description": null}}
            - "List chemistry activities" → {{"intent": "list", "category": "Chemistry", "subcategory": null, "activity_name": null, "difficulty_level": null, "filters": null, "description": null}}
            - "Start the history lesson" → {{"intent": "start", "category": "History", "subcategory": null, "activity_name": "history lesson", "difficulty_level": null, "filters": null, "description": null}}
            
            Return only the JSON object:
            """
            
            # Call LLM to extract information
            from app.config.agent_config import get_chat_completion_config
            config_settings = get_chat_completion_config()
            extraction_result = await agent_tools._chat_completion(
                prompt=extraction_prompt,
                temperature=0.1,
                max_tokens=300,
                json_mode=True
            )
            
            logger.info(f"LLM extraction result: {extraction_result}")
            
            # Parse the extracted information
            extracted_info = {}
            if "response" in extraction_result and "text" in extraction_result["response"]:
                try:
                    extracted_info = json.loads(extraction_result["response"]["text"])
                except json.JSONDecodeError:
                    logger.error("Failed to parse LLM extraction result as JSON")
                    extracted_info = {}
            elif "response" in extraction_result:
                # Handle case where response is already a dict
                extracted_info = extraction_result["response"]
            
            logger.info(f"Parsed extraction info: {extracted_info}")
            
            # Step 2: Fetch all relevant activity data
            action_intent = extracted_info.get("intent", "unknown")
            category = extracted_info.get("category")
            subcategory = extracted_info.get("subcategory")
            activity_name = extracted_info.get("activity_name")
            difficulty_level = extracted_info.get("difficulty_level")
            filters = extracted_info.get("filters")
            description = extracted_info.get("description")
            
            # Fetch categories and subcategories for reference
            categories_data = await fetch_categories_data(state)
            activities_data = await fetch_activities_data(state, category, difficulty_level)
            
            logger.info(f"Fetched categories: {len(categories_data) if categories_data else 0}")
            logger.info(f"Fetched activities: {len(activities_data) if activities_data else 0}")
            
            # Step 3: Perform action based on extracted intent
            if action_intent == "list" or action_intent == "list-activities" or action_intent == "search":
                message = await handle_list_activities(activities_data, category, subcategory, difficulty_level, filters)
                
            elif action_intent == "create":
                message = await handle_create_activity(extracted_info, categories_data, state)
                
            elif action_intent == "start":
                message = await handle_start_activity(activity_name, category, subcategory, state)
                
            elif action_intent == "edit":
                message = await handle_edit_activity(activity_name, category, subcategory, state)
                
            elif action_intent == "delete":
                message = await handle_delete_activity(activity_name, category, subcategory, state)
                
            else:
                # Default: Provide comprehensive guidance
                message = await provide_activity_guidance(categories_data, activities_data)
                
        else:
            # Use multi-agent system for general learning support
            from app.agents.multi_agent_system import multi_agent_system
            result = await multi_agent_system.process_learning_request(prompt)
            message = result.get("combined_response", get_response_template("error"))
        
        logger.info(f"Learning support result: {message}")
        logger.info(f"=== LEARNING_SUPPORT_HANDLER SUCCESS ===")
        
        # Return both the result and preserve the intent from the state
        return {
            "result": {"message": message, "session_type": "learning_support"},
            "intent": intent  # Preserve the intent from the state
        }
        
    except Exception as e:
        logger.error(f"=== LEARNING_SUPPORT_HANDLER ERROR ===")
        logger.error(f"Error details: {e}")
        return {"result": {"error": f"Learning support failed: {str(e)}"}}

async def fetch_categories_data(state: dict) -> list:
    """Fetch all categories and subcategories"""
    try:
        url = f"http://localhost:8000{settings.API_PREFIX}/activities/categories"
        headers = {}
        token = state.get("details", {}).get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return []

async def fetch_activities_data(state: dict, category: str = None, difficulty_level: str = None) -> list:
    """Fetch activities with optional filtering"""
    try:
        url = f"http://localhost:8000{settings.API_PREFIX}/activities/"
        params = {}
        if category:
            params["category"] = category
        if difficulty_level:
            params["difficulty"] = difficulty_level
        
        headers = {}
        token = state.get("details", {}).get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Handle paginated response
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            elif isinstance(data, list):
                return data
            else:
                return []
    except Exception as e:
        logger.error(f"Error fetching activities: {e}")
        return []

async def handle_list_activities(activities_data: list, category: str, subcategory: str, difficulty_level: str, filters: str) -> str:
    """Handle listing activities with filtering"""
    if not activities_data:
        category_text = f" for {category}" if category else ""
        difficulty_text = f" with {difficulty_level} difficulty" if difficulty_level else ""
        return f"No activities found{category_text}{difficulty_text}."
    
    # Filter activities based on category and subcategory
    filtered_activities = activities_data
    
    # Filter by category (case-insensitive)
    if category:
        filtered_activities = [
            activity for activity in filtered_activities 
            if activity.get("category") and category.lower() in activity["category"].get("name", "").lower()
        ]
    
    # Filter by subcategory (case-insensitive)
    if subcategory and filtered_activities:
        filtered_activities = [
            activity for activity in filtered_activities 
            if activity.get("sub_category") and subcategory.lower() in activity["sub_category"].get("name", "").lower()
        ]
    
    # Filter by difficulty level
    if difficulty_level and filtered_activities:
        filtered_activities = [
            activity for activity in filtered_activities 
            if activity.get("difficulty_level") and difficulty_level.lower() in activity["difficulty_level"].lower()
        ]
    
    if not filtered_activities:
        category_text = f" for {category}" if category else ""
        subcategory_text = f" - {subcategory}" if subcategory else ""
        difficulty_text = f" with {difficulty_level} difficulty" if difficulty_level else ""
        return f"No activities found{category_text}{subcategory_text}{difficulty_text}."
    
    # Format the response with just activity names
    activities_list = []
    for activity in filtered_activities:
        name = activity.get("name", "Unknown")
        activities_list.append(f"• {name}")
    
    # Create summary text
    category_text = f" for {category}" if category else ""
    subcategory_text = f" - {subcategory}" if subcategory else ""
    difficulty_text = f" ({difficulty_level} level)" if difficulty_level else ""
    
    summary = f"Here are the activities{category_text}{subcategory_text}{difficulty_text}:\n\n"
    summary += "\n".join(activities_list)
    
    return summary

async def handle_create_activity(extracted_info: dict, categories_data: list, state: dict) -> str:
    """Handle activity creation with guidance"""
    activity_name = extracted_info.get("activity_name", "Your Activity")
    category = extracted_info.get("category")
    subcategory = extracted_info.get("subcategory")
    difficulty_level = extracted_info.get("difficulty_level", "Intermediate")
    description = extracted_info.get("description", "Activity description")
    
    # Find matching category ID
    category_id = "uuid"  # Default
    if category and categories_data:
        for cat in categories_data:
            if cat.get("name", "").lower() == category.lower():
                category_id = str(cat.get("id"))
                break
    
    return f"""To create the activity "{activity_name}", use this API endpoint:

```POST /api/v1/activities
{{
  "name": "{activity_name}",
  "description": "{description}",
  "category_id": "{category_id}",
  "difficulty_level": "{difficulty_level}",
  "access_type": "public"
}}
```

**Extracted Details:**
- Name: {activity_name}
- Category: {category or "Not specified"}
- Subcategory: {subcategory or "Not specified"}
- Difficulty: {difficulty_level}
- Description: {description}

You can also create activities using templates or generate them with AI assistance."""

async def handle_start_activity(activity_name: str, category: str, subcategory: str, state: dict) -> str:
    """Handle starting an activity"""
    if not activity_name:
        return "Please specify an activity name to start."
    
    try:
        url = f"http://localhost:8000{settings.API_PREFIX}/agent/start-activity"
        payload = {
            "activity_name": activity_name,
            "category_name": category or "General"
        }
        
        headers = {}
        token = state.get("details", {}).get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            result_data = response.json()
            
            if result_data.get("status") == "started":
                return f"✅ Activity '{activity_name}' started successfully!"
            else:
                return f"Activity '{activity_name}' initiated. Check the response for details."
                
    except Exception as e:
        logger.error(f"Error starting activity: {e}")
        return f"Sorry, I couldn't start the activity '{activity_name}'. Error: {str(e)}"

async def handle_edit_activity(activity_name: str, category: str, subcategory: str, state: dict) -> str:
    """Handle editing an activity"""
    if not activity_name:
        return "Please specify an activity name to edit."
    
    return f"""To edit the activity "{activity_name}", you'll need to:

1. First find the activity ID using: `GET /api/v1/activities/`
2. Then update using: `PUT /api/v1/activities/{{activity_id}}`

**Activity Details:**
- Name: {activity_name}
- Category: {category or "Not specified"}
- Subcategory: {subcategory or "Not specified"}

Would you like me to help you find the activity ID first?"""

async def handle_delete_activity(activity_name: str, category: str, subcategory: str, state: dict) -> str:
    """Handle deleting an activity"""
    if not activity_name:
        return "Please specify an activity name to delete."
    
    return f"""To delete the activity "{activity_name}", you'll need to:

1. First find the activity ID using: `GET /api/v1/activities/`
2. Then delete using: `DELETE /api/v1/activities/{{activity_id}}`

**Activity Details:**
- Name: {activity_name}
- Category: {category or "Not specified"}
- Subcategory: {subcategory or "Not specified"}

⚠️ **Warning:** This action cannot be undone. Are you sure you want to delete this activity?"""

async def provide_activity_guidance(categories_data: list, activities_data: list) -> str:
    """Provide comprehensive activity management guidance"""
    categories_text = ""
    if categories_data:
        categories_list = [cat.get("name", "Unknown") for cat in categories_data]
        categories_text = f"\n\n**Available Categories:** {', '.join(categories_list)}"
    
    activities_count = len(activities_data) if activities_data else 0
    
    return f"""I can help you with comprehensive activity management!

**Current Status:**
- Total Activities: {activities_count}
- Available Categories: {len(categories_data) if categories_data else 0}{categories_text}

**Available Actions:**
1. **List Activities:** "Show me all math activities" or "List activities for beginners"
2. **Create Activity:** "Create a calculus quiz" or "Make a new science experiment"
3. **Start Activity:** "Start the algebra practice" or "Begin the physics lab"
4. **Edit Activity:** "Edit the calculus quiz" or "Update the science experiment"
5. **Delete Activity:** "Delete the old quiz" or "Remove the outdated experiment"

**Examples:**
- "List all activities of Maths"
- "Create a calculus quiz for beginners"
- "Start the algebra practice"
- "Show me all science activities for advanced students"
- "Find activities in the physics category"

What would you like to do with activities?"""
# Build workflow
workflow.add_node("classify_intent", classify_intent)
workflow.add_node("greet_user", greet_user)
workflow.add_node("describe_capabilities", describe_capabilities)
workflow.add_node("start_activity_tool", start_activity_tool)
workflow.add_node("generate_activity_handler", generate_activity_handler)
workflow.add_node("collaborative_learning_handler", collaborative_learning_handler)
workflow.add_node("single_agent_consultation_handler", single_agent_consultation_handler)
workflow.add_node("learning_support_handler", learning_support_handler)

# Routing function
def route_from_classify_intent(state):
    logger.info(f"=== ROUTE_FROM_CLASSIFY_INTENT START ===")
    logger.info(f"Input state: {state}")
    
    intent = state.get("intent")
    logger.info(f"Intent received: '{intent}'")
    
    routing_map = {
        "greetings": "greet_user",
        "capabilities": "describe_capabilities",
        "start-activity": "start_activity_tool",
        "generate-activity": "generate_activity_handler",
        "collaborative-learning": "collaborative_learning_handler",
        "single-agent-consultation": "single_agent_consultation_handler",
        "learning-support": "learning_support_handler",
        "list-activities": "learning_support_handler",  # Route list-activities to learning support
        "create-activity": "learning_support_handler",  # Route create-activity to learning support
        "edit-activity": "learning_support_handler",    # Route edit-activity to learning support
        "delete-activity": "learning_support_handler"   # Route delete-activity to learning support
    }
    
    # Handle AI learning intents only
    route = routing_map.get(intent, "learning_support_handler")
    logger.info(f"Routing intent '{intent}' to: {route}")
    return route

workflow.add_conditional_edges("classify_intent", route_from_classify_intent)

# Finish points
workflow.set_entry_point("classify_intent")
finish_nodes = [
    "greet_user", "describe_capabilities", "start_activity_tool", "generate_activity_handler",
    "collaborative_learning_handler", 
    "single_agent_consultation_handler", "learning_support_handler"
]
for node in finish_nodes:
    workflow.set_finish_point(node)

# Compile agent
agent = workflow.compile()
logger.info("Chat agent workflow compiled successfully")

async def run_agent(input_data: dict) -> dict:
    """Run the chat agent with input data"""
    print(f"=== RUN_AGENT START ===")
    print(f"Input data: {input_data}")
    
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
    print(f"Initial state: {state}")
    
    print(f"Invoking agent workflow...")
    result = await agent.ainvoke(state)
    print(f"Agent workflow result: {result}")
    
    reply = result.get("result", {}).get("message", "")
    enhanced_memory_store.add_message(session.session_id, "assistant", reply)
    
    # Extract intent from the workflow result - it should be preserved from classify_intent
    intent = result.get("intent", "unknown")
    print(f"Extracted intent from workflow result: {intent}")
    
    output = {
        "intent": intent,
        "result": result.get("result", {}),
        "session_id": session.session_id
    }
    print(f"Final output: {output}")
    
    print(f"=== RUN_AGENT SUCCESS ===")
    return output 

