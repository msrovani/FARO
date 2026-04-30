"""
Process Pool Executor for CPU-bound tasks.
Provides async wrappers for running CPU-intensive functions in separate processes.
"""
import asyncio
import time
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from typing import Any, Callable, Optional, TypeVar

from app.core.config import settings
from app.utils.performance_monitor import get_performance_monitor, performance_monitored
from app.utils.circuit_breaker import get_circuit_breaker, CircuitBreakerConfig

T = TypeVar('T')

# Global process pool executor
_process_pool: ProcessPoolExecutor | None = None
_adaptive_pool: ProcessPoolExecutor | None = None


def get_process_pool() -> ProcessPoolExecutor:
    """
    Get or create the global ProcessPoolExecutor instance.
    
    Returns:
        ProcessPoolExecutor instance
    """
    global _process_pool
    if _process_pool is None:
        max_workers = settings.process_pool_max_workers
        if isinstance(max_workers, str):
            max_workers = 4  # Fallback if auto-detection failed
        _process_pool = ProcessPoolExecutor(max_workers=max_workers)
    return _process_pool


def get_adaptive_process_pool(task_type: str = "general") -> ProcessPoolExecutor:
    """
    Get or create an adaptive ProcessPoolExecutor for a specific task type.
    
    Args:
        task_type: Type of task for adaptive configuration
        
    Returns:
        ProcessPoolExecutor instance with adaptive configuration
    """
    global _adaptive_pool
    if _adaptive_pool is None:
        # Use CPU-bound workers for adaptive pool
        max_workers = settings.process_pool_cpu_bound_workers
        if isinstance(max_workers, str):
            max_workers = 4  # Fallback
        _adaptive_pool = ProcessPoolExecutor(max_workers=max_workers)
    return _adaptive_pool


async def run_in_process_pool(
    func: Callable[..., T],
    *args: Any,
    task_type: str = "general",
    enable_monitoring: bool = True,
    enable_circuit_breaker: bool = False,
    **kwargs: Any
) -> T:
    """
    Run a CPU-bound function in the process pool with optional monitoring.
    
    Args:
        func: The function to execute
        *args: Positional arguments for the function
        task_type: Type of task for performance monitoring
        enable_monitoring: Enable performance monitoring
        enable_circuit_breaker: Enable circuit breaker protection
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the function
    """
    loop = asyncio.get_event_loop()
    pool = get_process_pool()
    
    # If kwargs are provided, use partial to bind them
    if kwargs:
        func = partial(func, **kwargs)
    
    start_time = time.time()
    success = False
    
    try:
        if enable_circuit_breaker:
            breaker = get_circuit_breaker(
                f"{task_type}_pool",
                CircuitBreakerConfig(
                    failure_threshold=5,
                    timeout_ms=30000,
                    max_execution_time_ms=10000,
                )
            )
            result = breaker.execute(func, *args)
        else:
            result = await loop.run_in_executor(pool, func, *args)
        
        success = True
        return result
    except Exception as e:
        raise e
    finally:
        if enable_monitoring:
            monitor = get_performance_monitor()
            execution_time_ms = (time.time() - start_time) * 1000
            monitor.record_execution(task_type, execution_time_ms, success)


async def run_batch_in_process_pool(
    func: Callable[..., T],
    args_list: list[tuple[Any, ...]],
    task_type: str = "general",
    enable_monitoring: bool = True,
    **kwargs: Any
) -> list[T]:
    """
    Run a CPU-bound function on multiple inputs in parallel with monitoring.
    
    Args:
        func: The function to execute
        args_list: List of argument tuples for each function call
        task_type: Type of task for performance monitoring
        enable_monitoring: Enable performance monitoring
        **kwargs: Keyword arguments to pass to all function calls
        
    Returns:
        List of results in the same order as args_list
    """
    loop = asyncio.get_event_loop()
    pool = get_process_pool()
    
    # If kwargs are provided, use partial to bind them
    if kwargs:
        func = partial(func, **kwargs)
    
    tasks = []
    for args in args_list:
        if enable_monitoring:
            task = _monitored_execution(loop, pool, func, args, task_type)
        else:
            task = loop.run_in_executor(pool, func, *args)
        tasks.append(task)
    
    return await asyncio.gather(*tasks)


async def _monitored_execution(
    loop: asyncio.AbstractEventLoop,
    pool: ProcessPoolExecutor,
    func: Callable,
    args: tuple,
    task_type: str,
) -> T:
    """Execute function with performance monitoring."""
    monitor = get_performance_monitor()
    start_time = time.time()
    success = False
    
    try:
        result = await loop.run_in_executor(pool, func, *args)
        success = True
        return result
    except Exception as e:
        raise
    finally:
        execution_time_ms = (time.time() - start_time) * 1000
        monitor.record_execution(task_type, execution_time_ms, success)


def shutdown_process_pool():
    """Shutdown the global ProcessPoolExecutor."""
    global _process_pool, _adaptive_pool
    if _process_pool is not None:
        _process_pool.shutdown(wait=True)
        _process_pool = None
    if _adaptive_pool is not None:
        _adaptive_pool.shutdown(wait=True)
        _adaptive_pool = None
