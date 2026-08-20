"""Pydantic-based settings configuration for development, staging, and production.

Supports environment-specific configuration with validation and type safety.
All sensitive values must come from environment variables or Secrets Manager.
"""

import json
import logging
from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


log = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="postgres", description="Database password")
    name: str = Field(default="bedrock_poc", description="Database name")
    pool_min_size: int = Field(default=5, ge=1, le=100, description="Min connection pool size")
    pool_max_size: int = Field(default=20, ge=1, le=200, description="Max connection pool size")
    pool_recycle: int = Field(default=3600, ge=60, description="Connection recycle time (seconds)")
    echo_queries: bool = Field(default=False, description="Log SQL queries to console")
    ssl_mode: Literal["disable", "allow", "prefer", "require"] = Field(
        default="prefer", description="SSL mode for database connection"
    )

    @property
    def url(self) -> str:
        """PostgreSQL connection URL."""
        ssl_suffix = "" if self.ssl_mode == "disable" else f"?sslmode={self.ssl_mode}"
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.name}{ssl_suffix}"
        )

    @property
    def sync_url(self) -> str:
        """Synchronous database URL (for SQLAlchemy)."""
        ssl_suffix = "" if self.ssl_mode == "disable" else f"?sslmode={self.ssl_mode}"
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.name}{ssl_suffix}"
        )

    model_config = {
        "env_prefix": "DB_",
        "case_sensitive": False,
    }


