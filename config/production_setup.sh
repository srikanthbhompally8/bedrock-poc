#!/bin/bash
# Production Environment Setup Script
# ===================================
# Run this script to configure a production environment for Bedrock POC.
# This script:
# - Validates environment variables
# - Creates necessary directories
# - Sets proper file permissions
# - Initializes database
# - Creates systemd service file
# - Performs security checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_USER="bedrock"
APP_GROUP="bedrock"
APP_DIR="/opt/bedrock-poc"
LOG_DIR="/var/log/bedrock-poc"
DATA_DIR="/var/lib/bedrock-poc"

echo -e "${GREEN}=== Bedrock POC Production Setup ===${NC}"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# 1. Validate environment variables
echo ""
echo "Checking environment variables..."
required_vars=(
    "ENVIRONMENT"
    "BEDROCK_MODEL_ID"
    "AWS_REGION"
    "DB_HOST"
    "DB_USER"
    "DB_PASSWORD"
    "DB_NAME"
    "AUTH_JWT_SECRET_KEY"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        missing_vars+=("$var")
    fi
done

if [[ ${#missing_vars[@]} -gt 0 ]]; then
    print_error "Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

if [[ "$ENVIRONMENT" != "production" ]]; then
    print_warning "ENVIRONMENT is set to '$ENVIRONMENT' (not 'production')"
fi

print_status "Environment variables validated"

# 2. Create application user and group
echo ""
echo "Setting up application user and group..."

if ! id "$APP_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d $APP_DIR "$APP_USER" || {
        print_error "Failed to create user $APP_USER"
        exit 1
    }
    print_status "Created user $APP_USER"
else
    print_status "User $APP_USER already exists"
fi

# 3. Create directories
echo ""
echo "Creating directories..."

for dir in "$APP_DIR" "$LOG_DIR" "$DATA_DIR"; do
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        print_status "Created $dir"
    else
        print_status "$dir already exists"
    fi
done

# 4. Set permissions
echo ""
echo "Setting directory permissions..."

chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"
chown -R "$APP_USER:$APP_GROUP" "$LOG_DIR"
chown -R "$APP_USER:$APP_GROUP" "$DATA_DIR"

chmod 750 "$APP_DIR"
chmod 750 "$LOG_DIR"
chmod 750 "$DATA_DIR"

print_status "Directory permissions set"

# 5. Create .env file
echo ""
echo "Creating .env file..."

if [[ ! -f "$APP_DIR/.env" ]]; then
    cat > "$APP_DIR/.env" << EOF
# Production Environment Configuration
ENVIRONMENT=$ENVIRONMENT
DEBUG=false
HOST=0.0.0.0
PORT=8000
WORKERS=$(nproc --all)

# Database
DB_HOST=$DB_HOST
DB_PORT=${DB_PORT:-5432}
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME
DB_POOL_MIN_SIZE=10
DB_POOL_MAX_SIZE=50
DB_SSL_MODE=require

# AWS Bedrock
BEDROCK_MODEL_ID=$BEDROCK_MODEL_ID
BEDROCK_REGION=$AWS_REGION

# Authentication
AUTH_JWT_SECRET_KEY=$AUTH_JWT_SECRET_KEY
AUTH_RATE_LIMIT_REQUESTS=100

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_LOG_FILE=$LOG_DIR/app.log

# Monitoring
MONITOR_ENABLE_METRICS=true
ENABLE_AUDIT_LOGGING=true
ENABLE_RATE_LIMITING=true
EOF

    chown "$APP_USER:$APP_GROUP" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    print_status "Created $APP_DIR/.env"
else
    print_warning "$APP_DIR/.env already exists (skipping)"
fi

# 6. Validate database connection
echo ""
echo "Validating database connection..."

if command -v psql &> /dev/null; then
    if PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" &>/dev/null; then
        print_status "Database connection successful"
    else
        print_error "Failed to connect to database"
        echo "  Host: $DB_HOST"
        echo "  User: $DB_USER"
        echo "  Database: $DB_NAME"
        exit 1
    fi
else
    print_warning "psql not installed, skipping database connection test"
fi

# 7. Initialize database (if needed)
echo ""
echo "Initializing database tables..."
cd "$APP_DIR"
python3 -c "
from bedrock_poc.database import init_db
init_db()
print('Database tables initialized')
" || print_warning "Database initialization may have failed (tables may already exist)"

# 8. Create systemd service file
echo ""
echo "Creating systemd service file..."

cat > /etc/systemd/system/bedrock-poc.service << 'EOF'
[Unit]
Description=Bedrock POC API Server
After=network.target postgresql.service

[Service]
Type=notify
User=bedrock
Group=bedrock
WorkingDirectory=/opt/bedrock-poc
Environment="PATH=/opt/bedrock-poc/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
EnvironmentFile=/opt/bedrock-poc/.env
ExecStart=/opt/bedrock-poc/.venv/bin/python -m uvicorn bedrock_poc.api.main:app \
    --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=bedrock-poc

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/log/bedrock-poc /var/lib/bedrock-poc

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
print_status "Systemd service file created"

# 9. Security checks
echo ""
echo "Running security checks..."

# Check JWT secret key
if [[ "$AUTH_JWT_SECRET_KEY" == "change-me"* ]] || [[ ${#AUTH_JWT_SECRET_KEY} -lt 32 ]]; then
    print_error "JWT_SECRET_KEY is too weak. Generate a secure key:"
    echo "  python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
    exit 1
fi
print_status "JWT secret key appears secure"

# Check firewall rules
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        if ! ufw status | grep -q "80/tcp\|443/tcp"; then
            print_warning "Firewall is active but HTTP/HTTPS ports may not be open"
        fi
    fi
fi

print_status "Security checks passed"

# 10. Summary
echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Verify .env file at $APP_DIR/.env contains correct credentials"
echo "2. Start the service: systemctl start bedrock-poc"
echo "3. Enable auto-start: systemctl enable bedrock-poc"
echo "4. Monitor logs: journalctl -u bedrock-poc -f"
echo ""
echo "For detailed setup instructions, see: docs/PRODUCTION_DEPLOYMENT.md"
