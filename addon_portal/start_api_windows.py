#!/usr/bin/env python
"""
Windows-specific API startup script.

This script sets the event loop policy BEFORE uvicorn starts,
ensuring psycopg async operations work correctly on Windows.
"""
import asyncio
import sys
import os

# Set event loop policy BEFORE importing uvicorn or the app
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("✓ Windows event loop policy set to SelectorEventLoop")

# Now import and run uvicorn
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8080
    port = int(os.environ.get("PORT", "8080"))
    # On Windows, uvicorn doesn't support true dual-stack with "::"
    # Use "0.0.0.0" for IPv4 (works with IPv4-mapped IPv6 addresses)
    # For full IPv6 support, we'd need to run two instances or use a different server
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"Starting Q2O Licensing API on {host}:{port}...")
    print("Using SelectorEventLoop for Windows compatibility")
    print("Listening on IPv4 (0.0.0.0) - accepts IPv4 connections")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=False,  # Set to True for development
        log_level="info"
    )

