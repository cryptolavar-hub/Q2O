from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl
from typing import Optional, List
from pathlib import Path

# .env file is located at project root: C:\Q2O_Combined\.env
# Using explicit path to ensure it's always found
ENV_FILE_PATH = Path(r'C:\Q2O_Combined\.env')

class Settings(BaseSettings):
    APP_NAME: str = "Q2O"
    ENV: str = "dev"

    # Database Configuration
    # Default: SQLite for development (no server required, zero setup)
    # Production: Set DB_DSN in .env to: postgresql+psycopg://q2o_user:password@localhost:5432/q2o
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

    # CORS - Allow all local development ports (IPv4 and IPv6)
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Tenant Portal
        "http://localhost:3001",  # Dashboard UI
        "http://localhost:3002",  # Admin Portal
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://[::1]:3000",  # IPv6 localhost
        "http://[::1]:3001",
        "http://[::1]:3002",
    ]

    # Sessions + OIDC SSO for admin
    SESSION_SECRET: str = "CHANGE_ME_SESSION_SECRET"
    OIDC_ISSUER: Optional[str] = None
    OIDC_CLIENT_ID: Optional[str] = None
    OIDC_CLIENT_SECRET: Optional[str] = None
    OIDC_REDIRECT_URL: Optional[str] = None

    # Logging Configuration
    LOG_ENABLED: bool = True  # Set to False to disable all logging
    LOG_LEVEL: str = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Timezone Configuration
    # Format: "UTC-5", "UTC+3", "America/New_York", "Europe/London", etc.
    # Used for date calculations in dashboards and analytics
    # Default: UTC (no offset)
    TIME_ZONE: str = "UTC"  # Server timezone for date calculations

    # LLM System Prompt (managed via LLM Management service, synced to .env)
    LLM_SYSTEM_PROMPT: Optional[str] = None

    # Email/SMS Configuration for OTP Delivery
    # SMTP Configuration (for email OTP delivery)
    SMTP_ENABLED: bool = False  # Set to True to enable email OTP delivery
    SMTP_HOST: Optional[str] = None  # e.g., smtp.gmail.com
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None  # e.g., noreply@q2o.com
    SMTP_FROM_NAME: str = "Q2O Platform"
    SMTP_USE_TLS: bool = True

    # SMS Configuration (for SMS/WhatsApp OTP delivery)
    # TODO: Integrate with Twilio, AWS SNS, or similar service
    SMS_ENABLED: bool = False
    SMS_PROVIDER: Optional[str] = None  # 'twilio', 'aws_sns', etc.
    SMS_API_KEY: Optional[str] = None
    SMS_API_SECRET: Optional[str] = None
    SMS_FROM_NUMBER: Optional[str] = None

    # .env file is located at: C:\Q2O_Combined\.env
    # Using explicit path to ensure it's always found
    model_config = SettingsConfigDict(env_file=str(ENV_FILE_PATH), extra="ignore")

settings = Settings()