from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from models.activity import Activity
from schemas.activity import ActivityCreate, ActivityUpdate, ActivityResponse
from api.deps import get_db, get_current_user
from models.user import User
import uuid

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
    db_activity = Activity(
        name=activity.name,
        description=activity.description,
        category_id=activity.category_id,
        sub_category_id=activity.sub_category_id,
        difficulty_level=activity.difficulty_level,
        access_type=activity.access_type,
        created_by=current_user.id,
        ai_guide=activity.ai_guide,
        follow_up_questions=activity.follow_up_questions
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

@router.get("/", response_model=List[ActivityResponse])
def list_activities(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all activities"""
    activities = db.query(Activity).offset(skip).limit(limit).all()
    return activities

@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity(
    activity_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific activity details"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    return activity

@router.put("/{activity_id}", response_model=ActivityResponse)
def update_activity(
    activity_id: uuid.UUID,
    activity_update: ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update activity"""
    db_activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not db_activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    # Check if user is the creator of the activity
    if db_activity.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this activity"
        )

    # Update activity fields
    for field, value in activity_update.dict(exclude_unset=True).items():
        setattr(db_activity, field, value)

    db.commit()
    db.refresh(db_activity)
    return db_activity

@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    activity_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete activity"""
    db_activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not db_activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    # Check if user is the creator of the activity
    if db_activity.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this activity"
        )

    db.delete(db_activity)
    db.commit()
    return None 