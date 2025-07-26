# app/models/role.py
from sqlalchemy import Column, String, DateTime, UUID, Boolean, func
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base

class Role(Base):
    __tablename__ = "roles"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name        = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    is_active   = Column(Boolean, default=True, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(),
                         onupdate=func.now(), nullable=False)

    # Join-table relationship
    role_permissions = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    # Direct many-to-many:
    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        viewonly=True,
    )

    # Relationship to UserRole
    user_roles = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan",
    )
