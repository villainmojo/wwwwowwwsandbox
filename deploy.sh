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

echo "Done."
