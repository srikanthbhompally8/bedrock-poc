# Nginx & Systemd Configuration Details

**Status:** ✅ Deployed on EC2  
**Instance:** 52.15.231.184 (us-east-2)  
**OS:** Amazon Linux 2

---

## **SYSTEMD SERVICE CONFIGURATION**

### **Service File Location**

```
/etc/systemd/system/bedrock-poc.service
```

### **Complete Service Configuration**

```ini
[Unit]
Description=Bedrock POC Streamlit App
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/bedrock-poc
Environment="PATH=/home/ec2-user/bedrock-poc/.venv/bin"
ExecStart=/home/ec2-user/bedrock-poc/.venv/bin/python -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### **Configuration Breakdown**

| Setting | Value | Purpose |
|---------|-------|---------|
| `Description` | Bedrock POC Streamlit App | Human-readable service name |
| `After=network.target` | network.target | Start after network is ready |
| `Type=simple` | simple | Foreground process (not daemonized) |
| `User=ec2-user` | ec2-user | Run as this user (not root) |
| `WorkingDirectory` | /home/ec2-user/bedrock-poc | App directory |
| `Environment` | PATH=... | Virtual env bin path |
| `ExecStart` | python -m streamlit run app.py | Command to start app |
| `--server.port 8501` | 8501 | Streamlit port (internal) |
| `--server.address 0.0.0.0` | 0.0.0.0 | Listen on all interfaces |
| `Restart=always` | always | Restart if it crashes |
| `RestartSec=10` | 10 seconds | Wait 10s before restart |
| `WantedBy=multi-user.target` | multi-user.target | Enable on boot |

---

## **SYSTEMD SERVICE MANAGEMENT**

### **Common Commands**

```bash
# Start the service
sudo systemctl start bedrock-poc

# Stop the service
sudo systemctl stop bedrock-poc

# Restart the service
sudo systemctl restart bedrock-poc

# Check status
sudo systemctl status bedrock-poc

# View logs (last 50 lines)
sudo journalctl -u bedrock-poc -n 50

# Follow logs in real-time
sudo journalctl -u bedrock-poc -f

# Enable auto-start on reboot
sudo systemctl enable bedrock-poc

# Disable auto-start on reboot
sudo systemctl disable bedrock-poc
```

### **Check Service Status**

```bash
sudo systemctl status bedrock-poc
```

**Expected output if running:**
```
● bedrock-poc.service - Bedrock POC Streamlit App
     Loaded: loaded (/etc/systemd/system/bedrock-poc.service; enabled; preset: disabled)
     Active: active (running) since Fri 2026-07-24 22:00:00 UTC
    Process: 12345 (ExecStart=/home/ec2-user/bedrock-poc/.venv/bin/python -m streamlit run app.py...)
   Main PID: 12346 (python)
      Tasks: 15 (limit: 4915)
     Memory: 450.2M
     CGroup: /system.slice/bedrock-poc.service
             └─12346 /home/ec2-user/bedrock-poc/.venv/bin/python -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

---

## **NGINX CONFIGURATION**

### **Nginx Config File Location**

```
/etc/nginx/sites-available/bedrock-poc
/etc/nginx/sites-enabled/bedrock-poc (symbolic link)
```

### **Complete Nginx Configuration**

```nginx
upstream streamlit {
    server 127.0.0.1:8501;
}

server {
    listen 80;
    server_name 52.15.231.184 _;

    client_max_body_size 100M;

    location / {
        proxy_pass http://streamlit;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Streamlit specific settings
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
        proxy_buffering off;
    }

    location /_stcore/stream {
        proxy_pass http://streamlit;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
        proxy_buffering off;
    }
}
```

### **Configuration Breakdown**

