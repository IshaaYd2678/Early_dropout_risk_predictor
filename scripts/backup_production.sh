#!/bin/bash
# Backup script for production data

set -e

BACKUP_DIR="/opt/backups/ews"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

echo "========================================="
echo "Early Warning System - Backup"
echo "========================================="

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
echo "Backing up database..."
docker exec ews_postgres pg_dump -U ews_user ews_production | gzip > $BACKUP_DIR/db_$DATE.sql.gz
echo "✅ Database backed up: db_$DATE.sql.gz"

# Backup ML models
echo "Backing up ML models..."
tar -czf $BACKUP_DIR/models_$DATE.tar.gz data/models/
echo "✅ Models backed up: models_$DATE.tar.gz"

# Backup logs
echo "Backing up logs..."
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/
echo "✅ Logs backed up: logs_$DATE.tar.gz"

# Remove old backups
echo "Cleaning old backups (older than $RETENTION_DAYS days)..."
find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -delete
echo "✅ Old backups removed"

# List backups
echo ""
echo "Current backups:"
ls -lh $BACKUP_DIR | tail -10

echo ""
echo "✅ Backup complete!"
