from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, UUID, func
from sqlalchemy.orm import relationship
from db.base import Base
import uuid
import enum

class SessionStatus(enum.Enum):
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    GRADED = "Graded"

class ActivitySession(Base):
    __tablename__ = "activity_sessions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    activity_id = Column(UUID, ForeignKey("activity.id"), nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(SessionStatus), nullable=False)
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    graded_at = Column(DateTime)
    graded_by = Column(UUID, ForeignKey("users.id"))
    grade = Column(String(2))
    feedback = Column(String(500))

    # Relationships
    activity = relationship("Activity", back_populates="sessions")
    user = relationship("User", foreign_keys=[user_id])
    grader = relationship("User", foreign_keys=[graded_by])
    ai_responses = relationship("ActivityAIResponse", back_populates="session") 