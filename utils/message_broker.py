"""
Message Broker Abstraction for Agent Communication.
Supports Redis (production) and in-memory (development/testing).
"""

import logging
import json
from typing import Dict, List, Callable, Optional, Any
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageBroker(ABC):
    """Abstract base class for message brokers."""
    
    @abstractmethod
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a channel."""
        pass
    
    @abstractmethod
    def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """Subscribe to messages on a channel."""
        pass
    
    @abstractmethod
    def unsubscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """Unsubscribe from a channel."""
        pass


class InMemoryMessageBroker(MessageBroker):
    """
    In-memory message broker for development and testing.
    Not suitable for production with multiple processes.
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = defaultdict(list)
        self.message_history: List[Dict[str, Any]] = []
        self.max_history = 1000
    
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a channel."""
        try:
            # Add metadata
            enriched_message = {
                "channel": channel,
                "timestamp": datetime.now().isoformat(),
                "data": message
            }
            
            # Store in history
            self.message_history.append(enriched_message)
            if len(self.message_history) > self.max_history:
                self.message_history.pop(0)
            
            # Deliver to subscribers
            callbacks = self.subscribers.get(channel, [])
            for callback in callbacks:
                try:
                    callback(enriched_message)
                except Exception as e:
                    logger.error(f"Error calling subscriber on channel '{channel}': {e}")
            
            # Also deliver to wildcard subscribers
            wildcard_callbacks = self.subscribers.get("*", [])
            for callback in wildcard_callbacks:
                try:
                    callback(enriched_message)
                except Exception as e:
                    logger.error(f"Error calling wildcard subscriber: {e}")
            
            logger.debug(f"Published message to channel '{channel}': {message.get('type', 'unknown')}")
            return True
        
        except Exception as e:
            logger.error(f"Error publishing message to channel '{channel}': {e}")
            return False
    
    def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """Subscribe to messages on a channel."""
        try:
            if callback not in self.subscribers[channel]:
                self.subscribers[channel].append(callback)
                logger.debug(f"Subscribed to channel '{channel}'")
            return True
        except Exception as e:
            logger.error(f"Error subscribing to channel '{channel}': {e}")
            return False
    
    def unsubscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """Unsubscribe from a channel."""
        try:
            if callback in self.subscribers[channel]:
                self.subscribers[channel].remove(callback)
                logger.debug(f"Unsubscribed from channel '{channel}'")
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from channel '{channel}': {e}")
            return False
    
    def get_history(self, channel: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get message history for a channel or all channels."""
        if channel:
            filtered = [msg for msg in self.message_history if msg.get("channel") == channel]
        else:
            filtered = self.message_history
        
        return filtered[-limit:]


class RedisMessageBroker(MessageBroker):
    """
    Redis-based message broker for production.
    Requires redis-py package.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            import redis
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.pubsub = self.redis_client.pubsub()
            self.subscriptions: Dict[str, Callable] = {}
            logger.info(f"Connected to Redis at {redis_url}")
        except ImportError:
            logger.error("redis package not installed. Install with: pip install redis")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a Redis channel."""
        try:
            enriched_message = {
                "channel": channel,
                "timestamp": datetime.now().isoformat(),
                "data": message
            }
            self.redis_client.publish(channel, json.dumps(enriched_message))
            logger.debug(f"Published message to Redis channel '{channel}'")
            return True
        except Exception as e:
            logger.error(f"Error publishing to Redis channel '{channel}': {e}")
            return False
    
    def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """Subscribe to messages on a Redis channel."""
        try:
            def message_handler(message):
                try:
                    data = json.loads(message['data'])
                    callback(data)
                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}")
            
            self.pubsub.subscribe(channel)
            self.subscriptions[channel] = callback
            
            # Start listening in background (would need threading)
            logger.debug(f"Subscribed to Redis channel '{channel}'")
            return True
        except Exception as e:
            logger.error(f"Error subscribing to Redis channel '{channel}': {e}")
            return False
    
    def unsubscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """Unsubscribe from a Redis channel."""
        try:
            self.pubsub.unsubscribe(channel)
            if channel in self.subscriptions:
                del self.subscriptions[channel]
            logger.debug(f"Unsubscribed from Redis channel '{channel}'")
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from Redis channel '{channel}': {e}")
            return False


# Singleton instance
_message_broker: Optional[MessageBroker] = None


def get_message_broker(broker_type: str = "memory", **kwargs) -> MessageBroker:
    """
    Get a message broker instance.
    
    Args:
        broker_type: "memory" or "redis"
        **kwargs: Additional arguments for broker (e.g., redis_url for Redis)
        
    Returns:
        MessageBroker instance
    """
    global _message_broker
    
    if broker_type == "redis":
        _message_broker = RedisMessageBroker(**kwargs)
    else:
        _message_broker = InMemoryMessageBroker()
    
    return _message_broker


def get_default_broker() -> MessageBroker:
    """Get the default (singleton) message broker."""
    global _message_broker
    if _message_broker is None:
        _message_broker = InMemoryMessageBroker()
    return _message_broker

