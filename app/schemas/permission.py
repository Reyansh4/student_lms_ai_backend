# app/schemas/permission.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class PermissionBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = None
    is_active: bool = True            # ← add this

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = None
    is_active: bool | None = None

class Permission(PermissionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    # is_active is inherited from PermissionBase

    class Config:
        orm_mode = True
