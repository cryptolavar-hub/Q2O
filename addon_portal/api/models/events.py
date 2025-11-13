"""
Event Logging Models - Database-backed event tracking for platform activities.

Tracks all major and minor events in the platform:
- Major: Tenant creation, project creation, code generation, etc.
- Minor: Code activations, device enrollment, user login, etc.
"""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .licensing import Base


class EventSeverity(str, enum.Enum):
    """Event severity levels."""
    MAJOR = "major"  # Important platform changes
    MINOR = "minor"  # Routine activities


class EventType(str, enum.Enum):
    """Event type categories."""
    # Major Events
    TENANT_CREATED = "tenant_created"
    TENANT_UPDATED = "tenant_updated"
    TENANT_DELETED = "tenant_deleted"
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"
    CODE_GENERATED = "code_generated"
    CODE_REVOKED = "code_revoked"
    
    # Minor Events
    CODE_ACTIVATED = "code_activated"
    DEVICE_ENROLLED = "device_enrolled"
    DEVICE_REVOKED = "device_revoked"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    SESSION_CREATED = "session_created"
    SESSION_EXPIRED = "session_expired"
    CONFIG_UPDATED = "config_updated"


class PlatformEvent(Base):
    """
    Platform event log for tracking all activities.
    
    Used for:
    - Recent Activities feed
    - Audit trail
    - Analytics and reporting
    - Debugging and troubleshooting
    """
    __tablename__ = "platform_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Event classification
    # Use String columns instead of Enum to store enum VALUES (lowercase) directly
    # This ensures compatibility with DB constraint: CHECK (severity IN ('major', 'minor'))
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(10), nullable=False, index=True)
    
    # Event description
    title = Column(String(255), nullable=False)  # Human-readable title
    description = Column(Text, nullable=True)  # Detailed description
    
    # Actor information
    actor_type = Column(String(50), nullable=True)  # "admin", "tenant", "system"
    actor_id = Column(Integer, nullable=True)  # ID of the actor (tenant_id, user_id, etc.)
    actor_name = Column(String(255), nullable=True)  # Name of the actor
    
    # Related entities
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(String(100), nullable=True, index=True)  # LLM project_id
    code_id = Column(Integer, ForeignKey("activation_codes.id", ondelete="SET NULL"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    
    # Event metadata (JSON for flexibility)
    event_metadata = Column(JSON, nullable=True)  # Additional event data (renamed from 'metadata' to avoid SQLAlchemy reserved name)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    
    __table_args__ = (
        Index("idx_events_created_at", "created_at"),
        Index("idx_events_tenant_type", "tenant_id", "event_type"),
        Index("idx_events_severity_type", "severity", "event_type"),
    )

