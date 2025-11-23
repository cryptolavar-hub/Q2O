#!/usr/bin/env python
"""
Windows-specific API startup script.

This script sets the event loop policy BEFORE uvicorn starts,
ensuring psycopg async operations work correctly on Windows.

DUAL-STACK MODE:
- Set ENABLE_DUAL_STACK=true in .env to enable IPv4 + IPv6
- Default: IPv4 only (0.0.0.0) for compatibility
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# CRITICAL: Load .env file from project root BEFORE starting the API
# This ensures all environment variables (including LLM API keys) are available
project_root = Path(__file__).resolve().parents[1]  # Go up from addon_portal to Q2O_Combined
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=False)
    print(f"[OK] Loaded .env file from: {env_path}")
else:
    print(f"[WARN] .env file not found at: {env_path}")

# Set event loop policy BEFORE importing uvicorn or the app
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("✓ Windows event loop policy set to SelectorEventLoop")

# Now import and run uvicorn
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8080
    port = int(os.environ.get("PORT", "8080"))
    
    # Check if dual-stack is enabled
    enable_dual_stack = os.environ.get("ENABLE_DUAL_STACK", "false").lower() == "true"
    
    if enable_dual_stack:
        # DUAL-STACK MODE: Run two uvicorn instances (IPv4 + IPv6)
        print("=" * 60)
        print("Starting Q2O Licensing API with Dual-Stack Support")
        print("=" * 60)
        print(f"IPv4: 0.0.0.0:{port}")
        print(f"IPv6: [::]:{port}")
        print("=" * 60)
        
        async def run_dual_stack():
            """Run both IPv4 and IPv6 servers concurrently."""
            config_ipv4 = uvicorn.Config(
                app="api.main:app",
                host="0.0.0.0",
                port=port,
                reload=False,
                log_level="info"
            )
            
            config_ipv6 = uvicorn.Config(
                app="api.main:app",
                host="::",
                port=port,
                reload=False,
                log_level="info"
            )
            
            server_ipv4 = uvicorn.Server(config_ipv4)
            server_ipv6 = uvicorn.Server(config_ipv6)
            
            # Run both concurrently
            await asyncio.gather(
                server_ipv4.serve(),
                server_ipv6.serve()
            )
        
        try:
            asyncio.run(run_dual_stack())
        except KeyboardInterrupt:
            print("\n✓ Shutting down dual-stack servers...")
        except Exception as e:
            print(f"✗ Error starting dual-stack servers: {e}")
            sys.exit(1)
    else:
        # SINGLE-STACK MODE: IPv4 only (default)
        host = os.environ.get("HOST", "0.0.0.0")
        
        print(f"Starting Q2O Licensing API on {host}:{port}...")
        print("Using SelectorEventLoop for Windows compatibility")
        print("Listening on IPv4 (0.0.0.0) - accepts IPv4 connections")
        print("Tip: Set ENABLE_DUAL_STACK=true in .env for IPv4 + IPv6 support")
        
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=False,  # Set to True for development
            log_level="info"
        )

