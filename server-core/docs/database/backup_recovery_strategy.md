# FARO Database Backup and Recovery Strategy

## Overview

This document outlines the comprehensive backup and recovery strategy for the FARO PostgreSQL database.

## Backup Strategy

### 1. Full Backups

**Frequency:** Daily  
**Time:** 02:00 AM UTC (low traffic period)  
**Retention:** 30 days  
**Method:** pg_dump

**Script:** `scripts/backup_full.sh`

```bash
#!/bin/bash
# Full database backup script
# Usage: ./scripts/backup_full.sh

DB_NAME="faro_db"
DB_USER="postgres"
BACKUP_DIR="/var/backups/faro"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/faro_full_${DATE}.sql.gz"

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

# Perform full backup
pg_dump -h localhost -U ${DB_USER} -d ${DB_NAME} | gzip > ${BACKUP_FILE}

# Verify backup
if [ $? -eq 0 ]; then
    echo "Backup successful: ${BACKUP_FILE}"
    # Upload to S3 (optional)
    # aws s3 cp ${BACKUP_FILE} s3://faro-backups/database/
else
    echo "Backup failed!"
    exit 1
fi

# Clean up old backups (keep last 30 days)
find ${BACKUP_DIR} -name "faro_full_*.sql.gz" -mtime +30 -delete
```

### 2. WAL Archiving for Point-in-Time Recovery (PITR)

**Configuration:** postgresql.conf

```ini
# Enable WAL archiving
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/16/wal/%f'
max_wal_senders = 3
wal_keep_size = 1GB
```

**Retention:** 7 days  
**Location:** `/var/lib/postgresql/16/wal/`

**Cleanup Script:** `scripts/cleanup_wal.sh`

```bash
#!/bin/bash
# Clean up old WAL files (keep last 7 days)
WAL_DIR="/var/lib/postgresql/16/wal"
find ${WAL_DIR} -type f -mtime +7 -delete
```

### 3. Schema-only Backups

**Frequency:** Weekly  
**Time:** Sunday 03:00 AM UTC  
**Retention:** 90 days

**Script:** `scripts/backup_schema.sh`

```bash
#!/bin/bash
# Schema-only backup
DB_NAME="faro_db"
DB_USER="postgres"
BACKUP_DIR="/var/backups/faro/schema"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/faro_schema_${DATE}.sql"

mkdir -p ${BACKUP_DIR}
pg_dump -h localhost -U ${DB_USER} -d ${DB_NAME} --schema-only > ${BACKUP_FILE}

# Clean up old schema backups (keep last 90 days)
find ${BACKUP_DIR} -name "faro_schema_*.sql" -mtime +90 -delete
```

## Recovery Procedures

### 1. Full Database Recovery

**Scenario:** Complete database failure or corruption

**Steps:**

1. **Stop the application:**
   ```bash
   # Stop the FARO server
   systemctl stop faro-server
   ```

2. **Drop the damaged database:**
   ```bash
   psql -U postgres -c "DROP DATABASE IF EXISTS faro_db;"
   ```

3. **Create a new database:**
   ```bash
   psql -U postgres -c "CREATE DATABASE faro_db;"
   ```

4. **Restore from backup:**
   ```bash
   gunzip -c /var/backups/faro/faro_full_YYYYMMDD_HHMMSS.sql.gz | psql -U postgres -d faro_db
   ```

5. **Verify the restore:**
   ```bash
   psql -U postgres -d faro_db -c "\dt"
   psql -U postgres -d faro_db -c "SELECT COUNT(*) FROM vehicleobservation;"
   ```

6. **Restart the application:**
   ```bash
   systemctl start faro-server
   ```

### 2. Point-in-Time Recovery (PITR)

**Scenario:** Need to recover to a specific point in time

**Steps:**

1. **Stop PostgreSQL:**
   ```bash
   systemctl stop postgresql
   ```

2. **Restore the base backup:**
   ```bash
   # Remove existing data directory
   rm -rf /var/lib/postgresql/16/main
   
   # Restore from base backup
   pg_restore -D /var/lib/postgresql/16/main /var/backups/faro/faro_full_YYYYMMDD_HHMMSS.sql.gz
   ```

3. **Configure recovery:**
   ```bash
   # Create recovery.conf
   echo "restore_command = 'cp /var/lib/postgresql/16/wal/%f %p'" > /var/lib/postgresql/16/main/recovery.conf
   echo "recovery_target_time = '2026-04-25 14:30:00 UTC'" >> /var/lib/postgresql/16/main/recovery.conf
   ```

4. **Start PostgreSQL:**
   ```bash
   systemctl start postgresql
   ```

5. **Verify recovery:**
   ```bash
   psql -U postgres -d faro_db -c "SELECT NOW();"
   ```

### 3. Table-level Recovery

**Scenario:** Need to recover a specific table

**Steps:**

1. **Extract table from backup:**
   ```bash
   pg_restore -h localhost -U postgres -d faro_db_temp \
     -t vehicleobservation \
     /var/backups/faro/faro_full_YYYYMMDD_HHMMSS.sql.gz
   ```

2. **Copy data to production:**
   ```bash
   psql -U postgres -d faro_db -c "
     INSERT INTO vehicleobservation 
     SELECT * FROM faro_db_temp.vehicleobservation
     ON CONFLICT DO NOTHING;
   "
   ```

