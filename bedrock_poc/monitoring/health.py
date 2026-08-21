"""Health check endpoints for application dependencies."""

import logging
from datetime import datetime
from typing import Dict, Any, List

from bedrock_poc.config import get_settings
from bedrock_poc.config.database import DatabaseManager

logger = logging.getLogger(__name__)


async def get_health_status() -> Dict[str, Any]:
    """Get overall application health status.

    Returns:
        Health status dictionary
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": get_settings().api_version,
    }


async def get_readiness_status() -> Dict[str, Any]:
    """Get application readiness status (dependencies check).

    Returns:
        Readiness status with dependency checks
    """
    settings = get_settings()
    checks = {}

    # Database check
    db_healthy = DatabaseManager.health_check()
    checks["database"] = {
        "status": "healthy" if db_healthy else "unhealthy",
        "host": settings.database.host,
        "database": settings.database.name,
    }

    # Redis check (if enabled)
    if settings.redis.enabled:
        redis_healthy = check_redis()
        checks["redis"] = {
            "status": "healthy" if redis_healthy else "unhealthy",
            "host": settings.redis.host,
            "port": settings.redis.port,
        }

    # Configuration check
    checks["configuration"] = {
        "status": "healthy",
        "environment": settings.environment,
    }

    # Determine overall status
    all_healthy = all(check["status"] == "healthy" for check in checks.values())
    overall_status = "ready" if all_healthy else "not_ready"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }


async def get_detailed_health() -> Dict[str, Any]:
    """Get detailed health information for monitoring dashboards.

    Returns:
        Detailed health information
    """
    settings = get_settings()
    details = {}

    # Application info
    details["application"] = {
        "name": settings.app_name,
        "version": settings.api_version,
        "environment": settings.environment,
        "debug": settings.debug,
    }

    # Configuration info
    details["configuration"] = {
        "database": {
            "host": settings.database.host,
            "port": settings.database.port,
            "pool_size": settings.database.pool_min_size,
            "max_connections": settings.database.pool_max_size,
        },
        "redis": {
            "enabled": settings.redis.enabled,
            "host": settings.redis.host if settings.redis.enabled else None,
            "port": settings.redis.port if settings.redis.enabled else None,
        },
        "bedrock": {
            "model_id": settings.bedrock.model_id,
            "region": settings.bedrock.region,
        },
    }

    # Logging info
    details["logging"] = {
        "level": settings.logging.level,
        "format": settings.logging.format,
        "request_logging": settings.logging.enable_request_logging,
    }

    # Monitoring info
    details["monitoring"] = {
        "metrics_enabled": settings.monitoring.enable_metrics,
        "health_checks_enabled": settings.monitoring.enable_health_checks,
        "tracing_enabled": settings.monitoring.enable_request_tracing,
    }

    # Dependencies health
    dependencies = {}
    dependencies["database"] = {
        "healthy": DatabaseManager.health_check(),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if settings.redis.enabled:
        dependencies["redis"] = {
            "healthy": check_redis(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    details["dependencies"] = dependencies

    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "details": details,
    }


def check_redis() -> bool:
    """Check Redis connectivity.

    Returns:
        True if Redis is healthy, False otherwise
    """
    try:
        settings = get_settings()
        if not settings.redis.enabled:
            return True

        import redis

        conn = redis.from_url(settings.redis.url)
        conn.ping()
        return True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return False


def get_health_summary() -> Dict[str, Any]:
    """Get a quick health summary for alerting.

    Returns:
        Health summary for operational monitoring
    """
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }

    # Critical checks
    critical_checks = [
        ("database", DatabaseManager.health_check()),
    ]

    summary["critical_checks"] = dict(critical_checks)
    summary["status"] = "ok" if all(check[1] for check in critical_checks) else "degraded"

    return summary
