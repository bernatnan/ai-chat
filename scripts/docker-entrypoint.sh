#!/bin/sh
set -e

echo "Copying custom icons to public and dist assets..."

# Copy custom icons from mounted volume to public assets
if [ -d /app/assets-custom ]; then
  cp /app/assets-custom/* /app/client/public/assets/ 2>/dev/null || true
  echo "✓ Copied icons to public/assets/"
fi

# Copy custom icons to dist assets (after Vite build)
if [ -d /app/assets-custom ] && [ -d /app/client/dist/assets ]; then
  cp /app/assets-custom/* /app/client/dist/assets/ 2>/dev/null || true
  echo "✓ Copied icons to dist/assets/"
fi

echo "Starting LibreChat server..."
exec node api/server/index.js
