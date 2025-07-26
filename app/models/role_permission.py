# app/models/role_permission.py
from sqlalchemy import Column, DateTime, UUID, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base

class RolePermission(Base):
    __tablename__ = "role_permissions"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id       = Column(UUID(as_uuid=True), ForeignKey("roles.id"),   nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=False)
    is_active     = Column(Boolean, default=True, nullable=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(),
                          onupdate=func.now(), nullable=False)

    # Relationships
    role       = relationship("Role",       back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
