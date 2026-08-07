"""Database configuration and session management for persistent storage."""

from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

Base = declarative_base()


def get_database_url() -> str:
    """Build PostgreSQL connection URL from environment variables.

    Expected format: postgresql://user:password@host:port/database

    Environment variables:
        DB_USER: PostgreSQL username (default: postgres)
        DB_PASSWORD: PostgreSQL password (default: postgres)
        DB_HOST: PostgreSQL host (default: localhost)
        DB_PORT: PostgreSQL port (default: 5432)
        DB_NAME: Database name (default: bedrock_poc)

    Returns:
        Full connection URL string.
    """
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "bedrock_poc")

    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def create_db_engine(url: str | None = None) -> Engine:
    """Create SQLAlchemy engine for database connections.

    Args:
        url: Database connection URL. If None, built from environment variables.

    Returns:
        Configured SQLAlchemy engine.
    """
    url = url or get_database_url()
    return create_engine(
        url,
        echo=False,  # Set to True for SQL query logging
        pool_pre_ping=True,  # Verify connections before using them
        pool_size=10,
        max_overflow=20,
    )


def init_db(engine: Engine | None = None) -> None:
    """Initialize database schema by creating all tables.

    Args:
        engine: SQLAlchemy engine. If None, creates one from environment.
    """
    if engine is None:
        engine = create_db_engine()
    Base.metadata.create_all(engine)


def get_session_factory(engine: Engine | None = None) -> sessionmaker:
    """Create a session factory for database operations.

    Args:
        engine: SQLAlchemy engine. If None, creates one from environment.

    Returns:
        Configured session factory.
    """
    if engine is None:
        engine = create_db_engine()
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_session(engine: Engine | None = None) -> Generator[Session, None, None]:
    """Context manager for database sessions.

    Usage:
        for session in get_session():
            user = session.query(User).first()

    Args:
        engine: SQLAlchemy engine. If None, creates one from environment.

    Yields:
        Database session.
    """
    if engine is None:
        engine = create_db_engine()
    factory = get_session_factory(engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()
