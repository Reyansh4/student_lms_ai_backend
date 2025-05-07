from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UUID, func
from sqlalchemy.orm import relationship
from db.base import Base
import uuid

class ActivityQuestion(Base):
    __tablename__ = "activity_questions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    activity_id = Column(UUID, ForeignKey("activities.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    solution_steps = Column(Text)
    answer = Column(String(500))
    ai_hint = Column(Text)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    activity = relationship("Activity", back_populates="questions")
    ai_responses = relationship("ActivityAIResponse", back_populates="question") 