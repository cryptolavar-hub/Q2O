"""
Message Protocol Definitions for Agent Communication.
Standardized message format for agent-to-agent communication.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime
import json


class MessageType(Enum):
    """Types of messages agents can send."""
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    REQUEST_HELP = "request_help"
    SHARE_RESULT = "share_result"
    AGENT_DISCOVERY = "agent_discovery"
    COORDINATION = "coordination"
    STATUS_UPDATE = "status_update"


@dataclass
class AgentMessage:
    """Standardized message format for agent communication."""
    message_id: str
    message_type: MessageType
    sender_agent_id: str
    sender_agent_type: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Message payload
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Optional routing
    target_agent_id: Optional[str] = None  # None = broadcast
    target_agent_type: Optional[str] = None  # None = broadcast
    channel: str = "agents"  # Default channel
    
    # Metadata
    correlation_id: Optional[str] = None  # For request/response correlation
    reply_to: Optional[str] = None  # Message ID to reply to
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_agent_id": self.sender_agent_id,
            "sender_agent_type": self.sender_agent_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "target_agent_id": self.target_agent_id,
            "target_agent_type": self.target_agent_type,
            "channel": self.channel,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary."""
        return cls(
            message_id=data["message_id"],
            message_type=MessageType(data["message_type"]),
            sender_agent_id=data["sender_agent_id"],
            sender_agent_type=data["sender_agent_type"],
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            payload=data.get("payload", {}),
            target_agent_id=data.get("target_agent_id"),
            target_agent_type=data.get("target_agent_type"),
            channel=data.get("channel", "agents"),
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to")
        )
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        """Create message from JSON string."""
        return cls.from_dict(json.loads(json_str))


# Message factory functions

def create_task_complete_message(
    sender_agent_id: str,
    sender_agent_type: str,
    task_id: str,
    result: Any,
    correlation_id: Optional[str] = None
) -> AgentMessage:
    """Create a task completion message."""
    import uuid
    
    return AgentMessage(
        message_id=str(uuid.uuid4()),
        message_type=MessageType.TASK_COMPLETE,
        sender_agent_id=sender_agent_id,
        sender_agent_type=sender_agent_type,
        payload={
            "task_id": task_id,
            "result": result,
            "status": "completed"
        },
        correlation_id=correlation_id
    )


def create_request_help_message(
    sender_agent_id: str,
    sender_agent_type: str,
    task_id: str,
    help_type: str,
    description: str,
    target_agent_type: Optional[str] = None
) -> AgentMessage:
    """Create a help request message."""
    import uuid
    
    return AgentMessage(
        message_id=str(uuid.uuid4()),
        message_type=MessageType.REQUEST_HELP,
        sender_agent_id=sender_agent_id,
        sender_agent_type=sender_agent_type,
        payload={
            "task_id": task_id,
            "help_type": help_type,
            "description": description
        },
        target_agent_type=target_agent_type
    )


def create_share_result_message(
    sender_agent_id: str,
    sender_agent_type: str,
    result_type: str,
    data: Any,
    target_agent_id: Optional[str] = None
) -> AgentMessage:
    """Create a result sharing message."""
    import uuid
    
    return AgentMessage(
        message_id=str(uuid.uuid4()),
        message_type=MessageType.SHARE_RESULT,
        sender_agent_id=sender_agent_id,
        sender_agent_type=sender_agent_type,
        payload={
            "result_type": result_type,
            "data": data
        },
        target_agent_id=target_agent_id
    )


def create_agent_discovery_message(
    sender_agent_id: str,
    sender_agent_type: str,
    capabilities: List[str]
) -> AgentMessage:
    """Create an agent discovery message."""
    import uuid
    
    return AgentMessage(
        message_id=str(uuid.uuid4()),
        message_type=MessageType.AGENT_DISCOVERY,
        sender_agent_id=sender_agent_id,
        sender_agent_type=sender_agent_type,
        payload={
            "capabilities": capabilities
        }
    )

