"""
Advanced Load Balancer for Agent System - Critical for Uptime
Provides high availability, redundancy, and intelligent task distribution.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class AgentHealthStatus(Enum):
    """Agent health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class AgentInstance:
    """Represents an agent instance in the pool."""
    agent_id: str
    agent_type: str
    agent: Any  # BaseAgent instance
    capacity: int = 5  # Max concurrent tasks
    current_load: int = 0
    health_status: AgentHealthStatus = AgentHealthStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    failure_count: int = 0
    success_count: int = 0
    total_tasks: int = 0
    average_task_time: float = 0.0
    last_activity: Optional[datetime] = None
    
    def is_available(self) -> bool:
        """Check if agent can accept new tasks."""
        return (
            self.health_status in [AgentHealthStatus.HEALTHY, AgentHealthStatus.DEGRADED] and
            self.current_load < self.capacity
        )
    
    def get_utilization(self) -> float:
        """Get current utilization percentage."""
        if self.capacity == 0:
            return 0.0
        return (self.current_load / self.capacity) * 100
    
    def get_success_rate(self) -> float:
        """Get success rate percentage."""
        if self.total_tasks == 0:
            return 0.0
        return (self.success_count / self.total_tasks) * 100


@dataclass
class QueuedTask:
    """Task in the queue with priority."""
    task: Any  # Task object
    priority: TaskPriority
    queued_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    assigned_to: Optional[str] = None


