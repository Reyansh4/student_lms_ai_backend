"""
Restructured chat agent using centralized tools and configuration
"""

import json
import httpx
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional
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
from app.config.azure_config import get_azure_openai_client
from app.config.langfuse_config import (
    TraceTracker, track_function_call, track_llm_generation, 
    traced_operation, langfuse_manager
)
from app.agents.multi_agent_system import MultiAgentSystem
from app.memory.enhanced_store import EnhancedMemoryStore
from app.prompts.agent_prompts import (
    INTENT_CLASSIFICATION_PROMPT,
    LEARNING_SUPPORT_PROMPT,
    ACTIVITY_CREATION_PROMPT,
    ACTIVITY_START_PROMPT
)

logger = get_logger(__name__)

# Initialize LangGraph workflow
workflow = StateGraph(dict)

async def classify_intent(state: dict, config: dict) -> dict:
    """Classify the user's intent using the agent tools"""
    logger.info(f"=== CLASSIFY_INTENT START ===")
    logger.info(f"Input state: {state}")
    
    prompt = state.get("prompt", "")
    messages = state.get("messages", [])
    details = state.get("details", {})
    
    logger.info(f"Classify intent received prompt: '{prompt}'")
    logger.info(f"Classify intent received {len(messages)} messages")
    logger.info(f"Classify intent received details: {details}")
    
    # Build the classification prompt with conversation context
    classification_prompt = f"""Classify the user's intent into one of these categories:

**Activity Management:**
- list-activities: User wants to see/list available activities (e.g., "list activities", "show activities", "find activities")
- create-activity: User wants to create a new activity in the database (e.g., "create a quiz", "make an activity", "new activity")
- edit-activity: User wants to modify an existing activity
- delete-activity: User wants to remove an activity
- start-activity: User wants to begin/start an activity like generate quiz questions, create quiz content, etc.

**AI Learning:**
- collaborative-learning: User wants comprehensive learning support with multiple specialized agents
- single-agent-consultation: User wants to consult a specific specialized agent (tutor, subject_expert, exercise_designer, evaluator, learning_coach, visual_learning_specialist)
- learning-support: General learning questions, study help, concept explanations

**General:**
- greetings: User is greeting the agent
- capabilities: User asks what you can do

**Important Guidelines:**
- If the user says "create", "make", or "new" followed by "quiz", "activity", "lesson", etc., classify as "create-activity"
- If the user says "generate" followed by content words, classify as "generate-activity"
- If the user mentions "list", "show", "find", "get", or "display" followed by "activities" or "activity", classify as "list-activities"
- "Create a Chemistry quiz" = create-activity (creates database entry)
- "Generate quiz questions" = generate-activity (generates content)
- "Start English activity" = start-activity (starts existing activity and generates content)

**Conversation Context:**
"""
    
    if messages:
        classification_prompt += "Recent conversation:\n"
        for msg in messages[-3:]:  # Last 3 messages for context
            role = "User" if msg["role"] == "user" else "AI"
            classification_prompt += f"{role}: {msg['content']}\n"
    
    classification_prompt += f"\n**Current User Input:** {prompt}\n\n"
    classification_prompt += "Return JSON with 'intent', 'confidence', and optionally 'target_agent' for single-agent-consultation."
    
    logger.info(f"Complete classification prompt template: {classification_prompt}")
    
    try:
        # Call the agent tools for classification
        result = await agent_tools.classify_intent(prompt)
        logger.info(f"Classification result from agent_tools: {result}")
        
        # Extract the final intent
        final_intent = result.get("intent", "unknown")
        confidence = result.get("confidence", 0.0)
        target_agent = result.get("target_agent")
        
        logger.info(f"Final intent: {final_intent}")
        logger.info(f"Confidence: {confidence}")
        logger.info(f"Target agent: {target_agent}")
        
        # Build the output
        output = {
            "prompt": prompt,
            "details": details,
            "db": state.get("db"),
            "messages": messages,
            "intent": final_intent,
            "confidence": confidence,
            "target_agent": target_agent
        }
        
        logger.info(f"Final output: {output}")
        logger.info(f"=== CLASSIFY_INTENT SUCCESS ===")
        return output
        
    except Exception as e:
        logger.error(f"=== CLASSIFY_INTENT ERROR ===")
        logger.error(f"Error in classify_intent: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return default output on error
        return {
            "prompt": prompt,
            "details": details,
            "db": state.get("db"),
            "messages": messages,
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
    """Handle starting activities and generating content"""
    logger.info(f"=== START_ACTIVITY_TOOL START ===")
    logger.info(f"Input state: {state}")
    
    prompt = state.get("prompt", "")
    details = state.get("details", {})
    conversation_history = details.get("conversation_history", [])
    
    logger.info(f"Start activity tool received prompt: '{prompt}'")
    logger.info(f"Start activity tool received details: {details}")
    logger.info(f"Start activity tool received {len(conversation_history)} conversation history items")
    
    try:
        # Extract activity information from the prompt
        activity_info = await extract_activity_info(prompt, conversation_history)
        logger.info(f"Extracted activity info: {activity_info}")
        
        # Check if activity exists
        activity = await find_activity(activity_info, state)
        if activity:
            logger.info(f"Found existing activity: {activity}")
            
            # Generate activity content (MCQs, questions, etc.)
            logger.info("Generating activity content...")
            activity_content = await generate_activity_content(activity, state)
            logger.info(f"Generated activity content: {activity_content}")
            
            return {
                "result": {
                    "message": f"🎯 **{activity.name} Activity Started!**\n\n{activity_content}",
                    "activity_id": activity.id,
                    "content_type": "mcq_quiz"
                }
            }
        else:
            logger.warning(f"No activity found for: {activity_info}")
            return {
                "result": {
                    "message": f"❌ Activity not found. Please check the activity name and try again.",
                    "error": "Activity not found"
                }
            }
            
    except Exception as e:
        logger.error(f"=== START_ACTIVITY_TOOL ERROR ===")
        logger.error(f"Error details: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"result": {"error": f"Failed to start activity: {str(e)}"}}
    
    logger.info(f"=== START_ACTIVITY_TOOL SUCCESS ===")

async def extract_activity_info(prompt: str, conversation_history: list) -> dict:
    """Extract activity information from prompt and conversation history"""
    logger.info(f"=== EXTRACT_ACTIVITY_INFO START ===")
    logger.info(f"Extracting from prompt: '{prompt}'")
    logger.info(f"Conversation history: {conversation_history}")
    
    # Build context from conversation history
    context_prompt = "Based on the conversation history and current request, extract activity information:\n\n"
    if conversation_history:
        context_prompt += "Conversation History:\n"
        for msg in conversation_history[-5:]:  # Last 5 messages
            role = "User" if msg['role'] == 'user' else "AI"
            context_prompt += f"{role}: {msg['content']}\n"
    
    context_prompt += f"\nCurrent Request: {prompt}\n\n"
    context_prompt += """Extract and return JSON with:
    - activity_name: The specific activity name mentioned
    - category: The subject category (e.g., English, Math, Science)
    - subcategory: The specific topic if mentioned
    - action: What user wants to do (start, generate, show MCQs, etc.)
    - content_type: What content to generate (mcq_quiz, questions, exercises, etc.)
    
    Examples:
    - "Start English Grammar Fundamentals" → {"activity_name": "English Grammar Fundamentals", "category": "English", "subcategory": "Grammar", "action": "start", "content_type": "mcq_quiz"}
    - "Show me MCQs for English Grammar" → {"activity_name": "English Grammar", "category": "English", "subcategory": "Grammar", "action": "show", "content_type": "mcq_quiz"}
    
    Return only valid JSON:"""
    
    logger.info(f"Context prompt for extraction: {context_prompt}")
    
    try:
        from app.config.agent_config import get_chat_completion_config
        config_settings = get_chat_completion_config()
        
        logger.info(f"Calling Azure API for activity extraction with config: {config_settings}")
        
        extraction_result = await agent_tools._chat_completion(
            prompt=context_prompt,
            temperature=0.1,
            max_tokens=300,
            json_mode=True
        )
        
        logger.info(f"Azure API extraction result: {extraction_result}")
        
        # Parse the extracted information
        extracted_info = {}
        if "response" in extraction_result and "text" in extraction_result["response"]:
            try:
                extracted_info = json.loads(extraction_result["response"]["text"])
                logger.info(f"Successfully parsed JSON: {extracted_info}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM extraction result as JSON: {e}")
                logger.error(f"Raw response text: {extraction_result['response']['text']}")
                extracted_info = {}
        elif "response" in extraction_result:
            extracted_info = extraction_result["response"]
            logger.info(f"Using direct response: {extracted_info}")
        
        logger.info(f"Final extracted activity info: {extracted_info}")
        logger.info(f"=== EXTRACT_ACTIVITY_INFO SUCCESS ===")
        return extracted_info
        
    except Exception as e:
        logger.error(f"=== EXTRACT_ACTIVITY_INFO ERROR ===")
        logger.error(f"Error in activity extraction: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {}

async def find_activity(activity_info: dict, state: dict) -> dict:
    """Find the activity in the database"""
    logger.info(f"=== FIND_ACTIVITY START ===")
    logger.info(f"Looking for activity with info: {activity_info}")
    
    try:
        db = state.get("db")
        if not db:
            logger.error("No database session available")
            return None
        
        # Query for the activity
        from app.models.activity import Activity
        from app.models.activity_category import ActivityCategory
        from app.models.activity_sub_category import ActivitySubCategory
        
        activity_name = activity_info.get("activity_name", "")
        category_name = activity_info.get("category", "")
        subcategory_name = activity_info.get("subcategory", "")
        
        logger.info(f"Searching for activity: name='{activity_name}', category='{category_name}', subcategory='{subcategory_name}'")
        
        # Build query
        query = db.query(Activity).join(ActivityCategory).join(ActivitySubCategory)
        
        if activity_name:
            query = query.filter(Activity.name.ilike(f"%{activity_name}%"))
        if category_name:
            query = query.filter(ActivityCategory.name.ilike(f"%{category_name}%"))
        if subcategory_name:
            query = query.filter(ActivitySubCategory.name.ilike(f"%{subcategory_name}%"))
        
        activity = query.first()
        
        if activity:
            logger.info(f"Found activity: {activity.name} (ID: {activity.id})")
            logger.info(f"Activity details: category={activity.category.name}, subcategory={activity.sub_category.name if activity.sub_category else 'None'}")
        else:
            logger.warning(f"No activity found matching criteria")
            
        logger.info(f"=== FIND_ACTIVITY SUCCESS ===")
        return activity
        
    except Exception as e:
        logger.error(f"=== FIND_ACTIVITY ERROR ===")
        logger.error(f"Error finding activity: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

async def generate_activity_content(activity: dict, state: dict) -> str:
    """Generate MCQ content for the activity"""
    logger.info(f"=== GENERATE_ACTIVITY_CONTENT START ===")
    logger.info(f"Generating content for activity: {activity}")
    
    try:
        # Build generation prompt
        generation_prompt = f"""Generate a comprehensive MCQ quiz for the activity: {activity.name}

Category: {activity.category.name}
Subcategory: {activity.sub_category.name if activity.sub_category else 'General'}

Generate 5 multiple choice questions with:
- Clear, educational questions
- 4 answer options (A, B, C, D)
- Correct answer marked
- Brief explanation for correct answer

Format the response as:
1. Question 1
   A) Option A
   B) Option B  
   C) Option C
   D) Option D
   **Correct Answer: X**
   **Explanation: Brief explanation**

2. Question 2
   ... (continue format)

Make the questions engaging and educational for {activity.difficulty_level if hasattr(activity, 'difficulty_level') else 'intermediate'} level students."""

        logger.info(f"Generation prompt: {generation_prompt}")
        
        # Call Azure API to generate content
        from app.config.agent_config import get_chat_completion_config
        config_settings = get_chat_completion_config()
        
        logger.info(f"Calling Azure API for content generation with config: {config_settings}")
        
        generation_result = await agent_tools._chat_completion(
            prompt=generation_prompt,
            temperature=0.7,
            max_tokens=1000
        )
        
        logger.info(f"Azure API generation result: {generation_result}")
        
        # Extract the generated content
        generated_content = ""
        if "response" in generation_result and "text" in generation_result["response"]:
            generated_content = generation_result["response"]["text"]
        elif "response" in generation_result:
            generated_content = str(generation_result["response"])
        else:
            generated_content = str(generation_result)
        
        logger.info(f"Generated content: {generated_content}")
        logger.info(f"=== GENERATE_ACTIVITY_CONTENT SUCCESS ===")
        return generated_content
        
    except Exception as e:
        logger.error(f"=== GENERATE_ACTIVITY_CONTENT ERROR ===")
        logger.error(f"Error generating content: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return "❌ Failed to generate activity content. Please try again."

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
    messages = state.get("messages", [])
    
    logger.info(f"Learning support handler received intent: '{intent}'")
    logger.info(f"Learning support handler received prompt: '{prompt}'")
    logger.info(f"Learning support handler received {len(messages)} conversation messages")
    
    try:
        # Check if this is an activity-related request
        activity_keywords = ["list activities", "show activities", "find activities", "create activity", "new activity", "start activity", "edit activity", "delete activity", "activity", "create", "make", "generate"]
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
            - activity_name: The specific activity name if mentioned or the topic of the activity if not mentioned
            - difficulty_level: Any difficulty level mentioned (beginner, intermediate, advanced) - if not mentioned, use "Intermediate"
            - filters: Any additional filters mentioned (by user, by date, by popularity, etc.)
            - description: Any description or requirements mentioned
            - final_description: Any final description or requirements mentioned or conclusion of what the user wants to do from the prompt or any other information that is important for the activity
            
            **Guidelines:**
            - Extract the exact category and subcategory names as mentioned in the prompt
            - Categories are main subjects like Mathematics, Physics, Biology, Chemistry, History, etc.
            - Subcategories are broader topics within each category like Trigonometry, Calculus, Refractive Index, Cell Biology, etc.
            - If no specific subcategory is mentioned, set subcategory to null
            - Preserve the exact spelling and case as mentioned in the prompt
            - For "create" intents: Use "create-activity" as the intent when user wants to make a new activity
            - For "start" intents: Use "start-activity" as the intent when user wants to begin an existing activity
            - For "list" intents: Use "list-activities" as the intent when user wants to see activities
            - For difficulty_level: Use "Intermediate" as default if not specified
            
            **Examples:**
            - "List all activities of Maths" → {{"intent": "list-activities", "category": "Mathematics", "subcategory": null, "activity_name": null, "difficulty_level": "Intermediate", "filters": null, "description": null}}
            - "Create a calculus quiz for beginners" → {{"intent": "create-activity", "category": "Mathematics", "subcategory": "Calculus", "activity_name": "calculus quiz", "difficulty_level": "beginner", "filters": null, "description": "quiz for beginners"}}
            - "Make a chemistry experiment" → {{"intent": "create-activity", "category": "Chemistry", "subcategory": null, "activity_name": "chemistry experiment", "difficulty_level": "Intermediate", "filters": null, "description": null}}
            - "Generate a physics quiz" → {{"intent": "create-activity", "category": "Physics", "subcategory": null, "activity_name": "physics quiz", "difficulty_level": "Intermediate", "filters": null, "description": null}}
            - "Create a Chemistry quiz on topic Hydrocarbon" → {{"intent": "create-activity", "category": "Chemistry", "subcategory": "Hydrocarbon", "activity_name": "Hydrocarbon quiz", "difficulty_level": "Intermediate", "filters": null, "description": "quiz on Hydrocarbon"}}
            - "Start the algebra practice" → {{"intent": "start-activity", "category": "Mathematics", "subcategory": "Algebra", "activity_name": "algebra practice", "difficulty_level": "Intermediate", "filters": null, "description": null}}
            - "Generate quiz questions for the activity" → {{"intent": "start-activity", "category": "Mathematics", "subcategory": "Algebra", "activity_name": "algebra practice", "difficulty_level": "Intermediate", "filters": null, "description": null}}
            
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
                
            elif action_intent == "create" or action_intent == "create-activity":
                message = await handle_create_activity(extracted_info, categories_data, state)
                
            elif action_intent == "start" or action_intent == "start-activity":
                message = await handle_start_activity(activity_name, category, subcategory, state)
                
            elif action_intent == "edit" or action_intent == "edit-activity":
                message = await handle_edit_activity(activity_name, category, subcategory, state)
                
            elif action_intent == "delete" or action_intent == "delete-activity":
                message = await handle_delete_activity(activity_name, category, subcategory, state)
                
            else:
                # Default: Provide comprehensive guidance
                message = await provide_activity_guidance(categories_data, activities_data)
                
        else:
            # Use multi-agent system for general learning support with conversation context
            from app.agents.multi_agent_system import multi_agent_system
            
            # Build conversation context from previous messages
            conversation_context = ""
            if messages and len(messages) > 1:
                # Get last few messages for context (excluding current one)
                recent_messages = messages[-3:-1]  # Last 2 messages before current
                conversation_context = "Previous conversation context:\n"
                for msg in recent_messages:
                    role = "You" if msg["role"] == "user" else "AI"
                    conversation_context += f"{role}: {msg['content']}\n"
                conversation_context += f"Current request: {prompt}"
                logger.info(f"Built conversation context: {conversation_context}")
            
            # If no context or simple response needed, give direct answer
            if not conversation_context or len(prompt.strip()) < 10:
                # For simple inputs like "A is correct", give direct response
                if prompt.strip().lower() in ["a", "a is correct", "b", "c", "d"]:
                    message = "I see you've selected an answer. To help you better, could you provide more context about what question or topic you're working on?"
                else:
                    message = "I'm here to help! Could you please provide more details about what you'd like to learn or discuss?"
            else:
                # Use multi-agent system with conversation context
                result = await multi_agent_system.process_learning_request(prompt, conversation_context)
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
        logger.info(f"Filtering by category: '{category}'")
        logger.info(f"Available categories in activities: {[activity.get('category', {}).get('name', 'Unknown') for activity in filtered_activities]}")
        
        filtered_activities = [
            activity for activity in filtered_activities 
            if activity.get("category") and (
                category.lower() in activity["category"].get("name", "").lower() or
                activity["category"].get("name", "").lower() in category.lower()
            )
        ]
        
        logger.info(f"After category filtering: {len(filtered_activities)} activities")
        logger.info(f"Matched categories: {[activity.get('category', {}).get('name', 'Unknown') for activity in filtered_activities]}")
    
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
    """Handle activity creation with automatic creation"""
    activity_name = extracted_info.get("activity_name", "Your Activity")
    category = extracted_info.get("category")
    subcategory = extracted_info.get("subcategory")
    difficulty_level = extracted_info.get("difficulty_level", "Intermediate")  # Default to Intermediate
    description = extracted_info.get("description", "Activity description")
    
    # Ensure difficulty_level is not None
    if difficulty_level is None:
        difficulty_level = "Intermediate"
    
    try:
        # Prepare the activity data for creation
        activity_data = {
            "name": activity_name,
            "description": description,
            "category_name": category or "General",
            "subcategory_name": subcategory or "General",
            "difficulty_level": difficulty_level,
            "access_type": "global",
            "ai_guide": True
        }
        
        # Make the API call to create the activity
        url = f"http://localhost:8000{settings.API_PREFIX}/activities/create_enhanced"
        headers = {"Content-Type": "application/json"}
        token = state.get("details", {}).get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=activity_data, headers=headers, timeout=30)
            response.raise_for_status()
            created_activity = response.json()
            
            # Extract details from the created activity
            activity_id = created_activity.get("id")
            final_description = created_activity.get("final_description", "")
            created_category = created_activity.get("category", {}).get("name", "Unknown")
            created_subcategory = created_activity.get("sub_category", {}).get("name", "Unknown")
            
            return f"""✅ **Activity Created Successfully!**

**Activity Details:**
- **Name:** {activity_name}
- **ID:** {activity_id}
- **Category:** {created_category}
- **Subcategory:** {created_subcategory}
- **Difficulty:** {difficulty_level}
- **Description:** {description}

**Auto-Generated Features:**
✅ Category "{created_category}" {'created' if category else 'found'}
✅ Subcategory "{created_subcategory}" {'created' if subcategory else 'found'}
✅ AI-generated final description: {len(final_description)} characters

**Final Description:**
{final_description[:200]}{'...' if len(final_description) > 200 else ''}

Your activity is now ready to use! You can start it by saying "Start the {activity_name}" or "Begin the {activity_name}"."""
            
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP Error {e.response.status_code}: {e.response.text}"
        logger.error(f"Error creating activity: {error_msg}")
        return f"""❌ **Failed to Create Activity**

**Error:** {error_msg}

**Attempted to create:**
- Name: {activity_name}
- Category: {category or 'General'}
- Subcategory: {subcategory or 'General'}
- Difficulty: {difficulty_level}

Please try again or check your permissions."""
        
    except Exception as e:
        logger.error(f"Error creating activity: {e}")
        return f"""❌ **Failed to Create Activity**

**Error:** {str(e)}

**Attempted to create:**
- Name: {activity_name}
- Category: {category or 'General'}
- Subcategory: {subcategory or 'General'}
- Difficulty: {difficulty_level}

Please try again later."""

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
    "greet_user", "describe_capabilities", "start_activity_tool",
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
    print(f"Input data: {input_data}")
    
    user_id = input_data.get("user_id")
    if not user_id:
        raise ValueError("user_id is required for session memory")
    
    # Set database session for enhanced memory store
    db = input_data.get("db")
    if db:
        enhanced_memory_store.set_db_session(db)
    
    # Get or create an enhanced memory session
    session = enhanced_memory_store.get_or_create_session(user_id)
    prompt = input_data.get("prompt", "")
    
    # Record the user turn with conversation management
    enhanced_memory_store.add_message(
        session.session_id, 
        "user", 
        prompt, 
        user_id=user_id,
        intent=input_data.get("intent"),
        topic=input_data.get("topic")
    )
    
    # Use conversation history from frontend if available, otherwise fall back to memory store
    details = input_data.get("details", {})
    conversation_history = details.get("conversation_history", [])
    
    if conversation_history:
        print(f"Using conversation history from frontend: {len(conversation_history)} messages")
        # Convert to the format expected by the agent
        messages = []
        for msg in conversation_history:
            if isinstance(msg, dict):
                # Handle dictionary format
                messages.append({
                    "role": msg.get("role", "user"), 
                    "content": msg.get("content", "")
                })
            elif isinstance(msg, str):
                # Handle string format - treat as user message
                messages.append({
                    "role": "user",
                    "content": msg
                })
            else:
                # Handle other formats
                messages.append({
                    "role": "user",
                    "content": str(msg)
                })
        # Add current user message
        messages.append({"role": "user", "content": prompt})
    else:
        print("No conversation history from frontend, using memory store")
        # Get conversation memory (last 10 messages) from memory store
        history = enhanced_memory_store.get_conversation_memory(session.session_id)
        messages = [{"role": m.role, "content": m.content} for m in history]
    
    print(f"Final messages for agent: {messages}")
    
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
    
    # Record the assistant response with conversation management
    enhanced_memory_store.add_message(
        session.session_id, 
        "assistant", 
        reply, 
        user_id=user_id,
        intent=result.get("intent"),
        topic=input_data.get("topic")
    )
    
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


class ChatAgent:
    """Enhanced chat agent with comprehensive Langfuse tracing"""
    
    def __init__(self):
        self.azure_client = get_azure_openai_client()
        self.multi_agent_system = MultiAgentSystem()
        self.enhanced_memory_store = EnhancedMemoryStore()
        
        # Get LangChain callback handler for LLM operations
        self.langfuse_handler = langfuse_manager.get_langchain_handler()
        
        logger.info("ChatAgent initialized with Langfuse tracing")
    
    def classify_intent(self, prompt: str) -> str:
        """Classify user intent with Langfuse tracing"""
        with traced_operation("Intent Classification") as trace:
            try:
                # Build the full classification prompt
                full_prompt = f"{INTENT_CLASSIFICATION_PROMPT}\n\nUser Input: {prompt}\n\nIntent:"
                
                # Track the classification attempt
                trace.add_span("Intent Classification", 
                             {"prompt": prompt, "full_prompt": full_prompt}, 
                             {"status": "processing"})
                
                # Get Azure OpenAI response
                response = self.azure_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": full_prompt}],
                    max_tokens=50,
                    temperature=0.1,
                    callbacks=[self.langfuse_handler] if self.langfuse_handler else None
                )
                
                intent = response.choices[0].message.content.strip().lower()
                
                # Track the result
                trace.add_span("Intent Result", 
                             {"raw_response": response.choices[0].message.content}, 
                             {"classified_intent": intent})
                
                # Track LLM generation
                track_llm_generation(
                    model="gpt-4",
                    prompt=full_prompt,
                    completion=intent,
                    metadata={
                        "operation": "intent_classification",
                        "tokens_used": response.usage.total_tokens if response.usage else None,
                        "model": "gpt-4"
                    },
                    trace=trace
                )
                
                logger.info(f"Intent classified as: {intent}")
                return intent
                
            except Exception as e:
                error_msg = f"Intent classification failed: {str(e)}"
                logger.error(error_msg)
                trace.finish("error", error_msg)
                return "unknown"
    
    def run_agent(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the main agent with comprehensive tracing"""
        with traced_operation("Chat Agent Run", 
                            user_id=input_data.get('user_id'),
                            session_id=input_data.get('session_id')) as trace:
            
            try:
                prompt = input_data.get('prompt', '')
                details = input_data.get('details', {})
                session_id = details.get('session_id')
                conversation_history = details.get('conversation_history', [])
                
                # Track input data
                trace.add_span("Input Processing", 
                             {"prompt": prompt, "details": details}, 
                             {"status": "received"})
                
                # Get conversation context
                if conversation_history:
                    # Use conversation history from input if available
                    messages = conversation_history
                    logger.info(f"Using conversation history from input: {len(messages)} messages")
                else:
                    # Fallback to memory store
                    messages = self.enhanced_memory_store.get_conversation_memory(session_id)
                    logger.info(f"Using memory store conversation: {len(messages)} messages")
                
                # Clean and format conversation history
                if messages and isinstance(messages, list):
                    clean_messages = []
                    for msg in messages:
                        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                            clean_messages.append(msg)
                        elif isinstance(msg, str):
                            clean_messages.append({
                                "role": "user",
                                "content": msg
                            })
                    messages = clean_messages
                    logger.info(f"Cleaned conversation history: {len(messages)} valid messages")
                else:
                    messages = []
                    logger.info("No valid conversation history available")
                
                # Track conversation context
                trace.add_span("Conversation Context", 
                             {"raw_history": conversation_history}, 
                             {"cleaned_messages": len(messages)})
                
                # Classify intent
                intent = self.classify_intent(prompt)
                
                # Track intent classification
                trace.add_span("Intent Classification Result", 
                             {"prompt": prompt}, 
                             {"intent": intent})
                
                # Route based on intent
                if intent == "learning_support":
                    result = self.learning_support_handler(prompt, messages, trace)
                elif intent == "activity_creation":
                    result = self.activity_creation_handler(prompt, messages, trace)
                elif intent == "activity_start":
                    result = self.activity_start_handler(prompt, messages, trace)
                else:
                    result = self.general_chat_handler(prompt, messages, trace)
                
                # Track final result
                trace.add_span("Agent Response", 
                             {"intent": intent, "prompt": prompt}, 
                             {"result": result})
                
                logger.info(f"Agent completed successfully with intent: {intent}")
                return result
                
            except Exception as e:
                error_msg = f"Agent run failed: {str(e)}"
                logger.error(f"{error_msg}\n{traceback.format_exc()}")
                trace.finish("error", error_msg)
                return {"error": error_msg}
    
    def learning_support_handler(self, prompt: str, messages: List[Dict], trace: TraceTracker) -> Dict[str, Any]:
        """Handle learning support requests with tracing"""
        with traced_operation("Learning Support Handler") as support_trace:
            try:
                # Build conversation context
                conversation_context = []
                for msg in messages[-5:]:  # Last 5 messages for context
                    conversation_context.append(f"{msg['role']}: {msg['content']}")
                
                context_text = "\n".join(conversation_context) if conversation_context else "No previous context"
                
                # Track context building
                support_trace.add_span("Context Building", 
                                     {"messages": messages}, 
                                     {"context_length": len(context_text)})
                
                # Handle simple inputs like "A is correct"
                if len(prompt.strip()) <= 20 and any(word in prompt.lower() for word in ['correct', 'wrong', 'a', 'b', 'c', 'd']):
                    response = f"I see you've selected an answer! That's great progress. {prompt} - Let me know if you'd like to continue with more questions or if you have any other learning needs."
                    
                    support_trace.add_span("Simple Response", 
                                         {"prompt": prompt}, 
                                         {"response": response})
                    
                    return {
                        "intent": "learning_support",
                        "result": {
                            "message": response,
                            "session_id": str(datetime.now().timestamp())
                        }
                    }
                
                # Process with multi-agent system
                result = self.multi_agent_system.process_learning_request(
                    prompt, 
                    conversation_context=context_text
                )
                
                # Track multi-agent processing
                support_trace.add_span("Multi-Agent Processing", 
                                     {"prompt": prompt, "context": context_text}, 
                                     {"result": result})
                
                return {
                    "intent": "learning_support",
                    "result": result
                }
                
            except Exception as e:
                error_msg = f"Learning support handler failed: {str(e)}"
                logger.error(error_msg)
                support_trace.finish("error", error_msg)
                return {"error": error_msg}
    
    def activity_creation_handler(self, prompt: str, messages: List[Dict], trace: TraceTracker) -> Dict[str, Any]:
        """Handle activity creation requests with tracing"""
        with traced_operation("Activity Creation Handler") as creation_trace:
            try:
                # Extract activity information
                activity_info = self.extract_activity_info(prompt)
                
                creation_trace.add_span("Activity Info Extraction", 
                                      {"prompt": prompt}, 
                                      {"activity_info": activity_info})
                
                # Generate activity content
                activity_content = self.generate_activity_content(activity_info, trace)
                
                creation_trace.add_span("Activity Content Generation", 
                                      {"activity_info": activity_info}, 
                                      {"content": activity_content})
                
                return {
                    "intent": "activity_creation",
                    "result": {
                        "message": f"Activity '{activity_info.get('name', 'Unknown')}' created successfully!",
                        "activity": activity_content,
                        "session_id": str(datetime.now().timestamp())
                    }
                }
                
            except Exception as e:
                error_msg = f"Activity creation handler failed: {str(e)}"
                logger.error(error_msg)
                creation_trace.finish("error", error_msg)
                return {"error": error_msg}
    
    def activity_start_handler(self, prompt: str, messages: List[Dict], trace: TraceTracker) -> Dict[str, Any]:
        """Handle activity start requests with tracing"""
        with traced_operation("Activity Start Handler") as start_trace:
            try:
                # Start the activity
                result = self.start_activity_tool(prompt, trace)
                
                start_trace.add_span("Activity Start", 
                                   {"prompt": prompt}, 
                                   {"result": result})
                
                return {
                    "intent": "activity_start",
                    "result": result
                }
                
            except Exception as e:
                error_msg = f"Activity start handler failed: {str(e)}"
                logger.error(error_msg)
                start_trace.finish("error", error_msg)
                return {"error": error_msg}
    
    def general_chat_handler(self, prompt: str, messages: List[Dict], trace: TraceTracker) -> Dict[str, Any]:
        """Handle general chat requests with tracing"""
        with traced_operation("General Chat Handler") as chat_trace:
            try:
                # Build conversation context
                conversation_context = []
                for msg in messages[-3:]:  # Last 3 messages for context
                    conversation_context.append(f"{msg['role']}: {msg['content']}")
                
                context_text = "\n".join(conversation_context) if conversation_context else "No previous context"
                
                chat_trace.add_span("Context Building", 
                                   {"messages": messages}, 
                                   {"context_length": len(context_text)})
                
                # Generate response using Azure OpenAI
                full_prompt = f"Context:\n{context_text}\n\nUser: {prompt}\n\nAssistant:"
                
                response = self.azure_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": full_prompt}],
                    max_tokens=500,
                    temperature=0.7,
                    callbacks=[self.langfuse_handler] if self.langfuse_handler else None
                )
                
                assistant_message = response.choices[0].message.content.strip()
                
                # Track LLM generation
                track_llm_generation(
                    model="gpt-4",
                    prompt=full_prompt,
                    completion=assistant_message,
                    metadata={
                        "operation": "general_chat",
                        "tokens_used": response.usage.total_tokens if response.usage else None,
                        "model": "gpt-4"
                    },
                    trace=chat_trace
                )
                
                chat_trace.add_span("Response Generation", 
                                   {"prompt": full_prompt}, 
                                   {"response": assistant_message})
                
                return {
                    "intent": "general_chat",
                    "result": {
                        "message": assistant_message,
                        "session_id": str(datetime.now().timestamp())
                    }
                }
                
            except Exception as e:
                error_msg = f"General chat handler failed: {str(e)}"
                logger.error(error_msg)
                chat_trace.finish("error", error_msg)
                return {"error": error_msg}
    
    def start_activity_tool(self, prompt: str, trace: TraceTracker) -> Dict[str, Any]:
        """Start an activity with tracing"""
        try:
            # Extract activity name from prompt
            activity_name = self.extract_activity_info(prompt).get('name', 'Unknown Activity')
            
            trace.add_span("Activity Start", 
                          {"prompt": prompt}, 
                          {"activity_name": activity_name})
            
            # Find the activity
            activity = self.find_activity(activity_name)
            
            if not activity:
                return {
                    "message": f"Activity '{activity_name}' not found. Please check the activity name and try again.",
                    "session_id": str(datetime.now().timestamp())
                }
            
            # Generate activity content
            content = self.generate_activity_content(activity, trace)
            
            trace.add_span("Activity Content Generation", 
                          {"activity": activity}, 
                          {"content": content})
            
            return {
                "message": f"Activity '{activity.name}' initiated. Check the response for details.",
                "activity": content,
                "session_id": str(datetime.now().timestamp())
            }
            
        except Exception as e:
            error_msg = f"Activity start failed: {str(e)}"
            logger.error(error_msg)
            trace.add_span("Activity Start Error", 
                          {"prompt": prompt}, 
                          {"error": error_msg})
            return {"error": error_msg}
    
    def extract_activity_info(self, prompt: str) -> Dict[str, Any]:
        """Extract activity information from prompt"""
        # Simple extraction - can be enhanced with more sophisticated parsing
        prompt_lower = prompt.lower()
        
        if "start" in prompt_lower and "activity" in prompt_lower:
            # Extract activity name
            parts = prompt.split()
            try:
                start_idx = parts.index("start")
                if start_idx + 2 < len(parts) and parts[start_idx + 1] == "activity":
                    activity_name = " ".join(parts[start_idx + 2:])
                    return {"name": activity_name, "type": "start"}
            except ValueError:
                pass
        
        return {"name": "Unknown Activity", "type": "unknown"}
    
    def find_activity(self, activity_name: str) -> Optional[Any]:
        """Find activity by name - placeholder implementation"""
        # This would typically query your database
        # For now, return a mock activity
        class MockActivity:
            def __init__(self, name):
                self.name = name
                self.description = f"Description for {name}"
                self.level = "Intermediate"
        
        return MockActivity(activity_name)
    
    def generate_activity_content(self, activity: Any, trace: TraceTracker) -> Dict[str, Any]:
        """Generate activity content with tracing"""
        try:
            # Generate MCQ questions for the activity
            mcq_prompt = f"""Generate 5 multiple choice questions for the activity: {activity.name}
            
            Activity Description: {activity.description}
            Level: {activity.level}
            
            Format each question as:
            Q1. [Question text]
            A) [Option A]
            B) [Option B]
            C) [Option C]
            D) [Option D]
            Correct Answer: [Letter]
            
            Make questions engaging and appropriate for {activity.level} level."""
            
            trace.add_span("MCQ Generation", 
                          {"activity": activity.name}, 
                          {"prompt": mcq_prompt})
            
            # Generate MCQs using Azure OpenAI
            response = self.azure_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": mcq_prompt}],
                max_tokens=1000,
                temperature=0.7,
                callbacks=[self.langfuse_handler] if self.langfuse_handler else None
            )
            
            mcq_content = response.choices[0].message.content.strip()
            
            # Track LLM generation
            track_llm_generation(
                model="gpt-4",
                prompt=mcq_prompt,
                completion=mcq_content,
                metadata={
                    "operation": "mcq_generation",
                    "activity_name": activity.name,
                    "tokens_used": response.usage.total_tokens if response.usage else None,
                    "model": "gpt-4"
                },
                trace=trace
            )
            
            trace.add_span("MCQ Result", 
                          {"prompt": mcq_prompt}, 
                          {"content": mcq_content})
            
            return {
                "name": activity.name,
                "description": activity.description,
                "level": activity.level,
                "mcq_questions": mcq_content,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"MCQ generation failed: {str(e)}"
            logger.error(error_msg)
            trace.add_span("MCQ Generation Error", 
                          {"activity": activity.name}, 
                          {"error": error_msg})
            return {"error": error_msg} 

