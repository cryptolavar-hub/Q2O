"""
Windows Event Loop Fix for psycopg async compatibility.

This module MUST be imported before any asyncio operations occur.
It sets the event loop policy to use SelectorEventLoop on Windows,
which is required for psycopg async operations.
"""
import asyncio
import sys

# Set event loop policy BEFORE any asyncio operations
if sys.platform == 'win32':
    # Check if policy is already set (avoid resetting if already correct)
    current_policy = asyncio.get_event_loop_policy()
    if not isinstance(current_policy, asyncio.WindowsSelectorEventLoopPolicy):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

