#!/bin/bash
set -euo pipefail

# Restic backup script for LibreChat stack
# Backups MongoDB (data-node/) + all non-git files to local and/or remote repos
# Configure targets in /root/.restic/restic-env.sh

source /root/.restic/restic-env.sh

BASE=/srv/ai-chat
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="$BASE/logs/backup-$TIMESTAMP.log"

mkdir -p "$BASE/tmp" "$BASE/logs"

exec >"$LOG_FILE" 2>&1

echo "[$(date)] Starting backup"
echo "[$(date)] Targets: local=$BACKUP_LOCAL remote=$BACKUP_REMOTE"

# Helper function: run a command for each enabled repo
run_for_repos() {
  local label="$1"
  shift
  if [ "$BACKUP_LOCAL" = true ]; then
    echo "[$(date)] $label → local"
    restic -r "$RESTIC_REPO_LOCAL" "$@"
  fi
  if [ "$BACKUP_REMOTE" = true ]; then
    echo "[$(date)] $label → remote"
    restic -r "$RESTIC_REPO_REMOTE" "$@"
  fi
}

# 1. Stop MongoDB for consistent dump
echo "[$(date)] Stopping MongoDB..."
docker stop chat-mongodb

# 2. Backup MongoDB data directory
echo "[$(date)] Backing up MongoDB data..."
run_for_repos "mongodb" backup "$BASE/data-node"

# 3. Restart MongoDB
echo "[$(date)] Starting MongoDB..."
docker start chat-mongodb

# 4. Backup everything else (excluding MongoDB, git, models)
echo "[$(date)] Backing up project files..."
run_for_repos "project" backup \
  --exclude-file="$BASE/scripts/restic-exclude.txt" \
  --exclude="data-node" \
  "$BASE"

# 5. Clean up
rm -rf "$BASE/tmp"

# 6. Apply retention policy
echo "[$(date)] Applying retention..."
run_for_repos "forget" forget \
  --keep-daily "$RESTIC_KEEP_DAILY" \
  --keep-weekly "$RESTIC_KEEP_WEEKLY" \
  --keep-monthly "$RESTIC_KEEP_MONTHLY" \
  --prune

# 7. Verify local repo integrity (partial)
if [ "$BACKUP_LOCAL" = true ]; then
  echo "[$(date)] Verifying local repo..."
  restic -r "$RESTIC_REPO_LOCAL" check --read-data-subset=5%
fi

echo "[$(date)] Backup complete"
