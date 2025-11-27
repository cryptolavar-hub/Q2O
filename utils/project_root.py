"""
Project Root Path Detection Utility

This module provides a single source of truth for determining the Q2O project root directory.
All code should use this utility instead of hardcoding paths.

The root is detected by finding the directory containing:
- .env file (if exists)
- main.py
- addon_portal/ directory
- Tenant_Projects/ directory
"""

from pathlib import Path
import os
from typing import Optional

# Cache the root path once detected
_cached_root: Optional[Path] = None


def get_project_root() -> Path:
    """
    Get the Q2O project root directory.
    
    Detection strategy (in order):
    1. Check Q2O_ROOT environment variable (if set)
    2. Find directory containing .env file (if exists)
    3. Find directory containing main.py
    4. Find directory containing addon_portal/ and Tenant_Projects/
    5. Fallback to current working directory
    
    Returns:
        Path: Absolute path to project root directory
        
    Raises:
        RuntimeError: If root cannot be determined
    """
    global _cached_root
    
    # Return cached value if available
    if _cached_root is not None:
        return _cached_root
    
    # Strategy 1: Check environment variable (highest priority)
    env_root = os.environ.get("Q2O_ROOT")
    if env_root:
        root = Path(env_root).resolve()
        if root.exists() and root.is_dir():
            _cached_root = root
            return root
    
    # Strategy 2: Find directory containing .env file
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        env_file = parent / '.env'
        if env_file.exists():
            _cached_root = parent
            return parent
    
    # Strategy 3: Find directory containing main.py
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        main_py = parent / 'main.py'
        if main_py.exists():
            _cached_root = parent
            return parent
    
    # Strategy 4: Find directory containing both addon_portal/ and Tenant_Projects/
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / 'addon_portal').exists() and (parent / 'Tenant_Projects').exists():
            _cached_root = parent
            return parent
    
    # Strategy 5: Fallback to current working directory
    cwd = Path.cwd().resolve()
    _cached_root = cwd
    return cwd


def get_env_file_path() -> Path:
    """
    Get the path to the .env file at project root.
    
    Returns:
        Path: Absolute path to .env file (may not exist)
    """
    return get_project_root() / '.env'


def reset_cache():
    """Reset the cached root path (useful for testing)."""
    global _cached_root
    _cached_root = None

