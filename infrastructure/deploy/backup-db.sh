#!/usr/bin/env bash
# Daily Postgres backup for copilot_dev. Install a cron entry (e.g. via `crontab -e`):
#   0 3 * * * /usr/bin/env bash <REPO_PATH>/infrastructure/deploy/backup-db.sh
# Replace <PLACEHOLDER>s below or export them in the crontab environment instead.
set -euo pipefail

DB_NAME="${COPILOT_DB_NAME:-copilot_dev}"
DB_USER="${COPILOT_DB_USER:-copilot}"
BACKUP_DIR="${COPILOT_BACKUP_DIR:-<REPO_PATH>/backups}"
KEEP_DAYS="${COPILOT_BACKUP_KEEP_DAYS:-14}"

mkdir -p "$BACKUP_DIR"
timestamp="$(date +%Y%m%d-%H%M%S)"
out_file="$BACKUP_DIR/${DB_NAME}-${timestamp}.sql.gz"

pg_dump --username="$DB_USER" --no-password "$DB_NAME" | gzip > "$out_file"
echo "Backed up $DB_NAME to $out_file"

# Prune backups older than KEEP_DAYS. The knowledge-base vector index (.qdrant, .qdrant-mcp) is
# not backed up - it is derived, rebuildable data (rag-core ingest against knowledge-base/, which
# is already in git), not source of truth. Only the relational database is.
find "$BACKUP_DIR" -name "${DB_NAME}-*.sql.gz" -mtime "+${KEEP_DAYS}" -delete
