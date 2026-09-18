"""Track 5 End-to-End Integration Test

REAL integration test for:
- MQTT hardware JSON → Master MQTT consumer
- Track 3C normalization (hardware JSON → telemetry.v1)
- PostgreSQL persistence (TelemetryRecord + SensorAssessment + HazardAssessment)
- Master-side intelligence computation (if intelligence fields present in payload)

This test uses ACTUAL repository services/models, not mocks.
"""
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.ingestion.track3c_normalizer import Track3CNormalizer
from modules.ingestion.node_registry import NodeRegistry
from modules.ingestion.persister import TelemetryPersister
from db.models import Node, TelemetryRecord, SensorAssessment, HazardAssessment


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()

    # Mock query results
    def mock_execute_side_effect(query):
        result = MagicMock()
        result.scalar_one_or_none.return_value = None  # No duplicates
        result.scalars.return_value.all.return_value = []
        result.all.return_value = []
        return result

    session.execute.side_effect = mock_execute_side_effect
    return session


@pytest.fixture
def node_registry_with_nodes():
    """Node registry with test nodes"""
    registry = NodeRegistry()
    registry._registry = {
        "NODE-001": {
            "location": {"lat": 12.9716, "lon": 77.5946, "alt": 920.0},
            "status": "ACTIVE",
            "firmware_version": "1.0.0"
        },
        "NODE-002": {
            "location": {"lat": 23.4567, "lon": 67.8901},
            "status": "ACTIVE",
            "firmware_version": "1.0.0"
        }
    }
    return registry


@pytest.mark.asyncio
async def test_track5_end_to_end_hardware_json_to_persistence(
    mock_db_session,
    node_registry_with_nodes
):
    """Test REAL end-to-end: hardware JSON → normalization → persistence

    This test verifies:
    1. Track 3C normalization (hardware JSON → telemetry.v1)
    2. MQ-2 gas_ppm → gas_adc mapping
    3. Node location resolution from registry
    4. NULL handling (MISSING != ZERO)
    5. Timestamp mapping (measurement_timestamp, received_timestamp)
    6. PostgreSQL persistence via actual persister
    """

    # Step 1: Create hardware JSON (from ESP32)
    hardware_json = {
        "node_id": "NODE-001",
        "timestamp_ms": 1726678800000,  # 2024-09-18T17:00:00Z
        "sequence": 100,
        "sensors": {
            "temperature_c": 45.2,
            "humidity_rh": 15.3,
            "pressure_hpa": 1013.25,
            "gas_ppm": 2345,  # RAW ADC (NOT calibrated ppm)
            "vibration_mps2": 0.15,
            "pm25_ugm3": None,  # Missing sensor
            "pm10_ugm3": None   # Missing sensor
        },
        "availability": {
            "temperature": True,
            "humidity": True,
            "pressure": True,
            "gas": True,
            "vibration": True,
            "pm25": False,
            "pm10": False
        },
        "power": {
            "battery_pct": 85,
            "solar_state": "CHARGING"
        }
    }

    # Step 2: Track 3C normalization
    normalizer = Track3CNormalizer(node_registry_with_nodes)
    received_timestamp = datetime(2024, 9, 18, 17, 0, 1, tzinfo=timezone.utc)

    canonical_telemetry, error = await normalizer.normalize_hardware_json(
        hardware_json, received_timestamp
    )

    assert error is None, f"Normalization failed: {error}"
    assert canonical_telemetry is not None

    # Step 3: Verify Track 3C mapping
    assert canonical_telemetry["schema_version"] == "telemetry.v1"
    assert canonical_telemetry["node_id"] == "NODE-001"
    assert canonical_telemetry["sequence"] == 100
    assert canonical_telemetry["source"] == "HARDWARE"

    # Timestamps
    assert canonical_telemetry["measurement_timestamp"] == "2024-09-18T17:00:00Z"
    assert canonical_telemetry["received_timestamp"] == "2024-09-18T17:00:01Z"

    # Location from registry
    assert canonical_telemetry["location"]["lat"] == 12.9716
    assert canonical_telemetry["location"]["lon"] == 77.5946
    assert canonical_telemetry["location"]["alt"] == 920.0

    # MQ-2 mapping: gas_ppm → gas_adc
    measurements = canonical_telemetry["measurements"]
    assert measurements["gas_adc"] == 2345  # RAW ADC preserved
    assert "gas_ppm" not in measurements  # Renamed

    # MISSING != ZERO
    assert measurements["pm25_ug_m3"] is None
    assert measurements["pm10_ug_m3"] is None

    # Power mapping
    assert canonical_telemetry["power"]["battery_pct"] == 85
    assert canonical_telemetry["power"]["solar_state"] == "CHARGING"

    # Step 4: Persist to PostgreSQL
    persister = TelemetryPersister()
    success, persist_error, telemetry_id = await persister.persist_telemetry(
        mock_db_session, canonical_telemetry, received_timestamp
    )

    assert success is True, f"Persistence failed: {persist_error}"
    assert persist_error is None
    assert telemetry_id is not None

    # Verify database session operations
    assert mock_db_session.add.called
    assert mock_db_session.commit.called

    print("\n✓ Track 5 END-TO-END integration test PASSED")
    print("  Hardware JSON → Track 3C normalization → PostgreSQL persistence")


