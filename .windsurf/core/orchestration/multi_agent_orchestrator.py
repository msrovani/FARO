"""
Multi-Agent Orchestrator - Real implementation for SUPERDEV 2.0
Implements agent coordination, task routing, and collaboration
"""
import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import logging
from enum import Enum
from collections import defaultdict, deque
import heapq

# Import our systems
try:
    from ..memory.hybrid_rag import HybridRAGMemory, MemoryData, MemoryQuery
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

try:
    from ..coordination.event_bus import EventBus, Event
    EVENT_BUS_AVAILABLE = True
except ImportError:
    EVENT_BUS_AVAILABLE = False


class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class TaskPriority(Enum):
    """Task priority enumeration"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentCapability:
    """Agent capability definition"""
    name: str
    description: str
    keywords: List[str]
    confidence: float
    max_concurrent_tasks: int = 1


@dataclass
class Agent:
    """Agent definition"""
    id: str
    name: str
    type: str
    capabilities: List[AgentCapability]
    status: AgentStatus = AgentStatus.IDLE
    current_tasks: Set[str] = None
    performance_metrics: Dict[str, float] = None
    last_active: str = ""
    
    def __post_init__(self):
        if self.current_tasks is None:
            self.current_tasks = set()
        if self.performance_metrics is None:
            self.performance_metrics = {"success_rate": 1.0, "avg_response_time": 0.0, "tasks_completed": 0}
        if self.last_active == "":
            self.last_active = datetime.now().isoformat()


@dataclass
class Task:
    """Task definition"""
    id: str
    type: str
    description: str
    priority: TaskPriority
    requirements: List[str]
    context: Dict[str, Any]
    created_at: str
    deadline: Optional[str] = None
    assigned_agent: Optional[str] = None
    status: str = "pending"  # pending, assigned, in_progress, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    agent_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AgentRegistry:
    """Registry for managing agents"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.capability_index: Dict[str, List[str]] = defaultdict(list)
        
    def register_agent(self, agent: Agent):
        """Register an agent"""
        self.agents[agent.id] = agent
        
        # Index capabilities
        for capability in agent.capabilities:
            for keyword in capability.keywords:
                self.capability_index[keyword.lower()].append(agent.id)
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            
            # Remove from capability index
            for capability in agent.capabilities:
                for keyword in capability.keywords:
                    if keyword.lower() in self.capability_index:
                        self.capability_index[keyword.lower()].remove(agent_id)
            
            del self.agents[agent_id]
    
    def find_agents_by_capability(self, keywords: List[str]) -> List[str]:
        """Find agents that match given keywords"""
        matching_agents = set()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in self.capability_index:
                matching_agents.update(self.capability_index[keyword_lower])
        
        return list(matching_agents)
    
    def get_available_agents(self) -> List[Agent]:
        """Get agents that are available for work"""
        return [
            agent for agent in self.agents.values()
            if agent.status == AgentStatus.IDLE and len(agent.current_tasks) < 1
        ]
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)


