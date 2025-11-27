#!/usr/bin/env python
"""
Wrapper script to run uvicorn with correct event loop policy on Windows.

This ensures the event loop policy is set BEFORE uvicorn creates the event loop,
which is required for psycopg async compatibility on Windows.
"""
import sys
import asyncio
import argparse

# CRITICAL: Set event loop policy BEFORE importing uvicorn
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Now import and run uvicorn
import uvicorn

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Run uvicorn with Windows event loop fix")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--log-level", default="info", help="Log level")
    parser.add_argument("app", nargs="?", default="api.main:app", help="Application to run")
    
    args = parser.parse_args()
    
    uvicorn.run(
        args.app,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=False
    )