## Backup Verification

### Weekly Backup Verification

**Script:** `scripts/verify_backup.sh`

```bash
#!/bin/bash
# Verify the most recent backup
BACKUP_FILE=$(ls -t /var/backups/faro/faro_full_*.sql.gz | head -1)
TEMP_DB="faro_verify_$(date +%s)"

# Create temporary database
psql -U postgres -c "CREATE DATABASE ${TEMP_DB};"

# Restore backup to temporary database
gunzip -c ${BACKUP_FILE} | psql -U postgres -d ${TEMP_DB}

# Verify table counts
psql -U postgres -d ${TEMP_DB} -c "
  SELECT 
    schemaname,
    tablename,
    n_tup_ins as row_count
  FROM pg_stat_user_tables
  ORDER BY tablename;
"

# Drop temporary database
psql -U postgres -c "DROP DATABASE ${TEMP_DB};"

echo "Backup verification completed"
```

## Monitoring and Alerting

### Backup Status Monitoring

**Prometheus Exporter:** Configure postgres_exporter to track backup status

**Alert Rules:**

```yaml
groups:
  - name: database_backups
    rules:
      - alert: BackupFailed
        expr: pg_backup_last_success_seconds == 0
        for: 30m
        labels:
          severity: critical
        annotations:
          summary: "Database backup failed"
          description: "Last backup failed or not completed"
      
      - alert: BackupOld
        expr: time() - pg_backup_last_success_seconds > 86400
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Database backup is old"
          description: "Last backup is more than 24 hours old"
      
      - alert: WALArchivingFailed
        expr: pg_wal_archive_failed > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "WAL archiving failed"
          description: "WAL files are not being archived"
```

## Geographic Distribution

### S3 Backup Replication

**Configuration:** AWS CLI

```bash
# Configure AWS credentials
aws configure

# Upload backups to S3
aws s3 sync /var/backups/faro s3://faro-backups/database --delete

# Enable cross-region replication
aws s3api put-bucket-replication \
  --bucket faro-backups \
  --replication-configuration file://replication.json
```

**replication.json:**
```json
{
  "Role": "arn:aws:iam::123456789012:role/replication-role",
  "Rules": [
    {
      "Status": "Enabled",
      "Priority": 1,
      "Filter": {
        "Prefix": "database/"
      },
      "Destination": {
        "Bucket": "arn:aws:s3:::faro-backups-dr",
        "StorageClass": "STANDARD_IA"
      }
    }
  ]
}
```

## Disaster Recovery Plan

### RTO (Recovery Time Objective): 4 hours
### RPO (Recovery Point Objective): 15 minutes

### Disaster Recovery Checklist

1. **Immediate Actions (0-30 minutes):**
   - [ ] Notify stakeholders
   - [ ] Assess the extent of damage
   - [ ] Determine recovery type (full vs PITR)
   - [ ] Stop application to prevent data corruption

2. **Recovery Actions (30 minutes - 4 hours):**
   - [ ] Select appropriate backup
   - [ ] Restore database
   - [ ] Verify data integrity
   - [ ] Test application connectivity
   - [ ] Restart application

3. **Post-Recovery (4-8 hours):**
   - [ ] Monitor system performance
   - [ ] Verify data consistency
   - [ ] Document the incident
   - [ ] Update disaster recovery procedures

## Automation

### Cron Jobs

```bash
# Full backup daily at 02:00 AM
0 2 * * * /opt/faro/scripts/backup_full.sh

# Schema backup weekly on Sunday at 03:00 AM
0 3 * * 0 /opt/faro/scripts/backup_schema.sh

# WAL cleanup daily at 04:00 AM
0 4 * * * /opt/faro/scripts/cleanup_wal.sh

# Backup verification weekly on Sunday at 05:00 AM
0 5 * * 0 /opt/faro/scripts/verify_backup.sh
```

### Systemd Services

**Service File:** `/etc/systemd/system/faro-backup.service`

```ini
[Unit]
Description=FARO Database Backup
After=postgresql.service

[Service]
Type=oneshot
ExecStart=/opt/faro/scripts/backup_full.sh
User=postgres
Group=postgres

[Install]
WantedBy=multi-user.target
```

**Timer File:** `/etc/systemd/system/faro-backup.timer`

```ini
[Unit]
Description=Daily FARO Database Backup

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

## Security Considerations

1. **Backup Encryption:**
   - Encrypt backups using GPG
   - Store encryption keys securely (AWS KMS)

2. **Access Control:**
   - Restrict backup directory access to postgres user only
   - Use PostgreSQL roles with minimal privileges for backup operations

3. **Network Security:**
   - Use SSL for remote backups
   - Restrict S3 bucket access using IAM policies

## Testing

### Monthly Disaster Recovery Drill

**Scenario:** Simulate complete database failure

**Steps:**
1. Create a test environment
2. Restore the most recent backup
3. Verify all data is intact
4. Test application functionality
5. Document any issues found
6. Update procedures as needed

## Contact Information

**Database Administrator:** dba@faro.gov.br  
**On-Call:** +55 11 99999-9999  
**Escalation:** cto@faro.gov.br

## References

- PostgreSQL Backup and Recovery: https://www.postgresql.org/docs/current/backup.html
- Point-in-Time Recovery: https://www.postgresql.org/docs/current/runtime-config-wal.html
- AWS S3 Best Practices: https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html
