"""Application settings."""
from __future__ import annotations

from pathlib import Path
import logging


from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/axisarch"
    DB_SCHEMA: str = "eam"
    PORT: int = 4000
    HOST: str = "0.0.0.0"
    # Comma-separated module keys to enable at runtime.
    # Supported keys: add, architecture_review, application_management,
    # data_management, project_management, technology_stack_management
    ENABLED_MODULES: str = (
        "add,architecture_review,application_management,"
        "data_management,project_management,technology_stack_management"
    )
    ENABLE_CMDB_SYNC: bool = False

    # CORS configuration
    CORS_ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    # Enterprise Edition configuration
    EE_ENABLED: bool = False  # Set to true to enable EE features (RBAC, audit, ownership, Keycloak, CMDB sync, Agent Watch)

    # Auth configuration
    # SECURITY: defaults to False (auth enabled).  Set AUTH_DISABLED=true in
    # your .env ONLY for local development.  Never disable in production.
    AUTH_DISABLED: bool = True
    AUTH_DEV_USER: str = "dev_admin"  # Dev mode: fixed username (itcode)
    AUTH_DEV_ROLE: str = "admin"  # Dev mode: fixed role

    # Auth mode: dev (fixed user), local (username/password + JWT), oidc (Keycloak SSO, EE only)
    AUTH_MODE: str = "dev"  # dev | local | oidc

    # Local auth JWT configuration (used when AUTH_MODE=local)
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 480  # 8 hours

    # Keycloak configuration (used when AUTH_DISABLED=False)
    KEYCLOAK_SERVER_URL: str = ""
    KEYCLOAK_REALM: str = "myapp"
    KEYCLOAK_CLIENT_ID: str = ""
    KEYCLOAK_CLIENT_SECRET: str = ""
    KEYCLOAK_ALGORITHMS: str = "RS256"

    # File upload configuration — S3-compatible object storage
    S3_ENDPOINT: str = ""
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = ""
    S3_PREFIX: str = "axisarch/app"  # Key prefix for uploaded files

    # EA agent configuration
    EA_AGENT_LLM_BASE_URL: str = ""
    EA_AGENT_LLM_API_KEY: str = ""
    EA_AGENT_LLM_MODEL: str = ""
    EA_AGENT_VISION_MODEL: str = ""
    EA_AGENT_LLM_TIMEOUT_SECONDS: int = 180
    EA_AGENT_LLM_MAX_RETRIES: int = 1
    EA_AGENT_APP_ARCH_RULE_NAME: str = "New_App"
    EA_AGENT_CONCURRENCY_LIMIT: int = 2

    # Agent Watch configuration
    AGENT_WATCH_ENABLED: bool = False
    AGENT_WATCH_APPLICATION_NAME: str = "AxisArch Review Assistant"
    AGENT_WATCH_CHATBOT_NAME: str = "AxisArch Review Assistant"
    AGENT_WATCH_TOKEN: str = ""
    AGENT_WATCH_COLLECTOR_URL: str = ""
    AGENT_WATCH_APIH_TOKEN_URL: str = ""
    AGENT_WATCH_APIH_ACCOUNT: str = ""
    AGENT_WATCH_APIH_KEY: str = ""
    AGENT_WATCH_APIH_SECRET: str = ""

    # Email notification service
    EMAIL_SERVICE_URL: str = ""
    EMAIL_FROM: str = "noreply@axisarch.local"
    EMAIL_DOMAIN: str = ""  # Domain suffix for itcode -> email
    EMAIL_DEFAULT_CC: str = ""

    # CMDB synchronization configuration
    CMDB_API_URL: str = ""
    CMDB_API_TOKEN: str = ""

    # Site URL (used in email links)
    SITE_URL: str = "http://localhost:3000"  # Site URL for email links

    # BCT direct email service (preferred over EMAIL_SERVICE_URL when configured)
    BCT_MS_URL: str = ""
    BCT_TOKEN_URL: str = ""
    BCT_APP_CODE: str = ""
    BCT_SDK_KEY: str = ""  # Base64-encoded PKCS8 RSA private key
    LOG_LEVEL: str = "DEBUG"  # Log output level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    DB_ECHO: bool = False  # Enable SQLAlchemy statement logging (dev only)

    class Config:
        # Prefer backend/.env so local dev works even when uvicorn is started
        # from the repo root (e.g. `--app-dir backend`). Fall back to root .env.
        _backend_env = Path(__file__).resolve().parents[1] / ".env"  # backend/.env
        _root_env = Path(__file__).resolve().parents[2] / ".env"  # repo root .env
        env_file = str(_backend_env) if _backend_env.exists() else str(_root_env)

settings = Settings()
