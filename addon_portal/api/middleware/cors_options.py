"""Custom ASGI middleware to handle OPTIONS requests before route matching.

This middleware intercepts OPTIONS requests at the ASGI level, before
FastAPI route matching, preventing 400 errors.
"""

from __future__ import annotations

from typing import Callable

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ..core.settings import settings
from ..core.logging import get_logger

LOGGER = get_logger(__name__)


class CORSOptionsMiddleware:
    """ASGI middleware to handle OPTIONS requests before route matching."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Only handle HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Intercept OPTIONS requests immediately at ASGI level
        if scope["method"] == "OPTIONS":
            origin = None
            # Extract origin from headers
            for header_name, header_value in scope.get("headers", []):
                if header_name == b"origin":
                    origin = header_value.decode("utf-8")
                    break

            path = scope.get("path", "")
            LOGGER.info(f"[CORSOptionsMiddleware] OPTIONS request intercepted at ASGI level for {path}, origin: {origin}")
            LOGGER.debug(f"[CORSOptionsMiddleware] Allowed origins: {settings.ALLOWED_ORIGINS}")

            # Check if origin is allowed - must match exactly
            allowed_origin = None
            if origin:
                # First, check if it's localhost - allow any localhost port for development
                if origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:") or origin.startswith("http://[::1]:"):
                    allowed_origin = origin
                    LOGGER.info(f"[CORSOptionsMiddleware] Allowing localhost origin: {origin}")
                # Try exact match
                elif origin in settings.ALLOWED_ORIGINS:
                    allowed_origin = origin
                    LOGGER.debug(f"[CORSOptionsMiddleware] Exact match found: {origin}")
                else:
                    # Try case-insensitive match
                    origin_lower = origin.lower()
                    for allowed in settings.ALLOWED_ORIGINS:
                        if allowed.lower() == origin_lower:
                            allowed_origin = origin  # Return original case
                            LOGGER.debug(f"[CORSOptionsMiddleware] Case-insensitive match found: {origin} -> {allowed}")
                            break

            if allowed_origin:
                LOGGER.info(f"[CORSOptionsMiddleware] OPTIONS request allowed for {path}, returning 200 with origin: {allowed_origin}")
                
                # Create response at ASGI level
                response_headers = [
                    (b"access-control-allow-origin", allowed_origin.encode("utf-8")),
                    (b"access-control-allow-methods", b"GET, POST, PUT, DELETE, OPTIONS, PATCH"),
                    (b"access-control-allow-headers", b"*"),
                    (b"access-control-allow-credentials", b"true"),
                    (b"access-control-max-age", b"3600"),
                    (b"content-length", b"0"),
                ]

                # Send response start
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": response_headers,
                })
                # Send response body (empty for OPTIONS)
                await send({
                    "type": "http.response.body",
                    "body": b"",
                })
                return
            else:
                LOGGER.warning(f"[CORSOptionsMiddleware] OPTIONS request rejected for {path}, origin not allowed: {origin}")
                # Send 403 response
                await send({
                    "type": "http.response.start",
                    "status": 403,
                    "headers": [(b"content-type", b"text/plain")],
                })
                await send({
                    "type": "http.response.body",
                    "body": b"Origin not allowed",
                })
                return

        # For non-OPTIONS requests, continue to next middleware/handler
        await self.app(scope, receive, send)

