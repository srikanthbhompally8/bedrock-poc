# Multi-stage Dockerfile for Bedrock POC
# Stage 1: Builder - Install dependencies
# Stage 2: Runtime - Minimal production image

FROM python:3.11-slim as builder

# Set working directory
WORKDIR /build

# Install system dependencies needed for compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================

FROM python:3.11-slim

# Set labels for container metadata
LABEL maintainer="Bedrock POC Team"
LABEL version="1.0"
LABEL description="AI-Powered Recruitment Platform using Amazon Bedrock"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production

# Set working directory
WORKDIR /app

# Install runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r bedrock && useradd -r -g bedrock bedrock

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY bedrock_poc/ /app/bedrock_poc/
COPY tests/ /app/tests/
COPY config/ /app/config/
COPY docs/ /app/docs/

# Copy configuration files
COPY .env.template /app/.env.template
COPY requirements.txt /app/requirements.txt

# Copy entrypoint script
COPY docker/entrypoint.sh /app/entrypoint.sh
COPY docker/health-check.sh /app/health-check.sh

# Make scripts executable
RUN chmod +x /app/entrypoint.sh /app/health-check.sh

# Change ownership to non-root user
RUN chown -R bedrock:bedrock /app

# Switch to non-root user
USER bedrock

# Expose ports
EXPOSE 8000 9090

# Health check - checks if API is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/health-check.sh

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command - start API server
CMD ["uvicorn", "bedrock_poc.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
