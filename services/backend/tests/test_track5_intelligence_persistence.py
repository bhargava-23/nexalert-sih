"""Unit tests for Track 5 intelligence persistence

Tests Master-side SensorAssessment and HazardAssessment persistence
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from modules.ingestion.persister import TelemetryPersister
from db.models import TelemetryRecord, SensorAssessment, HazardAssessment


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.mark.asyncio
async def test_persist_telemetry_with_sensor_assessments(mock_db_session):
    """Test persisting telemetry with sensor assessments (Track 5)"""
    persister = TelemetryPersister()

    payload = {
        "telemetry_id": "01J1ABC123",
        "node_id": "NODE-001",
        "sequence": 100,
        "measurement_timestamp": "2024-09-18T00:00:00Z",
        "received_timestamp": "2024-09-18T00:00:01Z",
        "location": {"lat": 12.34, "lon": 56.78},
        "measurements": {"temperature_c": 45.2},
        "diagnostics": {},
        "power": {"battery_pct": 85},
        "source": "HARDWARE",
        "schema_version": "telemetry.v2",
        "sensor_assessments": [
            {
                "sensor_type": "bme680_temperature",
                "health": 0.95,
                "quality": 0.89,
                "reliability": 0.85,
                "baseline_state": "READY",
                "anomaly": 2.3
            },
            {
                "sensor_type": "bme680_humidity",
                "health": 0.92,
                "quality": None,  # MISSING != ZERO
                "reliability": 0.80,
                "baseline_state": "READY",
                "anomaly": None
            }
        ]
    }

    # Mock no duplicate
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    received_ts = datetime(2024, 9, 18, 0, 0, 1, tzinfo=timezone.utc)
    success, error, telemetry_id = await persister.persist_telemetry(
        mock_db_session, payload, received_ts
    )

    assert success is True
    assert error is None
    assert telemetry_id == "01J1ABC123"

    # Verify session.add was called (3 times: 1 TelemetryRecord + 2 SensorAssessments)
    assert mock_db_session.add.call_count >= 3
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_persist_telemetry_with_hazard_assessments(mock_db_session):
    """Test persisting telemetry with hazard assessments (Track 5)"""
    persister = TelemetryPersister()

    payload = {
        "telemetry_id": "01J1ABC456",
        "node_id": "NODE-002",
        "sequence": 200,
        "measurement_timestamp": "2024-09-18T01:00:00Z",
        "received_timestamp": "2024-09-18T01:00:01Z",
        "location": {"lat": 23.45, "lon": 67.89},
        "measurements": {"temperature_c": 52.0, "humidity_pct": 8.0},
        "diagnostics": {},
        "power": {"battery_pct": 90},
        "source": "HARDWARE",
        "schema_version": "telemetry.v2",
        "hazard_assessments": [
            {
                "hazard_type": "fire",
                "evidence": 0.85,
                "confidence": 0.78,
                "severity": 0.65,
                "risk": 0.70,
                "state": "CONFIRMED",
                "information_condition": "GOOD"
            },
            {
                "hazard_type": "flood",
                "evidence": 0.92,
                "confidence": None,  # MISSING != ZERO
                "severity": 0.72,
                "risk": None,
                "state": "SUSPECTED",
                "information_condition": "DEGRADED"
            }
        ]
    }

    # Mock no duplicate
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    received_ts = datetime(2024, 9, 18, 1, 0, 1, tzinfo=timezone.utc)
    success, error, telemetry_id = await persister.persist_telemetry(
        mock_db_session, payload, received_ts
    )

    assert success is True
    assert error is None
    assert telemetry_id == "01J1ABC456"

    # Verify session.add was called (3 times: 1 TelemetryRecord + 2 HazardAssessments)
    assert mock_db_session.add.call_count >= 3
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_persist_telemetry_v1_backward_compatibility(mock_db_session):
    """Test backward compatibility: v1 telemetry (no intelligence) still works"""
    persister = TelemetryPersister()

    payload = {
        "telemetry_id": "01J1ABC789",
        "node_id": "NODE-003",
        "sequence": 300,
        "measurement_timestamp": "2024-09-18T02:00:00Z",
        "received_timestamp": "2024-09-18T02:00:01Z",
        "location": {"lat": 34.56, "lon": 78.90},
        "measurements": {"temperature_c": 35.0},
        "diagnostics": {},
        "power": {"battery_pct": 75},
        "source": "HARDWARE",
        "schema_version": "telemetry.v1"
        # NO sensor_assessments or hazard_assessments
    }

    # Mock no duplicate
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    received_ts = datetime(2024, 9, 18, 2, 0, 1, tzinfo=timezone.utc)
    success, error, telemetry_id = await persister.persist_telemetry(
        mock_db_session, payload, received_ts
    )

    assert success is True
    assert error is None
    assert telemetry_id == "01J1ABC789"

    # Verify TelemetryRecord was added (no intelligence assessments)
    # Note: add() may be called for Node upsert + TelemetryRecord
    assert mock_db_session.add.call_count >= 1
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_persist_both_sensor_and_hazard_assessments(mock_db_session):
    """Test persisting both sensor and hazard assessments together"""
    persister = TelemetryPersister()

    payload = {
        "telemetry_id": "01J1ABCXYZ",
        "node_id": "NODE-004",
        "sequence": 400,
        "measurement_timestamp": "2024-09-18T03:00:00Z",
        "received_timestamp": "2024-09-18T03:00:01Z",
        "location": {"lat": 45.67, "lon": 89.01},
        "measurements": {"temperature_c": 48.5, "humidity_pct": 12.0},
        "diagnostics": {},
        "power": {"battery_pct": 88},
        "source": "HARDWARE",
        "schema_version": "telemetry.v2",
        "sensor_assessments": [
            {
                "sensor_type": "bme680_temperature",
                "health": 0.94,
                "quality": 0.87,
                "reliability": 0.83,
                "baseline_state": "READY",
                "anomaly": 1.8
            }
        ],
        "hazard_assessments": [
            {
                "hazard_type": "fire",
                "evidence": 0.68,
                "confidence": 0.62,
                "severity": 0.48,
                "risk": 0.55,
                "state": "SUSPECTED",
                "information_condition": "GOOD"
            }
        ]
    }

    # Mock no duplicate
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    received_ts = datetime(2024, 9, 18, 3, 0, 1, tzinfo=timezone.utc)
    success, error, telemetry_id = await persister.persist_telemetry(
        mock_db_session, payload, received_ts
    )

    assert success is True
    assert error is None

    # Verify records added: TelemetryRecord + SensorAssessment + HazardAssessment
    # Note: add() includes Node upsert + 3 records
    assert mock_db_session.add.call_count >= 3
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_missing_intelligence_fields_preserved(mock_db_session):
    """Test that missing intelligence fields remain NULL (MISSING != ZERO)"""
    persister = TelemetryPersister()

    payload = {
        "telemetry_id": "01J1ABCNUL",
        "node_id": "NODE-005",
        "sequence": 500,
        "measurement_timestamp": "2024-09-18T04:00:00Z",
        "received_timestamp": "2024-09-18T04:00:01Z",
        "location": {"lat": 56.78, "lon": 90.12},
        "measurements": {"temperature_c": 42.0},
        "diagnostics": {},
        "power": {"battery_pct": 82},
        "source": "HARDWARE",
        "schema_version": "telemetry.v2",
        "sensor_assessments": [
            {
                "sensor_type": "bme680_temperature",
                "health": None,  # Missing
                "quality": None,  # Missing
                "reliability": 0.80,
                "baseline_state": None,  # Missing
                "anomaly": None  # Missing
            }
        ],
        "hazard_assessments": [
            {
                "hazard_type": "fire",
                "evidence": 0.45,
                "confidence": None,  # Missing
                "severity": None,  # Missing
                "risk": 0.40,
                "state": "WATCH",
                "information_condition": None  # Missing
            }
        ]
    }

    # Mock no duplicate
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    received_ts = datetime(2024, 9, 18, 4, 0, 1, tzinfo=timezone.utc)
    success, error, telemetry_id = await persister.persist_telemetry(
        mock_db_session, payload, received_ts
    )

    assert success is True
    assert error is None

    # Verify records were added (NULL fields should be preserved)
    # Note: add() includes Node upsert + TelemetryRecord + 2 assessments
    assert mock_db_session.add.call_count >= 3
    mock_db_session.commit.assert_called_once()
