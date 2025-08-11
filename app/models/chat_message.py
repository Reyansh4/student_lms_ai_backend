from sqlalchemy import Column, String, DateTime, ForeignKey, UUID, Text, JSON, func
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID, ForeignKey("conversations.id"), nullable=False)
    session_id = Column(String, nullable=False)  # From EnhancedMemoryStore
    activity_id = Column(UUID, ForeignKey("activity.id"), nullable=True)  # Optional activity context
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    intent = Column(String(50))  # "learning-support", "create-activity", etc.
    topic = Column(String(100))  # "chemistry", "mathematics", etc.
    message_metadata = Column(JSON)  # Additional data like embeddings, confidence
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="chat_messages")
    user = relationship("User", back_populates="chat_messages")
    activity = relationship("Activity", back_populates="chat_messages") 