class LoadBalancer:
    """
    Advanced load balancer for agent system.
    Provides high availability, failover, and intelligent routing.
    """
    
    def __init__(self):
        self.agent_pools: Dict[str, List[AgentInstance]] = {}  # agent_type -> [instances]
        self.task_queues: Dict[str, deque] = {}  # agent_type -> priority queue
        self.health_check_interval = 30  # seconds
        self.circuit_breaker_threshold = 5  # failures before circuit opens
        self.circuit_breaker_timeout = 60  # seconds before retry
        
        # Circuit breakers per agent
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}  # agent_id -> {state, failures, last_failure}
        
        # Metrics
        self.total_tasks_distributed = 0
        self.total_failovers = 0
        self.start_time = datetime.now()
        
        # Health check thread
        self._health_check_thread: Optional[threading.Thread] = None
        self._running = False
    
    def register_agent(self, agent: Any, capacity: int = 5, instance_id: Optional[str] = None):
        """
        Register an agent instance with the load balancer.
        
        Args:
            agent: BaseAgent instance
            capacity: Maximum concurrent tasks for this agent
            instance_id: Optional custom instance ID
        """
        instance_id = instance_id or f"{agent.agent_id}_{len(self.agent_pools.get(agent.agent_type.value, []))}"
        
        instance = AgentInstance(
            agent_id=instance_id,
            agent_type=agent.agent_type.value,
            agent=agent,
            capacity=capacity,
            health_status=AgentHealthStatus.HEALTHY
        )
        
        if agent.agent_type.value not in self.agent_pools:
            self.agent_pools[agent.agent_type.value] = []
            self.task_queues[agent.agent_type.value] = deque()
        
        self.agent_pools[agent.agent_type.value].append(instance)
        self.circuit_breakers[instance_id] = {
            "state": "closed",  # closed, open, half_open
            "failures": 0,
            "last_failure": None
        }
        
        logger.info(f"Registered agent {instance_id} ({agent.agent_type.value}) with capacity {capacity}")
        
        # Start health checks if not running
        if not self._running:
            self.start_health_checks()
    
    def start_health_checks(self):
        """Start background health check thread."""
        if self._running:
            return
        
        self._running = True
        
        def health_check_loop():
            while self._running:
                try:
                    self._perform_health_checks()
                    time.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"Error in health check loop: {e}")
        
        self._health_check_thread = threading.Thread(target=health_check_loop, daemon=True)
        self._health_check_thread.start()
        logger.info("Load balancer health checks started")
    
    def stop_health_checks(self):
        """Stop health check thread."""
        self._running = False
        if self._health_check_thread:
            self._health_check_thread.join(timeout=5)
    
    def _perform_health_checks(self):
        """Perform health checks on all agent instances."""
        for agent_type, instances in self.agent_pools.items():
            for instance in instances:
                self._check_agent_health(instance)
    
    def _check_agent_health(self, instance: AgentInstance):
        """Check health of a single agent instance."""
        try:
            # Check if agent is responsive
            status = instance.agent.get_status()
            
            # Update metrics
            instance.current_load = status.get("active_tasks", 0)
            instance.total_tasks = status.get("completed_tasks", 0) + status.get("failed_tasks", 0)
            
            # Determine health based on failure rate
            if instance.total_tasks > 0:
                failure_rate = (instance.failure_count / instance.total_tasks) * 100
                if failure_rate > 50:
                    instance.health_status = AgentHealthStatus.UNHEALTHY
                elif failure_rate > 20:
                    instance.health_status = AgentHealthStatus.DEGRADED
                else:
                    instance.health_status = AgentHealthStatus.HEALTHY
            
            instance.last_health_check = datetime.now()
            
            # Reset circuit breaker if healthy
            if instance.health_status == AgentHealthStatus.HEALTHY:
                cb = self.circuit_breakers[instance.agent_id]
                if cb["state"] == "open":
                    # Check if timeout passed
                    if cb["last_failure"] and \
                       (datetime.now() - cb["last_failure"]).total_seconds() > self.circuit_breaker_timeout:
                        cb["state"] = "half_open"
                        logger.info(f"Circuit breaker half-open for {instance.agent_id}")
        
        except Exception as e:
            logger.warning(f"Health check failed for {instance.agent_id}: {e}")
            instance.health_status = AgentHealthStatus.UNHEALTHY
            instance.failure_count += 1
    
    def route_task(self, task: Any, priority: TaskPriority = TaskPriority.NORMAL, 
                   routing_algorithm: str = "least_busy") -> Optional[AgentInstance]:
        """
        Route a task to an appropriate agent instance.
        
        Args:
            task: Task to route
            priority: Task priority
            routing_algorithm: "round_robin", "least_busy", "random", "health_based"
            
        Returns:
            AgentInstance if routing successful, None otherwise
        """
        agent_type = task.agent_type.value if hasattr(task.agent_type, 'value') else str(task.agent_type)
        
        if agent_type not in self.agent_pools:
            logger.warning(f"No agents registered for type {agent_type}")
            return None
        
        instances = self.agent_pools[agent_type]
        
        # Filter available instances (healthy and under capacity)
        available = [inst for inst in instances if inst.is_available() and 
                    self._is_circuit_closed(inst.agent_id)]
        
        if not available:
            logger.warning(f"No available agents for type {agent_type}")
            # Queue task for later
            self._queue_task(task, priority, agent_type)
            return None
        
        # Route based on algorithm
        if routing_algorithm == "least_busy":
            instance = min(available, key=lambda x: x.get_utilization())
        elif routing_algorithm == "round_robin":
            instance = available[self.total_tasks_distributed % len(available)]
        elif routing_algorithm == "health_based":
            # Prefer healthy over degraded
            healthy = [inst for inst in available if inst.health_status == AgentHealthStatus.HEALTHY]
            if healthy:
                instance = min(healthy, key=lambda x: x.get_utilization())
            else:
                instance = min(available, key=lambda x: x.get_utilization())
        else:
            instance = available[0]  # Default: first available
        
        # Assign task
        instance.current_load += 1
        instance.last_activity = datetime.now()
        self.total_tasks_distributed += 1
        
        logger.info(f"Routed task {task.id} to {instance.agent_id} ({routing_algorithm})")
        return instance
    
    def _is_circuit_closed(self, agent_id: str) -> bool:
        """Check if circuit breaker is closed (allowing traffic)."""
        cb = self.circuit_breakers.get(agent_id)
        if not cb:
            return True
        
        if cb["state"] == "closed":
            return True
        elif cb["state"] == "open":
            # Check if timeout passed
            if cb["last_failure"] and \
               (datetime.now() - cb["last_failure"]).total_seconds() > self.circuit_breaker_timeout:
                cb["state"] = "half_open"
                return True
            return False
        else:  # half_open
            return True
    
    def record_task_success(self, agent_id: str):
        """Record successful task completion."""
        instance = self._find_instance(agent_id)
        if instance:
            instance.success_count += 1
            instance.current_load = max(0, instance.current_load - 1)
            instance.total_tasks += 1
            
            # Reset circuit breaker
            cb = self.circuit_breakers[agent_id]
            if cb["state"] == "half_open":
                cb["state"] = "closed"
                cb["failures"] = 0
                logger.info(f"Circuit breaker closed for {agent_id} after successful task")
    
    def record_task_failure(self, agent_id: str):
        """Record task failure and update circuit breaker."""
        instance = self._find_instance(agent_id)
        if instance:
            instance.failure_count += 1
            instance.current_load = max(0, instance.current_load - 1)
            instance.total_tasks += 1
            
            # Update circuit breaker
            cb = self.circuit_breakers[agent_id]
            cb["failures"] += 1
            cb["last_failure"] = datetime.now()
            
            if cb["failures"] >= self.circuit_breaker_threshold:
                cb["state"] = "open"
                logger.warning(f"Circuit breaker opened for {agent_id} after {cb['failures']} failures")
            
            # Attempt failover if task was assigned
            # This would trigger retry logic
    
    def _find_instance(self, agent_id: str) -> Optional[AgentInstance]:
        """Find agent instance by ID."""
        for instances in self.agent_pools.values():
            for instance in instances:
                if instance.agent_id == agent_id:
                    return instance
        return None
    
    def _queue_task(self, task: Any, priority: TaskPriority, agent_type: str):
        """Queue task for later processing."""
        queued = QueuedTask(task=task, priority=priority)
        self.task_queues[agent_type].append(queued)
        logger.info(f"Queued task {task.id} for {agent_type} (priority: {priority.name})")
    
    def process_queued_tasks(self):
        """Process queued tasks when agents become available."""
        for agent_type, queue in self.task_queues.items():
            if not queue:
                continue
            
            instances = self.agent_pools.get(agent_type, [])
            available = [inst for inst in instances if inst.is_available() and 
                        self._is_circuit_closed(inst.agent_id)]
            
            while queue and available:
                # Get highest priority task
                queued_task = queue.popleft()
                instance = min(available, key=lambda x: x.get_utilization())
                
                if instance.agent.assign_task(queued_task.task):
                    instance.current_load += 1
                    logger.info(f"Processed queued task {queued_task.task.id}")
                else:
                    # Put back if assignment failed
                    queue.appendleft(queued_task)
                    break
    
    def get_pool_status(self, agent_type: str) -> Dict[str, Any]:
        """Get status of agent pool for a specific type."""
        instances = self.agent_pools.get(agent_type, [])
        
        healthy = sum(1 for inst in instances if inst.health_status == AgentHealthStatus.HEALTHY)
        total_capacity = sum(inst.capacity for inst in instances)
        current_load = sum(inst.current_load for inst in instances)
        
        return {
            "agent_type": agent_type,
            "total_instances": len(instances),
            "healthy_instances": healthy,
            "total_capacity": total_capacity,
            "current_load": current_load,
            "utilization_percent": (current_load / total_capacity * 100) if total_capacity > 0 else 0,
            "queued_tasks": len(self.task_queues.get(agent_type, [])),
            "instances": [
                {
                    "agent_id": inst.agent_id,
                    "health": inst.health_status.value,
                    "load": inst.current_load,
                    "capacity": inst.capacity,
                    "utilization": inst.get_utilization(),
                    "success_rate": inst.get_success_rate()
                }
                for inst in instances
            ]
        }
    
    def get_overall_status(self) -> Dict[str, Any]:
        """Get overall load balancer status."""
        total_instances = sum(len(instances) for instances in self.agent_pools.values())
        total_capacity = sum(sum(inst.capacity for inst in instances) 
                           for instances in self.agent_pools.values())
        total_load = sum(sum(inst.current_load for inst in instances) 
                        for instances in self.agent_pools.values())
        total_queued = sum(len(queue) for queue in self.task_queues.values())
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "total_agent_types": len(self.agent_pools),
            "total_instances": total_instances,
            "total_capacity": total_capacity,
            "current_load": total_load,
            "utilization_percent": (total_load / total_capacity * 100) if total_capacity > 0 else 0,
            "queued_tasks": total_queued,
            "tasks_distributed": self.total_tasks_distributed,
            "failovers": self.total_failovers,
            "uptime_seconds": uptime,
            "pools": {
                agent_type: self.get_pool_status(agent_type)
                for agent_type in self.agent_pools.keys()
            }
        }


# Singleton instance
_load_balancer: Optional[LoadBalancer] = None


def get_load_balancer() -> LoadBalancer:
    """Get the singleton LoadBalancer instance."""
    global _load_balancer
    if _load_balancer is None:
        _load_balancer = LoadBalancer()
    return _load_balancer

