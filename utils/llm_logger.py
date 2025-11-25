"""
Helper module for logging LLM usage to the database.
This is called asynchronously from the LLM service to avoid blocking.
"""

import logging
import hashlib
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


async def log_llm_usage_async(
    request_id: str,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    input_cost: float,
    output_cost: float,
    total_cost: float,
    duration_seconds: float,
    success: bool,
    cache_hit: bool = False,
    error_message: Optional[str] = None,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    agent_id: Optional[str] = None,
    system_prompt: Optional[str] = None,
    user_prompt: Optional[str] = None,
    response_preview: Optional[str] = None,
    log_metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Log LLM usage to the database asynchronously.
    
    This function should be called from a background task to avoid blocking
    the main LLM service execution.
    
    Returns:
        True if logged successfully, False otherwise
    """
    try:
        # Import here to avoid circular dependencies
        import sys
        from pathlib import Path
        
        # Add addon_portal to path if needed
        project_root = Path(__file__).resolve().parents[1]
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from addon_portal.api.models.llm_usage import LLMUsageLog
        from addon_portal.api.core.db import AsyncSessionLocal
        
        # Get database session
        async with AsyncSessionLocal() as db:
            # Calculate prompt hashes
            system_hash = None
            user_hash = None
            if system_prompt:
                system_hash = hashlib.md5(system_prompt.encode()).hexdigest()
            if user_prompt:
                user_hash = hashlib.md5(user_prompt.encode()).hexdigest()
            
            # Truncate response preview if too long
            if response_preview and len(response_preview) > 500:
                response_preview = response_preview[:500] + "..."
            
            # Create log entry
            log_entry = LLMUsageLog(
                request_id=request_id,
                project_id=project_id,
                task_id=task_id,
                agent_type=agent_type or "unknown",
                agent_id=agent_id,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                duration_seconds=duration_seconds,
                success=success,
                error_message=error_message,
                cache_hit=cache_hit,
                system_prompt_hash=system_hash,
                user_prompt_hash=user_hash,
                response_preview=response_preview,
                log_metadata=log_metadata,
                created_at=datetime.utcnow(),
            )
            
            db.add(log_entry)
            await db.commit()
            
            logger.debug(f"Logged LLM usage: {provider}/{model} - ${total_cost:.4f}")
            return True
            
    except Exception as e:
        # Log error but don't fail the LLM call
        logger.warning(f"Failed to log LLM usage to database: {e}")
        return False


def log_llm_usage_background(
    request_id: str,
    provider: str,
    model: str,
    usage: Any,  # LLMUsage object
    duration_seconds: float,
    success: bool,
    cache_hit: bool = False,
    error_message: Optional[str] = None,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    agent_id: Optional[str] = None,
    system_prompt: Optional[str] = None,
    user_prompt: Optional[str] = None,
    response_content: Optional[str] = None,
    log_metadata: Optional[Dict[str, Any]] = None,
):
    """
    Log LLM usage in a background task (fire-and-forget).
    
    This is a convenience wrapper that creates a background task
    to avoid blocking the main execution flow.
    """
    try:
        # Create background task
        asyncio.create_task(log_llm_usage_async(
            request_id=request_id,
            provider=provider,
            model=model,
            input_tokens=usage.input_tokens if usage else 0,
            output_tokens=usage.output_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            input_cost=usage.input_cost if usage else 0.0,
            output_cost=usage.output_cost if usage else 0.0,
            total_cost=usage.total_cost if usage else 0.0,
            duration_seconds=duration_seconds,
            success=success,
            cache_hit=cache_hit,
            error_message=error_message,
            project_id=project_id,
            task_id=task_id,
            agent_type=agent_type,
            agent_id=agent_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_preview=response_content,
            log_metadata=log_metadata,
        ))
    except Exception as e:
        # Fail silently - logging is non-critical
        logger.debug(f"Failed to create background logging task: {e}")

