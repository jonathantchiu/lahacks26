#!/usr/bin/env bash
# Pull latest code on the Vultr box and restart the service.
# Run on the box as root (or via `sudo bash deploy.sh`).
set -euo pipefail

APP_DIR="/opt/sentinelai"
APP_USER="sentinel"
BRANCH="${1:-claude/crazy-visvesvaraya-1e66df}"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

echo "==> git fetch + checkout ${BRANCH}"
sudo -u "${APP_USER}" git -C "${APP_DIR}" fetch --all --prune
sudo -u "${APP_USER}" git -C "${APP_DIR}" checkout "${BRANCH}"
sudo -u "${APP_USER}" git -C "${APP_DIR}" pull --ff-only

echo "==> pip install -r requirements.txt"
sudo -u "${APP_USER}" "${APP_DIR}/backend/venv/bin/pip" install -r "${APP_DIR}/backend/requirements.txt"

echo "==> systemd reload + restart"
systemctl daemon-reload
systemctl restart sentinelai
sleep 2
systemctl --no-pager status sentinelai | sed -n '1,10p'

echo
echo "==> health check"
curl -fsS http://127.0.0.1:8000/health && echo