| Setting | Value | Purpose |
|---------|-------|---------|
| `upstream streamlit` | server 127.0.0.1:8501 | Define backend server |
| `listen 80` | 80 | Listen on port 80 (HTTP) |
| `server_name` | 52.15.231.184 _ | Accept all domains/IPs |
| `client_max_body_size` | 100M | Max upload size |
| `proxy_pass` | http://streamlit | Forward to Streamlit |
| `proxy_set_header Host` | $host | Pass original host |
| `X-Real-IP` | $remote_addr | Pass client IP |
| `X-Forwarded-For` | $proxy_add_x_forwarded_for | Pass request chain |
| `X-Forwarded-Proto` | $scheme | Pass original protocol |
| `proxy_http_version` | 1.1 | Use HTTP/1.1 for upgrade |
| `Upgrade` | $http_upgrade | WebSocket upgrade header |
| `Connection` | "upgrade" | WebSocket connection |
| `proxy_read_timeout` | 86400 | 24 hour timeout (Streamlit) |
| `proxy_buffering` | off | Stream response immediately |
| `/_stcore/stream` | location block | Streamlit websocket endpoint |

---

## **HOW NGINX WORKS**

### **Request Flow**

```
User Browser
    ↓
http://52.15.231.184/ (Port 80)
    ↓
Nginx (Reverse Proxy)
    ↓ (forwards to)
Streamlit (127.0.0.1:8501, local only)
    ↓
Response back through Nginx
    ↓
User Browser
```

### **Why Nginx?**

1. **Security** - Streamlit not directly exposed to internet
2. **Performance** - Nginx caches static files
3. **Stability** - Handles connection buffering
4. **Websockets** - Enables real-time Streamlit features
5. **Monitoring** - Can log all traffic
6. **SSL/TLS** - Can add HTTPS (future)

---

## **NGINX MANAGEMENT**

### **Common Commands**

```bash
# Check Nginx syntax
sudo nginx -t

# Start Nginx
sudo systemctl start nginx

# Stop Nginx
sudo systemctl stop nginx

# Restart Nginx
sudo systemctl restart nginx

# Reload config (no downtime)
sudo systemctl reload nginx

# Check status
sudo systemctl status nginx

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### **Check Nginx Status**

```bash
sudo systemctl status nginx
```

**Expected output if running:**
```
● nginx.service - The NGINX HTTP and reverse proxy server
     Loaded: loaded (/usr/lib/systemd/system/nginx.service; enabled; preset: disabled)
     Active: active (running) since Fri 2026-07-24 22:00:00 UTC
    Process: 5678 (ExecStart=/usr/sbin/nginx -g daemon off;)
   Main PID: 5679 (nginx)
      Tasks: 2 (limit: 4915)
     Memory: 12.5M
```

---

## **ARCHITECTURE DIAGRAM**

```
┌─────────────────────────────────────────┐
│         Internet Users                  │
│    http://52.15.231.184/ (Port 80)      │
└────────────────┬────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│     Nginx Reverse Proxy (Port 80)       │
│  /etc/nginx/sites-available/bedrock-poc│
│  - Handles all incoming HTTP requests   │
│  - Routes to Streamlit backend          │
│  - Manages websockets                   │
│  - Handles file uploads (100MB max)     │
└────────────────┬────────────────────────┘
                 │
                 ↓ (localhost:8501)
┌─────────────────────────────────────────┐
│   Streamlit App (Port 8501, local only) │
│  - Manages by systemd service           │
│  - Auto-restarts on crash               │
│  - Logs to journalctl                   │
│  - Connects to AWS Bedrock              │
└─────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│      AWS Bedrock (us-east-2)            │
│  - Claude 3.5 Sonnet (text generation)  │
│  - Titan Embeddings (RAG)               │
└─────────────────────────────────────────┘
```

---

## **DEPLOYMENT CHECKLIST**

### **Initial Setup**

- [x] EC2 instance created (us-east-2)
- [x] Security group configured (allows port 80, 443, SSH)
- [x] Python 3.9 installed
- [x] Virtual environment created
- [x] Dependencies installed
- [x] AWS credentials configured
- [x] Bedrock models enabled

### **Systemd Setup**

- [x] Service file created: `/etc/systemd/system/bedrock-poc.service`
- [x] Permissions configured (runs as ec2-user)
- [x] Auto-restart enabled
- [x] Service enabled for boot
- [x] Service started and verified

### **Nginx Setup**

- [x] Nginx installed
- [x] Config file created: `/etc/nginx/sites-available/bedrock-poc`
- [x] Symlink created in sites-enabled
- [x] Config syntax validated
- [x] Nginx started and enabled for boot
- [x] Reverse proxy tested

### **Verification**

- [x] App accessible at http://52.15.231.184/
- [x] All features working (Chat, Summarize, Q&A, Parse Resume, RAG)
- [x] Logs accessible via journalctl
- [x] Service auto-restarts on crash
- [x] Nginx logs show successful requests

---

## **MONITORING & MAINTENANCE**

### **Daily Checks**

```bash
# Check if services are running
sudo systemctl status bedrock-poc
sudo systemctl status nginx

