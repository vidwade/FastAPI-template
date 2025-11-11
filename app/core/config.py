from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration driven by environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_name: str = "FastAPI Template"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./app.db"

    private_key_path: Annotated[Path, Field(default=Path("keys/private_key.pem"), description="Path to RSA private key")]
    public_key_path: Annotated[Path, Field(default=Path("keys/public_key.pem"), description="Path to RSA public key")]
    access_token_expire_minutes: int = 60
    token_algorithm: str = "RS256"

    local_upload_dir: Path = Path("uploads")
    s3_base_url: str | None = None
    s3_bucket_name: str | None = None

    mail_sender: EmailStr = "noreply@example.com"
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = False
    mailpit_host: str = "localhost"
    mailpit_port: int = 1025

    default_role_name: str = "basic_user"
    super_admin_role_name: str = "super_admin"

    @property
    def resolved_mail_host(self) -> str:
        return self.smtp_host or self.mailpit_host

    @property
    def resolved_mail_port(self) -> int:
        return self.smtp_port or self.mailpit_port

    @property
    def has_s3(self) -> bool:
        return bool(self.s3_base_url and self.s3_bucket_name)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.local_upload_dir.mkdir(parents=True, exist_ok=True)
    settings.private_key_path.parent.mkdir(parents=True, exist_ok=True)
    settings.public_key_path.parent.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()
