# FARO Database Connection Pooling with PgBouncer

## Overview

This document outlines the setup and configuration of PgBouncer for connection pooling in the FARO system.

## Architecture

```
Application → PgBouncer → PostgreSQL
```

## Benefits

- **Reduced connection overhead:** Reuses existing connections instead of creating new ones
- **Improved performance:** Faster connection establishment
- **Better resource utilization:** Limits maximum connections to PostgreSQL
- **Connection pooling:** Pool mode for transaction-level pooling
- **High availability:** Can be configured for failover

## Installation

### 1. Install PgBouncer

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install pgbouncer
```

**CentOS/RHEL:**
```bash
sudo yum install pgbouncer
```

**macOS:**
```bash
brew install pgbouncer
```

### 2. Configure PgBouncer

**Configuration file:** `/etc/pgbouncer/pgbouncer.ini`

```ini
[databases]
# FARO database configuration
faro_db = host=localhost port=5432 dbname=faro_db

# Admin database for PgBouncer management
pgbouncer = host=localhost port=5432 dbname=pgbouncer

[pgbouncer]
# Pooler mode
pool_mode = transaction

# Connection limits
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 10
reserve_pool_timeout = 3

# Server limits
max_db_connections = 100
max_user_connections = 100

# Timeouts
server_idle_timeout = 600
server_lifetime = 3600
server_connect_timeout = 15
server_login_retry = 5
query_timeout = 300
client_idle_timeout = 600

# Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
log_stats = 1
stats_period = 60

# Admin settings
admin_users = postgres
stats_users = postgres, faro_monitor

# Security
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Listen address
listen_addr = 127.0.0.1
listen_port = 6432

# Unix socket (optional)
unix_socket_dir = /var/run/postgresql

# TLS (optional for production)
# tls_protocols = secure
# tls_ca_file = /etc/ssl/certs/ca-certificates.crt
# tls_cert_file = /etc/ssl/certs/pgbouncer.crt
# tls_key_file = /etc/ssl/private/pgbouncer.key

# Disable prepared statements (required for transaction pooling)
ignore_startup_parameters = extra_float_digits
```

### 3. Configure User Authentication

**User list file:** `/etc/pgbouncer/userlist.txt`

```
# Format: "username" "md5hashed_password"
# Generate hash: echo -n "usernamepassword" | md5sum

"postgres" "md5e8a486538f22e72cae7e4f1b8e5f1b"
"faro" "md5a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5"
"faro_monitor" "md5p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5"
```

**Generate MD5 hash:**
```bash
# For user "faro" with password "senha"
echo -n "faro"senha" | md5sum
```

### 4. Configure PostgreSQL for PgBouncer

**postgresql.conf:**
```ini
# Increase max_connections to accommodate PgBouncer
max_connections = 200

# Enable logging for connection monitoring
log_connections = on
log_disconnections = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# Configure shared_buffers (25% of RAM)
shared_buffers = 4GB

# Configure effective_cache_size (50-75% of RAM)
effective_cache_size = 12GB

# Configure work_mem (based on max_connections)
work_mem = 16MB

# Configure maintenance_work_mem
maintenance_work_mem = 1GB
```

**pg_hba.conf:**
```ini
# Allow connections from PgBouncer
host    faro_db         faro            127.0.0.1/32            md5
host    faro_db         faro_monitor    127.0.0.1/32            md5
host    pgbouncer        postgres        127.0.0.1/32            md5
```

### 5. Create Systemd Service

**Service file:** `/etc/systemd/system/pgbouncer.service`

```ini
[Unit]
Description=PgBouncer connection pooler
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=pgbouncer
Group=pgbouncer
ExecStart=/usr/sbin/pgbouncer -d /etc/pgbouncer/pgbouncer.ini
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/run/postgresql /var/log/pgbouncer

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable pgbouncer
sudo systemctl start pgbouncer
```

## Update Application Configuration

### SQLAlchemy Configuration

**Update database URL in application:**

```python
# Original (direct connection)
DATABASE_URL = "postgresql+asyncpg://faro:senha@localhost:5432/faro_db"

