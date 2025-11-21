# CRITICAL: Import event loop fix FIRST, before any other imports
# This must happen before uvicorn creates the event loop
from . import _event_loop_fix  # noqa: F401, E402

import sys
import asyncio
from contextlib import asynccontextmanager
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

# GraphQL router (optional - only if strawberry is installed)
try:
    from .graphql import router as graphql_router
    GRAPHQL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"GraphQL not available: {e}. Install strawberry-graphql to enable GraphQL API.")
    graphql_router = None
    GRAPHQL_AVAILABLE = False

logger.info("Starting Q2O Licensing API...")

# Background task for periodic cleanup of stuck projects
async def periodic_cleanup_task():
    """Background task that runs cleanup every hour."""
    from .services.project_execution_service import cleanup_stuck_projects
    
    while True:
        try:
            await asyncio.sleep(3600)  # Wait 1 hour
            logger.info("Running periodic cleanup of stuck projects...")
            await cleanup_stuck_projects()
        except Exception as e:
            logger.error(f"Error in periodic cleanup task: {e}", exc_info=True)
            # Continue running even if cleanup fails
            await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Application startup: Starting background tasks...")
    
    # Start periodic cleanup task (runs every hour, NOT on startup)
    cleanup_task = asyncio.create_task(periodic_cleanup_task())
    logger.info("✓ Periodic cleanup task scheduled (runs every hour)")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown: Cancelling background tasks...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("✓ Background tasks cancelled")


# Create base FastAPI app with lifespan
base_app = FastAPI(
    title=f"{settings.APP_NAME} Licensing Service",
    lifespan=lifespan
)

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

# GraphQL API (only if strawberry is installed)
if GRAPHQL_AVAILABLE and graphql_router:
    base_app.include_router(graphql_router)  # GraphQL API for Multi-Agent Dashboard & Status Page
    logger.info("✓ GraphQL API enabled at /graphql")
else:
    logger.warning("⚠ GraphQL API disabled - install strawberry-graphql to enable")

# Mount static files directory if it exists
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    base_app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"✓ Static files mounted at /static from {static_dir}")
else:
    logger.debug(f"Static directory not found at {static_dir}, skipping static file mounting")

# Wrap with ASGI middleware for OPTIONS handling (runs before everything, at ASGI level)
logger.info("Registering CORSOptionsMiddleware as ASGI middleware...")
app = CORSOptionsMiddleware(base_app)
logger.info("CORSOptionsMiddleware registered successfully")
