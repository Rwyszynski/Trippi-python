from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserSummary(BaseModel):
    id: UUID
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_picture: Optional[str] = None

    class Config:
        from_attributes = True