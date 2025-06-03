from pydantic import BaseModel, EmailStr
from typing import Optional
from .base import TimestampModel
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: EmailStr
    phone_number: str
    full_name: Optional[str] = None
    is_active: bool = True
    preferred_currency: str = "USD"


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDBBase(UserBase, TimestampModel):
    id: int
    role_id: Optional[int] = None


class UserInDB(UserInDBBase):
    hashed_password: str


class User(UserInDBBase):
    pass


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    phone_number: str
    is_active: bool
    created_at: datetime
    preferred_currency: Optional[str] = None

    class Config:
        from_attributes = True
