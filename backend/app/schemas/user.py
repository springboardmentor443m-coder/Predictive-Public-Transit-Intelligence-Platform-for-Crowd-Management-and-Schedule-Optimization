from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    full_name: str
    role: str = "viewer"


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserSelfRegister(BaseModel):
    """Public sign-up payload — deliberately excludes role (always viewer)."""
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserRead(UserBase):
    id: str
    is_active: bool
    created_at: datetime
