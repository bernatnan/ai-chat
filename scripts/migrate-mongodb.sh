#!/bin/bash
set -euo pipefail

# MongoDB 4.4 → 8.0 migration script
# Dumps all data from existing 4.4 instance, removes old data,
# and prepares for the new 8.0 image.
#
# Usage:
#   Restore 4.4 data, then run this script BEFORE changing docker-compose.yml
#   scripts/migrate-mongodb.sh

BASE=/srv/ai-chat
DUMP_FILE="$BASE/tmp/mongodump-4.4.archive"

mkdir -p "$BASE/tmp"

echo "========================================="
echo "  MongoDB 4.4 → 8.0 Migration"
echo "========================================="
echo ""

# 1. Ensure MongoDB 4.4 container exists
if ! docker images mongo:4.4 --format "{{.Repository}}" 2>/dev/null | grep -q mongo; then
  echo "Pulling mongo:4.4 image..."
  docker compose pull mongodb
fi

# 2. Start MongoDB 4.4
echo "[1/4] Starting MongoDB 4.4..."
docker compose up -d mongodb
sleep 5

if ! docker ps -q -f name=chat-mongodb 2>/dev/null | grep -q .; then
  echo "ERROR: MongoDB container failed to start"
  exit 1
fi

# 3. Dump all databases
echo "[2/4] Dumping all databases..."
docker exec chat-mongodb mongodump --archive=/tmp/mongodump-4.4.archive
docker cp chat-mongodb:/tmp/mongodump-4.4.archive "$DUMP_FILE"
echo "  → Dump saved to $DUMP_FILE"

# 4. Stop and remove old data
echo "[3/4] Stopping MongoDB and removing old data..."
docker compose down
rm -rf "$BASE/data-node"

echo ""
echo "[4/4] Migration dump complete!"
echo ""
echo "========================================="
echo "  NEXT STEPS"
echo "========================================="
echo ""
echo "1. Update docker-compose.yml:"
echo "     mongo:4.4  →  mongo:8.0.20"
echo ""
echo "2. Start MongoDB 8.0 and restore:"
echo "     docker compose up -d mongodb"
echo "     docker cp $DUMP_FILE chat-mongodb:/tmp/"
echo "     docker exec chat-mongodb mongorestore --archive=/tmp/mongodump-4.4.archive"
echo ""
echo "3. Start the full stack:"
echo "     docker compose up -d"
echo ""
echo "4. Clean up:"
echo "     rm -f $DUMP_FILE"
echo ""
echo "========================================="
