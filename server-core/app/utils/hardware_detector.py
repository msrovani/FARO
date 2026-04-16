"""
Hardware Detection and Adaptive Configuration
Automatically detects available hardware capabilities and configures optimal settings.
"""
import os
import platform
import psutil
from dataclasses import dataclass
from typing import Optional


@dataclass
class HardwareCapabilities:
    """Detected hardware capabilities."""
    cpu_count: int
    cpu_count_physical: int
    total_memory_gb: float
    available_memory_gb: float
    gpu_available: bool
    gpu_type: Optional[str]  # "cuda", "mps", or None
    gpu_memory_gb: Optional[float]
    platform: str
    architecture: str


def detect_hardware() -> HardwareCapabilities:
    """
    Detect hardware capabilities automatically.
    
    Returns:
        HardwareCapabilities with detected specs
    """
    # CPU detection
    cpu_count = os.cpu_count() or 1
    cpu_count_physical = psutil.cpu_count(logical=False) or cpu_count
    
    # Memory detection
    memory = psutil.virtual_memory()
    total_memory_gb = memory.total / (1024**3)
    available_memory_gb = memory.available / (1024**3)
    
    # GPU detection
    gpu_available = False
    gpu_type = None
    gpu_memory_gb = None
    
    try:
        import torch
        if torch.cuda.is_available():
            gpu_available = True
            gpu_type = "cuda"
            gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            gpu_available = True
            gpu_type = "mps"
            # MPS doesn't expose memory easily, estimate based on system
            gpu_memory_gb = min(8.0, total_memory_gb * 0.5)
    except ImportError:
        pass
    
    # Platform detection
    platform_name = platform.system()
    architecture = platform.machine()
    
    return HardwareCapabilities(
        cpu_count=cpu_count,
        cpu_count_physical=cpu_count_physical,
        total_memory_gb=total_memory_gb,
        available_memory_gb=available_memory_gb,
        gpu_available=gpu_available,
        gpu_type=gpu_type,
        gpu_memory_gb=gpu_memory_gb,
        platform=platform_name,
        architecture=architecture,
    )


def calculate_optimal_workers(hardware: HardwareCapabilities, task_type: str = "general") -> int:
    """
    Calculate optimal number of workers based on hardware and task type.
    
    Args:
        hardware: Detected hardware capabilities
        task_type: Type of task ("general", "cpu_bound", "io_bound", "gpu_bound")
        
    Returns:
        Optimal number of workers
    """
    # Base calculation on physical cores
    if task_type == "cpu_bound":
        # CPU-bound tasks: 1-2 workers per physical core
        workers = max(1, hardware.cpu_count_physical)
        # Limit to avoid oversubscription
        workers = min(workers, hardware.cpu_count_physical * 2)
    elif task_type == "io_bound":
        # I/O-bound tasks: 2-4 workers per logical core
        workers = max(2, hardware.cpu_count * 2)
        workers = min(workers, hardware.cpu_count * 4)
    elif task_type == "gpu_bound":
        # GPU-bound tasks: limited by GPU, use fewer CPU workers
        workers = max(1, hardware.cpu_count_physical // 2)
        if hardware.gpu_available:
            workers = min(workers, 4)  # Don't overload GPU with too many workers
    else:
        # General: balanced approach
        workers = max(2, hardware.cpu_count)
    
    # Adjust based on available memory (reserve 2GB for system)
    memory_per_worker_gb = 0.5  # Estimated memory per worker
    max_workers_by_memory = int((hardware.available_memory_gb - 2.0) / memory_per_worker_gb)
    workers = min(workers, max_workers_by_memory)
    
    return max(1, workers)


def calculate_optimal_batch_size(hardware: HardwareCapabilities, task_type: str = "general") -> int:
    """
    Calculate optimal batch size based on hardware.
    
    Args:
        hardware: Detected hardware capabilities
        task_type: Type of task
        
    Returns:
        Optimal batch size
    """
    if task_type == "gpu_bound" and hardware.gpu_available:
        # GPU can handle larger batches
        if hardware.gpu_memory_gb and hardware.gpu_memory_gb >= 8:
            return 32
        elif hardware.gpu_memory_gb and hardware.gpu_memory_gb >= 4:
            return 16
        else:
            return 8
    elif task_type == "cpu_bound":
        # CPU-bound: smaller batches to avoid memory pressure
        return max(4, hardware.cpu_count_physical)
    else:
        # General: moderate batch size
        return max(8, hardware.cpu_count_physical * 2)


# Singleton hardware detection
_hardware_cache: Optional[HardwareCapabilities] = None


def get_hardware_capabilities() -> HardwareCapabilities:
    """
    Get cached hardware capabilities.
    
    Returns:
        HardwareCapabilities instance
    """
    global _hardware_cache
    if _hardware_cache is None:
        _hardware_cache = detect_hardware()
    return _hardware_cache
