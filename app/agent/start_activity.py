import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from rapidfuzz import fuzz, process
from app.services.azure_chat import AzureChat
import json
from sqlalchemy.orm import Session
from app.models.activity import Activity
from app.models.activity_category import ActivityCategory
from app.models.activity_sub_category import ActivitySubCategory

# Configure module-level logger
logger = logging.getLogger(__name__)

async def extract_activity_details(user_input: str) -> Dict[str, Optional[str]]:
    """
    Use LLM to extract activity_name, category_name, subcategory_name, and additional_details from user input.
    """
    logger.debug("extract_activity_details called with input: %r", user_input)
    system_message = (
        "You are an expert assistant for an educational LMS. "
        "Extract the following details from the user's message as accurately as possible: "
        "- activity_name: The name or title of the activity the user wants to start (if any).\n"
        "- category_name: The main category of the activity (if mentioned).\n"
        "- subcategory_name: The subcategory of the activity (if mentioned).\n"
        "- additional_details: Any extra details, such as number of questions for a quiz, or other relevant info.\n"
        "Return a valid JSON object with these keys: activity_name, category_name, subcategory_name, additional_details. "
        "If a value is not present, set it to null or an empty object for additional_details."
    )
    prompt = f"User input: {user_input}\nExtract the details as described."
    logger.info(f"System Message :{system_message} and User Input :{user_input}")
    chat = AzureChat(system_message=system_message, temperature=0.1, max_tokens=512)
    response = await chat.achat(prompt)
    logger.debug("LLM response: %s", response)
    try:
        details = json.loads(response)
        for key in ["activity_name", "category_name", "subcategory_name", "additional_details"]:
            if key not in details:
                details[key] = None if key != "additional_details" else {}
        if details["additional_details"] is None:
            details["additional_details"] = {}
        logger.debug("Parsed details: %r", details)
        return details
    except Exception:
        logger.exception("Failed to parse LLM response as JSON")
        return {"activity_name": None, "category_name": None, "subcategory_name": None, "additional_details": {}}

async def get_activities_from_db(db: Session) -> List[Dict[str, Any]]:
    """
    Fetch all activities from the database and return as a list of dicts for matching.
    """
    logger.debug("Fetching activities from DB")
    activities = db.query(Activity).filter(Activity.is_active == True).all()
    result = []
    for act in activities:
        category_name = act.category.name if act.category else None
        subcategory_name = act.sub_category.name if act.sub_category else None
        questions = []
        if hasattr(act, "questions") and act.questions:
            for q in act.questions:
                questions.append({"q": getattr(q, "question_text", None), "a": getattr(q, "answer_text", None)})
        entry = {
            "id": str(act.id),
            "name": act.name,
            "category_name": category_name,
            "subcategory_name": subcategory_name,
            "final_description": act.final_description,
            "type": "quiz" if questions else "activity",
            "questions": questions,
        }
        result.append(entry)
    logger.debug("Loaded %d activities", len(result))
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
    logger.debug(
        "Starting fuzzy matching: activity_name=%r, category_name=%r, subcategory_name=%r",
        activity_name, category_name, subcategory_name
    )
    candidates: List[Tuple[Dict[str, Any], int]] = []
    if activity_name:
        for act in db_activities:
            score = fuzz.token_set_ratio(activity_name, act["name"])
            candidates.append((act, score))
        candidates.sort(key=lambda x: x[1], reverse=True)
        logger.debug("Explicit match candidates: %r", [(c[0]["name"], c[1]) for c in candidates[:3]])
        if candidates and candidates[0][1] >= threshold:
            logger.info(
                "Explicit fuzzy match success: %s (score %d)",
                candidates[0][0]["name"], candidates[0][1]
            )
            return candidates[0][0], [(c[0]["name"], c[1]) for c in candidates[:3]]
    candidates.clear()
    for act in db_activities:
        score = fuzz.token_set_ratio(user_input, act.get("final_description", "") or "")
        candidates.append((act, score))
    candidates.sort(key=lambda x: x[1], reverse=True)
    logger.debug("Description match candidates: %r", [(c[0]["name"], c[1]) for c in candidates[:3]])
    if candidates and candidates[0][1] >= threshold:
        logger.info(
            "Description fuzzy match success: %s (score %d)",
            candidates[0][0]["name"], candidates[0][1]
        )
        return candidates[0][0], [(c[0]["name"], c[1]) for c in candidates[:3]]
    filtered = [
        act for act in db_activities if (
            category_name and act.get("category_name") and act["category_name"].lower() == category_name.lower()
        ) or (
            subcategory_name and act.get("subcategory_name") and act["subcategory_name"].lower() == subcategory_name.lower()
        )
    ]
    suggestions = [(act["name"], 0) for act in filtered[:3]]
    logger.warning("No fuzzy match above threshold, fallback suggestions: %r", suggestions)
    return None, suggestions