# With PgBouncer
DATABASE_URL = "postgresql+asyncpg://faro:senha@localhost:6432/faro_db"
```

**Note:** When using PgBouncer with transaction pooling, you must disable prepared statements:

```python
# In SQLAlchemy engine configuration
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {
            "prepare_threshold": 0,  # Disable prepared statements
        }
    }
)
```

### Environment Variables

**Update .env file:**
```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://faro:senha@localhost:6432/faro_db
```

## Monitoring PgBouncer

### PgBouncer Statistics

**Connect to PgBouncer admin console:**
```bash
psql -h localhost -p 6432 -U postgres -d pgbouncer
```

**Show statistics:**
```sql
SHOW STATS;
SHOW SERVERS;
SHOW CLIENTS;
SHOW POOLS;
SHOW LISTS;
```

### Prometheus Exporter

**Install pgbouncer_exporter:**
```bash
wget https://github.com/prometheus-community/pgbouncer_exporter/releases/download/v0.4.0/pgbouncer_exporter-0.4.0.linux-amd64.tar.gz
tar xvfz pgbouncer_exporter-0.4.0.linux-amd64.tar.gz
sudo mv pgbouncer_exporter-0.4.0.linux-amd64/pgbouncer_exporter /usr/local/bin/
sudo chmod +x /usr/local/bin/pgbouncer_exporter
```

**Configure exporter:**
```bash
# Environment file
echo "PGBOUNCER_URLS=postgres://postgres:password@localhost:6432/pgbouncer" > /etc/default/pgbouncer_exporter
```

**Systemd service:** `/etc/systemd/system/pgbouncer_exporter.service`

```ini
[Unit]
Description=PgBouncer Exporter
After=network.target pgbouncer.service

[Service]
Type=simple
User=prometheus
Group=prometheus
EnvironmentFile=/etc/default/pgbouncer_exporter
ExecStart=/usr/local/bin/pgbouncer_exporter --web.listen-address=:9127

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Add to Prometheus:**
```yaml
scrape_configs:
  - job_name: 'pgbouncer'
    static_configs:
      - targets: ['localhost:9127']
```

### Grafana Dashboard

**Import dashboard for PgBouncer monitoring:**

```json
{
  "dashboard": {
    "title": "PgBouncer Connection Pooling",
    "panels": [
      {
        "title": "Client Connections",
        "targets": [
          {
            "expr": "pgbouncer_pools_client_active_connections",
            "legendFormat": "{{database}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Server Connections",
        "targets": [
          {
            "expr": "pgbouncer_pools_server_active_connections",
            "legendFormat": "{{database}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Pool Utilization",
        "targets": [
          {
            "expr": "pgbouncer_pools_server_active_connections / pgbouncer_pools_server_max_connections",
            "legendFormat": "{{database}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Query Latency",
        "targets": [
          {
            "expr": "rate(pgbouncer_pools_query_count[5m])",
            "legendFormat": "{{database}}"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

## Performance Tuning

### Pool Mode Selection

**Transaction Pooling (Recommended):**
- Best for stateless applications
- Each client gets a server connection for the duration of a transaction
- Recommended for FARO (FastAPI + SQLAlchemy)

**Session Pooling:**
- Best for applications that use session features
- Each client gets a server connection for the duration of a session
- Not recommended for transaction pooling

**Statement Pooling:**
- Best for applications that use prepared statements heavily
- Not compatible with transaction pooling

### Connection Pool Sizing

**Calculate optimal pool size:**

```python
# Formula: (number of application servers) * (connections per server) / (pool size)

# Example:
# 10 application servers
# 50 connections per server
# Pool size: 25

# Total connections to PostgreSQL: 10 * 50 / 25 = 20
```

**Guidelines:**
- **Small deployment (< 100 concurrent users):** default_pool_size = 25
- **Medium deployment (100-1000 concurrent users):** default_pool_size = 50
- **Large deployment (> 1000 concurrent users):** default_pool_size = 100

### Timeout Configuration

**Adjust timeouts based on application requirements:**

```ini
# For fast queries (< 100ms)
query_timeout = 30

# For slow queries (> 1s)
query_timeout = 300

# For long-running queries (> 10s)
query_timeout = 600
```

## High Availability

### PgBouncer with HAProxy

**HAProxy configuration:** `/etc/haproxy/haproxy.cfg`

```
listen pgbouncer
    bind *:6432
    mode tcp
    balance roundrobin
    option tcp-check
    server pgbouncer1 10.0.0.1:6432 check
    server pgbouncer2 10.0.0.2:6432 check backup
