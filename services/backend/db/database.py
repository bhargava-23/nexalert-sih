"""Database configuration and session management

SQLAlchemy async engine and session factory.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from .models import Base


class DatabaseConfig:
    """Database configuration"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        async with self.async_session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    async def init_db(self):
        """Initialize database (create tables if needed)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        """Close database connection"""
        await self.engine.dispose()


# Global database instance (initialized in main.py)
db_config: DatabaseConfig | None = None


def get_db_config() -> DatabaseConfig:
    """Get global database config"""
    if db_config is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return db_config


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes"""
    config = get_db_config()
    async for session in config.get_session():
        yield session
