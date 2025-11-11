from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.role import RoleSchema


class UserBase(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72)
    role_name: str | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_image_url: str | None = None
    role: RoleSchema | None = None


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
