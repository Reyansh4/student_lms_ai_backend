from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UUID, func
from sqlalchemy.orm import relationship
from db.base import Base
import uuid

class ActivityAIResponse(Base):
    __tablename__ = "activity_ai_responses"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID, ForeignKey("activity_sessions.id"), nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    question_id = Column(UUID, ForeignKey("activity_questions.id"), nullable=False)
    ai_response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    session = relationship("ActivitySession", back_populates="ai_responses")
    user = relationship("User", foreign_keys=[user_id])
    question = relationship("ActivityQuestion", back_populates="ai_responses") 