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
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"Starting Q2O Licensing API on {host}:{port}...")
    print("Using SelectorEventLoop for Windows compatibility")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=False,  # Set to True for development
        log_level="info"
    )

