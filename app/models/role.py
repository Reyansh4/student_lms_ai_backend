from sqlalchemy import Column, String, DateTime, UUID, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)  
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan") 