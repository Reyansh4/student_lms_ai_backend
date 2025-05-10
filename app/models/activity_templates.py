import uuid
from sqlalchemy import Column, String, Text, ForeignKey, Enum, UUID
from app.db.base import Base
import enum

class DifficultyLevel(enum.Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"

class AccessType(enum.Enum):
    PRIVATE = "private"
    GLOBAL = "global"

class ActivityTemplate(Base):
    __tablename__ = "activity_templates"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category_id = Column(UUID, ForeignKey("activity_categories.id"), nullable=False)
    sub_category_id = Column(UUID, ForeignKey("activity_sub_categories.id"), nullable=False)
    difficulty_level = Column(Enum(DifficultyLevel), nullable=False)
    access_type = Column(Enum(AccessType), nullable=False)
    final_description = Column(Text)
    #created_by = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


