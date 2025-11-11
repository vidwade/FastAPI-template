from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import decode_token
from app.db.session import get_db
from app.models import Role, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


async def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")

    try:
        payload = decode_token(token)
    except Exception as exc:  # pragma: no cover - jwt raises various subclasses
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload") from exc

    statement = (
        select(User)
        .options(joinedload(User.role).joinedload(Role.apis))
        .where(User.id == user_id_int)
    )
    user = db.scalars(statement).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")

    return user


def require_permission(api_name: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        role = user.role
        if not role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no role assigned")
        if role.is_superuser:
            return user
        if any(api.api_name == api_name for api in role.apis):
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not permitted to access this resource")

    return dependency
