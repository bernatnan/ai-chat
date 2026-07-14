#!/bin/bash
set -euo pipefail

# MongoDB migration script
# Dumps data from a source MongoDB version, removes old data,
# and prepares for a target version.
#
# Usage:
#   scripts/migrate-mongodb.sh [source-version] [target-version]
#
# Examples:
#   scripts/migrate-mongodb.sh                          # 4.4 → 8.0.20 (default)
#   scripts/migrate-mongodb.sh 4.4 7.0                  # 4.4 → 7.0
#   scripts/migrate-mongodb.sh 5.0 8.0.20               # 5.0 → 8.0.20
#
# Run this AFTER restoring data-node/ from backup (with the old version).
# The script runs the OLD MongoDB as a temporary container to dump data.

SRC_VERSION="${1:-4.4}"
DST_VERSION="${2:-8.0.20}"
CONTAINER_NAME="chat-mongodb-migrate"

BASE=/srv/ai-chat
DUMP_FILE="$BASE/tmp/mongodump-${SRC_VERSION}.archive"

mkdir -p "$BASE/tmp"

echo "========================================="
echo "  MongoDB Migration: ${SRC_VERSION} → ${DST_VERSION}"
echo "========================================="
echo ""

# 1. Ensure the old MongoDB image is pulled
if ! docker images "mongo:${SRC_VERSION}" --format "{{.Repository}}" 2>/dev/null | grep -q mongo; then
  echo "Pulling mongo:${SRC_VERSION}..."
  docker pull "mongo:${SRC_VERSION}"
fi

# 2. Stop docker-compose MongoDB if running (any version)
echo "[1/4] Stopping docker-compose MongoDB..."
docker compose stop mongodb 2>/dev/null || true

# 3. Start temporary container with source version
echo "[2/4] Starting temporary mongo:${SRC_VERSION}..."
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
docker run -d --name "$CONTAINER_NAME" \
  -v "$BASE/data-node:/data/db" \
  "mongo:${SRC_VERSION}" --noauth
sleep 5

if ! docker ps -q -f "name=${CONTAINER_NAME}" 2>/dev/null | grep -q .; then
  echo "ERROR: Temporary MongoDB container failed to start"
  echo "Check if data-node/ contains valid ${SRC_VERSION} data"
  exit 1
fi

# 4. Dump all databases
echo "[3/4] Dumping all databases from ${SRC_VERSION}..."
docker exec "$CONTAINER_NAME" mongodump --archive="/tmp/mongodump-${SRC_VERSION}.archive"
docker cp "${CONTAINER_NAME}:/tmp/mongodump-${SRC_VERSION}.archive" "$DUMP_FILE"
echo "  → Dump saved to $DUMP_FILE"

# 5. Stop and remove temporary container, delete old data
echo "[4/4] Cleaning up old data..."
docker stop "$CONTAINER_NAME"
docker rm "$CONTAINER_NAME"
rm -rf "$BASE/data-node"

echo ""
echo "========================================="
echo "  Migration dump complete!"
echo "========================================="
echo ""
echo "NEXT STEPS"
echo ""
echo "1. Ensure docker-compose.yml has the target version:"
echo "     mongo:${SRC_VERSION}  →  mongo:${DST_VERSION}"
echo ""
echo "2. Start the target MongoDB and restore:"
echo "     docker compose up -d mongodb"
echo "     docker cp $DUMP_FILE chat-mongodb:/tmp/"
echo "     docker exec chat-mongodb mongorestore --archive=/tmp/mongodump-${SRC_VERSION}.archive"
echo ""
echo "3. Start the full stack:"
echo "     docker compose up -d"
echo ""
echo "4. Clean up:"
echo "     rm -f $DUMP_FILE"
echo ""
echo "========================================="
