#!/bin/bash
# Entrypoint script for Bedrock POC container
# Handles initialization, migration, and startup

set -e

echo "=========================================="
echo "Bedrock POC - Container Initialization"
echo "=========================================="
echo ""

# Check environment
echo "Environment: $ENVIRONMENT"
echo "Debug Mode: $DEBUG"
echo ""

# Wait for database if needed
if [ ! -z "$DB_HOST" ]; then
    echo "Waiting for database at $DB_HOST:$DB_PORT..."

    attempt=1
    max_attempts=30

    while [ $attempt -le $max_attempts ]; do
        if nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
            echo "✓ Database is ready"
            break
        fi

        echo "  Attempt $attempt/$max_attempts - waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done

    if [ $attempt -gt $max_attempts ]; then
        echo "✗ Database connection failed after $max_attempts attempts"
        exit 1
    fi
fi

echo ""

# Initialize database tables if needed
if [ "$INITIALIZE_DB" = "true" ] || [ ! -z "$DB_INIT" ]; then
    echo "Initializing database..."
    python -c "from bedrock_poc.database import init_db; init_db()" || {
        echo "Note: Database initialization failed (tables may already exist)"
    }
    echo ""
fi

# Validate configuration
echo "Validating configuration..."
python -c "
from bedrock_poc.config import get_settings
try:
    settings = get_settings()
    print('✓ Configuration validated successfully')
    print(f'  - App: {settings.app_name}')
    print(f'  - Environment: {settings.environment}')
    print(f'  - Debug: {settings.debug}')
    print(f'  - Database: {settings.database.name}@{settings.database.host}')
except Exception as e:
    print(f'✗ Configuration validation failed: {e}')
    exit(1)
" || exit 1

echo ""

# Health check
echo "Running health checks..."
python -c "
from bedrock_poc.config.database import DatabaseManager
if DatabaseManager.health_check():
    print('✓ Database connection successful')
else:
    print('✗ Database health check failed')
    exit(1)
" || exit 1

echo ""
echo "=========================================="
echo "✓ Initialization Complete"
echo "=========================================="
echo ""

# Start application
echo "Starting Bedrock POC API server..."
echo "Listening on http://0.0.0.0:${PORT:-8000}"
echo ""

# Execute the command passed as arguments (default: uvicorn)
exec "$@"
