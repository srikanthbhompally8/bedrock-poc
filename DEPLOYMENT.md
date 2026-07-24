# EC2 Deployment & Nginx Configuration Guide

## Deployment Overview

The Bedrock POC is deployed on AWS EC2 with Nginx as a reverse proxy.
This guide covers setup, configuration, and management.

```
Internet
    │
    ▼
Nginx (Port 80/443)
    │ Reverse proxy
    ▼
Streamlit App (Port 8501)
    │ bedrock_poc package
    ▼
AWS Bedrock API
```

## Current Deployment Status

| Property | Value |
|----------|-------|
| **Public IP** | 52.15.231.184 |
| **Instance Type** | t3.micro (free tier eligible) |
| **OS** | Amazon Linux 2 |
| **Deployment Method** | Systemd service + Nginx |
| **Service Status** | Running 24/7 |
| **Auto-Restart** | Enabled on failure |

**Access URL:** `http://52.15.231.184/`

## EC2 Instance Setup

### 1. Launch EC2 Instance

```bash
# AWS CLI (or use console)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.micro \
  --key-name your-key-pair \
  --security-groups default \
  --region us-east-1 \
  --iam-instance-profile Name=bedrock-poc-profile
```

**Recommended Configuration:**
- **AMI:** Amazon Linux 2 (free tier)
- **Type:** t3.micro (free tier / $0.0104/hour)
- **Storage:** 8 GB EBS (gp3)
- **Region:** us-east-1 (for Bedrock)
- **Security Group:** Allow SSH (22), HTTP (80), HTTPS (443)

### 2. Configure Security Group

```bash
# Allow SSH
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# Allow HTTP
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Allow HTTPS (future)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

### 3. Connect to Instance

```bash
ssh -i your-key.pem ec2-user@52.15.231.184
```

## Application Installation

### 1. Install Dependencies

```bash
sudo yum update -y
sudo yum install -y git python3.11 python3.11-venv nginx

# Verify Python
python3.11 --version
```

### 2. Clone Repository

```bash
cd /home/ec2-user
git clone https://github.com/your-username/bedrock-poc.git
cd bedrock-poc
```

### 3. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create .env File

```bash
cat > .env << 'EOF'
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
EOF
```

**Note:** On EC2 with an IAM role, AWS credentials are automatic. Don't add them to .env.

### 5. Test Application Locally

```bash
# Quick test
python3 cli.py chat <<< "Hello"

# Streamlit test (requires terminal)
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## Nginx Configuration

### 1. Create Nginx Config

```bash
sudo tee /etc/nginx/sites-available/bedrock-poc > /dev/null << 'EOF'
upstream streamlit {
    server 127.0.0.1:8501;
}

server {
    listen 80;
    server_name _;
    client_max_body_size 100M;

    location / {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        proxy_redirect off;

        # Headers for Streamlit
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "OK";
    }
}
EOF
```

### 2. Enable Site

```bash
# Remove default config
sudo rm -f /etc/nginx/sites-enabled/default

# Enable bedrock-poc config
sudo ln -s /etc/nginx/sites-available/bedrock-poc /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 3. Verify Nginx

```bash
sudo systemctl status nginx

# Check logs
sudo tail -f /var/log/nginx/error.log
```

## Systemd Service Setup

### 1. Create Service File

```bash
sudo tee /etc/systemd/system/bedrock-poc.service > /dev/null << 'EOF'
[Unit]
Description=Bedrock POC Application
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/bedrock-poc
Environment="PATH=/home/ec2-user/bedrock-poc/venv/bin"
Environment="AWS_REGION=us-east-1"
Environment="BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0"
ExecStart=/home/ec2-user/bedrock-poc/venv/bin/streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --logger.level=info

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

### 2. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable bedrock-poc
sudo systemctl start bedrock-poc

# Check status
sudo systemctl status bedrock-poc

# View logs
sudo journalctl -u bedrock-poc -n 50 -f
```

### 3. Service Management Commands

```bash
# Start
sudo systemctl start bedrock-poc

# Stop
sudo systemctl stop bedrock-poc

# Restart
sudo systemctl restart bedrock-poc

# View full logs
sudo journalctl -u bedrock-poc -n 100

# Real-time logs
sudo journalctl -u bedrock-poc -f

# Check if running
sudo systemctl is-active bedrock-poc
```

## Monitoring & Troubleshooting

### Health Check

```bash
# From local machine
curl http://52.15.231.184/health

# From EC2 instance
curl http://localhost/health
```

**Expected response:** `OK`

### Check Application Status

```bash
# Via SSH
ssh ec2-user@52.15.231.184 "sudo systemctl status bedrock-poc"

