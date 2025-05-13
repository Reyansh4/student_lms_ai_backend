from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityUpdate, ActivityResponse
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.activity_templates import ActivityTemplate
from app.core.logger import get_logger
from app.services.generate_clarification_questions import generate_clarification_questions
from app.agent.templates.activity.final_description import generate_final_description

# Add new schemas for request/response
class ClarificationQuestionsResponse(BaseModel):
    activity_id: UUID
    questions: List[Dict[str, str]]  # List of question objects with id and text
    status: str

class ClarificationAnswersRequest(BaseModel):
    answers: Dict[str, str]  # Map of question_id to answer

class FinalDescriptionResponse(BaseModel):
    activity_id: UUID
    final_description: str
    status: str

# Initialize logger
logger = get_logger(__name__)

router = APIRouter(
    prefix="/activities",
    tags=["activities"]
)

@router.post("/", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new activity"""
    logger.info(f"Creating new activity: {activity.name} by user: {current_user.email}")
    try:
        db_activity = Activity(
            name=activity.name,
            description=activity.description,
            category_id=activity.category_id,
            sub_category_id=activity.sub_category_id,
            difficulty_level=activity.difficulty_level,
            access_type=activity.access_type,
            created_by=current_user.id,
            ai_guide=activity.ai_guide,
            final_description=activity.final_description
        )
        db.add(db_activity)
        db.commit()
        db.refresh(db_activity)
        logger.info(f"Successfully created activity: {db_activity.id}")
        return db_activity
    except Exception as e:
        logger.error(f"Error creating activity: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the activity"
        )

@router.get("/", response_model=List[ActivityResponse])
def list_activities(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all activities"""
    logger.info(f"Listing activities for user: {current_user.email} (skip: {skip}, limit: {limit})")
    try:
        activities = db.query(Activity).offset(skip).limit(limit).all()
        logger.info(f"Found {len(activities)} activities")
        return activities
    except Exception as e:
        logger.error(f"Error listing activities: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching activities"
        )

@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific activity details"""
    logger.info(f"Fetching activity {activity_id} for user: {current_user.email}")
    try:
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            logger.warning(f"Activity not found: {activity_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        logger.info(f"Successfully retrieved activity: {activity_id}")
        return activity
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching activity {activity_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching the activity"
        )

@router.put("/{activity_id}", response_model=ActivityResponse)
def update_activity(
    activity_id: UUID,
    activity_update: ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update activity"""
    logger.info(f"Updating activity {activity_id} by user: {current_user.email}")
    try:
        db_activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not db_activity:
            logger.warning(f"Activity not found for update: {activity_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        if db_activity.created_by != current_user.id:
            logger.warning(f"Unauthorized update attempt for activity {activity_id} by user: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this activity"
            )

        for field, value in activity_update.dict(exclude_unset=True).items():
            setattr(db_activity, field, value)

        db.commit()
        db.refresh(db_activity)
        logger.info(f"Successfully updated activity: {activity_id}")
        return db_activity
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating activity {activity_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while updating the activity"
        )

@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete activity"""
    logger.info(f"Deleting activity {activity_id} by user: {current_user.email}")
    try:
        db_activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not db_activity:
            logger.warning(f"Activity not found for deletion: {activity_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        if db_activity.created_by != current_user.id:
            logger.warning(f"Unauthorized deletion attempt for activity {activity_id} by user: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this activity"
            )

        db.delete(db_activity)
        db.commit()
        logger.info(f"Successfully deleted activity: {activity_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting activity {activity_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while deleting the activity"
        )

@router.post("/create_activity_with_template/{template_id}", response_model=ActivityResponse)
def create_activity_with_template(
    template_id: UUID,
    activity_data: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new activity using a template"""
    logger.info(f"Creating activity from template {template_id} by user: {current_user.email}")
    try:
        template = db.query(ActivityTemplate).filter(ActivityTemplate.id == template_id).first()
        if not template:
            logger.warning(f"Template not found: {template_id}")
            raise HTTPException(status_code=404, detail="Template not found")

        db_activity = Activity(
            name=template.name,
            description=template.description,
            category_id=template.category_id,
            sub_category_id=template.sub_category_id,
            difficulty_level=template.difficulty_level,
            access_type=template.access_type,
            created_by=current_user.id,
            ai_guide=activity_data.ai_guide,
            final_description=activity_data.final_description
        )

        db.add(db_activity)
        db.commit()
        db.refresh(db_activity)
        logger.info(f"Successfully created activity from template: {db_activity.id}")
        return db_activity
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating activity from template {template_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the activity from template"
        )

@router.post("/{activity_id}/generate-clarification-questions", response_model=ClarificationQuestionsResponse)
def generate_activity_clarification_questions(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate 5 clarification questions for an activity using AI"""
    logger.info(f"Generating clarification questions for activity {activity_id} by user: {current_user.email}")
    try:
        # Get the activity
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            logger.warning(f"Activity not found: {activity_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )

        # Prepare activity details for the template
        activity_details = {
            "name": activity.name,
            "description": activity.description,
            "level": activity.difficulty_level,
            "category_name": activity.category.name if activity.category else None,
            "sub_category_name": activity.sub_category.name if activity.sub_category else None
        }

        # Generate exactly 5 clarification questions using the template
        questions = await generate_clarification_questions(activity_details)
        
        # Format questions with unique IDs
        formatted_questions = [
            {
                "id": f"q_{i+1}",
                "text": question
            }
            for i, question in enumerate(questions[:5])  # Ensure exactly 5 questions
        ]
        
        # Update activity with the generated questions
                                                                       
        logger.info(f"Successfully generated 5 clarification questions for activity: {activity_id}")
        return ClarificationQuestionsResponse(
            activity_id=activity_id,
            questions=formatted_questions,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error generating clarification questions for activity {activity_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while generating clarification questions: {str(e)}"
        )

@router.post("/{activity_id}/generate-final-description", response_model=FinalDescriptionResponse)
def generate_activity_final_description(
    activity_id: UUID,
    answers_request: ClarificationAnswersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate final description for an activity using AI based on clarification answers"""
    logger.info(f"Generating final description for activity {activity_id} by user: {current_user.email}")
    try:
        # Get the activity
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            logger.warning(f"Activity not found: {activity_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )

        # Verify that clarification questions exist
        if not activity.clarification_questions:
            logger.warning(f"No clarification questions found for activity: {activity_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Clarification questions must be generated first"
            )

        # Verify that all questions have been answered
        # question_ids = {q["id"] for q in activity.clarification_questions}
        # answer_ids = set(answers_request.answers.keys())
        # if question_ids != answer_ids:
        #     missing_questions = question_ids - answer_ids
        #     extra_answers = answer_ids - question_ids
        #     error_msg = []
        #     if missing_questions:
        #         error_msg.append(f"Missing answers for questions: {missing_questions}")
        #     if extra_answers:
        #         error_msg.append(f"Extra answers provided for non-existent questions: {extra_answers}")
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="All questions must be answered: " + "; ".join(error_msg)
        #     )

        # Prepare activity details and Q&A for the template
        activity_details = {
            "name": activity.name,
            "description": activity.description,
            "level": activity.difficulty_level,
            "category_name": activity.category.name if activity.category else None,
            "sub_category_name": activity.sub_category.name if activity.sub_category else None
        }

        # Format Q&A for the template
        qa_pairs = [
            {
                "question": next(q["text"] for q in activity.clarification_questions if q["id"] == q_id),
                "answer": answer
            }
            for q_id, answer in answers_request.answers.items()
        ]

        # Generate final description using the template
        final_description = await generate_final_description(
            activity_details=activity_details,
            clarification_qa=qa_pairs
        )
        
        # Update activity with the final description
        activity.final_description = final_description
        db.commit()
        
        logger.info(f"Successfully generated final description for activity: {activity_id}")
        return FinalDescriptionResponse(
            activity_id=activity_id,
            final_description=final_description,
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating final description for activity {activity_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while generating final description: {str(e)}"
        ) 
    


# AI Agent :-
# Input :- User Input, activity_final description, document(optional)

# It will call prompt template in which you have input. It will be zero shots. 