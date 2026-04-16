"""
Performance Monitoring and Adaptive Configuration
Monitors task performance and automatically adjusts configuration for optimal resource utilization.
"""
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Optional
from enum import Enum


class PerformanceState(Enum):
    """Performance state of a task type."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class PerformanceMetrics:
    """Performance metrics for a task type."""
    task_type: str
    avg_execution_time_ms: float
    p95_execution_time_ms: float
    p99_execution_time_ms: float
    success_rate: float
    error_count: int
    total_executions: int
    state: PerformanceState = PerformanceState.HEALTHY


@dataclass
class AdaptiveConfig:
    """Adaptive configuration for a task type."""
    task_type: str
    current_workers: int
    current_batch_size: int
    min_workers: int
    max_workers: int
    min_batch_size: int
    max_batch_size: int
    target_p95_ms: float
    target_p99_ms: float
    target_success_rate: float = 0.95


class PerformanceMonitor:
    """
    Monitors performance and provides adaptive configuration recommendations.
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics: dict[str, PerformanceMetrics] = {}
        self.configs: dict[str, AdaptiveConfig] = {}
        self.execution_times: dict[str, deque] = {}
        self.success_counts: dict[str, int] = {}
        self.error_counts: dict[str, int] = {}
    
    def record_execution(
        self,
        task_type: str,
        execution_time_ms: float,
        success: bool,
    ):
        """Record an execution for performance tracking."""
        if task_type not in self.execution_times:
            self.execution_times[task_type] = deque(maxlen=self.window_size)
            self.success_counts[task_type] = 0
            self.error_counts[task_type] = 0
        
        self.execution_times[task_type].append(execution_time_ms)
        
        if success:
            self.success_counts[task_type] += 1
        else:
            self.error_counts[task_type] += 1
        
        # Update metrics
        self._update_metrics(task_type)
    
    def _update_metrics(self, task_type: str):
        """Update performance metrics for a task type."""
        times = list(self.execution_times[task_type])
        if not times:
            return
        
        total = self.success_counts[task_type] + self.error_counts[task_type]
        success_rate = self.success_counts[task_type] / total if total > 0 else 0.0
        
        times_sorted = sorted(times)
        avg_time = sum(times) / len(times)
        p95_time = times_sorted[int(len(times_sorted) * 0.95)] if len(times_sorted) > 0 else avg_time
        p99_time = times_sorted[int(len(times_sorted) * 0.99)] if len(times_sorted) > 0 else avg_time
        
        # Determine performance state
        config = self.configs.get(task_type)
        if config:
            if (p99_time > config.target_p99_ms * 2 or 
                success_rate < config.target_success_rate * 0.5):
                state = PerformanceState.CRITICAL
            elif (p95_time > config.target_p95_ms or 
                  success_rate < config.target_success_rate):
                state = PerformanceState.DEGRADED
            else:
                state = PerformanceState.HEALTHY
        else:
            state = PerformanceState.HEALTHY
        
        self.metrics[task_type] = PerformanceMetrics(
            task_type=task_type,
            avg_execution_time_ms=avg_time,
            p95_execution_time_ms=p95_time,
            p99_execution_time_ms=p99_time,
            success_rate=success_rate,
            error_count=self.error_counts[task_type],
            total_executions=total,
            state=state,
        )
    
    def register_config(
        self,
        task_type: str,
        current_workers: int,
        current_batch_size: int,
        min_workers: int = 1,
        max_workers: int = 32,
        min_batch_size: int = 1,
        max_batch_size: int = 128,
        target_p95_ms: float = 1000,
        target_p99_ms: float = 2000,
        target_success_rate: float = 0.95,
    ):
        """Register adaptive configuration for a task type."""
        self.configs[task_type] = AdaptiveConfig(
            task_type=task_type,
            current_workers=current_workers,
            current_batch_size=current_batch_size,
            min_workers=min_workers,
            max_workers=max_workers,
            min_batch_size=min_batch_size,
            max_batch_size=max_batch_size,
            target_p95_ms=target_p95_ms,
            target_p99_ms=target_p99_ms,
            target_success_rate=target_success_rate,
        )
    
    def get_metrics(self, task_type: str) -> Optional[PerformanceMetrics]:
        """Get performance metrics for a task type."""
        return self.metrics.get(task_type)
    
    def should_scale_up(self, task_type: str) -> bool:
        """Check if workers should be scaled up."""
        metrics = self.metrics.get(task_type)
        config = self.configs.get(task_type)
        
        if not metrics or not config:
            return False
        
        # Scale up if performance is degraded and we have headroom
        if (metrics.state == PerformanceState.DEGRADED and 
            config.current_workers < config.max_workers):
            return True
        
        # Scale up if we're healthy but have low utilization
        if (metrics.state == PerformanceState.HEALTHY and 
            metrics.avg_execution_time_ms < config.target_p95_ms * 0.5 and
            config.current_workers < config.max_workers):
            return True
        
        return False
    
    def should_scale_down(self, task_type: str) -> bool:
        """Check if workers should be scaled down."""
        metrics = self.metrics.get(task_type)
        config = self.configs.get(task_type)
        
        if not metrics or not config:
            return False
        
        # Scale down if we're over-provisioned
        if (metrics.state == PerformanceState.HEALTHY and 
            metrics.avg_execution_time_ms < config.target_p95_ms * 0.3 and
            config.current_workers > config.min_workers):
            return True
        
        return False
    
    def should_increase_batch_size(self, task_type: str) -> bool:
        """Check if batch size should be increased."""
        metrics = self.metrics.get(task_type)
        config = self.configs.get(task_type)
        
        if not metrics or not config:
            return False
        
        # Increase batch if performance is healthy and we have headroom
        if (metrics.state == PerformanceState.HEALTHY and 
            metrics.p95_execution_time_ms < config.target_p95_ms * 0.5 and
            config.current_batch_size < config.max_batch_size):
            return True
        
        return False
    
    def should_decrease_batch_size(self, task_type: str) -> bool:
        """Check if batch size should be decreased."""
        metrics = self.metrics.get(task_type)
        config = self.configs.get(task_type)
        
        if not metrics or not config:
            return False
        
        # Decrease batch if performance is degraded
        if (metrics.state == PerformanceState.DEGRADED and 
            config.current_batch_size > config.min_batch_size):
            return True
        
        return False
    
    def get_adaptive_recommendation(self, task_type: str) -> dict:
        """Get adaptive configuration recommendation."""
        metrics = self.metrics.get(task_type)
        config = self.configs.get(task_type)
        
        if not metrics or not config:
            return {}
        
        recommendation = {
            "task_type": task_type,
            "current_state": metrics.state.value,
            "current_workers": config.current_workers,
            "current_batch_size": config.current_batch_size,
            "recommended_workers": config.current_workers,
            "recommended_batch_size": config.current_batch_size,
            "reason": "no_change",
        }
        
        # Check for critical state
        if metrics.state == PerformanceState.CRITICAL:
            # Scale down aggressively
            recommendation["recommended_workers"] = max(
                config.min_workers,
                config.current_workers // 2
            )
            recommendation["recommended_batch_size"] = max(
                config.min_batch_size,
                config.current_batch_size // 2
            )
            recommendation["reason"] = "critical_performance_scale_down"
        elif self.should_scale_up(task_type):
            recommendation["recommended_workers"] = min(
                config.max_workers,
                config.current_workers + 1
            )
            recommendation["reason"] = "performance_degraded_scale_up"
        elif self.should_scale_down(task_type):
            recommendation["recommended_workers"] = max(
                config.min_workers,
                config.current_workers - 1
            )
            recommendation["reason"] = "over_provisioned_scale_down"
        elif self.should_increase_batch_size(task_type):
            recommendation["recommended_batch_size"] = min(
                config.max_batch_size,
                config.current_batch_size * 2
            )
            recommendation["reason"] = "healthy_increase_batch"
        elif self.should_decrease_batch_size(task_type):
            recommendation["recommended_batch_size"] = max(
                config.min_batch_size,
                config.current_batch_size // 2
            )
            recommendation["reason"] = "degraded_decrease_batch"
        
        return recommendation


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def performance_monitored(task_type: str):
    """
    Decorator to monitor performance of a function.
    
    Args:
        task_type: Type of task for performance tracking
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            start_time = time.time()
            success = False
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception:
                raise
            finally:
                execution_time_ms = (time.time() - start_time) * 1000
                monitor.record_execution(task_type, execution_time_ms, success)
        
        return wrapper
    return decorator
