from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role_name: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
