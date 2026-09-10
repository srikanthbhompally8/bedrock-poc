#!/bin/bash
# Health check script for Bedrock POC container
# Verifies that the API is responding and operational

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/api/health}"
TIMEOUT="${TIMEOUT:-10}"
MAX_RETRIES="${MAX_RETRIES:-3}"

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo -e "${YELLOW}Warning: curl not available, skipping health check${NC}"
    exit 0
fi

attempt=1

while [ $attempt -le $MAX_RETRIES ]; do
    # Check API health endpoint
    if curl -sf --max-time $TIMEOUT "$API_URL$HEALTH_ENDPOINT" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API Health Check Passed${NC}"
        exit 0
    fi

    if [ $attempt -lt $MAX_RETRIES ]; then
        echo -e "${YELLOW}⚠ Health check attempt $attempt/$MAX_RETRIES failed, retrying...${NC}"
        sleep 2
    fi

    attempt=$((attempt + 1))
done

echo -e "${RED}✗ Health check failed after $MAX_RETRIES attempts${NC}"
echo "  URL: $API_URL$HEALTH_ENDPOINT"
exit 1
