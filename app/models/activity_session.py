from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, Enum, Text, Boolean, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import uuid
import enum

class SessionStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    GRADED = "graded"

class ActivitySession(Base):
    __tablename__ = "activity_sessions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    activity_id = Column(UUID, ForeignKey("activity.id"), nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    graded_by = Column(UUID, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(SessionStatus), default=SessionStatus.PENDING)
    score = Column(String(10), nullable=True)
    feedback = Column(Text, nullable=True)
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    graded_at = Column(DateTime, nullable=True)
    time_spent = Column(String(50), nullable=True)  # Store as string like "2h 30m"
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    activity = relationship("Activity", back_populates="sessions")
    user = relationship("User", foreign_keys=[user_id], back_populates="activity_sessions")
    grader = relationship("User", foreign_keys=[graded_by], back_populates="graded_sessions")
    # Evaluation relationships
    evaluations = relationship("EvaluationResult", back_populates="session", cascade="all, delete-orphan") 