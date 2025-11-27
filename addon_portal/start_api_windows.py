#!/usr/bin/env python
"""
Windows-specific API startup script with dual-stack (IPv4 + IPv6) support.

This script runs TWO separate subprocesses:
1. One bound to 0.0.0.0:8080 (IPv4)
2. One bound to [::]:8080 (IPv6)

Both instances share the same FastAPI app and run in separate processes.
"""
import asyncio
import sys
import os
import subprocess
import signal
from pathlib import Path

# Set event loop policy BEFORE importing uvicorn or the app
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("[OK] Windows event loop policy set to SelectorEventLoop")

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).resolve().parent

def start_ipv4_server(port: int):
    """Start IPv4 server in a separate subprocess."""
    print(f"[IPv4] Starting server on 0.0.0.0:{port}...")
    # Use wrapper script to ensure event loop policy is set before uvicorn starts
    wrapper_script = SCRIPT_DIR / "run_uvicorn.py"
    process = subprocess.Popen(
        [sys.executable, str(wrapper_script), "api.main:app", "--host", "0.0.0.0", "--port", str(port), "--log-level", "info"],
        cwd=SCRIPT_DIR,
        env={**os.environ, "SERVER_TYPE": "IPv4"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return process

def start_ipv6_server(port: int):
    """Start IPv6 server in a separate subprocess."""
    print(f"[IPv6] Starting server on [::]:{port}...")
    # Use wrapper script to ensure event loop policy is set before uvicorn starts
    wrapper_script = SCRIPT_DIR / "run_uvicorn.py"
    process = subprocess.Popen(
        [sys.executable, str(wrapper_script), "api.main:app", "--host", "::", "--port", str(port), "--log-level", "info"],
        cwd=SCRIPT_DIR,
        env={**os.environ, "SERVER_TYPE": "IPv6"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return process

def print_output(process, label):
    """Print output from a subprocess."""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[{label}] {line.rstrip()}")
    except Exception as e:
        print(f"[{label}] Error reading output: {e}")

if __name__ == "__main__":
    # Get port from environment or default to 8080
    port = int(os.environ.get("PORT", "8080"))
    
    # Check if dual-stack is enabled (default: true - always use dual-stack with separate subprocesses)
    # Set ENABLE_DUAL_STACK=false to disable and use single IPv4 mode
    enable_dual_stack = os.environ.get("ENABLE_DUAL_STACK", "true").lower() == "true"
    
    if enable_dual_stack:
        # DUAL-STACK MODE: Run two separate subprocesses (IPv4 + IPv6)
        print("=" * 60)
        print("Starting Q2O Licensing API with Dual-Stack Support")
        print("=" * 60)
        print(f"IPv4: 0.0.0.0:{port} (separate subprocess)")
        print(f"IPv6: [::]:{port} (separate subprocess)")
        print("=" * 60)
        print("Note: Each server runs in its own subprocess for better isolation")
        print("=" * 60)
        
        # Start both servers as separate subprocesses
        ipv4_process = start_ipv4_server(port)
        ipv6_process = start_ipv6_server(port)
        
        # Print output from both processes
        import threading
        ipv4_thread = threading.Thread(target=print_output, args=(ipv4_process, "IPv4"), daemon=True)
        ipv6_thread = threading.Thread(target=print_output, args=(ipv6_process, "IPv6"), daemon=True)
        ipv4_thread.start()
        ipv6_thread.start()
        
        def signal_handler(sig, frame):
            """Handle shutdown signals."""
            print("\n[OK] Shutting down dual-stack servers...")
            ipv4_process.terminate()
            ipv6_process.terminate()
            try:
                ipv4_process.wait(timeout=5)
                ipv6_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                ipv4_process.kill()
                ipv6_process.kill()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Wait for both processes
            ipv4_process.wait()
            ipv6_process.wait()
        except KeyboardInterrupt:
            signal_handler(None, None)
        except Exception as e:
            print(f"[ERROR] Error in dual-stack servers: {e}")
            ipv4_process.terminate()
            ipv6_process.terminate()
            sys.exit(1)
    else:
        # SINGLE-STACK MODE: IPv4 only (for compatibility)
        host = os.environ.get("HOST", "0.0.0.0")
        
        print(f"Starting Q2O Licensing API on {host}:{port}...")
        print("Using SelectorEventLoop for Windows compatibility")
        print("Listening on IPv4 (0.0.0.0) - accepts IPv4 connections")
        print("Tip: Set ENABLE_DUAL_STACK=true in .env for IPv4 + IPv6 support")
        
        import uvicorn
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=False,
            log_level="info"
        )
