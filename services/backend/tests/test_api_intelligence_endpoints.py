"""Test Track 5 intelligence API endpoints

Tests for sensor and hazard assessment API routes.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

from modules.api.routes import (
    get_sensor_assessments,
    get_node_sensor_assessments,
    get_node_hazard_assessments,
    get_hazards
)
from db.models import SensorAssessment, HazardAssessment


@pytest.fixture
def mock_db_session():
    """Mock database session for API route testing"""
    session = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def sample_sensor_assessment():
    """Sample sensor assessment for testing"""
    return SensorAssessment(
        assessment_id=1,
        telemetry_id="01J1ABC123",
        node_id="NODE-001",
        sensor_type="bme680_temperature",
        health=0.95,
        quality=0.89,
        reliability=0.85,
        baseline_state="READY",
        anomaly=2.3,
        created_at=datetime(2024, 9, 22, 10, 0, 0, tzinfo=timezone.utc)
    )


@pytest.fixture
def sample_hazard_assessment():
    """Sample hazard assessment for testing"""
    return HazardAssessment(
        assessment_id=1,
        telemetry_id="01J1ABC123",
        hazard_type="fire",
        evidence=0.72,
        confidence=0.68,
        severity=0.45,
        risk=0.52,
        state="SUSPECTED",
        information_condition="GOOD",
        created_at=datetime(2024, 9, 22, 10, 0, 0, tzinfo=timezone.utc)
    )


@pytest.mark.asyncio
async def test_get_sensor_assessments_global(mock_db_session, sample_sensor_assessment):
    """Test GET /sensor-assessments (global endpoint)"""
    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_sensor_assessment]
    mock_db_session.execute.return_value = mock_result

    # Call API route function
    result = await get_sensor_assessments(
        sensor_type=None,
        limit=100,
        session=mock_db_session
    )

    # Verify result
    assert len(result) == 1
    assert result[0].assessment_id == 1
    assert result[0].sensor_type == "bme680_temperature"
    assert result[0].health == 0.95
    assert result[0].quality == 0.89


@pytest.mark.asyncio
async def test_get_sensor_assessments_with_filter(mock_db_session, sample_sensor_assessment):
    """Test GET /sensor-assessments with sensor_type filter"""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_sensor_assessment]
    mock_db_session.execute.return_value = mock_result

    result = await get_sensor_assessments(
        sensor_type="bme680_temperature",
        limit=100,
        session=mock_db_session
    )

    assert len(result) == 1
    assert result[0].sensor_type == "bme680_temperature"


@pytest.mark.asyncio
async def test_get_node_sensor_assessments(mock_db_session, sample_sensor_assessment):
    """Test GET /nodes/{node_id}/sensor-assessments"""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_sensor_assessment]
    mock_db_session.execute.return_value = mock_result

    result = await get_node_sensor_assessments(
        node_id="NODE-001",
        sensor_type=None,
        limit=100,
        session=mock_db_session
    )

    assert len(result) == 1
    assert result[0].node_id == "NODE-001"
    assert result[0].sensor_type == "bme680_temperature"


@pytest.mark.asyncio
async def test_get_node_hazard_assessments(mock_db_session, sample_hazard_assessment):
    """Test GET /nodes/{node_id}/hazard-assessments"""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_hazard_assessment]
    mock_db_session.execute.return_value = mock_result

    result = await get_node_hazard_assessments(
        node_id="NODE-001",
        hazard_type=None,
        state=None,
        limit=100,
        session=mock_db_session
    )

    assert len(result) == 1
    assert result[0].hazard_type == "fire"
    assert result[0].state == "SUSPECTED"
    assert result[0].evidence == 0.72


@pytest.mark.asyncio
async def test_get_node_hazard_assessments_with_filters(mock_db_session, sample_hazard_assessment):
    """Test GET /nodes/{node_id}/hazard-assessments with filters"""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_hazard_assessment]
    mock_db_session.execute.return_value = mock_result

    result = await get_node_hazard_assessments(
        node_id="NODE-001",
        hazard_type="fire",
        state="SUSPECTED",
        limit=100,
        session=mock_db_session
    )

    assert len(result) == 1
    assert result[0].hazard_type == "fire"
    assert result[0].state == "SUSPECTED"


@pytest.mark.asyncio
async def test_sensor_assessment_null_fields_preserved(mock_db_session):
    """Test sensor assessment with NULL fields (MISSING != ZERO)"""
    # Create assessment with NULL fields
    assessment = SensorAssessment(
        assessment_id=2,
        telemetry_id="01J1ABC456",
        node_id="NODE-002",
        sensor_type="dht22_humidity",
        health=None,  # NULL
        quality=0.75,
        reliability=None,  # NULL
        baseline_state="DEGRADED",
        anomaly=None,  # NULL
        created_at=datetime(2024, 9, 22, 10, 5, 0, tzinfo=timezone.utc)
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [assessment]
    mock_db_session.execute.return_value = mock_result

    result = await get_sensor_assessments(
        sensor_type=None,
        limit=100,
        session=mock_db_session
    )

    assert len(result) == 1
    assert result[0].health is None  # NULL preserved
    assert result[0].quality == 0.75
    assert result[0].reliability is None  # NULL preserved
    assert result[0].anomaly is None  # NULL preserved


@pytest.mark.asyncio
async def test_hazard_assessment_null_fields_preserved(mock_db_session):
    """Test hazard assessment with NULL fields (MISSING != ZERO)"""
    # Create assessment with NULL fields
    assessment = HazardAssessment(
        assessment_id=2,
        telemetry_id="01J1ABC456",
        hazard_type="flood",
        evidence=0.55,
        confidence=None,  # NULL
        severity=None,  # NULL
        risk=0.45,
        state="WATCH",
        information_condition=None,  # NULL
        created_at=datetime(2024, 9, 22, 10, 5, 0, tzinfo=timezone.utc)
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [assessment]
    mock_db_session.execute.return_value = mock_result

    result = await get_hazards(
        hazard_type=None,
        state=None,
        limit=100,
        session=mock_db_session
    )

    assert len(result) == 1
    assert result[0].evidence == 0.55
    assert result[0].confidence is None  # NULL preserved
    assert result[0].severity is None  # NULL preserved
    assert result[0].information_condition is None  # NULL preserved
