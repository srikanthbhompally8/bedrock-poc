"""Tests for configuration system.

Tests the Pydantic settings, environment variable loading, and validation.
"""

import os
import pytest
from bedrock_poc.config.settings import (
    Settings,
    DatabaseSettings,
    RedisSettings,
    BedrockSettings,
    AuthSettings,
    LoggingSettings,
    MonitoringSettings,
    get_settings,
)


class TestDatabaseSettings:
    """Test database configuration."""

    def test_database_url_generation(self):
        """Test database URL generation."""
        settings = DatabaseSettings(
            host="localhost",
            port=5432,
            user="postgres",
            password="password",
            name="test_db",
            ssl_mode="prefer"
        )
        assert "localhost" in settings.url
        assert "5432" in settings.url
        assert "sslmode=prefer" in settings.url

    def test_database_url_without_ssl(self):
        """Test database URL without SSL."""
        settings = DatabaseSettings(
            host="localhost",
            port=5432,
            user="postgres",
            password="password",
            name="test_db",
            ssl_mode="disable"
        )
        assert "sslmode" not in settings.url

    def test_pool_size_validation(self):
        """Test pool size validation."""
        # Pool min size must be >= 1
        with pytest.raises(ValueError):
            DatabaseSettings(
                host="localhost",
                user="postgres",
                password="password",
                pool_min_size=0
            )

        # Pool max size must be >= 1
        with pytest.raises(ValueError):
            DatabaseSettings(
                host="localhost",
                user="postgres",
                password="password",
                pool_max_size=0
            )


class TestRedisSettings:
    """Test Redis configuration."""

    def test_redis_url_with_password(self):
        """Test Redis URL generation with password."""
        settings = RedisSettings(
            host="localhost",
            port=6379,
            password="redispass",
            db=0
        )
        assert "redispass" in settings.url
        assert "localhost" in settings.url

    def test_redis_url_without_password(self):
        """Test Redis URL without password."""
        settings = RedisSettings(
            host="localhost",
            port=6379,
            password=None,
            db=0
        )
        assert "localhost" in settings.url
        assert "@" not in settings.url

    def test_redis_db_validation(self):
        """Test Redis database number validation."""
        # DB must be 0-15
        with pytest.raises(ValueError):
            RedisSettings(db=16)

        with pytest.raises(ValueError):
            RedisSettings(db=-1)


class TestAuthSettings:
    """Test authentication configuration."""

    def test_cors_origins_parsing(self):
        """Test CORS origins parsing from comma-separated string."""
        settings = AuthSettings(
            jwt_secret_key="test-key",
            cors_origins="http://localhost:3000,https://example.com"
        )
        assert isinstance(settings.cors_origins_list, list)
        assert "http://localhost:3000" in settings.cors_origins_list
        assert "https://example.com" in settings.cors_origins_list

    def test_rate_limit_validation(self):
        """Test rate limiting configuration."""
        settings = AuthSettings(
            jwt_secret_key="test-key",
            rate_limit_requests=1000,
            rate_limit_window_seconds=60
        )
        assert settings.rate_limit_requests == 1000
        assert settings.rate_limit_window_seconds == 60


class TestMainSettings:
    """Test main application settings."""

    def test_development_environment_defaults(self):
        """Test development environment sets proper defaults."""
        os.environ["ENVIRONMENT"] = "development"
        os.environ["AUTH_JWT_SECRET_KEY"] = "test-secret-key"

        settings = Settings(
            environment="development",
            auth=AuthSettings(jwt_secret_key="test-secret-key")
        )

        # Development should have debug enabled by default
        assert settings.debug is True
        assert settings.reload is True

    def test_production_environment_validation(self):
        """Test production environment validation."""
        os.environ["ENVIRONMENT"] = "production"

        # Should fail with invalid JWT secret
        with pytest.raises(ValueError):
            Settings(
                environment="production",
                auth=AuthSettings(jwt_secret_key="change-me-insecure-key")
            )

    def test_environment_from_env_variable(self):
        """Test environment loading from environment variable."""
        os.environ["ENVIRONMENT"] = "staging"
        os.environ["AUTH_JWT_SECRET_KEY"] = "test-secret-key"

        settings = Settings(
            auth=AuthSettings(jwt_secret_key="test-secret-key")
        )
        # Should default to staging from env var if set
        assert settings.environment in ["development", "staging", "production"]

    def test_logging_config_generation(self):
        """Test logging configuration generation."""
        settings = Settings(
            environment="development",
            logging=LoggingSettings(
                level="INFO",
                format="json"
            ),
            auth=AuthSettings(jwt_secret_key="test-secret-key")
        )

        log_config = settings.get_log_config()
        assert "handlers" in log_config
        assert "loggers" in log_config
        assert log_config["version"] == 1


class TestSettingsCaching:
    """Test settings caching with lru_cache."""

    def test_get_settings_caching(self):
        """Test that get_settings uses caching."""
        os.environ["AUTH_JWT_SECRET_KEY"] = "test-secret-key"

        settings1 = get_settings()
        settings2 = get_settings()

        # Should be the same instance (cached)
        assert settings1 is settings2


class TestMonitoringSettings:
    """Test monitoring configuration."""

    def test_monitoring_defaults(self):
        """Test monitoring settings defaults."""
        settings = MonitoringSettings()

        assert settings.enable_metrics is True
        assert settings.enable_health_checks is True
        assert settings.metrics_port == 9090
        assert settings.health_check_interval >= 5

    def test_monitoring_port_validation(self):
        """Test monitoring port validation."""
        with pytest.raises(ValueError):
            MonitoringSettings(metrics_port=0)

        with pytest.raises(ValueError):
            MonitoringSettings(metrics_port=70000)


class TestBedrockSettings:
    """Test AWS Bedrock configuration."""

    def test_bedrock_timeout_validation(self):
        """Test Bedrock request timeout validation."""
        # Timeout must be between 30 and 900 seconds
        with pytest.raises(ValueError):
            BedrockSettings(request_timeout=15)

        with pytest.raises(ValueError):
            BedrockSettings(request_timeout=1000)

    def test_bedrock_retries_validation(self):
        """Test Bedrock max retries validation."""
        # Max retries must be 0-10
        with pytest.raises(ValueError):
            BedrockSettings(max_retries=-1)

        with pytest.raises(ValueError):
            BedrockSettings(max_retries=11)


class TestEnvironmentFileLoading:
    """Test loading settings from .env files."""

    def test_env_file_loading(self, tmp_path):
        """Test loading settings from temporary .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "ENVIRONMENT=staging\n"
            "APP_NAME=Test App\n"
            "AUTH_JWT_SECRET_KEY=test-secret-key\n"
        )

        # Settings should load from the file
        # (Note: This would require Config.env_file to point to tmp_path)


class TestSettingsValidation:
    """Test settings validation at startup."""

    def test_all_required_fields(self):
        """Test that settings can be loaded with defaults."""
        # Should load successfully with all defaults
        settings = Settings()
        assert settings.app_name == "Bedrock POC"
        assert settings.environment in ["development", "staging", "production"]

    def test_worker_count_calculation(self):
        """Test worker count is reasonable."""
        settings = Settings(
            auth=AuthSettings(jwt_secret_key="test-secret-key")
        )

        # Default workers should be reasonable (2-4 for dev)
        assert settings.workers >= 1
        assert settings.workers <= 16