async def handle_missing_info(
    details: Dict[str, Optional[str]],
    db_activities: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    If info is missing, suggest top 3 likely activities and ask user for clarification.
    """
    logger.debug("Handling missing info for details: %r", details)
    if not details["activity_name"]:
        filtered = [act for act in db_activities if (
            details.get("category_name") and act.get("category_name") and act["category_name"].lower() == details["category_name"].lower()
        ) or (
            details.get("subcategory_name") and act.get("subcategory_name") and act["subcategory_name"].lower() == details["subcategory_name"].lower()
        )]
        suggestions = [act["name"] for act in filtered[:3]]
        logger.info("Need clarification suggestions: %r", suggestions)
        return {
            "status": "need_clarification",
            "message": f"Could not determine the activity name. Based on your input, do you mean one of these: {', '.join(suggestions)}? Please specify the activity name.",
            "suggestions": suggestions
        }
    if not details["category_name"] and details["subcategory_name"]:
        for act in db_activities:
            if act.get("subcategory_name") and act["subcategory_name"].lower() == details["subcategory_name"].lower():
                details["category_name"] = act.get("category_name")
                logger.debug("Inferred category_name: %s", details["category_name"])
                break
    return {"status": "ok", "details": details}

async def simulate_activity_execution(activity: Dict[str, Any], details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate execution of the selected activity (e.g., start a quiz).
    """
    logger.debug("simulate_activity_execution called with activity=%r, details=%r", activity, details)
    if activity.get("type") == "quiz":
        num_questions = details.get("additional_details", {}).get("num_questions", len(activity.get("questions", [])))
        questions = activity.get("questions", [])[:num_questions]
        result = {
            "status": "started",
            "message": f"Starting quiz: {activity['name']}...",
            "questions": questions
        }
        logger.info("Quiz started with %d questions", len(questions))
        return result
    result = {
        "status": "started",
        "message": f"Starting activity: {activity['name']}...",
        "description": activity.get("final_description", "")
    }
    logger.info("Activity started: %s", activity["name"])
    return result

async def start_activity_handler(user_input: str, db: Session) -> Dict[str, Any]:
    """
    Main entry point for handling 'start-activity' intent. Requires db session.
    """
    logger.debug("start_activity_handler called with user_input: %r", user_input)
    details = await extract_activity_details(user_input)
    logger.debug("Details extracted: %r", details)
    db_activities = await get_activities_from_db(db)
    logger.debug("Retrieved %d activities", len(db_activities))
    activity, candidates = await fuzzy_match_activity(
        details.get("activity_name"),
        details.get("category_name"),
        details.get("subcategory_name"),
        user_input,
        db_activities
    )
    logger.debug("First fuzzy match: activity=%r, candidates=%r", activity, candidates)
    if activity:
        return await simulate_activity_execution(activity, details)
    missing_info = await handle_missing_info(details, db_activities)
    logger.debug("Missing info result: %r", missing_info)
    if missing_info.get("status") == "need_clarification":
        return missing_info
    activity, candidates = await fuzzy_match_activity(
        details.get("activity_name"),
        details.get("category_name"),
        details.get("subcategory_name"),
        user_input,
        db_activities
    )
    logger.debug("Second fuzzy match: activity=%r, candidates=%r", activity, candidates)
    if activity:
        return await simulate_activity_execution(activity, details)
    not_found = {
        "status": "not_found",
        "message": f"No matching activity found. Top suggestions: {', '.join([c[0] for c in candidates])}",
        "targets":[]
}