class TaskQueue:
    """Priority queue for tasks"""
    
    def __init__(self):
        self.tasks: List[Tuple[int, str, Task]] = []  # (priority, timestamp, task)
        self.task_index: Dict[str, Task] = {}
        self.counter = 0
        
    def add_task(self, task: Task):
        """Add task to queue"""
        priority = task.priority.value * -1  # Negative for max-heap
        timestamp = self.counter
        self.counter += 1
        
        heapq.heappush(self.tasks, (priority, timestamp, task))
        self.task_index[task.id] = task
    
    def get_next_task(self) -> Optional[Task]:
        """Get next task from queue"""
        if not self.tasks:
            return None
        
        _, _, task = heapq.heappop(self.tasks)
        
        if task.id in self.task_index:
            del self.task_index[task.id]
        
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self.task_index.get(task_id)
    
    def remove_task(self, task_id: str) -> bool:
        """Remove task from queue"""
        if task_id in self.task_index:
            del self.task_index[task_id]
            # Note: This is inefficient for heap, but works for our use case
            return True
        return False
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks"""
        return list(self.task_index.values())


class TaskDependencyManager:
    """Manage task dependencies"""
    
    def __init__(self):
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.dependents: Dict[str, Set[str]] = defaultdict(set)
        self.completed_tasks: Set[str] = set()
        
    def add_dependencies(self, task_id: str, dependencies: List[str]):
        """Add dependencies for a task"""
        for dep_id in dependencies:
            self.dependencies[task_id].add(dep_id)
            self.dependents[dep_id].add(task_id)
    
    def can_execute(self, task_id: str) -> bool:
        """Check if task can be executed (all dependencies completed)"""
        dependencies = self.dependencies.get(task_id, set())
        return dependencies.issubset(self.completed_tasks)
    
    def mark_completed(self, task_id: str):
        """Mark task as completed"""
        self.completed_tasks.add(task_id)
    
    def get_ready_tasks(self, tasks: List[Task]) -> List[Task]:
        """Get tasks that are ready to execute"""
        ready_tasks = []
        
        for task in tasks:
            if self.can_execute(task.id):
                ready_tasks.append(task)
        
        return ready_tasks


class MultiAgentOrchestrator:
    """Main Multi-Agent Orchestrator"""
    
    def __init__(self, memory_system: Optional[HybridRAGMemory] = None):
        self.memory_system = memory_system
        self.event_bus = EventBus() if EVENT_BUS_AVAILABLE else None
        
        self.agent_registry = AgentRegistry()
        self.task_queue = TaskQueue()
        self.dependency_manager = TaskDependencyManager()
        
        self.active_tasks: Dict[str, Task] = {}
        self.task_history: List[TaskResult] = []
        
        self.logger = logging.getLogger("MultiAgentOrchestrator")
        
        # Performance tracking
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_execution_time": 0.0,
            "agent_utilization": defaultdict(float)
        }
        
        # Register default agents
        self._register_default_agents()
        
        # Start background tasks
        self.running = True
        self.scheduler_task = None
        
    def _register_default_agents(self):
        """Register default specialized agents"""
        # Frontend Specialist
        frontend_agent = Agent(
            id="frontend-specialist",
            name="Frontend Specialist",
            type="specialist",
            capabilities=[
                AgentCapability(
                    name="react_development",
                    description="React component development and styling",
                    keywords=["react", "component", "css", "frontend", "ui"],
                    confidence=0.9
                ),
                AgentCapability(
                    name="javascript_typescript",
                    description="JavaScript/TypeScript development",
                    keywords=["javascript", "typescript", "js", "ts"],
                    confidence=0.85
                )
            ]
        )
        
        # Backend Specialist
        backend_agent = Agent(
            id="backend-specialist",
            name="Backend Specialist",
            type="specialist",
            capabilities=[
                AgentCapability(
                    name="api_development",
                    description="REST API and backend development",
                    keywords=["api", "backend", "server", "endpoint"],
                    confidence=0.9
                ),
                AgentCapability(
                    name="database_design",
                    description="Database design and optimization",
                    keywords=["database", "sql", "schema", "query"],
                    confidence=0.8
                )
            ]
        )
        
        # Database Architect
        db_agent = Agent(
            id="database-architect",
            name="Database Architect",
            type="specialist",
            capabilities=[
                AgentCapability(
                    name="database_architecture",
                    description="Database architecture and design",
                    keywords=["database", "architecture", "schema", "design"],
                    confidence=0.95
                ),
                AgentCapability(
                    name="performance_optimization",
                    description="Database performance optimization",
                    keywords=["performance", "optimization", "index", "query"],
                    confidence=0.85
                )
            ]
        )
        
        # Security Auditor
        security_agent = Agent(
            id="security-auditor",
            name="Security Auditor",
            type="specialist",
            capabilities=[
                AgentCapability(
                    name="security_analysis",
                    description="Security vulnerability analysis",
                    keywords=["security", "vulnerability", "audit", "owasp"],
                    confidence=0.9
                ),
                AgentCapability(
                    name="penetration_testing",
                    description="Penetration testing and security testing",
                    keywords=["penetration", "testing", "security", "pentest"],
                    confidence=0.85
                )
            ]
        )
        
        # Test Engineer
        test_agent = Agent(
            id="test-engineer",
            name="Test Engineer",
            type="specialist",
            capabilities=[
                AgentCapability(
                    name="test_development",
                    description="Test development and automation",
                    keywords=["test", "testing", "automation", "pytest"],
                    confidence=0.9
                ),
                AgentCapability(
                    name="quality_assurance",
                    description="Quality assurance and testing strategies",
                    keywords=["quality", "assurance", "qa", "testing"],
                    confidence=0.85
                )
            ]
        )
        
        # Register all agents
        for agent in [frontend_agent, backend_agent, db_agent, security_agent, test_agent]:
            self.agent_registry.register_agent(agent)
    
    async def start(self):
        """Start the orchestrator"""
        self.logger.info("Starting Multi-Agent Orchestrator")
        
        if self.event_bus:
            # Subscribe to events
            self.event_bus.subscribe("task_completed", self._handle_task_completed)
            self.event_bus.subscribe("task_failed", self._handle_task_failed)
            self.event_bus.subscribe("agent_status_changed", self._handle_agent_status_changed)
        
        # Start scheduler
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
    
    async def stop(self):
        """Stop the orchestrator"""
        self.logger.info("Stopping Multi-Agent Orchestrator")
        self.running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
    
    async def submit_task(self, task: Task) -> str:
        """Submit a task for execution"""
        # Add dependencies
        self.dependency_manager.add_dependencies(task.id, task.dependencies)
        
        # Add to queue
        self.task_queue.add_task(task)
        
        self.logger.info(f"Task submitted: {task.id} - {task.description}")
        
        # Store in memory if available
        if self.memory_system:
            task_memory = MemoryData(
                id=f"task_{task.id}",
                content=f"Task: {task.description}",
                mom_type="decision",
                category="task",
                importance=task.priority.value / 4.0,  # Normalize to 0-1
                tags=["task", task.type]
            )
            self.memory_system.store_with_citation(task_memory)
        
        return task.id
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Get ready tasks
                pending_tasks = self.task_queue.get_pending_tasks()
                ready_tasks = self.dependency_manager.get_ready_tasks(pending_tasks)
                
                # Process ready tasks
                for task in ready_tasks:
                    await self._assign_task(task)
                
                # Wait before next iteration
                await asyncio.sleep(1.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(5.0)
    
    async def _assign_task(self, task: Task):
        """Assign task to appropriate agent"""
        # Find suitable agents
        candidate_agents = self.agent_registry.find_agents_by_capability(task.requirements)
        
        if not candidate_agents:
            self.logger.warning(f"No agents found for task {task.id} with requirements: {task.requirements}")
            task.status = "failed"
            task.error = "No suitable agents available"
            return
        
        # Get available agents
        available_agents = [
            self.agent_registry.get_agent(agent_id) 
            for agent_id in candidate_agents
            if self.agent_registry.get_agent(agent_id) and 
               self.agent_registry.get_agent(agent_id).status == AgentStatus.IDLE
        ]
        
        if not available_agents:
            self.logger.warning(f"No available agents for task {task.id}")
            return  # Keep in queue for later
        
        # Select best agent (simple selection - could be improved with ML)
        best_agent = self._select_best_agent(available_agents, task)
        
        # Assign task
        await self._execute_task(task, best_agent)
    
    def _select_best_agent(self, agents: List[Agent], task: Task) -> Agent:
        """Select the best agent for a task"""
        # Simple scoring based on capabilities and performance
        best_score = -1
        best_agent = agents[0]
        
        for agent in agents:
            score = 0.0
            
            # Capability matching
            for capability in agent.capabilities:
                for requirement in task.requirements:
                    if requirement.lower() in [kw.lower() for kw in capability.keywords]:
                        score += capability.confidence
            
            # Performance metrics
            score += agent.performance_metrics["success_rate"] * 0.5
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent
    
    async def _execute_task(self, task: Task, agent: Agent):
        """Execute task on agent"""
        # Update task and agent status
        task.status = "assigned"
        task.assigned_agent = agent.id
        
        agent.status = AgentStatus.BUSY
        agent.current_tasks.add(task.id)
        agent.last_active = datetime.now().isoformat()
        
        # Remove from queue
        self.task_queue.remove_task(task.id)
        
        # Add to active tasks
        self.active_tasks[task.id] = task
        
        self.logger.info(f"Task {task.id} assigned to agent {agent.id}")
        
        # Emit event
        if self.event_bus:
            await self.event_bus.emit("task_assigned", {
                "task_id": task.id,
                "agent_id": agent.id
            })
        
        # Execute task (simulate execution)
        try:
            result = await self._simulate_task_execution(task, agent)
            
            # Handle result
            if result.success:
                await self._complete_task(task, agent, result)
            else:
                await self._fail_task(task, agent, result.error or "Unknown error")
                
        except Exception as e:
            await self._fail_task(task, agent, str(e))
    
    async def _simulate_task_execution(self, task: Task, agent: Agent) -> TaskResult:
        """Simulate task execution (in real system, this would call the actual agent)"""
        start_time = datetime.now()
        
        # Simulate execution time based on task complexity
        execution_time = 2.0 + len(task.description) * 0.1
        await asyncio.sleep(execution_time)
        
        # Simulate success/failure based on agent performance
        success_probability = agent.performance_metrics["success_rate"]
        success = success_probability > 0.7 or (hash(task.id) % 100) / 100 < success_probability
        
        if success:
            result = TaskResult(
                task_id=task.id,
                agent_id=agent.id,
                success=True,
                result={
                    "output": f"Task completed: {task.description}",
                    "artifacts": ["file1.txt", "file2.txt"],
                    "metrics": {"quality": 0.9, "performance": 0.85}
                },
                execution_time=execution_time
            )
        else:
            result = TaskResult(
                task_id=task.id,
                agent_id=agent.id,
                success=False,
                error="Simulated execution failure",
                execution_time=execution_time
            )
        
        return result
    
    async def _complete_task(self, task: Task, agent: Agent, result: TaskResult):
        """Complete task execution"""
        # Update task
        task.status = "completed"
        task.result = result.result
        
        # Update agent
        agent.current_tasks.discard(task.id)
        if len(agent.current_tasks) == 0:
            agent.status = AgentStatus.IDLE
        
        # Update agent performance metrics
        agent.performance_metrics["tasks_completed"] += 1
        agent.performance_metrics["success_rate"] = (
            (agent.performance_metrics["success_rate"] * (agent.performance_metrics["tasks_completed"] - 1) + 1.0) /
            agent.performance_metrics["tasks_completed"]
        )
        
        # Update metrics
        self.metrics["tasks_completed"] += 1
        self._update_avg_execution_time(result.execution_time)
        
        # Mark dependencies as completed
        self.dependency_manager.mark_completed(task.id)
        
        # Remove from active tasks
        if task.id in self.active_tasks:
            del self.active_tasks[task.id]
        
        # Add to history
        self.task_history.append(result)
        
        # Store in memory
        if self.memory_system:
            completion_memory = MemoryData(
                id=f"completed_{task.id}",
                content=f"Completed task: {task.description} by {agent.name}",
                mom_type="learning",
                category="task_execution",
                importance=0.7,
                tags=["completed", task.type, agent.type]
            )
            self.memory_system.store_with_citation(completion_memory)
        
        # Emit event
        if self.event_bus:
            await self.event_bus.emit("task_completed", {
                "task_id": task.id,
                "agent_id": agent.id,
                "result": result.result
            })
        
        self.logger.info(f"Task {task.id} completed by agent {agent.id}")
    
    async def _fail_task(self, task: Task, agent: Agent, error: str):
        """Fail task execution"""
        # Update task
        task.status = "failed"
        task.error = error
        
        # Update agent
        agent.current_tasks.discard(task.id)
        if len(agent.current_tasks) == 0:
            agent.status = AgentStatus.IDLE
        
        # Update agent performance metrics
        agent.performance_metrics["tasks_completed"] += 1
        agent.performance_metrics["success_rate"] = (
            (agent.performance_metrics["success_rate"] * (agent.performance_metrics["tasks_completed"] - 1)) /
            agent.performance_metrics["tasks_completed"]
        )
        
        # Update metrics
        self.metrics["tasks_failed"] += 1
        
        # Remove from active tasks
        if task.id in self.active_tasks:
            del self.active_tasks[task.id]
        
        # Store in memory
        if self.memory_system:
            failure_memory = MemoryData(
                id=f"failed_{task.id}",
                content=f"Failed task: {task.description} - {error}",
                mom_type="learning",
                category="task_execution",
                importance=0.6,
                tags=["failed", task.type, agent.type]
            )
            self.memory_system.store_with_citation(failure_memory)
        
        # Emit event
        if self.event_bus:
            await self.event_bus.emit("task_failed", {
                "task_id": task.id,
                "agent_id": agent.id,
                "error": error
            })
        
        self.logger.error(f"Task {task.id} failed: {error}")
    
    def _update_avg_execution_time(self, execution_time: float):
        """Update average execution time metric"""
        completed_tasks = self.metrics["tasks_completed"]
        current_avg = self.metrics["avg_execution_time"]
        
        self.metrics["avg_execution_time"] = (
            (current_avg * (completed_tasks - 1) + execution_time) / completed_tasks
        )
    
    async def _handle_task_completed(self, event_data: Dict[str, Any]):
        """Handle task completed event"""
        self.logger.debug(f"Task completed event: {event_data}")
    
    async def _handle_task_failed(self, event_data: Dict[str, Any]):
        """Handle task failed event"""
        self.logger.debug(f"Task failed event: {event_data}")
    
    async def _handle_agent_status_changed(self, event_data: Dict[str, Any]):
        """Handle agent status changed event"""
        self.logger.debug(f"Agent status changed event: {event_data}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            "agents": {
                "total": len(self.agent_registry.agents),
                "available": len(self.agent_registry.get_available_agents()),
                "busy": len([a for a in self.agent_registry.agents.values() if a.status == AgentStatus.BUSY]),
                "offline": len([a for a in self.agent_registry.agents.values() if a.status == AgentStatus.OFFLINE])
            },
            "tasks": {
                "pending": len(self.task_queue.get_pending_tasks()),
                "active": len(self.active_tasks),
                "completed": self.metrics["tasks_completed"],
                "failed": self.metrics["tasks_failed"]
            },
            "metrics": {
                "avg_execution_time": self.metrics["avg_execution_time"],
                "success_rate": (
                    self.metrics["tasks_completed"] / 
                    (self.metrics["tasks_completed"] + self.metrics["tasks_failed"])
                    if (self.metrics["tasks_completed"] + self.metrics["tasks_failed"]) > 0 else 0
                )
            }
        }
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed agent status"""
        agent = self.agent_registry.get_agent(agent_id)
        if not agent:
            return None
        
        return {
            "id": agent.id,
            "name": agent.name,
            "type": agent.type,
            "status": agent.status.value,
            "current_tasks": list(agent.current_tasks),
            "performance_metrics": agent.performance_metrics,
            "last_active": agent.last_active,
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "confidence": cap.confidence
                }
                for cap in agent.capabilities
            ]
        }


