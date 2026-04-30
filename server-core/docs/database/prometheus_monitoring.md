# FARO Database Monitoring with Prometheus

## Overview

This document outlines the setup and configuration of Prometheus monitoring for the FARO PostgreSQL database.

## Architecture

```
PostgreSQL → postgres_exporter → Prometheus → Grafana
```

## Installation

### 1. Install postgres_exporter

**Download:**
```bash
wget https://github.com/prometheus-community/postgres_exporter/releases/download/v0.12.0/postgres_exporter-0.12.0.linux-amd64.tar.gz
tar xvfz postgres_exporter-0.12.0.linux-amd64.tar.gz
sudo mv postgres_exporter-0.12.0.linux-amd64/postgres_exporter /usr/local/bin/
sudo chmod +x /usr/local/bin/postgres_exporter
```

**Create user:**
```bash
sudo useradd -rs /bin/false prometheus
```

### 2. Configure PostgreSQL User for Monitoring

**Create monitoring user:**
```sql
-- Connect to PostgreSQL as postgres
CREATE USER faro_monitor WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE faro_db TO faro_monitor;
GRANT USAGE ON SCHEMA public TO faro_monitor;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO faro_monitor;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO faro_monitor;
```

**Grant pg_stat_statements access:**
```sql
GRANT pg_read_all_stats TO faro_monitor;
```

### 3. Configure postgres_exporter

**Environment file:** `/etc/default/postgres_exporter`

```bash
DATA_SOURCE_NAME="postgresql://faro_monitor:secure_password@localhost:5432/faro_db?sslmode=disable"
PG_EXPORTER_EXTEND_QUERY_PATH="/etc/postgres_exporter/queries.yaml"
```

**Custom queries file:** `/etc/postgres_exporter/queries.yaml`

```yaml
# Custom queries for FARO-specific metrics
vehicleobservation_count:
  query: |
    SELECT 
      agency_id,
      COUNT(*) as count
    FROM vehicleobservation
    GROUP BY agency_id
  metrics:
    - agency_id:
        usage: "LABEL"
        description: "Agency ID"
    - count:
        usage: "GAUGE"
        description: "Number of vehicle observations"

sync_pending_count:
  query: |
    SELECT 
      agency_id,
      COUNT(*) as count
    FROM vehicleobservation
    WHERE sync_status = 'pending'
    GROUP BY agency_id
  metrics:
    - agency_id:
        usage: "LABEL"
        description: "Agency ID"
    - count:
        usage: "GAUGE"
        description: "Number of pending syncs"

alert_unacknowledged_count:
  query: |
    SELECT 
      agency_id,
      COUNT(*) as count
    FROM alert
    WHERE is_acknowledged = false
    GROUP BY agency_id
  metrics:
    - agency_id:
        usage: "LABEL"
        description: "Agency ID"
    - count:
        usage: "GAUGE"
        description: "Number of unacknowledged alerts"

watchlist_active_count:
  query: |
    SELECT 
      agency_id,
      COUNT(*) as count
    FROM watchlistentry
    WHERE is_active = true
    GROUP BY agency_id
  metrics:
    - agency_id:
        usage: "LABEL"
        description: "Agency ID"
    - count:
        usage: "GAUGE"
        description: "Number of active watchlist entries"

user_on_duty_count:
  query: |
    SELECT 
      agency_id,
      COUNT(*) as count
    FROM "user"
    WHERE is_on_duty = true AND is_active = true
    GROUP BY agency_id
  metrics:
    - agency_id:
        usage: "LABEL"
        description: "Agency ID"
    - count:
        usage: "GAUGE"
        description: "Number of on-duty users"
```

### 4. Create Systemd Service

**Service file:** `/etc/systemd/system/postgres_exporter.service`

```ini
[Unit]
Description=PostgreSQL Exporter
After=network.target postgresql.service

[Service]
Type=simple
User=prometheus
Group=prometheus
EnvironmentFile=/etc/default/postgres_exporter
ExecStart=/usr/local/bin/postgres_exporter \
  --web.listen-address=:9187 \
  --web.telemetry-path=/metrics \
  --extend.query-path=/etc/postgres_exporter/queries.yaml

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable postgres_exporter
sudo systemctl start postgres_exporter
```