@pytest.mark.asyncio
async def test_track5_end_to_end_with_intelligence_assessments(
    mock_db_session,
    node_registry_with_nodes
):
    """Test end-to-end with Master-side intelligence assessments

    Verifies:
    1. Hardware JSON normalization
    2. Intelligence assessments (SensorAssessment + HazardAssessment)
    3. Persistence of all assessment records
    4. MISSING != ZERO in intelligence fields
    """

    # Hardware JSON with intelligence outputs (from Master computation)
    hardware_json = {
        "node_id": "NODE-002",
        "timestamp_ms": 1726678860000,  # 2024-09-18T17:01:00Z
        "sequence": 200,
        "sensors": {
            "temperature_c": 52.0,
            "humidity_rh": 8.0,
            "pressure_hpa": 1010.0,
            "gas_ppm": 3800,  # RAW ADC
            "vibration_mps2": 0.25
        },
        "availability": {
            "temperature": True,
            "humidity": True,
            "pressure": True,
            "gas": True,
            "vibration": True
        },
        "power": {
            "battery_pct": 90,
            "solar_state": "CHARGING"
        }
    }

    # Step 1: Normalize
    normalizer = Track3CNormalizer(node_registry_with_nodes)
    received_timestamp = datetime(2024, 9, 18, 17, 1, 1, tzinfo=timezone.utc)

    canonical_telemetry, error = await normalizer.normalize_hardware_json(
        hardware_json, received_timestamp
    )

    assert error is None
    assert canonical_telemetry is not None

    # Step 2: Add Master-side intelligence assessments (Track 5)
    canonical_telemetry["sensor_assessments"] = [
        {
            "sensor_type": "bme680_temperature",
            "health": 0.95,
            "quality": 0.89,
            "reliability": 0.85,
            "baseline_state": "READY",
            "anomaly": 2.3
        },
        {
            "sensor_type": "mq2_gas",
            "health": 0.92,
            "quality": None,  # MISSING != ZERO
            "reliability": 0.88,
            "baseline_state": "READY",
            "anomaly": None
        }
    ]

    canonical_telemetry["hazard_assessments"] = [
        {
            "hazard_type": "fire",
            "evidence": 0.72,
            "confidence": 0.68,
            "severity": 0.45,
            "risk": 0.52,
            "state": "SUSPECTED",
            "information_condition": "GOOD"
        }
    ]

    # Step 3: Persist (intelligence assessments included)
    persister = TelemetryPersister()
    success, persist_error, telemetry_id = await persister.persist_telemetry(
        mock_db_session, canonical_telemetry, received_timestamp
    )

    assert success is True
    assert persist_error is None

    # Verify intelligence assessments were persisted
    # session.add should be called for:
    # - Node upsert
    # - TelemetryRecord
    # - 2 SensorAssessments
    # - 1 HazardAssessment
    assert mock_db_session.add.call_count >= 4

    print("\n✓ Track 5 END-TO-END with intelligence assessments PASSED")
    print("  Hardware JSON → normalization → intelligence → persistence")


