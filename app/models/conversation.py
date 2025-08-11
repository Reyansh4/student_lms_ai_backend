from sqlalchemy import Column, String, DateTime, ForeignKey, UUID, func
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(String, nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    title = Column(String(200))
    conversation_type = Column(String(50), default="general")
    activity_id = Column(UUID, ForeignKey("activity.id"), nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    activity = relationship("Activity", back_populates="conversations")
    activity_chats = relationship("ActivityChat", back_populates="conversation")
    chat_messages = relationship("ChatMessage", back_populates="conversation") 