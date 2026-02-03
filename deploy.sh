#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="/var/www/sengvis-playground"

echo "Deploying from: ${SRC_DIR}"
echo "Deploying to:   ${DEST_DIR}"

rsync -av --delete \
  --exclude '.git/' \
  --exclude '.github/' \
  --exclude 'api/' \
  "${SRC_DIR}/" "${DEST_DIR}/"

echo "Running post-deploy verification (warn-only)…"
if command -v python3 >/dev/null 2>&1; then
  python3 "${SRC_DIR}/blog/tools/verify_deploy.py" || true
else
  echo "[verify] python3 not found; skipping"
fi

echo "Done."
