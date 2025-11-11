from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, require_permission
from app.models import User
from app.schemas import RoleSchema, UserRead
from app.db.session import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Role

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/roles", response_model=list[RoleSchema])
async def list_roles(
    _: User = Depends(require_permission("admin:roles")),
    db: Session = Depends(get_db),
) -> list[Role]:
    roles = db.scalars(select(Role)).all()
    return roles
