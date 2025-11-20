"""
Task Tracking Integration for Agents

This module provides a bridge between agent task execution and the database task tracking system.
Agents use this to automatically track tasks in the agent_tasks table.
"""

import os
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Global database session manager (lazy initialization)
_db_session = None
_task_tracking_enabled = None


def _get_db_session():
    """Get or create database session for task tracking."""
    global _db_session
    
    if _db_session is not None:
        return _db_session
    
    try:
        # Use the same database connection as the API
        # Import here to avoid circular dependencies
        import sys
        from pathlib import Path
        
        # Add addon_portal to path if not already there
        project_root = Path(__file__).resolve().parents[2]
        addon_portal_path = project_root / "addon_portal"
        if str(addon_portal_path) not in sys.path:
            sys.path.insert(0, str(addon_portal_path))
        
        from api.core.db import AsyncSessionLocal
        
        # Create a new session (same factory as API)
        _db_session = AsyncSessionLocal()
        
        logger.info("Database session created for task tracking (using API connection)")
        return _db_session
    
    except Exception as e:
        logger.warning(f"Failed to create database session for task tracking: {e}")
        # Try fallback: create connection directly
        try:
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
            
            # Get database connection from environment
            database_url = os.getenv("DATABASE_URL") or os.getenv("DB_DSN")
            if not database_url:
                # Fallback to individual components
                db_host = os.getenv("DB_HOST", "localhost")
                db_port = os.getenv("DB_PORT", "5432")
                db_user = os.getenv("DB_USER", "q2o_user")
                db_password = os.getenv("DB_PASSWORD", "")
                db_name = os.getenv("DB_NAME", "q2o")
                
                # Use psycopg format (same as API)
                database_url = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            # Ensure async format
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+psycopg://")
            
            # Create async engine
            engine = create_async_engine(
                database_url,
                pool_pre_ping=True,
                echo=False,
                future=True
            )
            
            # Create session factory
            async_session = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
                future=True
            )
            
            # Create session
            _db_session = async_session()
            
            logger.info("Database session created for task tracking (fallback method)")
            return _db_session
        except Exception as e2:
            logger.error(f"Fallback database connection also failed: {e2}")
            return None


def is_task_tracking_enabled() -> bool:
    """Check if task tracking is enabled."""
    global _task_tracking_enabled
    
    if _task_tracking_enabled is not None:
        return _task_tracking_enabled
    
    # Check environment variable
    enabled = os.getenv("ENABLE_TASK_TRACKING", "true").lower() == "true"
    _task_tracking_enabled = enabled
    
    return enabled


async def create_task_in_db(
    project_id: str,
    agent_type: str,
    task_name: str,
    task_description: Optional[str] = None,
    task_type: Optional[str] = None,
    agent_id: Optional[str] = None,
    priority: int = 1,
    tenant_id: Optional[int] = None,
) -> Optional[str]:
    """
    Create a task in the database.
    
    Returns:
        task_id if successful, None otherwise
    """
    if not is_task_tracking_enabled():
        return None
    
    try:
        from addon_portal.api.services.agent_task_service import create_task
        
        db = _get_db_session()
        if not db:
            logger.warning("Database session not available for task tracking")
            return None
        
        task = await create_task(
            db=db,
            project_id=project_id,
            agent_type=agent_type,
            task_name=task_name,
            task_description=task_description,
            task_type=task_type,
            agent_id=agent_id,
            priority=priority,
            tenant_id=tenant_id,
        )
        
        return task.task_id
    
    except Exception as e:
        logger.warning(f"Failed to create task in database: {e}")
        return None


async def update_task_status_in_db(
    task_id: str,
    status: str,
    progress_percentage: Optional[float] = None,
    error_message: Optional[str] = None,
    error_stack_trace: Optional[str] = None,
    execution_metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Update task status in the database.
    
    Returns:
        True if successful, False otherwise
    """
    if not is_task_tracking_enabled():
        return False
    
    try:
        from addon_portal.api.services.agent_task_service import update_task_status
        
        db = _get_db_session()
        if not db:
            logger.warning("Database session not available for task tracking")
            return False
        
        await update_task_status(
            db=db,
            task_id=task_id,
            status=status,
            progress_percentage=progress_percentage,
            error_message=error_message,
            error_stack_trace=error_stack_trace,
            execution_metadata=execution_metadata,
        )
        
        return True
    
    except Exception as e:
        logger.warning(f"Failed to update task status in database: {e}")
        return False


async def update_task_llm_usage_in_db(
    task_id: str,
    llm_calls_count: Optional[int] = None,
    llm_tokens_used: Optional[int] = None,
    llm_cost_usd: Optional[float] = None,
) -> bool:
    """
    Update LLM usage for a task in the database.
    
    Returns:
        True if successful, False otherwise
    """
    if not is_task_tracking_enabled():
        return False
    
    try:
        from addon_portal.api.services.agent_task_service import update_task_llm_usage
        
        db = _get_db_session()
        if not db:
            logger.warning("Database session not available for task tracking")
            return False
        
        await update_task_llm_usage(
            db=db,
            task_id=task_id,
            llm_calls_count=llm_calls_count,
            llm_tokens_used=llm_tokens_used,
            llm_cost_usd=llm_cost_usd,
        )
        
        return True
    
    except Exception as e:
        logger.warning(f"Failed to update LLM usage in database: {e}")
        return False


def run_async(coro):
    """Run async function synchronously (for use in sync agent code)."""
    import platform
    import selectors
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        # Windows compatibility: Use SelectorEventLoop for psycopg async
        if platform.system() == "Windows":
            loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

