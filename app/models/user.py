from sqlalchemy import Boolean, Column, String, DateTime, UUID, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    phone = Column(String)
    city = Column(String)
    country = Column(String)
    prime_member = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    created_activities = relationship("Activity", back_populates="creator", foreign_keys="Activity.created_by", cascade="all, delete-orphan")
    activity_sessions = relationship("ActivitySession", back_populates="user", foreign_keys="ActivitySession.user_id", cascade="all, delete-orphan")
    graded_sessions = relationship("ActivitySession", back_populates="grader", foreign_keys="ActivitySession.graded_by", cascade="all, delete-orphan")
    activity_ai_responses = relationship("ActivityAIResponse", back_populates="user", foreign_keys="ActivityAIResponse.user_id", cascade="all, delete-orphan")
    