```

### PgBouncer with Multiple PostgreSQL Servers

**Configure multiple databases in pgbouncer.ini:**

```ini
[databases]
faro_db_primary = host=pg-primary.example.com port=5432 dbname=faro_db
faro_db_replica = host=pg-replica.example.com port=5432 dbname=faro_db
```

**Application configuration for read/write splitting:**

```python
# Write operations
WRITE_DB_URL = "postgresql+asyncpg://faro:senha@localhost:6432/faro_db_primary"

# Read operations
READ_DB_URL = "postgresql+asyncpg://faro:senha@localhost:6432/faro_db_replica"
```

## Security

### TLS Configuration

**Enable TLS for production:**

```ini
# In pgbouncer.ini
tls_protocols = secure
tls_ca_file = /etc/ssl/certs/ca-certificates.crt
tls_cert_file = /etc/ssl/certs/pgbouncer.crt
tls_key_file = /etc/ssl/private/pgbouncer.key
```

**Generate certificates:**
```bash
# Generate CA
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt

# Generate server certificate
openssl genrsa -out pgbouncer.key 2048
openssl req -new -key pgbouncer.key -out pgbouncer.csr
openssl x509 -req -days 3650 -in pgbouncer.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out pgbouncer.crt
```

### Access Control

**Restrict access to PgBouncer:**

```ini
# In pgbouncer.ini
listen_addr = 127.0.0.1  # Only local connections
# Or use firewall rules
```

**Firewall rules:**
```bash
# Allow only application server IP
sudo ufw allow from 10.0.0.10 to any port 6432
```

## Troubleshooting

### Common Issues

**PgBouncer not starting:**
```bash
# Check logs
sudo journalctl -u pgbouncer -f

# Verify configuration
pgbouncer -d /etc/pgbouncer/pgbouncer.ini -R

# Check userlist.txt format
cat /etc/pgbouncer/userlist.txt
```

**Connection refused:**
```bash
# Check if PgBouncer is running
sudo systemctl status pgbouncer

# Check if port is listening
sudo netstat -tlnp | grep 6432

# Test connection
psql -h localhost -p 6432 -U faro -d faro_db
```

**Prepared statement errors:**
```python
# Disable prepared statements in SQLAlchemy
connect_args={
    "server_settings": {
        "prepare_threshold": 0,
    }
}
```

**Pool exhaustion:**
```bash
# Check pool statistics
psql -h localhost -p 6432 -U postgres -d pgbouncer -c "SHOW POOLS;"

# Increase pool size
# Edit pgbouncer.ini
default_pool_size = 50

# Reload PgBouncer
sudo systemctl reload pgbouncer
```

## Maintenance

### Reload Configuration

```bash
# Reload without dropping connections
sudo systemctl reload pgbouncer

# Or send SIGHUP
sudo kill -HUP $(pgrep pgbouncer)
```

### Restart PgBouncer

```bash
# Graceful restart (waits for connections to finish)
sudo systemctl restart pgbouncer

# Force restart (drops connections)
sudo systemctl stop pgbouncer
sudo systemctl start pgbouncer
```

### Clean Old Connections

```bash
# Connect to PgBouncer admin console
psql -h localhost -p 6432 -U postgres -d pgbouncer

# Disconnect idle clients
RECONNECT;

# Or disconnect specific client
DISCONNECT <client_pid>;
```

## Verification

### Test Connection Pooling

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def test_pooling():
    engine = create_async_engine(
        "postgresql+asyncpg://faro:senha@localhost:6432/faro_db",
        pool_pre_ping=True,
    )
    
    # Test multiple connections
    async with engine.begin() as conn:
        result = await conn.execute("SELECT 1")
        print(f"Result: {result.fetchone()}")
    
    await engine.dispose()

asyncio.run(test_pooling())
```

### Benchmark Performance

**Compare direct connection vs PgBouncer:**

```bash
# Direct connection
pgbench -h localhost -p 5432 -U faro -d faro_db -c 10 -j 2 -T 60

# Through PgBouncer
pgbench -h localhost -p 6432 -U faro -d faro_db -c 10 -j 2 -T 60
```

## References

- PgBouncer Documentation: https://www.pgbouncer.org/usage.html
- PostgreSQL Connection Pooling: https://wiki.postgresql.org/wiki/Connection_pooling
- SQLAlchemy Connection Pooling: https://docs.sqlalchemy.org/en/14/core/pooling.html
