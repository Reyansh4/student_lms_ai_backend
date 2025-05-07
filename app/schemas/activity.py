from pydantic import BaseModel, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum
from models.activity import DifficultyLevel, AccessType

class ActivityBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: UUID4
    sub_category_id: UUID4
    difficulty_level: DifficultyLevel
    access_type: AccessType
    ai_guide: bool = False
    final_description: Optional[str] = None

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID4] = None
    sub_category_id: Optional[UUID4] = None
    difficulty_level: Optional[DifficultyLevel] = None
    access_type: Optional[AccessType] = None
    ai_guide: Optional[bool] = None
    is_active: Optional[bool] = None

class ActivityResponse(ActivityBase):
    id: UUID4
    created_by: UUID4
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Activity Session schemas
class SessionStatus(str, Enum):
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    GRADED = "Graded"

class ActivitySessionBase(BaseModel):
    status: SessionStatus

class ActivitySessionCreate(ActivitySessionBase):
    pass

class ActivitySessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    submitted_at: Optional[datetime] = None
    graded_by: Optional[UUID] = None
    grade: Optional[float] = None

class ActivitySession(ActivitySessionBase):
    id: UUID
    activity_id: UUID
    user_id: UUID
    submitted_at: Optional[datetime] = None
    graded_by: Optional[UUID] = None
    grade: Optional[float] = None

    class Config:
        from_attributes = True 