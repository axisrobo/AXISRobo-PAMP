"""FastAPI application entry point."""
from app.config import settings
import logging
from app.utils.logging import setup_logging
setup_logging()

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth.middleware import AuthMiddleware
from app.utils.response_envelope import ResponseEnvelopeMiddleware, envelope_response
from app.database import run_migrations

# Infrastructure
from app import health

# Module A/B/C/D: Domain sub-modules
from app.module_registry import (
    parse_enabled_modules,
    iter_enabled_module_registrations,
)

# Module C: Auth & Users
from app.auth import api as auth
from app.ai_assessment import routes as ai_assessment
from app.ai_model_registry import routes as ai_model_registry
from app.user_management import users as user_management


from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.ee.cmdb.sync import sync_cmdb_applications

# Scheduler initialization
scheduler = AsyncIOScheduler()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    await run_migrations()

    enabled_modules = parse_enabled_modules(settings.ENABLED_MODULES)
    should_enable_cmdb_sync = settings.EE_ENABLED and settings.ENABLE_CMDB_SYNC and "application_management" in enabled_modules

    if should_enable_cmdb_sync:
        scheduler.add_job(sync_cmdb_applications, 'cron', hour=2, minute=0, timezone='Asia/Shanghai')
        scheduler.start()
        logger.info("Scheduler started, CMDB sync scheduled daily at 02:00 AM")
    else:
        logger.info("CMDB sync scheduler disabled (EE_ENABLED=%s)", settings.EE_ENABLED)
    # Initialize plugin registry
    from app.plugins import plugin_registry
    from app.config import settings as _cfg
    if _cfg.CMDB_API_URL:
        logger.info("Plugin: CMDB sync configured")
    if _cfg.EMAIL_SERVICE_URL:
        logger.info("Plugin: Email service configured")
    if _cfg.S3_ENDPOINT:
        logger.info("Plugin: S3 storage configured")

    # Wire concrete provider implementations
    from app.config import settings as _cfg2

    # Auth provider registration
    if _cfg2.AUTH_MODE == "dev" or _cfg2.AUTH_DISABLED:
        from app.auth.providers import DevAuthProvider
        plugin_registry.register("auth", DevAuthProvider(_cfg2))
        logger.info("Plugin: auth -> DevAuthProvider (dev mode)")
    elif _cfg2.AUTH_MODE == "local":
        from app.auth.providers import LocalAuthProvider
        plugin_registry.register("auth", LocalAuthProvider(_cfg2))
        logger.info("Plugin: auth -> LocalAuthProvider (local mode)")
    elif _cfg2.AUTH_MODE == "oidc" and _cfg2.EE_ENABLED and _cfg2.KEYCLOAK_SERVER_URL:
        from app.ee.auth.keycloak_provider import KeycloakAuthProvider
        plugin_registry.register("auth", KeycloakAuthProvider(_cfg2))
        logger.info("Plugin: auth -> KeycloakAuthProvider (EE)")
    else:
        from app.auth.providers import DevAuthProvider
        plugin_registry.register("auth", DevAuthProvider(_cfg2))
        logger.info("Plugin: auth -> DevAuthProvider (OSS fallback)")

    # Storage provider registration
    if _cfg2.S3_ENDPOINT:
        from app.utils.s3_storage import S3Storage
        plugin_registry.register("storage", S3Storage(_cfg2))
        logger.info("Plugin: storage -> S3Storage")

    # Email provider registration
    from app.utils.email_service import create_email_provider
    plugin_registry.register("email", create_email_provider())
    logger.info("Plugin: email -> configured provider")

    try:
        yield
    finally:
        # Shutdown logic
        if scheduler.running:
            scheduler.shutdown()

app = FastAPI(title="AxisArch API", version="2.0.0", lifespan=lifespan)

logger = logging.getLogger("eam.api")

# Middleware — order matters: CORS first, then Auth
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)
app.add_middleware(ResponseEnvelopeMiddleware)


# ---------------------------------------------------------------------------
# Global exception handlers (JSON envelope)
# ---------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Keep explicit details for 4xx; mask 5xx.
    message = str(exc.detail) if exc.status_code < 500 else None
    return envelope_response(status_code=exc.status_code, message=message, data=None)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Map FastAPI's default 422 to 400.
    return envelope_response(
        status_code=400,
        message="Invalid request parameters",
        data={"errors": exc.errors()},
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Handles 404 / 405 that may not become FastAPI's HTTPException.
    message = str(getattr(exc, "detail", "")) if exc.status_code < 500 else None
    return envelope_response(status_code=exc.status_code, message=message or None, data=None)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s", request.method, request.url.path, exc_info=True)
    return envelope_response(status_code=500, message=None, data=None)

# Register routers
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(ai_assessment.router, prefix="/api/ai-assessment", tags=["AI Assessment"])
app.include_router(ai_model_registry.router, prefix="/api/ai-models", tags=["AI Model Registry"])
app.include_router(user_management.router, prefix="/api/users", tags=["Users"])

enabled_modules = parse_enabled_modules(settings.ENABLED_MODULES)
enabled_module_registrations = iter_enabled_module_registrations(enabled_modules)
known_module_keys = {module.key for module in enabled_module_registrations}
unknown_module_keys = sorted(enabled_modules - known_module_keys)
if unknown_module_keys:
    logger.warning("Unknown module keys in ENABLED_MODULES (ignored): %s", unknown_module_keys)
for module in enabled_module_registrations:
    app.include_router(module.router, prefix=module.prefix)

logger.info("Enabled API modules: %s", sorted(enabled_modules))


if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
