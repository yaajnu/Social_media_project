# AWS EC2 Deployment Guide

## Prerequisites

1. **AWS CLI** installed and configured:
   ```bash
   aws configure
   # Enter: Access Key ID, Secret Access Key, Region (e.g. us-east-1), output format (json)
   ```

2. **EC2 Key Pair** — create one in the AWS Console under EC2 → Key Pairs, download the `.pem` file.

3. **GitHub repo** — push your code to GitHub first (or use the S3 option in the bootstrap script).

---

## Step 1 — Edit the bootstrap script

Open `deploy/ec2_bootstrap.sh` and set:

```bash
GITHUB_REPO="https://github.com/YOUR_USERNAME/YOUR_REPO.git"
```

Also replace the placeholder API keys in the `.env` section:
```bash
GEMINI_API_KEY=your-actual-key
CLOUDFARE_API_KEY=your-actual-key
```

> **Security tip**: Don't commit real keys to GitHub. Instead, leave placeholders in the bootstrap script and set them via SSH after launch (see Step 4).

---

## Step 2 — Edit the launch script

Open `deploy/launch_ec2.sh` and set:

```bash
KEY_PAIR_NAME="your-key-pair-name"   # name of your .pem key pair (without .pem)
REGION="us-east-1"                   # your preferred AWS region
```

Check the AMI ID for your region — Ubuntu 22.04 LTS AMIs vary by region:
- us-east-1: `ami-0c7217cdde317cfec`
- us-west-2: `ami-03f65b8614a860c29`
- eu-west-1: `ami-0694d931cee176e7d`

Find the latest at: https://cloud-images.ubuntu.com/locator/ec2/

---

## Step 3 — Launch

```bash
chmod +x deploy/launch_ec2.sh
./deploy/launch_ec2.sh
```

This will:
- Create a security group (ports 22, 80, 8501)
- Launch a `t2.micro` instance (free tier)
- Attach the bootstrap script as User Data
- Print the public IP when ready

Bootstrap takes **5–10 minutes** to complete. Watch progress:
```bash
ssh -i ~/.ssh/your-key.pem ubuntu@<PUBLIC_IP> 'tail -f /var/log/bootstrap.log'
```

---

## Step 4 — Set your API keys (if you left placeholders)

```bash
ssh -i ~/.ssh/your-key.pem ubuntu@<PUBLIC_IP>
nano ~/app/.env
# Edit the keys, save with Ctrl+O, exit with Ctrl+X
sudo systemctl restart streamlit-app
```

---

## Step 5 — Access the app

Open in your browser:
```
http://<PUBLIC_IP>
```

---

## Updating the app after code changes

Push your changes to GitHub, then run:
```bash
./deploy/update_app.sh <PUBLIC_IP> ~/.ssh/your-key.pem
```

---

## Useful SSH commands

```bash
# Check if app is running
sudo systemctl status streamlit-app

# View live app logs
sudo journalctl -u streamlit-app -f

# Restart the app
sudo systemctl restart streamlit-app

# View bootstrap log
cat /var/log/bootstrap.log
```

---

## Cost

- **t2.micro**: Free for 12 months (750 hrs/month = 24/7 coverage)
- **20 GB gp3 EBS**: Free tier includes 30 GB
- **Data transfer**: First 100 GB/month outbound is free
- **After 12 months**: ~$8.50/month

## Free tier eligibility check

https://console.aws.amazon.com/billing/home#/freetier
