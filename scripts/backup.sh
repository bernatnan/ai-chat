#!/bin/bash
set -euo pipefail

# Restic backup script for LibreChat stack
# Backups only non-versioned files (see table below) to local and/or remote repos
# Configure targets in /root/.restic/restic-env.sh
#
# Backed up:
#   /srv/ai-chat/.env           - Environment secrets
#   /srv/ai-chat/librechat.yaml - Local LibreChat config
#   /srv/ai-chat/data-node/     - MongoDB database
#   /srv/ai-chat/uploads/       - User uploaded files
#   /srv/ai-chat/images/        - Generated images

source /root/.restic/restic-env.sh

BASE=/srv/ai-chat
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="$BASE/logs/backup-$TIMESTAMP.log"

mkdir -p "$BASE/logs"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "[$(date)] Starting backup"
echo "[$(date)] Targets: local=${BACKUP_LOCAL:-false} remote=${BACKUP_REMOTE:-false}"

# Helper: run a command for each enabled repo
run_for_repos() {
  local label="$1"
  shift
  if [ "${BACKUP_LOCAL:-false}" = true ]; then
    echo "[$(date)] $label → local"
    restic -r "$RESTIC_REPO_LOCAL" "$@"
  fi
  if [ "${BACKUP_REMOTE:-false}" = true ]; then
    echo "[$(date)] $label → remote"
    restic -r "$RESTIC_REPO_REMOTE" "$@"
  fi
}

# 1. Stop MongoDB for consistent dump
echo "[$(date)] Stopping MongoDB..."
docker stop chat-mongodb 2>/dev/null || echo "[$(date)] MongoDB not running, skipping stop"

# 2. Backup everything in one snapshot (MongoDB + non-versioned files)
echo "[$(date)] Backing up all non-versioned files..."
cd "$BASE"
run_for_repos "backup" backup \
  "data-node" ".env" "librechat.yaml" "uploads" "images" "generated_files"

# 3. Restart MongoDB
echo "[$(date)] Starting MongoDB..."
docker start chat-mongodb 2>/dev/null || echo "[$(date)] MongoDB not found, skipping start"

# 5. Apply retention policy
echo "[$(date)] Applying retention..."
run_for_repos "forget" forget \
  --keep-daily "${RESTIC_KEEP_DAILY:-7}" \
  --keep-weekly "${RESTIC_KEEP_WEEKLY:-4}" \
  --keep-monthly "${RESTIC_KEEP_MONTHLY:-6}" \
  --prune

# 6. Verify local repo integrity (partial)
if [ "${BACKUP_LOCAL:-false}" = true ]; then
  echo "[$(date)] Verifying local repo..."
  restic -r "$RESTIC_REPO_LOCAL" check --read-data-subset=5%
fi

echo "[$(date)] Backup complete"
