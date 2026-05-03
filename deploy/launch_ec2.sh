#!/bin/bash
# =============================================================================
# Local Launch Script — creates the EC2 instance via AWS CLI
# =============================================================================
# Prerequisites on your local machine:
#   - AWS CLI installed and configured (aws configure)
#   - An existing EC2 key pair (set KEY_PAIR_NAME below)
#
# Usage:
#   chmod +x deploy/launch_ec2.sh
#   ./deploy/launch_ec2.sh
# =============================================================================

set -euo pipefail

# ── CONFIGURATION — edit these ────────────────────────────────────────────────
KEY_PAIR_NAME="your-key-pair-name"          # Your existing EC2 key pair name
REGION="us-east-1"                          # AWS region
INSTANCE_TYPE="t2.micro"                    # Free tier eligible
AMI_ID="ami-0c7217cdde317cfec"             # Ubuntu 22.04 LTS (us-east-1) — update if using different region
SECURITY_GROUP_NAME="streamlit-app-sg"
INSTANCE_NAME="trend-to-content-engine"

# ── STEP 1: Create security group ─────────────────────────────────────────────
echo "Creating security group..."
SG_ID=$(aws ec2 create-security-group \
    --group-name "${SECURITY_GROUP_NAME}" \
    --description "Streamlit app security group" \
    --region "${REGION}" \
    --query 'GroupId' \
    --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
        --group-names "${SECURITY_GROUP_NAME}" \
        --region "${REGION}" \
        --query 'SecurityGroups[0].GroupId' \
        --output text)

echo "Security group ID: ${SG_ID}"

# Allow SSH (port 22) from anywhere — restrict to your IP in production
aws ec2 authorize-security-group-ingress \
    --group-id "${SG_ID}" \
    --protocol tcp --port 22 --cidr 0.0.0.0/0 \
    --region "${REGION}" 2>/dev/null || true

# Allow HTTP (port 80) — Nginx reverse proxy
aws ec2 authorize-security-group-ingress \
    --group-id "${SG_ID}" \
    --protocol tcp --port 80 --cidr 0.0.0.0/0 \
    --region "${REGION}" 2>/dev/null || true

# Allow Streamlit direct access (port 8501) — optional, remove if using Nginx only
aws ec2 authorize-security-group-ingress \
    --group-id "${SG_ID}" \
    --protocol tcp --port 8501 --cidr 0.0.0.0/0 \
    --region "${REGION}" 2>/dev/null || true

# ── STEP 2: Launch instance with bootstrap script as User Data ─────────────────
echo "Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "${AMI_ID}" \
    --instance-type "${INSTANCE_TYPE}" \
    --key-name "${KEY_PAIR_NAME}" \
    --security-group-ids "${SG_ID}" \
    --user-data file://deploy/ec2_bootstrap.sh \
    --region "${REGION}" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${INSTANCE_NAME}}]" \
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Instance launched: ${INSTANCE_ID}"

# ── STEP 3: Wait for instance to be running ────────────────────────────────────
echo "Waiting for instance to reach 'running' state..."
aws ec2 wait instance-running \
    --instance-ids "${INSTANCE_ID}" \
    --region "${REGION}"

# ── STEP 4: Get public IP ──────────────────────────────────────────────────────
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "${INSTANCE_ID}" \
    --region "${REGION}" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo ""
echo "============================================================"
echo "  Instance ID : ${INSTANCE_ID}"
echo "  Public IP   : ${PUBLIC_IP}"
echo "  Region      : ${REGION}"
echo "============================================================"
echo ""
echo "Bootstrap is running in the background (~5-10 min to complete)."
echo ""
echo "SSH into the instance:"
echo "  ssh -i ~/.ssh/${KEY_PAIR_NAME}.pem ubuntu@${PUBLIC_IP}"
echo ""
echo "Watch bootstrap progress:"
echo "  ssh -i ~/.ssh/${KEY_PAIR_NAME}.pem ubuntu@${PUBLIC_IP} 'tail -f /var/log/bootstrap.log'"
echo ""
echo "Once bootstrap completes, your app will be at:"
echo "  http://${PUBLIC_IP}"
echo ""
echo "To update your .env with real API keys after bootstrap:"
echo "  ssh -i ~/.ssh/${KEY_PAIR_NAME}.pem ubuntu@${PUBLIC_IP} 'nano ~/app/.env && sudo systemctl restart streamlit-app'"
