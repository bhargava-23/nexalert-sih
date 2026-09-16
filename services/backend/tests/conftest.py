"""Pytest fixtures for backend tests"""
import pytest
import pytest_asyncio
import asyncio
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from db.models import Base
from db.models_b2 import Incident, IncidentHazardAssessment, RegionalHazardAssessment


# Test database URL
# For Phase 2C-2 multi-hazard tests, use PostgreSQL with PostGIS
# Set TEST_DATABASE_URL environment variable to override default
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/nexalert_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session

    Uses PostgreSQL test database for Geography/PostGIS support.
    Set TEST_DATABASE_URL environment variable to configure.

    Default: postgresql+asyncpg://postgres:postgres@localhost:5432/nexalert_test
    """
    # Create async engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Create session
    async with async_session_factory() as session:
        yield session

    # Cleanup
    await engine.dispose()
