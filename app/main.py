from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.api.routes import auth, dummy, files, users
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


def create_app() -> FastAPI:
    app = FastAPI(title=settings.project_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(users.router, prefix=settings.api_prefix)
    app.include_router(files.router, prefix=settings.api_prefix)
    app.include_router(dummy.router, prefix=settings.api_prefix)

    @app.on_event("startup")
    def _create_tables() -> None:
        Base.metadata.create_all(bind=engine)

    @app.get("/")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok", "app": settings.project_name}

    return app


app = create_app()
