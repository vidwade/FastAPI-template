from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Role, RoleAPI, User
from app.schemas import LoginRequest, SignupRequest, TokenSchema, UserRead
from app.services.email import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> UserRead:
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    role_name = payload.role_name or settings.default_role_name
    role = db.scalar(select(Role).where(Role.name == role_name))
    if role is None:
        role = Role(name=role_name, description="Default role created on demand")
        db.add(role)
        db.flush()
    if role_name == settings.default_role_name and not any(api.api_name == "files:profile-picture" for api in role.apis):
        db.add(RoleAPI(role_id=role.id, api_name="files:profile-picture"))

    try:
        hashed_password = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user = User(
        username=payload.username,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        hashed_password=hashed_password,
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    try:
        await email_service.send_mail_async(
            subject="Welcome to the FastAPI template",
            recipients=[user.email],
            body=f"Hi {user.first_name}, your account has been created successfully.",
        )
    except Exception as exc:  # pragma: no cover - depends on external service
        logger.warning("Failed to send welcome email: %s", exc)

    return user


def _issue_token(user: User) -> TokenSchema:
    role = user.role
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User role missing")
    permissions = [api.api_name for api in role.apis] if not role.is_superuser else ["*"]
    token = create_access_token(subject=str(user.id), role=role.name, permissions=permissions)
    return TokenSchema(access_token=token)


def _authenticate(db: Session, identifier: str, password: str) -> User:
    statement = (
        select(User)
        .options(joinedload(User.role).joinedload(Role.apis))
        .where(or_(User.username == identifier, User.email == identifier))
    )
    user = db.scalars(statement).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user


@router.post("/login", response_model=TokenSchema)
async def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenSchema:
    user = _authenticate(db, payload.username, payload.password)
    return _issue_token(user)


@router.post("/token", response_model=TokenSchema)
async def login_with_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenSchema:
    user = _authenticate(db, form_data.username, form_data.password)
    return _issue_token(user)
