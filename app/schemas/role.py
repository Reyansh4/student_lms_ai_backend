from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

class RoleCreate(RoleBase):
    permissions: List[UUID]

class Role(RoleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RolePermissionCreate(BaseModel):
    role_id: UUID
    permission_id: UUID 