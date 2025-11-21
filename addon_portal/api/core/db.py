from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .settings import settings

# Convert DSN to async-compatible format
# psycopg 3.x has built-in async support, so postgresql+psycopg:// works for async
# For SQLite, we need sqlite+aiosqlite:///
async_dsn = settings.DB_DSN
if async_dsn.startswith("sqlite:///"):
    async_dsn = async_dsn.replace("sqlite:///", "sqlite+aiosqlite:///")
# postgresql+psycopg:// already works with async in psycopg 3.x

# Create async engine
engine = create_async_engine(
    async_dsn,
    pool_pre_ping=True,
    echo=False,  # Set to True for SQL query logging
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    future=True
)

class Base(DeclarativeBase):
    """SQLAlchemy declarative base (2.0 style)"""
    pass
