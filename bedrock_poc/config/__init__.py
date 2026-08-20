"""Configuration management for Bedrock POC application.

This module provides environment-specific configuration using Pydantic BaseSettings.
Supports development, staging, and production environments with proper validation.
"""

from bedrock_poc.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
