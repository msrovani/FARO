"""
Adaptive Insertion Strategy for F.A.R.O.

Implements intelligent batch sizing and mode switching based on:
- Database congestion level
- Error rate
- Average latency
- Volume of operations

Modes:
- BATCH_MODE: add_all() + commit per batch (default)
- PARALLEL_BATCH_MODE: Multiple batches in parallel
- COPY_MODE: PostgreSQL COPY for bulk load
- INDIVIDUAL_MODE: Fallback for errors/high latency
"""

import time
from enum import Enum
from typing import Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class InsertionMode(Enum):
    BATCH_MODE = "BATCH_MODE"
    PARALLEL_BATCH_MODE = "PARALLEL_BATCH_MODE"
    COPY_MODE = "COPY_MODE"
    INDIVIDUAL_MODE = "INDIVIDUAL_MODE"


class AdaptiveInsertionStrategy:
    def __init__(
        self,
        initial_batch_size: int = 50,
        max_batch_size: int = 200,
        min_batch_size: int = 10
    ):
        self.mode = InsertionMode.BATCH_MODE
        self.batch_size = initial_batch_size
        self.max_batch_size = max_batch_size
        self.min_batch_size = min_batch_size
        
        # Metrics
        self.error_rate = 0.0
        self.avg_latency = 0.0
        self.db_congestion_level = 0.0  # 0-1 scale
        
        # History for adaptive decisions
        self.total_operations = 0
        self.total_errors = 0
        self.latency_history: List[float] = []
        self.max_history_size = 100
    
    async def check_db_congestion(self, db: AsyncSession) -> float:
        """Monitor database congestion level (0-1 scale)"""
        try:
            # Check active connections
            result = await db.execute(text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"))
            active_connections = result.scalar() or 0
            
            # Check blocked queries
            result = await db.execute(text("SELECT count(*) FROM pg_locks WHERE NOT granted"))
            blocked_queries = result.scalar() or 0
            
            # Simple congestion metric
            max_connections = 100  # Typical PostgreSQL default
            self.db_congestion_level = min(1.0, (active_connections / max_connections) + (blocked_queries * 0.1))
            
            return self.db_congestion_level
        except Exception as e:
            logger.warning(f"Error calculating DB congestion: {e}")
            return 0.5  # Assume moderate congestion on error
    
    def update_metrics(self, success: bool, latency: float):
        """Update metrics after an operation"""
        self.total_operations += 1
        if not success:
            self.total_errors += 1
        
        # Update error rate with exponential smoothing
        self.error_rate = (self.error_rate * 0.9) + ((1.0 if not success else 0.0) * 0.1)
        
        # Update latency with exponential smoothing
        self.avg_latency = (self.avg_latency * 0.9) + (latency * 0.1)
        
        # Maintain latency history
        self.latency_history.append(latency)
        if len(self.latency_history) > self.max_history_size:
            self.latency_history.pop(0)
    
    async def adapt_mode(self, db: AsyncSession) -> InsertionMode:
        """Adapt insertion mode based on current conditions"""
        congestion = await self.check_db_congestion(db)
        old_mode = self.mode
        
        # Mode switching logic
        if self.error_rate > 0.05:
            # High error rate - fallback to individual
            self.mode = InsertionMode.INDIVIDUAL_MODE
            self.batch_size = 1
        elif congestion > 0.8:
            # High congestion - reduce batch size
            self.mode = InsertionMode.BATCH_MODE
            self.batch_size = max(self.min_batch_size, self.batch_size // 2)
        elif congestion > 0.5:
            # Moderate congestion - use batch mode
            self.mode = InsertionMode.BATCH_MODE
        elif self.avg_latency < 0.1 and self.batch_size < self.max_batch_size:
            # Low latency - increase batch size, consider parallel
            self.batch_size = min(self.max_batch_size, self.batch_size * 2)
            if self.batch_size >= 100:
                self.mode = InsertionMode.PARALLEL_BATCH_MODE
            else:
                self.mode = InsertionMode.BATCH_MODE
        elif self.avg_latency > 5.0:
            # High latency - reduce batch size
            self.mode = InsertionMode.BATCH_MODE
            self.batch_size = max(self.min_batch_size, self.batch_size // 2)
        
        return self.mode
    
    def get_stats(self) -> dict:
        """Get current statistics"""
        return {
            "mode": self.mode.value,
            "batch_size": self.batch_size,
            "error_rate": self.error_rate,
            "avg_latency": self.avg_latency,
            "db_congestion": self.db_congestion_level,
            "total_operations": self.total_operations,
            "total_errors": self.total_errors
        }
