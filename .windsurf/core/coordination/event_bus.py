"""
Event Bus Implementation for SUPERDEV 2.0
Provides asynchronous communication between components
"""
import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from collections import defaultdict
from enum import Enum


class EventType(Enum):
    """Standard event types"""
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_ASSIGNED = "task_assigned"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    MEMORY_CAPTURE = "memory_capture"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    FLAVOR_SWITCH = "flavor_switch"
    CONTEXT_UPDATED = "context_updated"


@dataclass
class Event:
    """Event structure"""
    id: str
    type: str
    data: Dict[str, Any]
    timestamp: str
    source: str
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp == "":
            self.timestamp = datetime.now().isoformat()


@dataclass
class EventSubscription:
    """Event subscription"""
    event_type: str
    handler: Callable
    filter_func: Optional[Callable] = None
    active: bool = True


class EventBus:
    """Asynchronous Event Bus for component communication"""
    
    def __init__(self):
        self.subscriptions: Dict[str, List[EventSubscription]] = defaultdict(list)
        self.event_history: List[Event] = []
        self.max_history = 1000
        self.logger = logging.getLogger("EventBus")
        
        # Event queue for async processing
        self.event_queue = asyncio.Queue()
        self.running = False
        self.processor_task = None
        
        # Statistics
        self.stats = {
            "events_published": 0,
            "events_processed": 0,
            "subscriptions_active": 0,
            "handlers_failed": 0
        }
    
    async def start(self):
        """Start the event bus"""
        if self.running:
            return
        
        self.running = True
        self.processor_task = asyncio.create_task(self._process_events())
        self.logger.info("EventBus started")
    
    async def stop(self):
        """Stop the event bus"""
        if not self.running:
            return
        
        self.running = False
        
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("EventBus stopped")
    
    async def emit(self, event_type: str, data: Dict[str, Any], source: str = "unknown", session_id: Optional[str] = None) -> str:
        """Emit an event"""
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            data=data,
            timestamp=datetime.now().isoformat(),
            source=source,
            session_id=session_id
        )
        
        # Add to queue for processing
        await self.event_queue.put(event)
        
        # Update statistics
        self.stats["events_published"] += 1
        
        return event.id
    
    async def emit_sync(self, event_type: str, data: Dict[str, Any], source: str = "unknown", session_id: Optional[str] = None) -> str:
        """Emit an event and wait for processing"""
        event_id = await self.emit(event_type, data, source, session_id)
        
        # Wait for event to be processed
        while any(e.id == event_id for e in self.event_queue._queue):
            await asyncio.sleep(0.01)
        
        return event_id
    
    def subscribe(self, event_type: str, handler: Callable, filter_func: Optional[Callable] = None) -> str:
        """Subscribe to an event type"""
        subscription = EventSubscription(
            event_type=event_type,
            handler=handler,
            filter_func=filter_func
        )
        
        self.subscriptions[event_type].append(subscription)
        self.stats["subscriptions_active"] += 1
        
        self.logger.debug(f"Subscribed to {event_type}")
        
        return subscription.id if hasattr(subscription, 'id') else str(len(self.subscriptions[event_type]))
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """Unsubscribe from an event type"""
        subscriptions = self.subscriptions.get(event_type, [])
        
        for i, sub in enumerate(subscriptions):
            if sub.handler == handler:
                sub.active = False
                subscriptions.pop(i)
                self.stats["subscriptions_active"] -= 1
                self.logger.debug(f"Unsubscribed from {event_type}")
                break
    
    async def _process_events(self):
        """Process events from the queue"""
        while self.running:
            try:
                # Get event from queue
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                
                # Process event
                await self._handle_event(event)
                
                self.stats["events_processed"] += 1
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing event: {e}")
    
    async def _handle_event(self, event: Event):
        """Handle a single event"""
        # Add to history
        self.event_history.append(event)
        
        # Trim history if needed
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # Get subscriptions for this event type
        subscriptions = self.subscriptions.get(event.type, [])
        
        # Process each subscription
        for subscription in subscriptions:
            if not subscription.active:
                continue
            
            # Apply filter if present
            if subscription.filter_func and not subscription.filter_func(event):
                continue
            
            try:
                # Call handler
                if asyncio.iscoroutinefunction(subscription.handler):
                    await subscription.handler(event.data)
                else:
                    subscription.handler(event.data)
                    
            except Exception as e:
                self.logger.error(f"Error in event handler for {event.type}: {e}")
                self.stats["handlers_failed"] += 1
    
    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Get events from history"""
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        return events[-limit:] if limit > 0 else events
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            **self.stats,
            "queue_size": self.event_queue.qsize(),
            "history_size": len(self.event_history),
            "active_subscriptions": {
                event_type: len([s for s in subs if s.active])
                for event_type, subs in self.subscriptions.items()
            }
        }


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


async def start_global_event_bus():
    """Start the global event bus"""
    event_bus = get_event_bus()
    await event_bus.start()


async def stop_global_event_bus():
    """Stop the global event bus"""
    event_bus = get_event_bus()
    await event_bus.stop()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SUPERDEV Event Bus")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def test_event_bus():
        event_bus = EventBus()
        await event_bus.start()
        
        # Test handlers
        async def task_completed_handler(data):
            print(f"Task completed: {data}")
        
        async def task_failed_handler(data):
            print(f"Task failed: {data}")
        
        # Subscribe to events
        event_bus.subscribe("task_completed", task_completed_handler)
        event_bus.subscribe("task_failed", task_failed_handler)
        
        # Emit test events
        await event_bus.emit("task_completed", {
            "task_id": "task-1",
            "agent_id": "agent-1",
            "result": {"status": "success"}
        }, source="test")
        
        await event_bus.emit("task_failed", {
            "task_id": "task-2",
            "agent_id": "agent-2",
            "error": "Simulated failure"
        }, source="test")
        
        # Wait for processing
        await asyncio.sleep(1.0)
        
        # Print statistics
        stats = event_bus.get_statistics()
        print(f"Event Bus Statistics: {json.dumps(stats, indent=2)}")
        
        await event_bus.stop()
    
    asyncio.run(test_event_bus())
