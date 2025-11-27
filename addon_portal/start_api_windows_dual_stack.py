#!/usr/bin/env python
"""
Windows-specific API startup script with dual-stack (IPv4 + IPv6) support.

This script runs TWO uvicorn instances:
1. One bound to 0.0.0.0:8080 (IPv4)
2. One bound to [::]:8080 (IPv6)

Both instances share the same FastAPI app and run concurrently.
"""
import asyncio
import sys
import os
from concurrent.futures import ThreadPoolExecutor

# Set event loop policy BEFORE importing uvicorn or the app
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        print("[OK] Windows event loop policy set to SelectorEventLoop")

def run_uvicorn_server(host: str, port: int, app_path: str):
    """Run a uvicorn server in a separate thread."""
    import uvicorn
    
    config = uvicorn.Config(
        app=app_path,
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    # Run in current event loop
    asyncio.run(server.serve())

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8080
    port = int(os.environ.get("PORT", "8080"))
    app_path = "api.main:app"
    
    print("=" * 60)
    print("Starting Q2O Licensing API with Dual-Stack Support")
    print("=" * 60)
    print(f"IPv4: 0.0.0.0:{port}")
    print(f"IPv6: [::]:{port}")
    print("Using SelectorEventLoop for Windows compatibility")
    print("=" * 60)
    
    # Run both servers concurrently using asyncio
    async def run_dual_stack():
        """Run both IPv4 and IPv6 servers concurrently."""
        import uvicorn
        
        # Create configs for both servers
        config_ipv4 = uvicorn.Config(
            app=app_path,
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level="info"
        )
        
        config_ipv6 = uvicorn.Config(
            app=app_path,
            host="::",
            port=port,
            reload=False,
            log_level="info"
        )
        
        # Create servers
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
        print("\n[OK] Shutting down dual-stack servers...")
    except Exception as e:
        print(f"[ERROR] Error starting dual-stack servers: {e}")
        sys.exit(1)

