from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RoleAPI(Base):
    __tablename__ = "role_apis"
    __table_args__ = (UniqueConstraint("role_id", "api_name", name="uq_role_api_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    api_name: Mapped[str] = mapped_column(String(100), nullable=False)

    role: Mapped["Role"] = relationship("Role", back_populates="apis")
