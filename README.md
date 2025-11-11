# FastAPI Template

A batteries-included FastAPI starter with asymmetric JWT auth, SQLAlchemy models, role-based access control, local/S3-aware file uploads, and Typer-powered CLI utilities for bootstrapping new projects.

## Feature Overview
- 🔐 **Asymmetric authentication** – RSA key pair (PEM) for signing/verifying JWT access tokens with configurable expiry.
- 🗂️ **Role-based access control** – Roles, per-API permissions, and FastAPI dependencies that enforce access rules.
- 🧑‍💻 **User management** – Signup (username, first/last name, email, password), login, self-profile route, and profile picture uploads.
- ☁️ **Storage + mail fallbacks** – Upload to S3 when configured, otherwise persist files under `uploads/`. SMTP is used when provided, otherwise a local Mailpit instance (`localhost:1025`).
- 🛠️ **CLI commands** – Generate RSA keys, create a super admin, and seed dummy roles/users aligned with the example APIs.
- 📦 **SQLAlchemy + Pydantic** – Clean separation of models/schemas with modern SQLAlchemy 2.0 patterns and Pydantic v2 settings.

## Getting Started
1. **Install dependencies** (via [uv](https://github.com/astral-sh/uv) or your preferred tool):
   ```bash
   uv sync
   ```
2. **Create your key pair** (once per environment):
   ```bash
   uv run python -m app.cli generate-keys
   ```
3. **Apply migrations / create tables** – tables are auto-created on startup, but you can also run any CLI command (they bootstrap the DB).
4. **Launch the API**:
   ```bash
   uv run fastapi dev app/main.py
   ```

## Environment Variables (`.env`)
| Key | Description | Default |
| --- | ----------- | ------- |
| `DATABASE_URL` | SQLAlchemy connection string (install `psycopg[binary]` for Postgres) | `sqlite:///./app.db` |
| `PRIVATE_KEY_PATH` / `PUBLIC_KEY_PATH` | Paths to RSA PEM files | `keys/private_key.pem`, `keys/public_key.pem` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry in minutes | `60` |
| `S3_BASE_URL` | Base URL for uploaded objects (e.g. `https://s3.amazonaws.com/mybucket`) | _unset_ |
| `S3_BUCKET_NAME` | Target bucket name | _unset_ |
| `LOCAL_UPLOAD_DIR` | Local fallback directory | `uploads` |
| `MAIL_SENDER` | Default `From` address | `noreply@example.com` |
| `SMTP_HOST` / `SMTP_PORT` | SMTP server details | falls back to Mailpit (`localhost:1025`) |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | Optional SMTP credentials | _unset_ |
| `SMTP_USE_TLS` | Enable `STARTTLS` when SMTP is configured | `False` |
| `MAILPIT_HOST` / `MAILPIT_PORT` | Mailpit host/port for fallback | `localhost` / `1025` |
| `DEFAULT_ROLE_NAME` | Name of the default role assigned at signup | `basic_user` |
| `SUPER_ADMIN_ROLE_NAME` | Name used for the CLI super admin role | `super_admin` |

> When `S3_BASE_URL` or `SMTP_HOST` are absent, the template automatically switches to the local filesystem or Mailpit transport respectively.

## CLI Reference
All commands run through Typer: `uv run python -m app.cli <command>`

- `generate-keys` – emit a new RSA key pair (`--overwrite` if you need to regenerate).
- `create-super-admin` – interactive prompts to provision a super admin tied to the `SUPER_ADMIN_ROLE_NAME` role.
- `seed-dummy-data` – inserts the example roles (`finance_analyst`, `operations_manager`, `support_agent`, etc.) plus matching dummy users for the sample APIs.

## Available APIs
Base prefix: `/api`

- `POST /auth/signup` – Create a user (username, first name, last name, email, password, optional role name).
- `POST /auth/login` – Obtain a RSA-signed JWT access token using a JSON payload.
- `POST /auth/token` – Same as above but accepts the standard OAuth2 password form data (used by Swagger “Authorize” button).
- `GET /users/me` – Fetch the authenticated profile.
- `GET /users/roles` – Requires `admin:roles` permission (or super admin); returns all roles.
- `POST /files/profile-picture` – Upload a profile image (roles need `files:profile-picture`).
- Dummy secured endpoints under `/dummy/...` demonstrate permission checks (`reports:finance`, `support:tickets:create`, etc.).

Attach the `Authorization: Bearer <token>` header returned by the login route to access protected endpoints.

## File Upload & Email Behavior
- **Uploads**: When `S3_BASE_URL` and `S3_BUCKET_NAME` are present, files upload via `boto3` and the URL is composed from the base URL + object key. Without S3 settings, files land under `uploads/profile-pictures/...` inside the repo.
- **Email**: If SMTP settings are missing, emails send to `MAILPIT_HOST:MAILPIT_PORT` so you can inspect them via a local Mailpit UI.

## Development Notes
- Pydantic settings auto-create the `keys/` and `uploads/` folders.
- RSA key caches refresh automatically after running the keygen CLI.
- Role permissions live in the `role_apis` table, making it easy to attach new APIs by inserting `role_id` + `api_name` rows.
- The codebase sticks to standard FastAPI dependency patterns, so swapping to async SQLAlchemy or adding Alembic migrations later is straightforward.
- bcrypt is pinned to `<4.1` because passlib's autodetection routine is incompatible with newer releases; run `uv pip install 'bcrypt>=4.0.1,<4.1'` if your environment already cached a later version.
- Bcrypt restricts passwords to 72 bytes, so the API validation and CLI enforce that upper bound to avoid hashing errors.