# Check recent errors
sudo journalctl -u bedrock-poc -n 20 -p err
```

### **Weekly Maintenance**

```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check if service restarted unexpectedly
sudo journalctl -u bedrock-poc --since "7 days ago" | grep Restart

# Rotate logs if needed
sudo logrotate -f /etc/logrotate.d/nginx
```

### **Monthly Review**

- [ ] Check CloudWatch metrics for API usage
- [ ] Review error logs for patterns
- [ ] Verify auto-restart is working
- [ ] Test failover (kill service, verify restart)
- [ ] Update dependencies if needed
- [ ] Review and optimize Nginx config

---

## **TROUBLESHOOTING**

### **502 Bad Gateway Error**

**Cause:** Streamlit app not running on port 8501

```bash
# Check if Streamlit is running
sudo systemctl status bedrock-poc

# View detailed error
sudo journalctl -u bedrock-poc -n 30 --no-pager

# Restart service
sudo systemctl restart bedrock-poc
```

### **Nginx Won't Start**

**Cause:** Config syntax error

```bash
# Check syntax
sudo nginx -t

# If error, fix config
sudo nano /etc/nginx/sites-available/bedrock-poc

# Reload (if only config change)
sudo systemctl reload nginx
```

### **App Crashes Repeatedly**

**Cause:** Usually missing dependencies or AWS credentials

```bash
# View crash logs
sudo journalctl -u bedrock-poc -f

# SSH and test manually
ssh -i your-key.pem ec2-user@52.15.231.184
cd /home/ec2-user/bedrock-poc
source .venv/bin/activate
streamlit run app.py
```

### **High Memory Usage**

**Cause:** Streamlit keeps adding to memory

```bash
# View memory
ps aux | grep streamlit

# Restart service to clear
sudo systemctl restart bedrock-poc
```

---

## **PERFORMANCE OPTIMIZATION**

### **Nginx Optimizations**

Already configured:
- ✅ Websocket support (for Streamlit)
- ✅ No buffering (real-time streaming)
- ✅ Long timeout (86400s = 24 hours)
- ✅ Large upload support (100MB)

### **Streamlit Optimizations**

Can be added to service:
```bash
# Add to ExecStart for better performance:
--server.headless=true
--server.enableXsrfProtection=false
--client.toolbarMode=minimal
```

### **System Optimizations**

```bash
# Increase max open files
ulimit -n 65536

# Set in /etc/security/limits.conf:
ec2-user soft nofile 65536
ec2-user hard nofile 65536
```

---

## **BACKUP & RECOVERY**

### **Backup Service Config**

```bash
# Backup service file
sudo cp /etc/systemd/system/bedrock-poc.service ~/bedrock-poc.service.bak

# Backup Nginx config
sudo cp /etc/nginx/sites-available/bedrock-poc ~/nginx-bedrock-poc.bak
```

### **Restore Service Config**

```bash
# If service file corrupted
sudo cp ~/bedrock-poc.service.bak /etc/systemd/system/bedrock-poc.service
sudo systemctl daemon-reload
```

---

## **SUMMARY**

| Component | Status | Location | Port |
|-----------|--------|----------|------|
| **Systemd Service** | ✅ Running | /etc/systemd/system/bedrock-poc.service | N/A |
| **Streamlit App** | ✅ Running | /home/ec2-user/bedrock-poc | 8501 (internal) |
| **Nginx Reverse Proxy** | ✅ Running | /etc/nginx/sites-available/bedrock-poc | 80 (public) |
| **Public Access** | ✅ Available | http://52.15.231.184/ | 80 |

---

**For additional support, contact AWS Support or refer to:**
- Nginx Docs: https://nginx.org/en/docs/
- Streamlit Docs: https://docs.streamlit.io/
- Systemd Docs: https://www.freedesktop.org/software/systemd/man/

