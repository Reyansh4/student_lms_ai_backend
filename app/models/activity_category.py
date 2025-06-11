from sqlalchemy import Column, String, DateTime, UUID, func
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid

class ActivityCategory(Base):
    __tablename__ = "activity_categories"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    activities = relationship("Activity", back_populates="category")
    sub_categories = relationship("ActivitySubCategory", back_populates="category") 