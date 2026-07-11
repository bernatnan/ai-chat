#!/bin/bash
set -euo pipefail

# Restic backup script for LibreChat stack
# Backups MongoDB (data-node/) + all non-git files to local and remote repos

source /root/.restic/restic-env.sh

BASE=/srv/ai-chat
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="$BASE/logs/backup-$TIMESTAMP.log"

mkdir -p "$BASE/tmp" "$BASE/logs"

exec >"$LOG_FILE" 2>&1

echo "[$(date)] Starting backup"

# 1. Stop MongoDB for consistent dump
echo "[$(date)] Stopping MongoDB..."
docker stop chat-mongodb

# 2. Backup MongoDB data directory to both repos
echo "[$(date)] Backing up MongoDB data..."
restic -r "$RESTIC_REPO_LOCAL" backup "$BASE/data-node"
restic -r "$RESTIC_REPO_REMOTE" backup "$BASE/data-node"

# 3. Restart MongoDB
echo "[$(date)] Starting MongoDB..."
docker start chat-mongodb

# 4. Backup everything else (excluding MongoDB, git, models)
echo "[$(date)] Backing up project files..."
restic -r "$RESTIC_REPO_LOCAL" backup \
  --exclude-file="$BASE/scripts/restic-exclude.txt" \
  --exclude="data-node" \
  "$BASE"

restic -r "$RESTIC_REPO_REMOTE" backup \
  --exclude-file="$BASE/scripts/restic-exclude.txt" \
  --exclude="data-node" \
  "$BASE"

# 5. Clean up
rm -rf "$BASE/tmp"

# 6. Apply retention policy
echo "[$(date)] Applying retention..."
restic -r "$RESTIC_REPO_LOCAL" forget \
  --keep-daily "$RESTIC_KEEP_DAILY" \
  --keep-weekly "$RESTIC_KEEP_WEEKLY" \
  --keep-monthly "$RESTIC_KEEP_MONTHLY" \
  --prune

restic -r "$RESTIC_REPO_REMOTE" forget \
  --keep-daily "$RESTIC_KEEP_DAILY" \
  --keep-weekly "$RESTIC_KEEP_WEEKLY" \
  --keep-monthly "$RESTIC_KEEP_MONTHLY" \
  --prune

# 7. Verify local repo integrity (partial)
echo "[$(date)] Verifying local repo..."
restic -r "$RESTIC_REPO_LOCAL" check --read-data-subset=5%

echo "[$(date)] Backup complete"
