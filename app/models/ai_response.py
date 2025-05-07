from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from db.base import Base

class AIResponse(Base):
    __tablename__ = "ai_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    question = Column(Text, nullable=False)
    response = Column(JSON, nullable=False)
    status = Column(String, nullable=False)  # Pending/Approved
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    student = relationship("User", back_populates="ai_responses") 