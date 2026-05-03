#!/bin/bash
# =============================================================================
# EC2 Bootstrap Script — Trend-to-Content Automation Engine
# Uses Python venv (no conda required)
# =============================================================================
set -euo pipefail
exec > /var/log/bootstrap.log 2>&1
echo "=== Bootstrap started at $(date) ==="

APP_USER="ubuntu"
APP_DIR="/home/${APP_USER}/app"
VENV_DIR="${APP_DIR}/venv"
STREAMLIT_PORT="8501"
GITHUB_REPO="https://github.com/yaajnu/Social_media_project.git"

# ── SYSTEM UPDATE ─────────────────────────────────────────────────────────────
echo "=== Updating system packages ==="
apt-get update -y
apt-get install -y git curl wget python3-pip python3-venv python3-dev nginx

# ── CLONE REPO ────────────────────────────────────────────────────────────────
echo "=== Cloning repository ==="
rm -rf "${APP_DIR}"
sudo -u "${APP_USER}" git clone "${GITHUB_REPO}" "${APP_DIR}"

# ── CREATE VENV AND INSTALL DEPS ──────────────────────────────────────────────
echo "=== Creating virtual environment ==="
sudo -u "${APP_USER}" python3 -m venv "${VENV_DIR}"

echo "=== Installing dependencies ==="
sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install --upgrade pip -q
sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"

# ── WRITE .env ────────────────────────────────────────────────────────────────
echo "=== Writing .env ==="
cat > "${APP_DIR}/.env" << 'ENVFILE'
LLM_PROVIDER=gemini
GEMINI_API_KEY=REPLACE_WITH_YOUR_GEMINI_KEY
OPENAI_API_KEY=REPLACE_WITH_YOUR_OPENAI_KEY
CLOUDFARE_API_KEY=REPLACE_WITH_YOUR_CLOUDFARE_KEY
ENVFILE
chown "${APP_USER}:${APP_USER}" "${APP_DIR}/.env"
chmod 600 "${APP_DIR}/.env"

# ── CONFIGURE STREAMLIT ───────────────────────────────────────────────────────
echo "=== Configuring Streamlit ==="
sudo -u "${APP_USER}" mkdir -p "/home/${APP_USER}/.streamlit"
cat > "/home/${APP_USER}/.streamlit/config.toml" << TOML
[server]
port = ${STREAMLIT_PORT}
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
TOML
chown -R "${APP_USER}:${APP_USER}" "/home/${APP_USER}/.streamlit"

# ── SYSTEMD SERVICE ───────────────────────────────────────────────────────────
echo "=== Creating systemd service ==="
cat > /etc/systemd/system/streamlit-app.service << SERVICE
[Unit]
Description=Trend-to-Content Automation Engine
After=network.target

[Service]
Type=simple
User=${APP_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${VENV_DIR}/bin/python -m streamlit run app.py --server.port ${STREAMLIT_PORT} --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable streamlit-app
systemctl start streamlit-app

# ── NGINX ─────────────────────────────────────────────────────────────────────
echo "=== Configuring Nginx ==="
cat > /etc/nginx/sites-available/streamlit << NGINX
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:${STREAMLIT_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 86400;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/streamlit
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
systemctl enable nginx

echo "=== Bootstrap complete at $(date) ==="
echo "=== App available at http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4) ==="
