"""
Circuit Breaker Middleware for FastAPI
Applies circuit breaker pattern to critical endpoints for fault tolerance.
"""
import time
from enum import Enum
from typing import Callable, Optional, TypeVar
from functools import wraps
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Import Prometheus metrics
try:
    from app.core.observability import (
        CIRCUIT_BREAKER_STATE,
        CIRCUIT_BREAKER_FAILURES,
        CIRCUIT_BREAKER_REJECTIONS,
        record_circuit_state,
    )
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False

T = TypeVar('T')


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service has recovered


class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: float = 60.0,
        excluded_status_codes: set = None,
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.excluded_status_codes = excluded_status_codes or {401, 403, 404, 422}


class CircuitBreakerState:
    """Tracks circuit breaker state."""
    def __init__(self):
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change = time.time()


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState()
    
    def record_success(self):
        """Record a successful execution."""
        self.state.failures = 0
        self.state.successes += 1
        
        if self.state.state == CircuitState.HALF_OPEN:
            if self.state.successes >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
    
    def record_failure(self, status_code: int = 500):
        """Record a failed execution."""
        if status_code in self.config.excluded_status_codes:
            return
            
        self.state.failures += 1
        self.state.last_failure_time = time.time()
        self.state.successes = 0
        
        # Record metrics
        if METRICS_ENABLED:
            CIRCUIT_BREAKER_FAILURES.labels(endpoint=self.name).inc()
        
        if self.state.state == CircuitState.CLOSED:
            if self.state.failures >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)
        elif self.state.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state."""
        self.state.state = new_state
        self.state.last_state_change = time.time()
        self.state.failures = 0
        self.state.successes = 0
        
        # Record state change metrics
        if METRICS_ENABLED:
            state_value = {"closed": 0, "open": 1, "half_open": 2}[new_state.value]
            CIRCUIT_BREAKER_STATE.labels(endpoint=self.name).observe(state_value)
            # Also update Gauge for real-time state
            record_circuit_state(endpoint=self.name, state=state_value)
    
    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state.state == CircuitState.CLOSED:
            return True
        elif self.state.state == CircuitState.OPEN:
            # Check if timeout has passed
            if time.time() - self.state.last_state_change > self.config.timeout_seconds:
                self._transition_to(CircuitState.HALF_OPEN)
                return True
            return False
        elif self.state.state == CircuitState.HALF_OPEN:
            return True
        return False
    
    def get_status(self) -> dict:
        """Get circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.state.value,
            "failures": self.state.failures,
            "successes": self.state.successes,
            "last_failure": self.state.last_failure_time,
        }


# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
) -> CircuitBreaker:
    """Get or create circuit breaker."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def with_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator to add circuit breaker protection to a function."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            breaker = get_circuit_breaker(name, config)
            
            if not breaker.can_execute():
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "Service Unavailable",
                        "message": f"Circuit breaker {name} is OPEN",
                        "retry_after": int(breaker.config.timeout_seconds),
                    }
                )
            
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                # Get status code from response if available
                status_code = 500
                if hasattr(e, 'status_code'):
                    status_code = e.status_code
                breaker.record_failure(status_code)
                raise
        
        return wrapper
    return decorator


# Critical endpoints that should have circuit breaker protection
CIRCUIT_BREAKER_ENDPOINTS = {
    "mobile_sync": CircuitBreakerConfig(
        failure_threshold=10,
        success_threshold=3,
        timeout_seconds=120.0,
        excluded_status_codes={401, 403},
    ),
    "ocr_processing": CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout_seconds=60.0,
        excluded_status_codes={401, 403, 422},
    ),
    "algorithm_execution": CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout_seconds=60.0,
        excluded_status_codes={401, 403},
    ),
    "database_query": CircuitBreakerConfig(
        failure_threshold=15,
        success_threshold=3,
        timeout_seconds=30.0,
        excluded_status_codes={401, 403, 404},
    ),
}


def get_endpoint_circuit_breaker(endpoint_name: str) -> CircuitBreaker:
    """Get circuit breaker for a specific endpoint."""
    config = CIRCUIT_BREAKER_ENDPOINTS.get(endpoint_name)
    return get_circuit_breaker(endpoint_name, config)