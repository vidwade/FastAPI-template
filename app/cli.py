from __future__ import annotations

import getpass
from pathlib import Path
from typing import Iterable

import typer
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import MAX_PASSWORD_BYTES, hash_password, reset_key_cache
from app.db import Base
from app.db.session import SessionLocal, engine
from app.models import Role, RoleAPI, User

cli = typer.Typer(help="Utility commands for the FastAPI template")


@cli.command("generate-keys")
def generate_keys(
    private_key_path: Path = typer.Option(settings.private_key_path, help="Where to store the private key"),
    public_key_path: Path = typer.Option(settings.public_key_path, help="Where to store the public key"),
    overwrite: bool = typer.Option(False, help="Overwrite existing key files if they exist"),
) -> None:
    private_key_path.parent.mkdir(parents=True, exist_ok=True)
    public_key_path.parent.mkdir(parents=True, exist_ok=True)

    if not overwrite and (private_key_path.exists() or public_key_path.exists()):
        raise typer.BadParameter("Key files already exist. Use --overwrite to replace them.")

    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    private_bytes = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    private_key_path.write_bytes(private_bytes)
    public_key_path.write_bytes(public_bytes)
    reset_key_cache()
    typer.echo(f"Keys written to {private_key_path} and {public_key_path}")


def _get_or_create_role(session: Session, *, name: str, description: str, permissions: Iterable[str], is_superuser: bool = False) -> Role:
    role = session.scalars(select(Role).where(Role.name == name)).first()
    if role:
        role.description = role.description or description
        role.is_superuser = role.is_superuser or is_superuser
    else:
        role = Role(name=name, description=description, is_superuser=is_superuser)
        session.add(role)
        session.flush()

    existing_permissions = {api.api_name for api in role.apis}
    for perm in permissions:
        if perm not in existing_permissions:
            session.add(RoleAPI(role_id=role.id, api_name=perm))
    return role


@cli.command("create-super-admin")
def create_super_admin(
    username: str = typer.Option(..., prompt=True),
    email: str = typer.Option(..., prompt=True),
    first_name: str = typer.Option("System", prompt=True),
    last_name: str = typer.Option("Admin", prompt=True),
    password: str | None = typer.Option(None, prompt=False, hide_input=True),
) -> None:
    password = password or getpass.getpass("Password: ")
    if not password:
        raise typer.BadParameter("Password cannot be empty")
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise typer.BadParameter(f"Password cannot exceed {MAX_PASSWORD_BYTES} bytes due to bcrypt limitations.")

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        existing = session.scalars(select(User).where(or_(User.username == username, User.email == email))).first()
        if existing:
            raise typer.BadParameter("A user with that username or email already exists")

        role = _get_or_create_role(
            session,
            name=settings.super_admin_role_name,
            description="Super administrator with full access",
            permissions=["*"],
            is_superuser=True,
        )

        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hash_password(password),
            role=role,
        )
        session.add(user)
        session.commit()
    typer.echo("Super admin created successfully")


@cli.command("seed-dummy-data")
def seed_dummy_data() -> None:
    role_definitions = [
        {
            "name": settings.super_admin_role_name,
            "description": "Super admins can access everything",
            "permissions": ["*"],
            "is_superuser": True,
        },
        {
            "name": "finance_analyst",
            "description": "Finance can view finance reports",
            "permissions": ["reports:finance"],
        },
        {
            "name": "operations_manager",
            "description": "Operations can read their reports",
            "permissions": ["reports:operations"],
        },
        {
            "name": "support_agent",
            "description": "Support agents can manage tickets",
            "permissions": ["support:tickets:view", "support:tickets:create"],
        },
        {
            "name": settings.default_role_name,
            "description": "Basic user with profile upload access",
            "permissions": ["files:profile-picture"],
        },
    ]

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        for role_def in role_definitions:
            _get_or_create_role(session, **role_def)

        dummy_users = [
            {
                "username": "finance_user",
                "email": "finance@example.com",
                "first_name": "Fin",
                "last_name": "User",
                "role_name": "finance_analyst",
            },
            {
                "username": "ops_user",
                "email": "ops@example.com",
                "first_name": "Ops",
                "last_name": "User",
                "role_name": "operations_manager",
            },
            {
                "username": "support_user",
                "email": "support@example.com",
                "first_name": "Support",
                "last_name": "Agent",
                "role_name": "support_agent",
            },
            {
                "username": "basic_user",
                "email": "basic@example.com",
                "first_name": "Basic",
                "last_name": "User",
                "role_name": settings.default_role_name,
            },
        ]

        for dummy in dummy_users:
            if session.scalars(select(User).where(User.username == dummy["username"])).first():
                continue
            role = session.scalars(select(Role).where(Role.name == dummy["role_name"])).first()
            if not role:
                continue
            user = User(
                username=dummy["username"],
                email=dummy["email"],
                first_name=dummy["first_name"],
                last_name=dummy["last_name"],
                hashed_password=hash_password("ChangeMe123!"),
                role=role,
            )
            session.add(user)

        session.commit()
    typer.echo("Dummy roles and users have been created.")


if __name__ == "__main__":
    cli()
