from sqlalchemy import Column, String, DateTime, ForeignKey, UUID, func
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime

class ActivityChat(Base):
    __tablename__ = "activity_chats"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID, ForeignKey("conversations.id"), nullable=False)
    activity_id = Column(UUID, ForeignKey("activity.id"), nullable=False)
    chat_type = Column(String(50))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="activity_chats")
    activity = relationship("Activity", back_populates="activity_chats") 