# Factory function
def create_multi_agent_orchestrator(memory_system: Optional[HybridRAGMemory] = None) -> MultiAgentOrchestrator:
    """Create a Multi-Agent Orchestrator"""
    return MultiAgentOrchestrator(memory_system)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SUPERDEV Multi-Agent Orchestrator")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and test orchestrator
    memory_system = HybridRAGMemory() if MEMORY_AVAILABLE else None
    orchestrator = create_multi_agent_orchestrator(memory_system)
    
    async def test_orchestrator():
        await orchestrator.start()
        
        # Create test tasks
        tasks = [
            Task(
                id="task-1",
                type="frontend",
                description="Create React component for user profile",
                priority=TaskPriority.HIGH,
                requirements=["react", "component", "frontend"],
                context={"project": "web-app"},
                created_at=datetime.now().isoformat()
            ),
            Task(
                id="task-2",
                type="backend",
                description="Implement REST API for user management",
                priority=TaskPriority.MEDIUM,
                requirements=["api", "backend", "endpoint"],
                context={"project": "web-app"},
                created_at=datetime.now().isoformat(),
                dependencies=["task-1"]  # Depends on frontend completion
            ),
            Task(
                id="task-3",
                type="database",
                description="Design database schema for users",
                priority=TaskPriority.HIGH,
                requirements=["database", "schema", "design"],
                context={"project": "web-app"},
                created_at=datetime.now().isoformat()
            )
        ]
        
        # Submit tasks
        for task in tasks:
            await orchestrator.submit_task(task)
        
        # Wait for completion
        await asyncio.sleep(10.0)
        
        # Print status
        status = orchestrator.get_status()
        print(f"Orchestrator Status: {json.dumps(status, indent=2)}")
        
        # Print agent details
        for agent_id in ["frontend-specialist", "backend-specialist", "database-architect"]:
            agent_status = orchestrator.get_agent_status(agent_id)
            if agent_status:
                print(f"Agent {agent_id}: {json.dumps(agent_status, indent=2)}")
        
        await orchestrator.stop()
    
    asyncio.run(test_orchestrator())
