#!/usr/bin/env bash
# One-time setup on a fresh Ubuntu 22.04 / 24.04 Vultr instance.
# Run as a sudo-capable user.  Idempotent: safe to re-run.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/<owner>/<repo>/<branch>/infrastructure/setup.sh | sudo bash -s -- <repo-url> <branch> <domain>
# OR copy this file to the box and:
#   sudo ./setup.sh <repo-url> <branch> <domain>
set -euo pipefail

REPO_URL="${1:-https://github.com/jonathantchiu/lahacks26.git}"
BRANCH="${2:-claude/crazy-visvesvaraya-1e66df}"
DOMAIN="${3:-}"
APP_DIR="/opt/sentinelai"
APP_USER="sentinel"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

echo "==> apt update + base deps"
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3.11 python3.11-venv python3-pip \
  ffmpeg libsm6 libxext6 libgl1 \
  nginx git curl ca-certificates \
  certbot python3-certbot-nginx

echo "==> create app user"
if ! id -u "${APP_USER}" >/dev/null 2>&1; then
  useradd --system --create-home --shell /usr/sbin/nologin "${APP_USER}"
fi

echo "==> clone repo to ${APP_DIR}"
mkdir -p "${APP_DIR}"
chown "${APP_USER}:${APP_USER}" "${APP_DIR}"
if [[ ! -d "${APP_DIR}/.git" ]]; then
  sudo -u "${APP_USER}" git clone --branch "${BRANCH}" "${REPO_URL}" "${APP_DIR}"
else
  sudo -u "${APP_USER}" git -C "${APP_DIR}" fetch --all
  sudo -u "${APP_USER}" git -C "${APP_DIR}" checkout "${BRANCH}"
  sudo -u "${APP_USER}" git -C "${APP_DIR}" pull --ff-only
fi

echo "==> python venv + deps"
sudo -u "${APP_USER}" python3.11 -m venv "${APP_DIR}/backend/venv"
sudo -u "${APP_USER}" "${APP_DIR}/backend/venv/bin/pip" install --upgrade pip wheel
sudo -u "${APP_USER}" "${APP_DIR}/backend/venv/bin/pip" install -r "${APP_DIR}/backend/requirements.txt"

echo "==> .env"
if [[ ! -f "${APP_DIR}/backend/.env" ]]; then
  cp "${APP_DIR}/backend/.env.example" "${APP_DIR}/backend/.env"
  chown "${APP_USER}:${APP_USER}" "${APP_DIR}/backend/.env"
  chmod 600 "${APP_DIR}/backend/.env"
  echo
  echo "  ⚠️  Edit ${APP_DIR}/backend/.env with real keys before starting:"
  echo "      sudo -u ${APP_USER} \$EDITOR ${APP_DIR}/backend/.env"
  echo
fi

echo "==> install systemd unit"
install -m 644 "${APP_DIR}/infrastructure/sentinelai.service" /etc/systemd/system/sentinelai.service
systemctl daemon-reload
systemctl enable sentinelai

echo "==> install nginx site"
SITE_TMP=$(mktemp)
sed "s/__DOMAIN__/${DOMAIN:-_}/g" "${APP_DIR}/infrastructure/nginx.conf" > "${SITE_TMP}"
install -m 644 "${SITE_TMP}" /etc/nginx/sites-available/sentinelai
ln -sf /etc/nginx/sites-available/sentinelai /etc/nginx/sites-enabled/sentinelai
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "==> firewall"
if command -v ufw >/dev/null; then
  ufw allow 'Nginx Full' || true
  ufw allow OpenSSH || true
fi

echo
echo "✅ base install complete."
echo
echo "Next steps:"
echo "  1. Edit ${APP_DIR}/backend/.env with API keys"
echo "  2. Start the app:        sudo systemctl start sentinelai && sudo journalctl -u sentinelai -f"
echo "  3. Issue HTTPS cert:     sudo certbot --nginx -d ${DOMAIN:-yourdomain.com}"
echo "  4. Verify:               curl https://${DOMAIN:-yourdomain.com}/health"
