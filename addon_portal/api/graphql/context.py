"""
GraphQL Context Builder

Provides database session, dataloaders, and user info to each GraphQL request.
"""
from typing import Optional
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import BaseContext

from .dataloaders import create_dataloaders
from ..core.db import AsyncSessionLocal
from ..core.logging import get_logger

logger = get_logger(__name__)


class GraphQLContext(BaseContext):
    """
    Context object passed to all GraphQL resolvers
    
    Contains:
    - db: Database session (async)
    - dataloaders: Batch/cache loaders for performance
    - user: Authenticated user (if any)
    - request: Original FastAPI request
    """
    
    def __init__(
        self,
        db: AsyncSession,
        request: Request,
        user: Optional[dict] = None
    ):
        super().__init__()
        self.db = db
        self.request = request
        self.user = user
        
        # Create DataLoaders (per-request caching)
        self.dataloaders = create_dataloaders(db)
    
    def __getitem__(self, key: str):
        """Allow dict-style access for DataLoaders"""
        if key == "db":
            return self.db
        elif key == "request":
            return self.request
        elif key == "user":
            return self.user
        else:
            return self.dataloaders.get(key)


async def get_graphql_context(
    request: Request = None,
) -> GraphQLContext:
    """
    Context factory for GraphQL requests
    
    Creates a new context for each request with:
    - Fresh async database session
    - Request-scoped DataLoaders
    - User authentication (from JWT if present)
    
    Note: For WebSocket subscriptions, request might be None or have different structure
    """
    # Create async database session
    db = AsyncSessionLocal()
    
    try:
        # Extract user from JWT token (optional)
        user = None
        if request:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # In production, decode JWT and extract user
                # from ..core.auth import decode_jwt
                # token = auth_header.split(" ")[1]
                # user = decode_jwt(token)
                pass
        
        # Create context
        context = GraphQLContext(
            db=db,
            request=request,
            user=user
        )
        
        if request:
            logger.debug(f"Created GraphQL context for request: {request.url.path}")
        else:
            logger.debug("Created GraphQL context for WebSocket/subscription")
        
        return context
    
    except Exception as e:
        logger.error(f"Error creating GraphQL context: {e}", exc_info=True)
        try:
            await db.close()
        except Exception:
            pass
        raise

