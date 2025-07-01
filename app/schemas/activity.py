from pydantic import BaseModel, UUID4, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum
from app.models.activity import DifficultyLevel, AccessType



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

# Category Schemas
class CategoryCreate(BaseModel):
    name: str
    description: str = ""

class CategoryResponse(BaseModel):
    id: UUID
    name: str
    description: str

    class Config:
        from_attributes = True

# SubCategory Schemas
class SubCategoryCreate(BaseModel):
    category_id: UUID
    name: str
    description: str = ""

class SubCategoryResponse(BaseModel):
    id: UUID
    category_id: UUID
    name: str
    description: str

    class Config:
        from_attributes = True


class ActivityBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: UUID4
    sub_category_id: UUID4
    difficulty_level: DifficultyLevel
    access_type: AccessType
    ai_guide: bool = False
    final_description: Optional[str] = None
    created_by: UUID4

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
    final_description: Optional[str] = None

class ActivityResponse(ActivityBase):
    id: UUID4
    created_by: UUID4
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # ← NEW nested fields
    category: CategoryResponse
    sub_category: SubCategoryResponse

    class Config:
        # Pydantic v2 shorthand for from_attributes
        from_attributes = True

class PaginatedActivityResponse(BaseModel):
    items: List[ActivityResponse]
    total_length: int
    skip: int
    limit: int
    has_next: bool
    has_previous: bool

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




# New schemas for extended start-activity
class ExtendedStartActivityInput(BaseModel):
    activity_id: Optional[UUID] = Field(None, description="Fetch by ID if provided")
    activity_name: Optional[str] = Field(None, description="Name to fuzzy-match")
    category_name: Optional[str] = Field(None, description="Category to fuzzy-match")
    subcategory_name: Optional[str] = Field(None, description="Subcategory to fuzzy-match")

class ExtendedStartActivityResponse(BaseModel):
    status: str = Field(..., description="'started' for direct ID, 'matched' for fuzzy results")
    final_description: Optional[str] = Field(None, description="Description from matched or fetched activity")
    suggestions: Optional[List[Dict[str, Any]]] = Field(None, description="Top-k fuzzy matches with scores")