"""
Event Logging Service - Centralized event logging for platform activities.
"""

import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models.events import PlatformEvent, EventType, EventSeverity
from ..core.logging import get_logger

LOGGER = get_logger(__name__)


def log_event(
    session: Session,
    event_type: EventType,
    severity: EventSeverity,
    title: str,
    description: Optional[str] = None,
    actor_type: Optional[str] = None,
    actor_id: Optional[int] = None,
    actor_name: Optional[str] = None,
    tenant_id: Optional[int] = None,
    project_id: Optional[str] = None,
    code_id: Optional[int] = None,
    device_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> PlatformEvent:
    """
    Log a platform event to the database.
    
    Args:
        session: Database session
        event_type: Type of event (from EventType enum)
        severity: Event severity (MAJOR or MINOR)
        title: Human-readable event title
        description: Optional detailed description
        actor_type: Type of actor ("admin", "tenant", "system")
        actor_id: ID of the actor
        actor_name: Name of the actor
        tenant_id: Related tenant ID
        project_id: Related project ID
        code_id: Related activation code ID
        device_id: Related device ID
        metadata: Additional event metadata (JSON)
    
    Returns:
        Created PlatformEvent record
    """
    try:
        # Explicitly use .value to ensure enum VALUES (lowercase) are stored, not enum NAMES (uppercase)
        # This matches the database constraint: CHECK (severity IN ('major', 'minor'))
        event = PlatformEvent(
            event_type=event_type.value,  # Extract 'tenant_created' from EventType.TENANT_CREATED
            severity=severity.value,  # Extract 'major' from EventSeverity.MAJOR
            title=title,
            description=description,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_name=actor_name,
            tenant_id=tenant_id,
            project_id=project_id,
            code_id=code_id,
            device_id=device_id,
            event_metadata=metadata or {},
        )
        session.add(event)
        # Flush to get the ID, but don't commit yet (let caller handle commit)
        session.flush()
        session.refresh(event)
        
        LOGGER.info(
            "event_logged",
            extra={
                "event_id": event.id,
                "event_type": event_type.value,
                "severity": severity.value,
                "title": title,
            }
        )
        
        return event
    except Exception as e:
        LOGGER.error("event_logging_failed", extra={"error": str(e), "event_type": event_type.value, "traceback": traceback.format_exc()})
        # Don't rollback - let the caller handle transaction management
        raise


# Convenience functions for common events

def log_tenant_created(session: Session, tenant_id: int, tenant_name: str, actor_name: Optional[str] = None):
    """Log tenant creation event."""
    return log_event(
        session=session,
        event_type=EventType.TENANT_CREATED,
        severity=EventSeverity.MAJOR,
        title=f"New tenant created: {tenant_name}",
        description=f"Tenant '{tenant_name}' was created in the system",
        actor_type="admin",
        actor_name=actor_name or "System",
        tenant_id=tenant_id,
        metadata={"tenant_name": tenant_name},
    )


def log_tenant_updated(session: Session, tenant_id: int, tenant_name: str, changes: Dict[str, Any], actor_name: Optional[str] = None):
    """Log tenant update event."""
    return log_event(
        session=session,
        event_type=EventType.TENANT_UPDATED,
        severity=EventSeverity.MAJOR,
        title=f"Tenant updated: {tenant_name}",
        description=f"Tenant '{tenant_name}' was updated",
        actor_type="admin",
        actor_name=actor_name or "System",
        tenant_id=tenant_id,
        metadata={"tenant_name": tenant_name, "changes": changes},
    )


def log_tenant_deleted(session: Session, tenant_id: int, tenant_name: str, actor_name: Optional[str] = None):
    """Log tenant deletion event."""
    return log_event(
        session=session,
        event_type=EventType.TENANT_DELETED,
        severity=EventSeverity.MAJOR,
        title=f"Tenant deleted: {tenant_name}",
        description=f"Tenant '{tenant_name}' and all related data were deleted",
        actor_type="admin",
        actor_name=actor_name or "System",
        tenant_id=tenant_id,
        metadata={"tenant_name": tenant_name},
    )


def log_code_generated(session: Session, code_id: int, tenant_id: int, tenant_name: str, code_count: int, actor_name: Optional[str] = None):
    """Log activation code generation event."""
    return log_event(
        session=session,
        event_type=EventType.CODE_GENERATED,
        severity=EventSeverity.MAJOR,
        title=f"Generated {code_count} activation code(s) for {tenant_name}",
        description=f"{code_count} activation code(s) were generated for tenant '{tenant_name}'",
        actor_type="admin",
        actor_name=actor_name or "System",
        tenant_id=tenant_id,
        code_id=code_id,
        metadata={"code_count": code_count, "tenant_name": tenant_name},
    )


def log_code_revoked(session: Session, code_id: int, tenant_id: int, tenant_name: str, actor_name: Optional[str] = None):
    """Log activation code revocation event."""
    return log_event(
        session=session,
        event_type=EventType.CODE_REVOKED,
        severity=EventSeverity.MAJOR,
        title=f"Activation code revoked for {tenant_name}",
        description=f"An activation code was revoked for tenant '{tenant_name}'",
        actor_type="admin",
        actor_name=actor_name or "System",
        tenant_id=tenant_id,
        code_id=code_id,
        metadata={"tenant_name": tenant_name},
    )


def log_code_activated(session: Session, code_id: int, tenant_id: int, tenant_name: str, project_id: Optional[str] = None):
    """Log activation code usage event."""
    return log_event(
        session=session,
        event_type=EventType.CODE_ACTIVATED,
        severity=EventSeverity.MINOR,
        title=f"Activation code used by {tenant_name}",
        description=f"An activation code was used to activate a project",
        actor_type="tenant",
        tenant_id=tenant_id,
        code_id=code_id,
        project_id=project_id,
        metadata={"tenant_name": tenant_name, "project_id": project_id},
    )


def log_project_created(session: Session, project_id: str, tenant_id: int, tenant_name: str, client_name: str, actor_name: Optional[str] = None):
    """Log project creation event."""
    return log_event(
        session=session,
        event_type=EventType.PROJECT_CREATED,
        severity=EventSeverity.MAJOR,
        title=f"Project created: {client_name}",
        description=f"New project '{client_name}' was created for tenant '{tenant_name}'",
        actor_type="tenant",
        actor_name=actor_name or tenant_name,
        tenant_id=tenant_id,
        project_id=project_id,
        metadata={"client_name": client_name, "tenant_name": tenant_name},
    )


def log_project_updated(session: Session, project_id: str, tenant_id: int, client_name: str, changes: Dict[str, Any], actor_name: Optional[str] = None):
    """Log project update event."""
    return log_event(
        session=session,
        event_type=EventType.PROJECT_UPDATED,
        severity=EventSeverity.MAJOR,
        title=f"Project updated: {client_name}",
        description=f"Project '{client_name}' was updated",
        actor_type="tenant",
        actor_name=actor_name,
        tenant_id=tenant_id,
        project_id=project_id,
        metadata={"client_name": client_name, "changes": changes},
    )


def log_project_deleted(session: Session, project_id: str, tenant_id: int, client_name: str, actor_name: Optional[str] = None):
    """Log project deletion event."""
    return log_event(
        session=session,
        event_type=EventType.PROJECT_DELETED,
        severity=EventSeverity.MAJOR,
        title=f"Project deleted: {client_name}",
        description=f"Project '{client_name}' was deleted",
        actor_type="tenant",
        actor_name=actor_name,
        tenant_id=tenant_id,
        project_id=project_id,
        metadata={"client_name": client_name},
    )


def log_device_enrolled(session: Session, device_id: int, tenant_id: int, tenant_name: str, device_label: Optional[str] = None):
    """Log device enrollment event."""
    return log_event(
        session=session,
        event_type=EventType.DEVICE_ENROLLED,
        severity=EventSeverity.MINOR,
        title=f"Device enrolled for {tenant_name}",
        description=f"A new device was enrolled for tenant '{tenant_name}'",
        actor_type="tenant",
        tenant_id=tenant_id,
        device_id=device_id,
        metadata={"tenant_name": tenant_name, "device_label": device_label},
    )


def log_device_revoked(session: Session, device_id: int, tenant_id: int, tenant_name: str, actor_name: Optional[str] = None):
    """Log device revocation event."""
    return log_event(
        session=session,
        event_type=EventType.DEVICE_REVOKED,
        severity=EventSeverity.MINOR,
        title=f"Device revoked for {tenant_name}",
        description=f"A device was revoked for tenant '{tenant_name}'",
        actor_type="admin",
        actor_name=actor_name or "System",
        tenant_id=tenant_id,
        device_id=device_id,
        metadata={"tenant_name": tenant_name},
    )


def log_user_login(session: Session, tenant_id: Optional[int] = None, tenant_name: Optional[str] = None, actor_type: str = "admin"):
    """Log user login event."""
    return log_event(
        session=session,
        event_type=EventType.USER_LOGIN,
        severity=EventSeverity.MINOR,
        title=f"User logged in",
        description=f"User logged into {actor_type} portal",
        actor_type=actor_type,
        tenant_id=tenant_id,
        metadata={"tenant_name": tenant_name},
    )


def log_user_logout(session: Session, tenant_id: Optional[int] = None, tenant_name: Optional[str] = None, actor_type: str = "admin"):
    """Log user logout event."""
    return log_event(
        session=session,
        event_type=EventType.USER_LOGOUT,
        severity=EventSeverity.MINOR,
        title=f"User logged out",
        description=f"User logged out of {actor_type} portal",
        actor_type=actor_type,
        tenant_id=tenant_id,
        metadata={"tenant_name": tenant_name},
    )

