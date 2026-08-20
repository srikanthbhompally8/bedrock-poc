"""Database connection and session management with connection pooling.

Provides SQLAlchemy engine and session factory with optimal configuration
for development, staging, and production environments.
"""

import logging
from typing import Optional

from sqlalchemy import create_engine, event, pool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from bedrock_poc.config.settings import get_settings


log = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections, pooling, and session creation."""

    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None

    @classmethod
    def initialize(cls) -> Engine:
        """Initialize database engine with connection pooling.

        Returns:
            SQLAlchemy Engine instance
        """
        if cls._engine is not None:
            return cls._engine

        settings = get_settings()
        db_config = settings.database

        # Configure connection pool based on environment
        pool_config = {
            "poolclass": pool.NullPool if settings.environment == "development" else pool.QueuePool,
            "pool_size": db_config.pool_min_size,
            "max_overflow": db_config.pool_max_size - db_config.pool_min_size,
            "pool_recycle": db_config.pool_recycle,
            "pool_pre_ping": True,  # Verify connections before using
            "echo": db_config.echo_queries,
        }

        # Create engine
        cls._engine = create_engine(db_config.sync_url, **pool_config)

        # Set up connection event handlers for debugging
        if settings.debug:
            @event.listens_for(Engine, "connect")
            def receive_connect(dbapi_conn, connection_record):
                log.debug(f"Database connection established: {connection_record}")

            @event.listens_for(Engine, "checkin")
            def receive_checkin(dbapi_conn, connection_record):
                log.debug("Database connection returned to pool")

        log.info(
            f"Database engine initialized",
            extra={
                "host": db_config.host,
                "port": db_config.port,
                "database": db_config.name,
                "pool_size": db_config.pool_min_size,
                "max_overflow": db_config.pool_max_size - db_config.pool_min_size,
            },
        )

        return cls._engine

    @classmethod
    def get_engine(cls) -> Engine:
        """Get or initialize database engine.

        Returns:
            SQLAlchemy Engine instance
        """
        if cls._engine is None:
            return cls.initialize()
        return cls._engine

    @classmethod
    def get_session_factory(cls) -> sessionmaker:
        """Get or create session factory.

        Returns:
            SQLAlchemy sessionmaker instance
        """
        if cls._session_factory is None:
            engine = cls.get_engine()
            cls._session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        return cls._session_factory

    @classmethod
    def get_session(cls) -> Session:
        """Create a new database session.

        Returns:
            SQLAlchemy Session instance
        """
        factory = cls.get_session_factory()
        return factory()

    @classmethod
    def close(cls):
        """Close all database connections and cleanup."""
        if cls._engine is not None:
            cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
            log.info("Database connections closed")

    @classmethod
    def health_check(cls) -> bool:
        """Check database connectivity.

        Returns:
            True if database is accessible, False otherwise
        """
        try:
            engine = cls.get_engine()
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            log.error(f"Database health check failed: {e}")
            return False


def get_db_session() -> Session:
    """Dependency injection function for FastAPI.

    Yields:
        SQLAlchemy Session instance
    """
    session = DatabaseManager.get_session()
    try:
        yield session
    finally:
        session.close()
