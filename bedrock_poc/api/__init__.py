"""API routes for Bedrock POC."""

from .jobs import router as jobs_router

__all__ = ["jobs_router"]
