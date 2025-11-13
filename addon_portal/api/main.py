from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from .core.settings import settings
from .core.exceptions import register_exception_handlers
from .core.logging import configure_logging, get_logger
from .middleware.cors_options import CORSOptionsMiddleware
from .routers import authz, licenses, billing_stripe, admin_pages, auth_sso, usage, llm_management, admin_api, tenant_api

# Configure logging first
configure_logging()
logger = get_logger(__name__)
logger.info("Starting Q2O Licensing API...")

# Create base FastAPI app
base_app = FastAPI(title=f"{settings.APP_NAME} Licensing Service")

# CORS middleware for actual requests
base_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

base_app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)

register_exception_handlers(base_app)

base_app.include_router(authz.router)
base_app.include_router(licenses.router)
base_app.include_router(billing_stripe.router)
base_app.include_router(auth_sso.router)
base_app.include_router(usage.router)
base_app.include_router(admin_pages.router)
base_app.include_router(llm_management.router)  # LLM Management Dashboard API
base_app.include_router(admin_api.router)  # Admin Portal JSON API (Tenants, Codes, Devices)
base_app.include_router(tenant_api.router)  # Tenant API (Authentication & Project Management)

base_app.mount("/static", StaticFiles(directory="api/static"), name="static")

# Wrap with ASGI middleware for OPTIONS handling (runs before everything, at ASGI level)
logger.info("Registering CORSOptionsMiddleware as ASGI middleware...")
app = CORSOptionsMiddleware(base_app)
logger.info("CORSOptionsMiddleware registered successfully")