### 5. Configure Prometheus

**Prometheus configuration:** `/etc/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
    scrape_interval: 15s
    scrape_timeout: 10s
```

**Reload Prometheus:**
```bash
sudo systemctl reload prometheus
```

## Grafana Dashboards

### Dashboard 1: Database Overview

**Import dashboard:** Use JSON below or import from Grafana.com

```json
{
  "dashboard": {
    "title": "FARO Database Overview",
    "panels": [
      {
        "title": "Active Connections",
        "targets": [
          {
            "expr": "pg_stat_activity_count{datname='faro_db'}",
            "legendFormat": "Connections"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Transaction Throughput",
        "targets": [
          {
            "expr": "rate(pg_stat_database_xact_commit{datname='faro_db'}[5m])",
            "legendFormat": "Commits/sec"
          },
          {
            "expr": "rate(pg_stat_database_xact_rollback{datname='faro_db'}[5m])",
            "legendFormat": "Rollbacks/sec"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Cache Hit Ratio",
        "targets": [
          {
            "expr": "pg_stat_database_blks_hit{datname='faro_db'} / (pg_stat_database_blks_hit{datname='faro_db'} + pg_stat_database_blks_read{datname='faro_db'})",
            "legendFormat": "Cache Hit Ratio"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Database Size",
        "targets": [
          {
            "expr": "pg_database_size_bytes{datname='faro_db'}",
            "legendFormat": "Size (bytes)"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

### Dashboard 2: FARO Application Metrics

```json
{
  "dashboard": {
    "title": "FARO Application Metrics",
    "panels": [
      {
        "title": "Vehicle Observations by Agency",
        "targets": [
          {
            "expr": "vehicleobservation_count",
            "legendFormat": "{{agency_id}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Pending Syncs by Agency",
        "targets": [
          {
            "expr": "sync_pending_count",
            "legendFormat": "{{agency_id}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Unacknowledged Alerts by Agency",
        "targets": [
          {
            "expr": "alert_unacknowledged_count",
            "legendFormat": "{{agency_id}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "On-Duty Users by Agency",
        "targets": [
          {
            "expr": "user_on_duty_count",
            "legendFormat": "{{agency_id}}"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

## Alerting Rules

**Alert rules file:** `/etc/prometheus/rules/faro_database.yml`

```yaml
groups:
  - name: faro_database
    interval: 30s
    rules:
      # Connection alerts
      - alert: HighConnectionCount
        expr: pg_stat_activity_count{datname='faro_db'} > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High number of database connections"
          description: "Database has {{ $value }} active connections (threshold: 80)"
      
      - alert: CriticalConnectionCount
        expr: pg_stat_activity_count{datname='faro_db'} > 100
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Critical number of database connections"
          description: "Database has {{ $value }} active connections (threshold: 100)"
      
      # Performance alerts
      - alert: SlowQueries
        expr: rate(pg_stat_statements_mean_exec_time_seconds{datname='faro_db'}[5m]) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow queries detected"
          description: "Average query execution time is {{ $value }}s (threshold: 1s)"
      
      - alert: HighLockWait
        expr: pg_locks_count{mode='waiting'} > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High number of waiting locks"
          description: "{{ $value }} locks are waiting (threshold: 10)"
      
      # Cache alerts
      - alert: LowCacheHitRatio
        expr: pg_stat_database_blks_hit{datname='faro_db'} / (pg_stat_database_blks_hit{datname='faro_db'} + pg_stat_database_blks_read{datname='faro_db'}) < 0.9
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit ratio"
          description: "Cache hit ratio is {{ $value | humanizePercentage }} (threshold: 90%)"
      
      # Replication alerts (if configured)
      - alert: ReplicationLag
        expr: pg_stat_replication_lag_seconds > 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High replication lag"
          description: "Replication lag is {{ $value }}s (threshold: 30s)"
      
      # Application-specific alerts
      - alert: HighPendingSyncs
        expr: sum(sync_pending_count) > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High number of pending syncs"
          description: "{{ $value }} observations are pending sync (threshold: 1000)"
      
      - alert: CriticalPendingSyncs
        expr: sum(sync_pending_count) > 5000
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Critical number of pending syncs"
          description: "{{ $value }} observations are pending sync (threshold: 5000)"
      
      - alert: HighUnacknowledgedAlerts
        expr: sum(alert_unacknowledged_count) > 50
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "High number of unacknowledged alerts"
          description: "{{ $value }} alerts are unacknowledged (threshold: 50)"
      
      - alert: CriticalUnacknowledgedAlerts
        expr: sum(alert_unacknowledged_count) > 100
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Critical number of unacknowledged alerts"
          description: "{{ $value }} alerts are unacknowledged (threshold: 100)"
      
      # Storage alerts
      - alert: DatabaseSizeGrowing
        expr: rate(pg_database_size_bytes{datname='faro_db'}[1h]) > 1073741824
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Database growing rapidly"
          description: "Database is growing at {{ $value | humanizeDataRate }} (threshold: 1GB/h)"
      
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint='/var/lib/postgresql'} / node_filesystem_size_bytes{mountpoint='/var/lib/postgresql'}) < 0.2
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space on PostgreSQL data directory"
          description: "Only {{ $value | humanizePercentage }} disk space available (threshold: 20%)"
```

## Verification

### Test postgres_exporter

```bash
# Check if exporter is running
curl http://localhost:9187/metrics

# Verify custom metrics
curl http://localhost:9187/metrics | grep vehicleobservation_count
curl http://localhost:9187/metrics | grep sync_pending_count
```

### Test Prometheus

```bash
# Check if Prometheus is scraping
curl http://localhost:9090/api/v1/targets

# Query metrics
curl http://localhost:9090/api/v1/query?query=pg_stat_activity_count
```

## Maintenance

### Update postgres_exporter

```bash
# Download new version
wget https://github.com/prometheus-community/postgres_exporter/releases/download/vX.Y.Z/postgres_exporter-vX.Y.Z.linux-amd64.tar.gz
tar xvfz postgres_exporter-vX.Y.Z.linux-amd64.tar.gz

# Stop service
sudo systemctl stop postgres_exporter

# Replace binary
sudo mv postgres_exporter-vX.Y.Z.linux-amd64/postgres_exporter /usr/local/bin/
sudo chmod +x /usr/local/bin/postgres_exporter

# Start service
sudo systemctl start postgres_exporter
```

### Update custom queries

```bash
# Edit queries file
sudo vim /etc/postgres_exporter/queries.yaml

# Reload exporter
sudo systemctl reload postgres_exporter
```

## Troubleshooting

### Common Issues

**Exporter not starting:**
```bash
# Check logs
sudo journalctl -u postgres_exporter -f

# Verify DATA_SOURCE_NAME
cat /etc/default/postgres_exporter

# Test database connection
psql -h localhost -U faro_monitor -d faro_db
```

**Metrics not appearing in Prometheus:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify exporter is accessible
curl http://localhost:9187/metrics

# Check Prometheus logs
sudo journalctl -u prometheus -f
```

**Custom queries not working:**
```bash
# Verify queries file syntax
yamllint /etc/postgres_exporter/queries.yaml

# Test query manually
psql -h localhost -U faro_monitor -d faro_db -c "SELECT agency_id, COUNT(*) FROM vehicleobservation GROUP BY agency_id"
```

## Security Considerations

1. **Use SSL/TLS:**
   - Configure postgres_exporter to use SSL
   - Use `sslmode=require` in DATA_SOURCE_NAME

2. **Restrict access:**
   - Use firewall rules to restrict access to exporter
   - Configure Prometheus authentication

3. **Secure credentials:**
   - Store database password in a secure location
   - Use environment variables or secret management

## References

- postgres_exporter GitHub: https://github.com/prometheus-community/postgres_exporter
- PostgreSQL Monitoring: https://wiki.postgresql.org/wiki/Monitoring
- Prometheus Documentation: https://prometheus.io/docs/
- Grafana Documentation: https://grafana.com/docs/
