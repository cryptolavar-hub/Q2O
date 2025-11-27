"""
Event Loop Utilities for Windows Compatibility

Provides helper functions to create event loops compatible with PostgreSQL async operations.
On Windows, psycopg requires SelectorEventLoop instead of the default ProactorEventLoop.
"""

import asyncio
import platform
import selectors
from typing import Optional


def create_compatible_event_loop() -> asyncio.AbstractEventLoop:
    """
    Create an event loop compatible with PostgreSQL async operations.
    
    On Windows, uses SelectorEventLoop (required for psycopg).
    On other platforms, uses the default event loop.
    
    Returns:
        Compatible event loop instance
    """
    if platform.system() == "Windows":
        # Windows: Use SelectorEventLoop for psycopg async compatibility
        loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
    else:
        # Unix/Linux/Mac: Use default event loop
        loop = asyncio.new_event_loop()
    
    return loop


def setup_event_loop() -> asyncio.AbstractEventLoop:
    """
    Create and set a compatible event loop.
    
    Returns:
        The created event loop
    """
    loop = create_compatible_event_loop()
    asyncio.set_event_loop(loop)
    return loop

