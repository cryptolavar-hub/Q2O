"""
Messaging Mixin for Agents - Enables agent-to-agent communication.
"""

import logging
from typing import Dict, Any, Optional, Callable
from utils.message_broker import get_default_broker
from utils.message_protocol import (
    AgentMessage, MessageType,
    create_task_complete_message,
    create_request_help_message,
    create_share_result_message,
    create_agent_discovery_message
)

logger = logging.getLogger(__name__)


class MessagingMixin:
    """Mixin that adds messaging capabilities to agents."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Call parent init
        self.message_broker = get_default_broker()
        self.message_handlers: Dict[MessageType, Callable] = {}
        self._setup_default_handlers()
        
        # Subscribe to agent channel
        self.message_broker.subscribe("agents", self._handle_incoming_message)
        self.message_broker.subscribe(f"agents.{self.agent_type.value}", self._handle_incoming_message)
        self.message_broker.subscribe(f"agents.{self.agent_id}", self._handle_incoming_message)
        
        # Announce presence
        self.announce_presence()
    
    def _setup_default_handlers(self):
        """Setup default message handlers."""
        self.message_handlers[MessageType.TASK_COMPLETE] = self._handle_task_complete
        self.message_handlers[MessageType.REQUEST_HELP] = self._handle_request_help
        self.message_handlers[MessageType.SHARE_RESULT] = self._handle_share_result
        self.message_handlers[MessageType.AGENT_DISCOVERY] = self._handle_agent_discovery
    
    def _handle_incoming_message(self, message: Dict[str, Any]):
        """Handle incoming message from broker."""
        try:
            # Extract the actual message data
            msg_data = message.get("data", message)
            agent_msg = AgentMessage.from_dict(msg_data)
            
            # Check if message is for this agent
            if agent_msg.target_agent_id and agent_msg.target_agent_id != self.agent_id:
                return  # Not for us
            
            if agent_msg.target_agent_type and agent_msg.target_agent_type != self.agent_type.value:
                return  # Not for our agent type
            
            # Don't process our own messages
            if agent_msg.sender_agent_id == self.agent_id:
                return
            
            # Route to appropriate handler
            handler = self.message_handlers.get(agent_msg.message_type)
            if handler:
                handler(agent_msg)
            else:
                logger.debug(f"No handler for message type {agent_msg.message_type.value}")
        
        except Exception as e:
            logger.error(f"Error handling incoming message: {e}", exc_info=True)
    
    def send_message(self, message: AgentMessage):
        """Send a message via the message broker."""
        try:
            self.message_broker.publish(message.channel, message.to_dict())
            logger.debug(f"Sent message {message.message_type.value} to channel {message.channel}")
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
    
    def announce_presence(self):
        """Announce agent presence and capabilities."""
        try:
            capabilities = self._get_capabilities()
            message = create_agent_discovery_message(
                sender_agent_id=self.agent_id,
                sender_agent_type=self.agent_type.value,
                capabilities=capabilities
            )
            self.send_message(message)
            logger.info(f"Announced presence: {self.agent_id} ({self.agent_type.value})")
        except Exception as e:
            logger.error(f"Error announcing presence: {e}")
    
    def _get_capabilities(self) -> list:
        """Get list of agent capabilities (to be overridden by subclasses)."""
        return [self.agent_type.value]
    
    def request_help(self, task_id: str, help_type: str, description: str, target_agent_type: Optional[str] = None):
        """Request help from other agents."""
        message = create_request_help_message(
            sender_agent_id=self.agent_id,
            sender_agent_type=self.agent_type.value,
            task_id=task_id,
            help_type=help_type,
            description=description,
            target_agent_type=target_agent_type
        )
        self.send_message(message)
        logger.info(f"Requested help for task {task_id}: {help_type}")
    
    def request_research(self, query: str, task_id: str = None, urgency: str = "normal", depth: str = "adaptive"):
        """
        Request research from ResearcherAgent.
        
        Convenience method for agents to request web research during task execution.
        
        Args:
            query: Research query (e.g., "FastAPI OAuth best practices")
            task_id: ID of the requesting task (optional)
            urgency: Urgency level - "low", "normal", "high" (default: "normal")
            depth: Research depth - "quick", "deep", "comprehensive", "adaptive" (default: "adaptive")
        
        Example:
            # In your agent's process_task method:
            if self.needs_external_info:
                self.request_research(
                    query="JWT validation best practices Python",
                    task_id=task.id,
                    urgency="high"
                )
        """
        message = AgentMessage(
            message_type=MessageType.REQUEST_HELP,  # Reuse REQUEST_HELP for research
            sender_agent_id=self.agent_id,
            sender_agent_type=self.agent_type.value,
            target_agent_type="researcher",  # Target ResearcherAgent
            channel="research",  # Research-specific channel
            payload={
                "help_type": "research",
                "query": query,
                "task_id": task_id or "adhoc",
                "urgency": urgency,
                "depth": depth,
                "requesting_agent": self.agent_id
            }
        )
        self.send_message(message)
        logger.info(f"Requested research from {self.agent_id}: {query} (urgency: {urgency})")
    
    def share_result(self, result_type: str, data: Any, target_agent_id: Optional[str] = None):
        """Share a result with other agents."""
        message = create_share_result_message(
            sender_agent_id=self.agent_id,
            sender_agent_type=self.agent_type.value,
            result_type=result_type,
            data=data,
            target_agent_id=target_agent_id
        )
        self.send_message(message)
        logger.info(f"Shared result: {result_type}")
    
    def notify_task_complete(self, task_id: str, result: Any):
        """Notify other agents about task completion."""
        message = create_task_complete_message(
            sender_agent_id=self.agent_id,
            sender_agent_type=self.agent_type.value,
            task_id=task_id,
            result=result
        )
        self.send_message(message)
        logger.info(f"Notified task completion: {task_id}")
    
    # Default message handlers (can be overridden)
    
    def _handle_task_complete(self, message: AgentMessage):
        """Handle task completion message from another agent."""
        task_id = message.payload.get("task_id")
        logger.debug(f"Received task completion notification: {task_id} from {message.sender_agent_id}")
        # Subclasses can override to react to task completions
    
    def _handle_request_help(self, message: AgentMessage):
        """Handle help request from another agent."""
        task_id = message.payload.get("task_id")
        help_type = message.payload.get("help_type")
        description = message.payload.get("description")
        logger.debug(f"Received help request: {help_type} for task {task_id} from {message.sender_agent_id}")
        # Subclasses can override to provide help
    
    def _handle_share_result(self, message: AgentMessage):
        """Handle result sharing message from another agent."""
        result_type = message.payload.get("result_type")
        logger.debug(f"Received shared result: {result_type} from {message.sender_agent_id}")
        # Subclasses can override to use shared results
    
    def _handle_agent_discovery(self, message: AgentMessage):
        """Handle agent discovery message."""
        capabilities = message.payload.get("capabilities", [])
        logger.debug(f"Discovered agent: {message.sender_agent_id} ({message.sender_agent_type}) with capabilities: {capabilities}")
        # Subclasses can override to maintain agent registry
    
    def register_message_handler(self, message_type: MessageType, handler: Callable[[AgentMessage], None]):
        """Register a custom message handler."""
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for {message_type.value}")

