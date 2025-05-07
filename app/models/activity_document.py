from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON, UUID, func
from sqlalchemy.orm import relationship
from db.base import Base
import uuid
import enum

class FileType(enum.Enum):
    CSV = "csv"
    PDF = "pdf"
    TEXT = "text"
    TEXTBOX = "textbox"
    IMAGE = "image"

class ActivityDocument(Base):
    __tablename__ = "activity_documents"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    activity_id = Column(UUID, ForeignKey("activity.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    description = Column(String(500))
    file_metadata = Column(JSON)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    activity = relationship("Activity", back_populates="documents") 