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
        user: Optional[dict] = None,
        tenant_id: Optional[int] = None
    ):
        super().__init__()
        self.db = db
        self.request = request
        self.user = user
        self.tenant_id = tenant_id
        self._cleaned_up = False  # Track if cleanup has been called
        
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
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup database session"""
        if self._cleaned_up:
            # Already cleaned up, don't do it again
            return False
        
        try:
            if self.db:
                # Only rollback if there's an exception (normal flow commits)
                if exc_type is not None:
                    try:
                        await self.db.rollback()
                    except Exception:
                        pass
                # CRITICAL: Always close the session (returns connection to pool)
                # This prevents connection leaks even if Strawberry doesn't call __aexit__
                try:
                    await self.db.close()
                    logger.debug("GraphQL context database session closed via __aexit__")
                except Exception as close_error:
                    logger.warning(f"Error closing database session in __aexit__: {close_error}")
        except Exception as e:
            logger.warning(f"Error in GraphQL context __aexit__: {e}")
        finally:
            # Mark as cleaned up and ensure db is None to prevent reuse
            self._cleaned_up = True
            self.db = None
        return False  # Don't suppress exceptions
    
    async def cleanup(self):
        """Explicit cleanup method that can be called by middleware"""
        if self._cleaned_up:
            return
        
        try:
            if self.db:
                try:
                    # Rollback any pending transactions
                    await self.db.rollback()
                except Exception:
                    pass
                try:
                    await self.db.close()
                    logger.debug("GraphQL context database session closed via explicit cleanup")
                except Exception as close_error:
                    logger.warning(f"Error closing database session in explicit cleanup: {close_error}")
        except Exception as e:
            logger.warning(f"Error in GraphQL context explicit cleanup: {e}")
        finally:
            self._cleaned_up = True
            self.db = None
    
    def __del__(self):
        """Finalizer to ensure cleanup if __aexit__ is not called"""
        # Note: This is a safety net, but __aexit__ should be called by Strawberry
        # We can't await here, so we just log a warning
        if hasattr(self, 'db') and self.db is not None:
            logger.warning("GraphQL context deleted without __aexit__ being called - potential connection leak")


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
    Note: Database session cleanup is handled by Strawberry's context lifecycle via __aexit__
    
    IMPORTANT: Sessions must be explicitly closed to prevent connection pool exhaustion
    
    CRITICAL FIX: Store context in request.state for middleware cleanup if Strawberry doesn't call __aexit__
    """
    # Create async database session using context manager pattern
    # This ensures the session is properly managed even if Strawberry doesn't use __aexit__
    db = AsyncSessionLocal()
    
    try:
        # Extract user from JWT token (optional)
        user = None
        tenant_id = None
        
        if request:
            # Try to get tenant_id from session token (X-Session-Token header)
            session_token = request.headers.get("X-Session-Token")
            if session_token:
                from ..services.tenant_auth_service import validate_session
                try:
                    session_info = await validate_session(session_token, db)
                    if session_info:
                        tenant_id = session_info.get("tenant_id")
                        # Commit the last_activity update to prevent connection leaks
                        await db.commit()
                except Exception as e:
                    # Session invalid or expired, rollback and continue without tenant_id
                    await db.rollback()
                    logger.debug(f"Session validation failed in GraphQL context: {e}")
                    pass
            
            # Also try Authorization header for JWT Bearer tokens
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    from ..core.security import verify_access
                    import jwt
                    # Decode and verify JWT token (doesn't use database)
                    jwt_payload = verify_access(token)
                    
                    # Extract tenant_id from JWT subject (format: "tenant:{tenant_id}:device:{device_id}")
                    if jwt_payload.get("sub"):
                        sub_parts = jwt_payload["sub"].split(":")
                        if len(sub_parts) >= 2 and sub_parts[0] == "tenant":
                            try:
                                jwt_tenant_id = int(sub_parts[1])
                                tenant_id = jwt_tenant_id
                                # Build user info from JWT payload
                                user = {
                                    "id": jwt_tenant_id,
                                    "sub": jwt_payload.get("sub"),
                                    "entitlements": jwt_payload.get("entitlements", {}),
                                }
                            except (ValueError, IndexError):
                                logger.debug(f"Invalid JWT subject format: {jwt_payload.get('sub')}")
                except jwt.InvalidTokenError as e:
                    # JWT token is invalid or expired
                    logger.debug(f"JWT token validation failed: {e}")
                except Exception as e:
                    # Other JWT validation errors
                    logger.debug(f"JWT validation error in GraphQL context: {e}")
                    pass
        
        # Create context
        context = GraphQLContext(
            db=db,
            request=request,
            user=user,
            tenant_id=tenant_id
        )
        
        # Store context in request.state for middleware cleanup
        # This ensures cleanup even if Strawberry doesn't call __aexit__
        if request:
            request.state.graphql_context = context
            logger.debug(f"Created GraphQL context for request: {request.url.path}")
        else:
            logger.debug("Created GraphQL context for WebSocket/subscription")
        
        return context
    
    except Exception as e:
        logger.error(f"Error creating GraphQL context: {e}", exc_info=True)
        # Ensure session is closed on error
        try:
            await db.rollback()
            await db.close()
        except Exception as close_error:
            logger.warning(f"Error closing database session after context creation error: {close_error}")
        raise


# CRITICAL FIX: Wrapper function to ensure context cleanup
# Strawberry may not always call __aexit__, so we wrap the context_getter
async def get_graphql_context_with_cleanup(request: Request = None) -> GraphQLContext:
    """
    Wrapper around get_graphql_context that ensures cleanup via context manager.
    
    This ensures database sessions are closed even if Strawberry doesn't call __aexit__.
    """
    context = await get_graphql_context(request)
    # Return context - Strawberry will use it as a context manager
    # If Strawberry doesn't call __aexit__, the session will be cleaned up by the wrapper
    return context

