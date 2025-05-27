from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from uuid import UUID
import json
import logging
from pathlib import Path

from app.models.activity import Activity
from app.schemas.activity import (
    ActivityCreate, 
    ActivityUpdate, 
    ActivityResponse,
    ClarificationQuestionsResponse,
    ClarificationAnswersRequest,
    FinalDescriptionResponse
)
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.activity_templates import ActivityTemplate
from app.core.logger import get_logger
from app.services.chat_completion import ChatCompletion
from app.models.chat_models import ChatCompletionRequest, Message
from app.agent.templates.activity.final_description import generate_final_description


# Initialize logger and AI client
logger = get_logger(__name__)
ai_client = ChatCompletion()

router = APIRouter(
    prefix="/activities",
    tags=["activities"]
)

@router.post("/{activity_id}/generate-clarification-questions", response_model=ClarificationQuestionsResponse)
async def generate_activity_clarification_questions(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate 3-5 clarification questions for an activity using Azure OpenAI and a markdown template"""
    logger.info(f"Generating clarification questions for activity {activity_id} by user: {current_user.email}")
    # Load clarification questions template
    TEMPLATE_PATH = Path(__file__).parent.parent / "agent" / "templates" / "activity" / "clarification_questions.md"
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Clarification template not found at {TEMPLATE_PATH}")
    CLARIFICATION_TEMPLATE = TEMPLATE_PATH.read_text()
    # Fetch activity
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        logger.warning(f"Activity not found: {activity_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    # Prepare activity details JSON as user_input
    user_input = {
        "name": activity.name,
        "description": activity.description,
        "level": activity.difficulty_level,
        "category_name": activity.category.name if activity.category else None,
        "sub_category_name": activity.sub_category.name if activity.sub_category else None
    }
    user_input_json = json.dumps(user_input, indent=2)

    # Build prompt by injecting user_input into the markdown template
    prompt = CLARIFICATION_TEMPLATE.format(user_input=user_input_json)

    # Build AI request
    request = ChatCompletionRequest(
        messages=[
            Message(role="system", content="You are an AI assistant that creates targeted clarification questions."),
            Message(role="user", content=prompt)
        ],
        max_tokens=300,
        temperature=0.1
    )

    # Call Azure OpenAI
    response = await ai_client.create(request)
    text = response.choices[0].message.content.strip()

    # Extract JSON from OUTPUT section
    json_output = text
    if "## OUTPUT" in text:
        json_output = text.split("## OUTPUT", 1)[1].strip()
    try:
        raw_questions: List[str] = json.loads(json_output)
    except json.JSONDecodeError:
        logger.error("Failed to parse questions JSON: %s", text)
        raise HTTPException(status_code=500, detail="Invalid response format from AI service")

    # Format and persist up to 5 questions
    formatted = [{"id": f"q_{i+1}", "text": q} for i, q in enumerate(raw_questions[:5])]
    activity.clarification_questions = formatted
    db.commit()

    logger.info(f"Successfully generated clarification questions for activity {activity_id}")
    return ClarificationQuestionsResponse(
        activity_id=activity_id,
        questions=formatted,
        status="success"
    )

# The generate-final-description endpoint remains unchanged for brevity
@router.post("/{activity_id}/generate-final-description", response_model=FinalDescriptionResponse)
def generate_activity_final_description(
    activity_id: UUID,
    answers_request: ClarificationAnswersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pass  # unchanged
