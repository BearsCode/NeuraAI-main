#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/neuraai}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

mkdir -p "${BACKUP_DIR}"

echo "=== Backup started: ${TIMESTAMP} ==="

# PostgreSQL
echo "--- Dumping PostgreSQL ---"
docker compose exec -T postgres pg_dumpall -U postgres \
  | gzip > "${BACKUP_DIR}/postgres_${TIMESTAMP}.sql.gz"
echo "  OK: $(du -h "${BACKUP_DIR}/postgres_${TIMESTAMP}.sql.gz" | cut -f1)"

# MinIO data (tar the volume)
echo "--- Backing up MinIO ---"
docker run --rm -v neuraai_minio_data:/data -v "${BACKUP_DIR}:/backup" alpine \
  tar czf "/backup/minio_${TIMESTAMP}.tar.gz" -C /data .
echo "  OK: $(du -h "${BACKUP_DIR}/minio_${TIMESTAMP}.tar.gz" | cut -f1)"

# Redis RDB
echo "--- Backing up Redis ---"
docker compose exec -T redis redis-cli SAVE
docker run --rm -v neuraai_redis_data:/data -v "${BACKUP_DIR}:/backup" alpine \
  cp /data/dump.rdb "/backup/redis_${TIMESTAMP}.rdb"
echo "  OK: $(du -h "${BACKUP_DIR}/redis_${TIMESTAMP}.rdb" | cut -f1)"

# .env config
echo "--- Backing up .env ---"
cp .env "${BACKUP_DIR}/env_${TIMESTAMP}.txt"
echo "  OK"

# Cleanup old backups
echo "--- Cleaning backups older than ${RETENTION_DAYS} days ---"
find "${BACKUP_DIR}" -name "*.gz" -mtime "+${RETENTION_DAYS}" -delete
find "${BACKUP_DIR}" -name "*.rdb" -mtime "+${RETENTION_DAYS}" -delete
find "${BACKUP_DIR}" -name "env_*.txt" -mtime "+${RETENTION_DAYS}" -delete

echo "=== Backup finished ==="
