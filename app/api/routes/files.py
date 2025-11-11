from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.models import User
from app.schemas import UserRead
from app.services.storage import storage_service

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/profile-picture", response_model=UserRead)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("files:profile-picture")),
    db: Session = Depends(get_db),
) -> User:
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only image uploads are supported")

    try:
        location = await storage_service.save_profile_picture(current_user.id, file)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    current_user.profile_image_url = location
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
