from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from .core.settings import settings
from .core.exceptions import register_exception_handlers
from .routers import authz, licenses, billing_stripe, admin_pages, auth_sso, usage, llm_management, admin_api

app = FastAPI(title=f"{settings.APP_NAME} Licensing Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)

register_exception_handlers(app)

app.include_router(authz.router)
app.include_router(licenses.router)
app.include_router(billing_stripe.router)
app.include_router(auth_sso.router)
app.include_router(usage.router)
app.include_router(admin_pages.router)
app.include_router(llm_management.router)  # LLM Management Dashboard API
app.include_router(admin_api.router)  # Admin Portal JSON API (Tenants, Codes, Devices)

app.mount("/static", StaticFiles(directory="api/static"), name="static")
