from sqlalchemy import Column, String, Text, DateTime, UUID, ForeignKey, Integer, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import uuid

class ActivityQuestion(Base):
    __tablename__ = "activity_questions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    activity_id = Column(UUID, ForeignKey("activity.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    solution_steps = Column(Text)
    answer = Column(String(500))
    ai_hint = Column(Text)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    activity = relationship("Activity", back_populates="questions")
    ai_responses = relationship("ActivityAIResponse", back_populates="question") 