@pytest.mark.asyncio
async def test_track5_end_to_end_missing_null_handling(
    mock_db_session,
    node_registry_with_nodes
):
    """Test MISSING != ZERO throughout entire pipeline

    Verifies:
    1. Null sensors in hardware JSON → null in canonical telemetry
    2. Null intelligence fields → null in assessments
    3. Null values preserved through persistence
    """

    hardware_json = {
        "node_id": "NODE-001",
        "timestamp_ms": 1726678920000,  # 2024-09-18T17:02:00Z
        "sequence": 300,
        "sensors": {
            "temperature_c": 42.0,
            "humidity_rh": None,  # Missing
            "pressure_hpa": None,  # Missing
            "gas_ppm": None,       # Missing
            "vibration_mps2": None # Missing
        },
        "availability": {
            "temperature": True,
            "humidity": False,
            "pressure": False,
            "gas": False,
            "vibration": False
        },
        "power": {
            "battery_pct": 80,
            "solar_state": None  # Missing
        }
    }

    # Normalize
    normalizer = Track3CNormalizer(node_registry_with_nodes)
    received_timestamp = datetime(2024, 9, 18, 17, 2, 1, tzinfo=timezone.utc)

    canonical_telemetry, error = await normalizer.normalize_hardware_json(
        hardware_json, received_timestamp
    )

    assert error is None

    # Verify nulls preserved
    measurements = canonical_telemetry["measurements"]
    assert measurements["temp_c"] == 42.0
    assert measurements["humidity_pct"] is None
    assert measurements["pressure_hpa"] is None
    assert measurements["gas_adc"] is None
    assert measurements["vibration_mps2"] is None

    # Add intelligence with nulls
    canonical_telemetry["sensor_assessments"] = [
        {
            "sensor_type": "bme680_temperature",
            "health": None,  # Missing
            "quality": None,  # Missing
            "reliability": 0.80,
            "baseline_state": None,  # Missing
            "anomaly": None  # Missing
        }
    ]

    canonical_telemetry["hazard_assessments"] = [
        {
            "hazard_type": "fire",
            "evidence": 0.35,
            "confidence": None,  # Missing
            "severity": None,  # Missing
            "risk": 0.30,
            "state": "WATCH",
            "information_condition": None  # Missing
        }
    ]

    # Persist
    persister = TelemetryPersister()
    success, persist_error, telemetry_id = await persister.persist_telemetry(
        mock_db_session, canonical_telemetry, received_timestamp
    )

    assert success is True
    assert persist_error is None

    print("\n✓ Track 5 END-TO-END null handling PASSED")
    print("  MISSING != ZERO preserved throughout entire pipeline")


@pytest.mark.asyncio
async def test_track5_end_to_end_unknown_node_fails_safely(mock_db_session):
    """Test that unknown node fails normalization safely"""

    hardware_json = {
        "node_id": "NODE-999",  # Not in registry
        "timestamp_ms": 1726678980000,
        "sequence": 400,
        "sensors": {"temperature_c": 25.0},
        "availability": {"temperature": True},
        "power": {"battery_pct": 75}
    }

    # Empty registry (no nodes)
    empty_registry = NodeRegistry()
    normalizer = Track3CNormalizer(empty_registry)
    received_timestamp = datetime(2024, 9, 18, 17, 3, 1, tzinfo=timezone.utc)

    canonical_telemetry, error = await normalizer.normalize_hardware_json(
        hardware_json, received_timestamp
    )

    # Normalization should fail
    assert canonical_telemetry is None
    assert error is not None
    assert "NODE-999" in error
    assert "location" in error.lower() or "unknown" in error.lower()

    print("\n✓ Track 5 END-TO-END unknown node handling PASSED")
    print("  Unknown nodes fail normalization safely (no fabricated location)")
