from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: UUID
    prime_member: bool
    is_active: bool
    is_available: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 