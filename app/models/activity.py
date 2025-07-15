from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum, UUID, func, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
import enum

class DifficultyLevel(enum.Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"

class AccessType(enum.Enum):
    PRIVATE = "private"
    GLOBAL = "global"

class ActivityStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DEACTIVE = "deactive"

class Activity(Base):
    __tablename__ = "activity"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category_id = Column(UUID, ForeignKey("activity_categories.id"), nullable=False)
    sub_category_id = Column(UUID, ForeignKey("activity_sub_categories.id"), nullable=False)
    difficulty_level = Column(Enum(DifficultyLevel), nullable=False)
    access_type = Column(Enum(AccessType), nullable=False)
    created_by = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ai_guide = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    status = Column(String(20), nullable=False, default=ActivityStatus.PENDING.value)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    final_description = Column(Text)
    clarification_questions = Column(JSON)

    # Relationships
    category = relationship("ActivityCategory", back_populates="activities")
    sub_category = relationship("ActivitySubCategory", back_populates="activities")
    creator = relationship("User", foreign_keys=[created_by])
    questions = relationship("ActivityQuestion", back_populates="activity")
    sessions = relationship("ActivitySession", back_populates="activity")
    documents = relationship("ActivityDocument", back_populates="activity")
    # Add new document relationships for RAG system
    rag_documents = relationship("Document", back_populates="activity")
    document_chat_sessions = relationship("DocumentChatSession", back_populates="activity") 