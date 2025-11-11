from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleAPISchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    api_name: str


class RoleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    is_superuser: bool
    created_at: datetime
    apis: list[RoleAPISchema] = Field(default_factory=list)


class RoleCreate(BaseModel):
    name: str
    description: str | None = None
    api_names: list[str] = Field(default_factory=list)
    is_superuser: bool = False