# View application logs
ssh ec2-user@52.15.231.184 "sudo journalctl -u bedrock-poc -n 20"
```

### Nginx Logs

```bash
# Error log
sudo tail -f /var/log/nginx/error.log

# Access log
sudo tail -f /var/log/nginx/access.log

# Both
sudo tail -f /var/log/nginx/*.log
```

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `502 Bad Gateway` | Streamlit not running | `sudo systemctl restart bedrock-poc` |
| `Connection refused` | Nginx can't reach Streamlit | Check firewall, verify port 8501 is open |
| `AWS credentials error` | IAM role not attached | Add IAM role to EC2 instance |
| `Cannot import streamlit` | Virtual env not activated | Check systemd `Environment` paths |
| `Port already in use` | Another app on port 8501 | Change port in systemd service |

### Debug Mode

Enable more logging for troubleshooting:

```bash
# Edit service file
sudo nano /etc/systemd/system/bedrock-poc.service

# Change log level
# --logger.level=info  →  --logger.level=debug

sudo systemctl daemon-reload
sudo systemctl restart bedrock-poc
```

## Updates & Maintenance

### Deploy Code Changes

```bash
ssh ec2-user@52.15.231.184 << 'EOF'
cd bedrock-poc
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart bedrock-poc
EOF
```

### Update Dependencies

```bash
ssh ec2-user@52.15.231.184 << 'EOF'
cd bedrock-poc
source venv/bin/activate
pip install --upgrade -r requirements.txt
sudo systemctl restart bedrock-poc
EOF
```

### Backup Data

```bash
# Note: This POC doesn't persist data (in-memory only)
# For production, backup EC2 snapshots and vector DB

# Create EBS snapshot
aws ec2 create-snapshot \
  --volume-id vol-xxxxxxxx \
  --description "Bedrock POC backup $(date +%Y-%m-%d)"
```

## SSL/HTTPS Setup (Optional)

For production, use Let's Encrypt with Nginx:

```bash
# Install certbot
sudo amazon-linux-extras install python3.8-certbot -y

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Update Nginx config
sudo nano /etc/nginx/sites-available/bedrock-poc
# Add:
# server {
#     listen 443 ssl http2;
#     ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
# }

sudo systemctl restart nginx
```

## Cost Optimization

| Component | Cost | Optimization |
|-----------|------|-------------|
| EC2 t3.micro | $0.0104/hour | Use free tier, auto-scale |
| Data transfer | $0.09/GB out | CloudFront CDN for static assets |
| Bedrock API | $0.003-0.015 per K tokens | Cache summaries, batch requests |
| EBS storage | $0.10/month | Use gp3, minimum size |

**Estimated monthly cost:** $10-15

## Auto-Scaling (Future)

For higher traffic, set up auto-scaling:

```bash
# Create Launch Template
aws ec2 create-launch-template \
  --launch-template-name bedrock-poc \
  --version-description "POC with systemd" \
  --launch-template-data '{
    "ImageId": "ami-...",
    "InstanceType": "t3.micro",
    "IamInstanceProfile": {"Name": "bedrock-poc-profile"}
  }'

# Create Auto Scaling Group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name bedrock-poc-asg \
  --launch-template LaunchTemplateName=bedrock-poc \
  --min-size 1 \
  --max-size 3 \
  --desired-capacity 1 \
  --availability-zones us-east-1a us-east-1b

# Add Load Balancer
aws elbv2 create-load-balancer \
  --name bedrock-poc-alb \
  --subnets subnet-xxxxxxxx subnet-yyyyyyyy
```

## Checklist

- [ ] EC2 instance launched (t3.micro, Amazon Linux 2)
- [ ] Security group allows SSH, HTTP, HTTPS
- [ ] IAM role with Bedrock permissions attached
- [ ] Repository cloned and app installed
- [ ] `.env` file created with AWS configuration
- [ ] Nginx configured and running
- [ ] Systemd service created and enabled
- [ ] Application accessible at `http://52.15.231.184/`
- [ ] Health check passing
- [ ] Logs being collected (journalctl)
- [ ] Cost monitoring enabled in AWS Billing

## Support

- **SSH into instance:** `ssh -i your-key.pem ec2-user@52.15.231.184`
- **View live logs:** `sudo journalctl -u bedrock-poc -f`
- **Restart app:** `sudo systemctl restart bedrock-poc`
- **Check Nginx:** `sudo systemctl status nginx`

## Tear Down (if needed)

```bash
# Stop instances
aws ec2 stop-instances --instance-ids i-xxxxxxxx

# Terminate (delete permanently)
aws ec2 terminate-instances --instance-ids i-xxxxxxxx
```

This will stop all charges (except EBS storage, which requires explicit deletion).
