from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.logger import get_logger
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.activity import Activity
from app.agent.evaluation_agent import EvaluationAgent
from app.models.evaluation import EvaluationResult, EvaluationType, EvaluationStatus
from pydantic import BaseModel
from datetime import datetime

logger = get_logger(__name__)

router = APIRouter()

# Pydantic models for request/response
class EvaluationRequest(BaseModel):
    activity_id: str
    session_id: Optional[str] = None
    evaluation_type: str = "comprehensive"  # quiz, progress, document, comprehensive
    chat_context: str = ""

class EvaluationResponse(BaseModel):
    evaluation_id: str
    evaluation_type: str
    overall_score: Optional[float]
    accuracy_percentage: Optional[float]
    difficulty_breakdown: Optional[dict]
    strengths: Optional[List[str]]
    weaknesses: Optional[List[str]]
    recommendations: Optional[List[str]]
    follow_up_questions: Optional[List[str]]
    learning_path: Optional[List[dict]]
    knowledge_gaps: Optional[List[str]]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

class EvaluationHistoryResponse(BaseModel):
    user_id: str
    activity_id: str
    evaluation_count: int
    evaluations: List[dict]

@router.post("/evaluate", response_model=EvaluationResponse)
async def trigger_evaluation(
    request: EvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger an evaluation for a user in a specific activity.
    Can be called from UI or chat interface.
    """
    try:
        # Validate activity exists and user has access
        activity = db.query(Activity).filter(Activity.id == UUID(request.activity_id)).first()
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Check if user has access to this activity
        if activity.access_type.value == "private" and str(activity.created_by) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this activity"
            )
        
        # Create evaluation agent
        evaluation_agent = EvaluationAgent(db)
        
        # Run evaluation
        result = await evaluation_agent.evaluate(
            user_id=current_user.id,
            activity_id=UUID(request.activity_id),
            session_id=UUID(request.session_id) if request.session_id else None,
            chat_context=request.chat_context,
            triggered_by="ui"
        )
        
        # Get the evaluation record
        evaluation = db.query(EvaluationResult).filter(
            EvaluationResult.user_id == current_user.id,
            EvaluationResult.activity_id == UUID(request.activity_id)
        ).order_by(EvaluationResult.created_at.desc()).first()
        
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Evaluation record not found"
            )
        
        logger.info(f"Evaluation triggered successfully for user {current_user.id} in activity {request.activity_id}")
        
        return EvaluationResponse(
            evaluation_id=str(evaluation.id),
            evaluation_type=evaluation.evaluation_type.value,
            overall_score=evaluation.overall_score,
            accuracy_percentage=evaluation.accuracy_percentage,
            difficulty_breakdown=evaluation.difficulty_breakdown,
            strengths=evaluation.strengths,
            weaknesses=evaluation.weaknesses,
            recommendations=evaluation.recommendations,
            follow_up_questions=evaluation.follow_up_questions,
            learning_path=evaluation.learning_path,
            knowledge_gaps=evaluation.knowledge_gaps,
            status=evaluation.status.value,
            created_at=evaluation.created_at,
            completed_at=evaluation.completed_at
        )
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )

@router.get("/history/{activity_id}", response_model=EvaluationHistoryResponse)
async def get_evaluation_history(
    activity_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get evaluation history for a user in a specific activity.
    """
    try:
        # Validate activity exists and user has access
        activity = db.query(Activity).filter(Activity.id == UUID(activity_id)).first()
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Check if user has access to this activity
        if activity.access_type.value == "private" and str(activity.created_by) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this activity"
            )
        
        # Get evaluation history
        evaluations = db.query(EvaluationResult).filter(
            EvaluationResult.user_id == current_user.id,
            EvaluationResult.activity_id == UUID(activity_id)
        ).order_by(EvaluationResult.created_at.desc()).all()
        
        history = []
        for eval_result in evaluations:
            history.append({
                "evaluation_id": str(eval_result.id),
                "evaluation_type": eval_result.evaluation_type.value,
                "overall_score": eval_result.overall_score,
                "accuracy_percentage": eval_result.accuracy_percentage,
                "status": eval_result.status.value,
                "created_at": eval_result.created_at.isoformat(),
                "completed_at": eval_result.completed_at.isoformat() if eval_result.completed_at else None
            })
        
        logger.info(f"Retrieved evaluation history for user {current_user.id} in activity {activity_id}")
        
        return EvaluationHistoryResponse(
            user_id=str(current_user.id),
            activity_id=activity_id,
            evaluation_count=len(history),
            evaluations=history
        )
        
    except Exception as e:
        logger.error(f"Failed to get evaluation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get evaluation history: {str(e)}"
        )

@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation_result(
    evaluation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific evaluation result by ID.
    """
    try:
        # Get evaluation record
        evaluation = db.query(EvaluationResult).filter(
            EvaluationResult.id == UUID(evaluation_id),
            EvaluationResult.user_id == current_user.id
        ).first()
        
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found"
            )
        
        logger.info(f"Retrieved evaluation {evaluation_id} for user {current_user.id}")
        
        return EvaluationResponse(
            evaluation_id=str(evaluation.id),
            evaluation_type=evaluation.evaluation_type.value,
            overall_score=evaluation.overall_score,
            accuracy_percentage=evaluation.accuracy_percentage,
            difficulty_breakdown=evaluation.difficulty_breakdown,
            strengths=evaluation.strengths,
            weaknesses=evaluation.weaknesses,
            recommendations=evaluation.recommendations,
            follow_up_questions=evaluation.follow_up_questions,
            learning_path=evaluation.learning_path,
            knowledge_gaps=evaluation.knowledge_gaps,
            status=evaluation.status.value,
            created_at=evaluation.created_at,
            completed_at=evaluation.completed_at
        )
        
    except Exception as e:
        logger.error(f"Failed to get evaluation result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get evaluation result: {str(e)}"
        )

@router.delete("/{evaluation_id}")
async def delete_evaluation(
    evaluation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific evaluation result.
    """
    try:
        # Get evaluation record
        evaluation = db.query(EvaluationResult).filter(
            EvaluationResult.id == UUID(evaluation_id),
            EvaluationResult.user_id == current_user.id
        ).first()
        
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found"
            )
        
        # Delete the evaluation
        db.delete(evaluation)
        db.commit()
        
        logger.info(f"Deleted evaluation {evaluation_id} for user {current_user.id}")
        
        return {"message": "Evaluation deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete evaluation: {str(e)}"
        ) 