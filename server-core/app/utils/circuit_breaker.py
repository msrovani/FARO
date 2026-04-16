"""
Circuit Breaker Pattern for Fault Tolerance
Automatically falls back to alternative implementations when performance degrades.
"""
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, TypeVar
from functools import wraps

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker state."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Number of failures before opening
    success_threshold: int = 2  # Number of successes to close circuit
    timeout_ms: int = 60000  # Time to wait before trying half-open
    max_execution_time_ms: float = 5000  # Max execution time before considering failure


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[float] = None
    last_state_change: Optional[float] = None


class CircuitBreaker:
    """
    Circuit breaker for fault tolerance.
    Automatically falls back when performance degrades.
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        fallback: Optional[Callable] = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.fallback = fallback
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.last_state_change = time.time()
    
    def record_success(self):
        """Record a successful execution."""
        self.stats.total_successes += 1
        self.stats.consecutive_failures = 0
        self.stats.consecutive_successes += 1
        
        if self.state == CircuitState.HALF_OPEN:
            if self.stats.consecutive_successes >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
    
    def record_failure(self):
        """Record a failed execution."""
        self.stats.total_failures += 1
        self.stats.consecutive_failures += 1
        self.stats.consecutive_successes = 0
        self.stats.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            if self.stats.consecutive_failures >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)
        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state."""
        self.state = new_state
        self.last_state_change = time.time()
        self.stats.consecutive_failures = 0
        self.stats.consecutive_successes = 0
    
    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if time.time() - self.last_state_change > (self.config.timeout_ms / 1000):
                self._transition_to(CircuitState.HALF_OPEN)
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        return False
    
    def execute(self, func: Callable, *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        self.stats.total_calls += 1
        
        if not self.can_execute():
            if self.fallback:
                return self.fallback(*args, **kwargs)
            raise Exception(f"Circuit breaker {self.name} is OPEN")
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Check for timeout
            if execution_time_ms > self.config.max_execution_time_ms:
                self.record_failure()
                if self.fallback:
                    return self.fallback(*args, **kwargs)
                raise Exception(f"Execution timeout: {execution_time_ms}ms")
            
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            if self.fallback:
                return self.fallback(*args, **kwargs)
            raise e
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self.stats.total_calls,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
            "consecutive_failures": self.stats.consecutive_failures,
            "consecutive_successes": self.stats.consecutive_successes,
            "failure_rate": self.stats.total_failures / self.stats.total_calls if self.stats.total_calls > 0 else 0.0,
            "last_failure_time": self.stats.last_failure_time,
            "last_state_change": self.last_state_change,
        }


# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
    fallback: Optional[Callable] = None,
) -> CircuitBreaker:
    """Get or create circuit breaker."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config, fallback)
    return _circuit_breakers[name]


def with_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
    fallback: Optional[Callable] = None,
):
    """
    Decorator to add circuit breaker protection to a function.
    
    Args:
        name: Name of the circuit breaker
        config: Circuit breaker configuration
        fallback: Fallback function to call when circuit is open
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            breaker = get_circuit_breaker(name, config, fallback)
            return breaker.execute(func, *args, **kwargs)
        return wrapper
    return decorator
