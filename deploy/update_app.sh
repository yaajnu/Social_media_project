#!/bin/bash
# =============================================================================
# Update Script — pull latest code and restart the app on the EC2 instance
# =============================================================================
# Usage (run from your LOCAL machine):
#   chmod +x deploy/update_app.sh
#   ./deploy/update_app.sh <EC2_PUBLIC_IP> <KEY_PAIR_PATH>
#
# Example:
#   ./deploy/update_app.sh 54.123.45.67 ~/.ssh/my-key.pem
# =============================================================================

set -euo pipefail

EC2_IP="${1:?Usage: $0 <EC2_PUBLIC_IP> <KEY_PAIR_PATH>}"
KEY_PATH="${2:?Usage: $0 <EC2_PUBLIC_IP> <KEY_PAIR_PATH>}"

echo "Connecting to ${EC2_IP}..."

ssh -i "${KEY_PATH}" -o StrictHostKeyChecking=no "ubuntu@${EC2_IP}" << 'REMOTE'
set -e
echo "=== Pulling latest code ==="
cd ~/app
git pull origin main

echo "=== Installing any new dependencies ==="
~/miniconda3/envs/reddit_proj_env/bin/pip install -r requirements.txt --quiet

echo "=== Restarting Streamlit service ==="
sudo systemctl restart streamlit-app

echo "=== Service status ==="
sudo systemctl status streamlit-app --no-pager

echo "=== Update complete ==="
REMOTE

echo "App updated and restarted at http://${EC2_IP}"
