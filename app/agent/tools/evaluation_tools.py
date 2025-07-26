from typing import Dict, Any, Optional
from uuid import UUID
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from app.core.logger import get_logger
from app.agent.evaluation_agent import EvaluationAgent

logger = get_logger(__name__)

@tool
async def evaluate_user_performance(
    user_id: str,
    activity_id: str,
    session_id: Optional[str] = None,
    chat_context: str = "",
    db: Session = None
) -> Dict[str, Any]:
    """
    Evaluate user performance in a learning activity.
    
    Args:
        user_id: The user's ID
        activity_id: The activity ID to evaluate
        session_id: Optional session ID for specific session evaluation
        chat_context: Context from the current conversation
        db: Database session
    
    Returns:
        Dictionary containing evaluation results including scores, strengths, weaknesses, and recommendations
    """
    try:
        # Convert string IDs to UUID
        user_uuid = UUID(user_id)
        activity_uuid = UUID(activity_id)
        session_uuid = UUID(session_id) if session_id else None
        
        # Create evaluation agent
        evaluation_agent = EvaluationAgent(db)
        
        # Run evaluation
        result = await evaluation_agent.evaluate(
            user_id=user_uuid,
            activity_id=activity_uuid,
            session_id=session_uuid,
            chat_context=chat_context,
            triggered_by="chat"
        )
        
        logger.info(f"Evaluation completed for user {user_id} in activity {activity_id}")
        return result
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        return {
            "error": "Evaluation failed",
            "message": str(e),
            "evaluation_type": "failed"
        }

@tool
async def get_evaluation_history(
    user_id: str,
    activity_id: str,
    db: Session = None
) -> Dict[str, Any]:
    """
    Get evaluation history for a user in a specific activity.
    
    Args:
        user_id: The user's ID
        activity_id: The activity ID
        db: Database session
    
    Returns:
        Dictionary containing evaluation history
    """
    try:
        from app.models.evaluation import EvaluationResult
        
        # Convert string IDs to UUID
        user_uuid = UUID(user_id)
        activity_uuid = UUID(activity_id)
        
        # Query evaluation history
        evaluations = db.query(EvaluationResult).filter(
            EvaluationResult.user_id == user_uuid,
            EvaluationResult.activity_id == activity_uuid
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
        
        return {
            "user_id": user_id,
            "activity_id": activity_id,
            "evaluation_count": len(history),
            "evaluations": history
        }
        
    except Exception as e:
        logger.error(f"Failed to get evaluation history: {str(e)}")
        return {
            "error": "Failed to get evaluation history",
            "message": str(e)
        }

@tool
async def analyze_learning_progress(
    user_id: str,
    activity_id: str,
    db: Session = None
) -> Dict[str, Any]:
    """
    Analyze learning progress for a user in a specific activity.
    
    Args:
        user_id: The user's ID
        activity_id: The activity ID
        db: Database session
    
    Returns:
        Dictionary containing learning progress analysis
    """
    try:
        from app.models.evaluation import LearningProgress
        from app.models.activity_session import ActivitySession
        
        # Convert string IDs to UUID
        user_uuid = UUID(user_id)
        activity_uuid = UUID(activity_id)
        
        # Get learning progress
        progress = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_uuid,
            LearningProgress.activity_id == activity_uuid
        ).first()
        
        # Get recent sessions
        recent_sessions = db.query(ActivitySession).filter(
            ActivitySession.user_id == user_uuid,
            ActivitySession.activity_id == activity_uuid
        ).order_by(ActivitySession.created_at.desc()).limit(10).all()
        
        # Calculate progress metrics
        total_sessions = len(recent_sessions)
        completed_sessions = len([s for s in recent_sessions if s.status.value == "completed"])
        completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        # Calculate average time spent
        total_time = 0
        for session in recent_sessions:
            if session.time_spent:
                # Convert time string to seconds (assuming format like "2h 30m")
                time_parts = session.time_spent.split()
                hours = 0
                minutes = 0
                for part in time_parts:
                    if 'h' in part:
                        hours = int(part.replace('h', ''))
                    elif 'm' in part:
                        minutes = int(part.replace('m', ''))
                total_time += hours * 3600 + minutes * 60
        
        avg_time_per_session = total_time / total_sessions if total_sessions > 0 else 0
        
        return {
            "user_id": user_id,
            "activity_id": activity_id,
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "completion_rate": completion_rate,
            "average_time_per_session": avg_time_per_session,
            "total_time_spent": total_time,
            "progress_data": {
                "completion_percentage": progress.completion_percentage if progress else 0,
                "engagement_score": progress.engagement_score if progress else None,
                "learning_style": progress.learning_style if progress else None
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze learning progress: {str(e)}")
        return {
            "error": "Failed to analyze learning progress",
            "message": str(e)
        } 