"""Database connection and session management for the Legal Document Intelligence Platform."""

import os
from typing import Generator

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/legaldb"  # 可由環境變數覆蓋

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class DatabaseManager:
    """Manager class for database operations."""

    def __init__(self) -> None:
        """Initialize the database manager."""
        self.engine = engine
        self.SessionLocal = SessionLocal

    def _create_engine(self) -> Engine:
        """Create and configure the database engine.
        
        Returns:
            Engine: Configured SQLAlchemy engine instance.
        
        Raises:
            SQLAlchemyError: If database connection fails.
        """
        try:
            # Get database configuration from environment variables
            db_user = os.getenv("POSTGRES_USER", "legal_user")
            db_password = os.getenv("POSTGRES_PASSWORD", "legal_pass")
            db_host = os.getenv("POSTGRES_HOST", "localhost")
            db_port = os.getenv("POSTGRES_PORT", "5432")
            db_name = os.getenv("POSTGRES_DB", "legal_doc_db")

            # Create database URL
            database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

            # Create engine with appropriate configuration
            engine = create_engine(
                database_url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                echo=bool(os.getenv("SQL_ECHO", "false").lower() == "true")
            )

            return engine

        except SQLAlchemyError as e:
            logger.error(f"Failed to create database engine: {str(e)}")
            raise

    def create_database(self) -> None:
        """Create all database tables.
        
        Raises:
            SQLAlchemyError: If table creation fails.
        """
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise

    def get_db(self) -> Generator[Session, None, None]:
        """Get database session.
        
        Yields:
            Session: Database session.
        """
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def dispose(self) -> None:
        """Dispose of the database engine."""
        self.engine.dispose()
        logger.info("Database engine disposed")


# Create a global instance of DatabaseManager
db_manager = DatabaseManager()
