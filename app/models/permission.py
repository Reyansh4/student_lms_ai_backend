from sqlalchemy import Column, String, DateTime, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from db.base import Base

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan") 