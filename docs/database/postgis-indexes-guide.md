# PostGIS Spatial Indexes Guide for F.A.R.O.

## Overview

This document describes the spatial indexes required for optimal PostGIS performance in the F.A.R.O. system. Proper spatial indexing is critical for queries involving location data, clustering, and proximity searches.

## Required Spatial Indexes

### 1. AgentLocationLog Table

```sql
-- Primary spatial index for location queries
CREATE INDEX IF NOT EXISTS idx_agentlocationlog_location_gist 
ON agentlocationlog USING GIST (location);

-- Composite index for common queries (agency + time + location)
CREATE INDEX IF NOT EXISTS idx_agentlocationlog_agency_time_location 
ON agentlocationlog USING GIST (agency_id, recorded_at, location);

-- BRIN index for temporal-spatial data (if using TimescaleDB)
CREATE INDEX IF NOT EXISTS idx_agentlocationlog_recorded_at_brin 
ON agentlocationlog USING BRIN (recorded_at);
```

### 2. VehicleObservation Table

```sql
-- Primary spatial index for observation location queries
CREATE INDEX IF NOT EXISTS idx_vehicleobservation_location_gist 
ON vehicleobservation USING GIST (location);

-- Composite index for agency-scoped spatial queries
CREATE INDEX IF NOT EXISTS idx_vehicleobservation_agency_location_gist 
ON vehicleobservation USING GIST (agency_id, location);

-- Index for plate number lookups
CREATE INDEX IF NOT EXISTS idx_vehicleobservation_plate_number 
ON vehicleobservation (plate_number);

-- Composite index for temporal-spatial queries
CREATE INDEX IF NOT EXISTS idx_vehicleobservation_time_location_gist 
ON vehicleobservation USING GIST (observed_at_local, location);
```

### 3. SuspiciousRoute Table

```sql
-- Spatial index for route geometry intersection queries
CREATE INDEX IF NOT EXISTS idx_suspiciousroute_route_geometry_gist 
ON suspiciousroute USING GIST (route_geometry);

-- Index for active/approved routes
CREATE INDEX IF NOT EXISTS idx_suspiciousroute_active_approved 
ON suspiciousroute (is_active, approval_status);
```

### 4. RoutePattern Table

```sql
-- Spatial index for pattern geometry
CREATE INDEX IF NOT EXISTS idx_routepattern_centroid_location_gist 
ON routepattern USING GIST (centroid_location);

CREATE INDEX IF NOT EXISTS idx_routepattern_bounding_box_gist 
ON routepattern USING GIST (bounding_box);
```

## Index Maintenance

### Reindexing Strategy

```sql
-- Reindex spatial indexes periodically (monthly recommended)
REINDEX INDEX idx_agentlocationlog_location_gist;
REINDEX INDEX idx_vehicleobservation_location_gist;
REINDEX INDEX idx_suspiciousroute_route_geometry_gist;
```

### Analyze Tables

```sql
-- Update statistics after bulk inserts
ANALYZE agentlocationlog;
ANALYZE vehicleobservation;
ANALYZE suspiciousroute;
```

## Performance Considerations

### ST_DWithin vs ST_Distance

- **ST_DWithin**: Uses spatial index, O(log n) complexity - USE FOR FILTERS
- **ST_Distance**: Calculates exact distance, O(n) complexity - USE FOR REPORTING ONLY

**Example:**
```sql
-- ✅ GOOD - Uses index
SELECT * FROM observations 
WHERE ST_DWithin(location, ST_MakePoint(-73.9, 40.7), 1000);

-- ❌ BAD - Full table scan
SELECT * FROM observations 
WHERE ST_Distance(location, ST_MakePoint(-73.9, 40.7)) < 1000;
```

### ST_ClusterDBSCAN Performance

- Requires spatial index on geometry column
- eps parameter should match typical cluster radius
- minpoints should be tuned based on data density

### ST_Extent Optimization

- Use ST_Extent with GROUP BY for bounding box calculations
- Prefer over individual ST_XMin/ST_XMax calls for multiple geometries

## Query Optimization Tips

### 1. Use CTEs for Complex Spatial Queries

```sql
WITH filtered_data AS (
    SELECT id, location 
    FROM vehicleobservation 
    WHERE agency_id = :agency_id
        AND observed_at_local >= :start_date
),
clusters AS (
    SELECT 
        ST_ClusterDBSCAN(location, eps := 500, minpoints := 5) OVER () as cluster_id,
        id
    FROM filtered_data
)
SELECT cluster_id, COUNT(*) 
FROM clusters 
WHERE cluster_id IS NOT NULL 
GROUP BY cluster_id;
```

### 2. Limit Geometry Size

```sql
-- Simplify geometries for visualization
SELECT ST_SimplifyPreserveTopology(geometry, 0.0001) 
FROM large_polygons;
```

### 3. Use Appropriate SRID

- **SRID 4326**: WGS84 (latitude/longitude) - Use for storage
- **SRID 3857**: Web Mercator - Use for map visualization
- **Projected SRIDs**: Use for distance calculations requiring high precision

## Monitoring Index Usage

```sql
-- Check index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

## Cleanup

### Remove Unused Indexes

```sql
-- Identify unused indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes 
WHERE idx_scan = 0 
    AND indexname LIKE '%gist%';
```

## Migration Script

A migration script should be added to create these indexes:

```python
# alembic/versions/XXXX_postgis_spatial_indexes.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # AgentLocationLog indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_agentlocationlog_location_gist 
        ON agentlocationlog USING GIST (location);
    """)
    
    # VehicleObservation indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_vehicleobservation_location_gist 
        ON vehicleobservation USING GIST (location);
    """)
    
    # SuspiciousRoute indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_suspiciousroute_route_geometry_gist 
        ON suspiciousroute USING GIST (route_geometry);
    """)

def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_agentlocationlog_location_gist")
    op.execute("DROP INDEX IF EXISTS idx_vehicleobservation_location_gist")
    op.execute("DROP INDEX IF EXISTS idx_suspiciousroute_route_geometry_gist")
```