class RedisSettings(BaseSettings):
    """Redis cache configuration."""

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    password: Optional[str] = Field(default=None, description="Redis password")
    db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    ttl_seconds: int = Field(default=3600, ge=60, description="Cache TTL in seconds")
    enabled: bool = Field(default=False, description="Enable Redis caching")

    @property
    def url(self) -> str:
        """Redis connection URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"

    model_config = {
        "env_prefix": "REDIS_",
        "case_sensitive": False,
    }


class BedrockSettings(BaseSettings):
    """AWS Bedrock configuration."""

    model_id: str = Field(
        default="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        description="Bedrock model ID",
    )
    region: str = Field(default="us-east-1", description="AWS region")
    request_timeout: int = Field(default=300, ge=30, le=900, description="Request timeout (seconds)")
    max_retries: int = Field(default=3, ge=0, le=10, description="Max API retries")

    model_config = {
        "env_prefix": "BEDROCK_",
        "case_sensitive": False,
    }


class AuthSettings(BaseSettings):
    """Authentication configuration."""

    jwt_secret_key: str = Field(description="JWT secret key (keep secure!)")
    jwt_algorithm: Literal["HS256", "HS512"] = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, ge=1, le=720, description="JWT expiration in hours")
    api_key_prefix: str = Field(default="sk_", description="API key prefix")
    rate_limit_requests: int = Field(default=100, ge=1, description="Rate limit: requests per window")
    rate_limit_window_seconds: int = Field(
        default=60, ge=1, description="Rate limit window in seconds"
    )
    enable_cors: bool = Field(default=True, description="Enable CORS")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8501",
        description="Comma-separated CORS origins",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = {
        "env_prefix": "AUTH_",
        "case_sensitive": False,
    }


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Log level"
    )
    format: Literal["json", "text"] = Field(default="text", description="Log format")
    enable_request_logging: bool = Field(default=True, description="Log HTTP requests")
    enable_database_logging: bool = Field(default=False, description="Log database queries")
    log_file: Optional[str] = Field(default=None, description="Log file path (optional)")
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")

    model_config = {
        "env_prefix": "LOG_",
        "case_sensitive": False,
    }


class MonitoringSettings(BaseSettings):
    """Monitoring and metrics configuration."""

    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, ge=1, le=65535, description="Metrics server port")
    enable_health_checks: bool = Field(default=True, description="Enable health check endpoints")
    health_check_interval: int = Field(default=30, ge=5, description="Health check interval (seconds)")
    enable_request_tracing: bool = Field(default=False, description="Enable distributed tracing")
    jaeger_enabled: bool = Field(default=False, description="Enable Jaeger tracing")
    jaeger_host: str = Field(default="localhost", description="Jaeger host")
    jaeger_port: int = Field(default=6831, ge=1, le=65535, description="Jaeger port")

    model_config = {
        "env_prefix": "MONITOR_",
        "case_sensitive": False,
    }


class Settings(BaseSettings):
    """Main application settings combining all configuration modules.

    Supports environment-specific configurations through the ENVIRONMENT variable.
    Validates all settings at startup and provides type-safe access throughout the app.
    """

    # Application
    app_name: str = Field(default="Bedrock POC", description="Application name")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Deployment environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    api_version: str = Field(default="v1", description="API version")
    api_prefix: str = Field(default="/api", description="API URL prefix")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=4, ge=1, le=16, description="Number of workers")
    reload: bool = Field(default=False, description="Auto-reload on code changes")

    # Sub-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    bedrock: BedrockSettings = Field(default_factory=BedrockSettings)
    auth: AuthSettings = Field(default_factory=lambda: AuthSettings(jwt_secret_key="change-me-in-production"))
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)

    # Features
    enable_audit_logging: bool = Field(default=True, description="Enable audit logging")
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")

    @field_validator("debug", mode="before")
    @classmethod
    def set_debug_from_environment(cls, v, info):
        """Auto-enable debug in development environment."""
        environment = info.data.get("environment", "development")
        if environment == "development" and v is False:
            return True
        return v

    @field_validator("reload", mode="before")
    @classmethod
    def set_reload_from_environment(cls, v, info):
        """Auto-enable reload in development environment."""
        environment = info.data.get("environment", "development")
        if environment == "development" and v is False:
            return True
        return v

    def __init__(self, **data):
        """Initialize settings with validation."""
        super().__init__(**data)
        self._validate_environment()

    def _validate_environment(self):
        """Validate environment-specific settings at startup."""
        if self.environment == "production":
            if not self.auth.jwt_secret_key or self.auth.jwt_secret_key.startswith("change-me"):
                raise ValueError("PRODUCTION: JWT_SECRET_KEY must be set to a secure value")
            if self.debug:
                log.warning("PRODUCTION: Debug mode is enabled - consider disabling")
            if self.logging.level == "DEBUG":
                log.warning("PRODUCTION: Debug logging enabled - consider reducing verbosity")
        elif self.environment == "staging":
            if not self.auth.jwt_secret_key:
                log.warning("STAGING: JWT_SECRET_KEY not set - using default (not recommended)")

    def get_log_config(self) -> dict:
        """Get logging configuration for structlog/Python logging."""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                },
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(timestamp)s %(level)s %(name)s %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "level": self.logging.level,
                    "class": "logging.StreamHandler",
                    "formatter": "json" if self.logging.format == "json" else "standard",
                },
                "file": {
                    "level": self.logging.level,
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": self.logging.log_file,
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 10,
                    "formatter": "json" if self.logging.format == "json" else "standard",
                } if self.logging.log_file else None,
            },
            "loggers": {
                "": {
                    "handlers": ["default"] + (["file"] if self.logging.log_file else []),
                    "level": self.logging.level,
                    "propagate": True,
                }
            },
        }

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @classmethod
    def model_json_schema(cls, **kwargs):
        """Customize JSON schema with examples."""
        schema = super().model_json_schema(**kwargs)
        props = schema.get("properties", {})
        if "environment" in props:
            props["environment"]["examples"] = ["development", "staging", "production"]
        if "debug" in props:
            props["debug"]["examples"] = [True, False]
        return schema


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    This function is cached to avoid reloading settings on every call.
    Use this function to access application settings throughout the app.

    Example:
        from bedrock_poc.config import get_settings
        settings = get_settings()
        db_url = settings.database.url
    """
    settings = Settings()
    log.info(
        f"Loaded configuration for {settings.environment} environment",
        extra={
            "app": settings.app_name,
            "version": settings.api_version,
            "database": settings.database.name,
            "debug": settings.debug,
        },
    )
    return settings
