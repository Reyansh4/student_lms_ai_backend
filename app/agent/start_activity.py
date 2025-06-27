import re
from typing import List, Dict, Any, Optional, Tuple
from rapidfuzz import fuzz, process
from app.services.azure_chat import AzureChat
import json
from sqlalchemy.orm import Session
from app.models.activity import Activity
from app.models.activity_category import ActivityCategory
from app.models.activity_sub_category import ActivitySubCategory

async def extract_activity_details(user_input: str) -> Dict[str, Optional[str]]:
    """
    Use LLM to extract activity_name, category_name, subcategory_name, and additional_details from user input.
    """
    system_message = (
        "You are an expert assistant for an educational LMS. "
        "Extract the following details from the user's message as accurately as possible: "
        "- activity_name: The name or title of the activity the user wants to start (if any).\n"
        "- category_name: The main category of the activity (if mentioned).\n"
        "- subcategory_name: The subcategory of the activity (if mentioned).\n"
        "- additional_details: Any extra details, such as number of questions for a quiz, or other relevant info.\n"
        "Return a valid JSON object with these keys: activity_name, category_name, subcategory_name, additional_details. "
        "If a value is not present, set it to null or an empty object for additional_details. "
        "Example output: {\"activity_name\": \"Python Basics Quiz\", \"category_name\": \"Programming\", \"subcategory_name\": \"Python\", \"additional_details\": {\"num_questions\": 5}}"
    )
    prompt = f"User input: {user_input}\nExtract the details as described."
    chat = AzureChat(system_message=system_message, temperature=0.2, max_tokens=512)
    response = await chat.achat(prompt)
    # Try to parse the LLM's response as JSON
    try:
        details = json.loads(response)
        # Ensure all required keys are present
        for key in ["activity_name", "category_name", "subcategory_name", "additional_details"]:
            if key not in details:
                details[key] = None if key != "additional_details" else {}
        if details["additional_details"] is None:
            details["additional_details"] = {}
        return details
    except Exception:
        # Fallback: return empty structure if parsing fails
        return {"activity_name": None, "category_name": None, "subcategory_name": None, "additional_details": {}}

async def get_activities_from_db(db: Session) -> List[Dict[str, Any]]:
    """
    Fetch all activities from the database and return as a list of dicts for matching.
    """
    activities = db.query(Activity).filter(Activity.is_active == True).all()
    result = []
    for act in activities:
        # Fetch category and subcategory names
        category_name = act.category.name if act.category else None
        subcategory_name = act.sub_category.name if act.sub_category else None
        # Fetch questions if available (optional, for quiz simulation)
        questions = []
        if hasattr(act, "questions") and act.questions:
            for q in act.questions:
                questions.append({"q": getattr(q, "question_text", None), "a": getattr(q, "answer_text", None)})
        result.append({
            "id": str(act.id),
            "name": act.name,
            "category_name": category_name,
            "subcategory_name": subcategory_name,
            "final_description": act.final_description,
            "type": "quiz" if questions else "activity",
            "questions": questions,
        })
    return result

async def fuzzy_match_activity(
    activity_name: Optional[str],
    category_name: Optional[str],
    subcategory_name: Optional[str],
    user_input: str,
    db_activities: List[Dict[str, Any]],
    threshold: int = 85
) -> Tuple[Optional[Dict[str, Any]], List[Tuple[str, int]]]:
    """
    Fuzzy and semantic match for activity_name against the mock DB.
    Returns the best match (if above threshold) and top 3 candidates.
    """
    candidates = []
    if activity_name:
        for act in db_activities:
            score = fuzz.token_set_ratio(activity_name, act["name"])
            candidates.append((act, score))
        candidates.sort(key=lambda x: x[1], reverse=True)
        if candidates and candidates[0][1] >= threshold:
            return candidates[0][0], [(c[0]["name"], c[1]) for c in candidates[:3]]
    for act in db_activities:
        score = fuzz.token_set_ratio(user_input, act["final_description"] or "")
        candidates.append((act, score))
    candidates.sort(key=lambda x: x[1], reverse=True)
    if candidates and candidates[0][1] >= threshold:
        return candidates[0][0], [(c[0]["name"], c[1]) for c in candidates[:3]]
    filtered = [act for act in db_activities if (category_name and act["category_name"] and act["category_name"].lower() == category_name.lower()) or (subcategory_name and act["subcategory_name"] and act["subcategory_name"].lower() == subcategory_name.lower())]
    fallback = [(act["name"], 0) for act in filtered[:3]]
    return None, fallback

async def handle_missing_info(
    details: Dict[str, Optional[str]],
    db_activities: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    If info is missing, suggest top 3 likely activities and ask user for clarification.
    """
    suggestions = []
    if not details["activity_name"]:
        filtered = [act for act in db_activities if (details["category_name"] and act["category_name"] and act["category_name"].lower() == details["category_name"].lower()) or (details["subcategory_name"] and act["subcategory_name"] and act["subcategory_name"].lower() == details["subcategory_name"].lower())]
        suggestions = [act["name"] for act in filtered[:3]]
        return {
            "status": "need_clarification",
            "message": f"Could not determine the activity name. Based on your input, do you mean one of these: {', '.join(suggestions)}? Please specify the activity name.",
            "suggestions": suggestions
        }
    if not details["category_name"] and details["subcategory_name"]:
        for act in db_activities:
            if act["subcategory_name"] and act["subcategory_name"].lower() == details["subcategory_name"].lower():
                details["category_name"] = act["category_name"]
                break
    return {"status": "ok", "details": details}

async def simulate_activity_execution(activity: Dict[str, Any], details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate execution of the selected activity (e.g., start a quiz).
    """
    if activity["type"] == "quiz":
        num_questions = details.get("additional_details", {}).get("num_questions", len(activity["questions"]))
        questions = activity["questions"][:num_questions]
        return {
            "status": "started",
            "message": f"Starting quiz: {activity['name']}...",
            "questions": questions
        }
    return {
        "status": "started",
        "message": f"Starting activity: {activity['name']}...",
        "description": activity.get("final_description", "")
    }

async def start_activity_handler(user_input: str, db: Session) -> Dict[str, Any]:
    """
    Main entry point for handling 'start-activity' intent. Requires db session.
    """
    details = await extract_activity_details(user_input)
    db_activities = await get_activities_from_db(db)
    # Try to match activity immediately
    activity, candidates = await fuzzy_match_activity(
        details["activity_name"],
        details["category_name"],
        details["subcategory_name"],
        user_input,
        db_activities
    )
    if activity:
        return await simulate_activity_execution(activity, details)
    # If no activity found, handle missing info and prompt for clarification
    missing_info = await handle_missing_info(details, db_activities)
    if missing_info["status"] == "need_clarification":
        return missing_info
    # Try again after clarification (e.g., if category inferred from subcategory)
    activity, candidates = await fuzzy_match_activity(
        details["activity_name"],
        details["category_name"],
        details["subcategory_name"],
        user_input,
        db_activities
    )
    if activity:
        return await simulate_activity_execution(activity, details)
    return {
        "status": "not_found",
        "message": f"No matching activity found. Top suggestions: {', '.join([c[0] for c in candidates])}",
        "suggestions": [c[0] for c in candidates]
    }
