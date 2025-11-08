from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl
from typing import Optional, List

class Settings(BaseSettings):
    APP_NAME: str = "Quick2Odoo"
    ENV: str = "dev"

    # Database Configuration
    # Default: SQLite for development (no server required, zero setup)
    # Production: Set DB_DSN in .env to: postgresql+psycopg2://q2o_user:password@localhost:5432/q2o
    # 
    # SQLite pros: Zero setup, perfect for development/testing
    # PostgreSQL pros: Production-grade, concurrent users, scalability, ACID compliance
    DB_DSN: str = "sqlite:///./q2o_licensing.db"

    # JWT
    JWT_ISSUER: str = "q2o-auth"
    JWT_AUDIENCE: str = "q2o-clients"
    JWT_PRIVATE_KEY: str = "CHANGE_ME_RSA_PRIV_PEM"
    JWT_PUBLIC_KEY: str = "CHANGE_ME_RSA_PUB_PEM"
    JWT_ACCESS_TTL_SECONDS: int = 900  # 15m
    JWT_REFRESH_TTL_SECONDS: int = 60 * 60 * 24 * 14  # 14d

    # Stripe
    STRIPE_SECRET_KEY: str = "sk_test_xxx"
    STRIPE_WEBHOOK_SECRET: str = "whsec_xxx"

    # Activation codes
    ACTIVATION_CODE_PEPPER: str = "CHANGE_ME_ACTIVATION_PEPPER"

    # Branding CDN (optional)
    BRANDING_CDN_BASE: Optional[AnyHttpUrl] = None

    # CORS - Allow all local development ports
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Tenant Portal
        "http://localhost:3001",  # Dashboard UI
        "http://localhost:3002",  # Admin Portal
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ]

    # Sessions + OIDC SSO for admin
    SESSION_SECRET: str = "CHANGE_ME_SESSION_SECRET"
    OIDC_ISSUER: Optional[str] = None
    OIDC_CLIENT_ID: Optional[str] = None
    OIDC_CLIENT_SECRET: Optional[str] = None
    OIDC_REDIRECT_URL: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()