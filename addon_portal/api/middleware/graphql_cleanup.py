"""
FastAPI Middleware for GraphQL Context Cleanup

Ensures database sessions are properly closed after GraphQL requests,
even if Strawberry GraphQL doesn't call __aexit__ on the context.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from ..core.logging import get_logger

logger = get_logger(__name__)


class GraphQLContextCleanupMiddleware(BaseHTTPMiddleware):
    """
    Middleware to ensure GraphQL context database sessions are closed.
    
    This middleware runs after each request and checks if there's a GraphQL context
    in the request state that hasn't been cleaned up. If so, it ensures the database
    session is closed to prevent connection leaks.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request and ensure cleanup after response."""
        try:
            response = await call_next(request)
        finally:
            # Always run cleanup, even if the request raised an exception
            # Check if this was a GraphQL request
            if request.url.path.startswith("/graphql"):
                # Try to get the context from request state
                if hasattr(request.state, 'graphql_context'):
                    context = request.state.graphql_context
                    # Use the explicit cleanup method if available
                    if hasattr(context, 'cleanup'):
                        try:
                            await context.cleanup()
                        except Exception as e:
                            logger.warning(
                                f"Error calling explicit cleanup on GraphQL context: {e}",
                                extra={"path": request.url.path}
                            )
                    # Fallback: check if db is still active and close it
                    elif hasattr(context, 'db') and context.db is not None:
                        try:
                            # Check if session is still active
                            if hasattr(context.db, 'is_active') and context.db.is_active:
                                logger.warning(
                                    "GraphQL context session still active after request - forcing cleanup",
                                    extra={"path": request.url.path}
                                )
                                try:
                                    await context.db.rollback()
                                except Exception:
                                    pass
                                try:
                                    await context.db.close()
                                    logger.debug("GraphQL context session closed by middleware")
                                except Exception as close_error:
                                    logger.warning(
                                        f"Error closing GraphQL context session in middleware: {close_error}",
                                        extra={"path": request.url.path}
                                    )
                        except Exception as e:
                            logger.warning(
                                f"Error checking GraphQL context session in middleware: {e}",
                                extra={"path": request.url.path}
                            )
        
        return response

