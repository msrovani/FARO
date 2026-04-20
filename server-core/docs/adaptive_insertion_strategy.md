# Adaptive Insertion Strategy for F.A.R.O.

## Overview

Implements intelligent batch sizing and mode switching based on real-time database conditions to optimize insertion performance automatically.

## Architecture

### Component: `app/utils/adaptive_insertion.py`

**Class:** `AdaptiveInsertionStrategy`

**Modes:**
- **BATCH_MODE:** `add_all()` + commit per batch (default, 50 items)
- **PARALLEL_BATCH_MODE:** Multiple batches in parallel (for high throughput, 100-200 items)
- **COPY_MODE:** PostgreSQL COPY for bulk load (future implementation for massive loads)
- **INDIVIDUAL_MODE:** Fallback for errors/high latency (1 item per commit)

### Dynamic Triggers

**Mode Switching Logic:**
```
Error rate > 5% → INDIVIDUAL_MODE (fallback)
Congestion > 80% → Reduce batch size to minimum (10)
Congestion > 50% → BATCH_MODE (moderate)
Latency < 100ms → Increase batch size, consider PARALLEL_BATCH_MODE
Latency > 5s → Reduce batch size
```

**Congestion Monitoring:**
- Active connections: `SELECT count(*) FROM pg_stat_activity WHERE state = 'active'`
- Blocked queries: `SELECT count(*) FROM pg_locks WHERE NOT granted`
- Congestion metric: `(active_connections / max_connections) + (blocked_queries * 0.1)`

**Metrics:**
- Error rate (exponential smoothing: 0.9)
- Average latency (exponential smoothing: 0.9)
- DB congestion level (0-1 scale)
- Total operations/errors
- Latency history (last 100 operations)

### Integration: `app/api/v1/endpoints/mobile.py`

**Endpoint:** `/api/v1/mobile/sync/batch`

**Implementation:**
1. Initialize `AdaptiveInsertionStrategy` with batch size 10-200
2. Adapt mode based on current DB conditions
3. Process items in dynamic batches
4. Commit per batch (not per item)
5. Update metrics after each batch
6. Re-adapt mode for next batch

**Benefits:**
- **Automatic optimization:** No manual tuning required
- **Adaptive:** Responds to real-time conditions
- **Resilient:** Fallback to individual mode on errors
- **Efficient:** Batch commits reduce database overhead
- **Scalable:** Dynamic sizing handles varying loads

## Performance Impact

**Expected Gains:**
- **Normal load:** 5-10x faster (batch vs individual)
- **High load:** 10-20x faster (parallel batches)
- **Congested:** Automatic degradation to prevent overload
- **Error recovery:** Fallback to individual mode

**Trade-offs:**
- Slightly increased memory usage (batch buffering)
- Mode switching adds ~10ms overhead
- Requires monitoring of DB stats

## Configuration

**Default Settings:**
```python
initial_batch_size = 50
max_batch_size = 200
min_batch_size = 10
```

**Tuning Guidelines:**
- Increase `max_batch_size` for high-memory servers
- Decrease `min_batch_size` for low-latency requirements
- Adjust congestion thresholds based on DB capacity

## Monitoring

**Metrics Available:**
```python
adaptive_strategy.get_stats()
# Returns:
{
    "mode": "BATCH_MODE",
    "batch_size": 50,
    "error_rate": 0.02,
    "avg_latency": 0.15,
    "db_congestion": 0.3,
    "total_operations": 1000,
    "total_errors": 20
}
```

## Future Enhancements

**Planned Features:**
- COPY_MODE implementation for bulk loads (>10k items)
- Parallel batch execution with `asyncio.gather()`
- Queue-based load management with backpressure
- Integration with Prometheus metrics
- Historical analysis for predictive mode selection

## Usage Example

```python
from app.utils.adaptive_insertion import AdaptiveInsertionStrategy

# Initialize
strategy = AdaptiveInsertionStrategy(
    initial_batch_size=50,
    max_batch_size=200,
    min_batch_size=10
)

# Adapt mode
await strategy.adapt_mode(db)

# Process in batches
for batch in items:
    batch_start = time.time()
    # ... process batch ...
    await db.commit()
    
    # Update metrics
    strategy.update_metrics(success=True, latency=time.time() - batch_start)
    
    # Re-adapt for next batch
    await strategy.adapt_mode(db)
```

## Conclusion

The adaptive insertion strategy provides automatic performance optimization for database insertions in F.A.R.O., adapting to real-time conditions without manual intervention. It balances throughput, latency, and reliability through intelligent mode switching and dynamic batch sizing.
