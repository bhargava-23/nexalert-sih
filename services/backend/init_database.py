#!/usr/bin/env python3
"""Initialize NexAlert database schema

Creates all tables from SQLAlchemy models using Base.metadata.create_all().
This is the canonical schema initialization method for the NexAlert backend.

Usage:
    python init_database.py

Database connection from environment or defaults:
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    POSTGRES_DB=nexalert_dev
    POSTGRES_USER=nexalert
    POSTGRES_PASSWORD=nexalert_dev_password
"""
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine

# Import all models so they register with Base.metadata
from db.models import Base, Node, TelemetryRecord, SensorAssessment, HazardAssessment
from db.models_b2 import (
    Incident,
    IncidentObservation,
    IncidentHazardAssessment,
    RegionalHazardAssessment,
    NodeStatus
)
from db.models_c import (
    FireSpreadModel,
    FireSpreadModelRun,
    FireSpreadModelResult
)


async def init_database():
    """Initialize database schema"""

    # Build database URL from environment or defaults
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "nexalert_dev")
    user = os.getenv("POSTGRES_USER", "nexalert")
    password = os.getenv("POSTGRES_PASSWORD", "nexalert_dev_password")

    database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

    print(f"Initializing database schema...")
    print(f"  Host: {host}:{port}")
    print(f"  Database: {database}")
    print(f"  User: {user}")
    print()

    # Create async engine
    engine = create_async_engine(
        database_url,
        echo=True,  # Show SQL statements
        pool_pre_ping=True
    )

    try:
        # Create all tables
        async with engine.begin() as conn:
            print("Creating tables from Base.metadata...")
            await conn.run_sync(Base.metadata.create_all)

        print()
        print("✓ Database schema initialized successfully")
        print()
        print("Tables created:")
        print("  - nodes (Node registry)")
        print("  - telemetry_records (TelemetryRecord)")
        print("  - sensor_assessments (SensorAssessment - Track 5)")
        print("  - hazard_assessments (HazardAssessment - Track 5)")
        print("  - incidents (Incident)")
        print("  - incident_observations (IncidentObservation)")
        print("  - incident_hazard_assessments (IncidentHazardAssessment)")
        print("  - regional_hazard_assessments (RegionalHazardAssessment)")
        print("  - node_status (NodeStatus)")
        print("  - fire_spread_models (FireSpreadModel - Track C)")
        print("  - fire_spread_model_runs (FireSpreadModelRun - Track C)")
        print("  - fire_spread_model_results (FireSpreadModelResult - Track C)")
        print()
        print("PostGIS extension preserved (spatial_ref_sys table)")
        print()

        return True

    except Exception as e:
        print(f"✗ Database initialization failed: {str(e)}", file=sys.stderr)
        return False

    finally:
        await engine.dispose()


if __name__ == "__main__":
    success = asyncio.run(init_database())
    sys.exit(0 if success else 1)
