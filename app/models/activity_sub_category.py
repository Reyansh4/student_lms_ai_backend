from sqlalchemy import Column, String, DateTime, ForeignKey, UUID, func
from sqlalchemy.orm import relationship
from db.base import Base
import uuid

class ActivitySubCategory(Base):
    __tablename__ = "activity_sub_categories"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID, ForeignKey("activity_categories.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    category = relationship("ActivityCategory", back_populates="sub_categories")
    activities = relationship("Activity", back_populates="sub_category") 