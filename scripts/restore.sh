#!/bin/bash
set -euo pipefail

# Restic restore script for LibreChat stack
# Restores non-versioned files from local or remote repo
# Configure targets in /root/.restic/restic-env.sh
#
# Usage:
#   scripts/restore.sh              # restore latest from remote
#   scripts/restore.sh --source local  # restore latest from local
#   scripts/restore.sh --snapshot abc123  # restore specific snapshot

source /root/.restic/restic-env.sh

BASE=/srv/ai-chat
RESTORE_TARGET=/tmp/restic-restore

# Parse args
SOURCE="${1:-remote}"  # default: remote
SNAPSHOT="${2:-latest}"

if [ "$SOURCE" = "local" ]; then
  REPO="$RESTIC_REPO_LOCAL"
elif [ "$SOURCE" = "remote" ]; then
  REPO="$RESTIC_REPO_REMOTE"
else
  echo "Usage: $0 [local|remote] [snapshot-id]"
  echo "  source:    local or remote (default: remote)"
  echo "  snapshot:  snapshot ID or 'latest' (default: latest)"
  exit 1
fi

echo "[$(date)] Restoring from $SOURCE repo (snapshot: $SNAPSHOT)..."
echo "[$(date)] Repo: $REPO"

# 1. Stop MongoDB if container exists
if docker ps -q -f name=chat-mongodb 2>/dev/null | grep -q .; then
  echo "[$(date)] Stopping MongoDB..."
  docker stop chat-mongodb
else
  echo "[$(date)] MongoDB container not running, skipping stop"
fi

# 2. Restore to temp directory
echo "[$(date)] Restoring files to $RESTORE_TARGET..."
rm -rf "$RESTORE_TARGET"
restic -r "$REPO" restore "$SNAPSHOT" --target "$RESTORE_TARGET"

# 3. Copy files to destination (clean replace)
echo "[$(date)] Copying files to $BASE..."
mkdir -p "$BASE/data-node" "$BASE/uploads" "$BASE/images" "$BASE/logs" "$BASE/generated_files"
for item in .env librechat.yaml data-node uploads images generated_files; do
  src="$RESTORE_TARGET/$item"
  if [ -e "$src" ]; then
    echo "  → $item"
    rm -rf "$BASE/$item"
    cp -a "$src" "$BASE/"
  fi
done

# 4. Clean up
rm -rf "$RESTORE_TARGET"

# 5. Start MongoDB if it was stopped and Docker is available
if docker info 2>/dev/null | grep -q "Server Version"; then
  echo "[$(date)] Starting services..."
  docker start chat-mongodb 2>/dev/null || echo "[$(date)] MongoDB container not found, skipping start"
fi

echo "[$(date)] Restore complete"
echo "[$(date)] Run 'docker compose up -d' to start the full stack"
