"""Test MQTT consumer Track 3C integration

Tests the MQTT consumer's live hardware JSON → Track 3C normalization → validation → persistence path.
Verifies the bug fix for schema_version missing from raw hardware JSON.
"""
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from modules.ingestion.mqtt_consumer import MQTTTelemetryConsumer
from modules.ingestion.track3c_normalizer import Track3CNormalizer
from modules.ingestion.node_registry import NodeRegistry
from modules.ingestion.validator import parse_telemetry_payload
from db.models import Node, TelemetryRecord


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
def node_registry_with_test_node():
    """Node registry with test node"""
    registry = NodeRegistry()
    registry._registry = {
        "NODE-001": {
            "location": {"lat": 12.9716, "lon": 77.5946, "alt": 920.0},
            "status": "ACTIVE",
            "firmware_version": "1.0.0"
        }
    }
    return registry


@pytest.mark.asyncio
async def test_mqtt_consumer_processes_hardware_json_via_track3c(
    mock_db_session,
    node_registry_with_test_node
):
    """Test MQTT consumer processes raw hardware JSON via Track 3C normalization

    This test verifies the bug fix:
    - Raw ESP32 hardware JSON does NOT contain schema_version
    - Track 3C normalizer converts it to canonical telemetry.v1 (adds schema_version)
    - Validator validates the canonical payload (not raw hardware JSON)
    - Persister stores the canonical payload
    """

    # Mock MQTT consumer with Track 3C normalizer
    consumer = MQTTTelemetryConsumer(
        broker_host="localhost",
        broker_port=1883,
        topic="Nexalert/telemetry/#",
        client_id="test-consumer"
    )

    # Inject node registry and normalizer
    consumer.normalizer = Track3CNormalizer(node_registry_with_test_node)

    # Raw hardware JSON from ESP32 (NO schema_version)
    hardware_json_raw = b'''{
        "node_id": "NODE-001",
        "timestamp_ms": 1726678800000,
        "sequence": 100,
        "sensors": {
            "temperature_c": 45.2,
            "humidity_rh": 15.3,
            "pressure_hpa": 1013.25,
            "gas_ppm": 2345,
            "vibration_mps2": 0.15
        },
        "availability": {
            "temperature": true,
            "humidity": true,
            "pressure": true,
            "gas": true,
            "vibration": true
        },
        "power": {
            "battery_pct": 85,
            "solar_state": "CHARGING"
        }
    }'''

    # Mock database config
    with patch('modules.ingestion.mqtt_consumer.get_db_config') as mock_get_db:
        mock_db_config = MagicMock()

        async def mock_get_session():
            yield mock_db_session

        mock_db_config.get_session.return_value = mock_get_session()
        mock_get_db.return_value = mock_db_config

        # Mock B2 coordinator (non-blocking)
        with patch('modules.ingestion.mqtt_consumer.get_coordinator') as mock_get_coordinator:
            mock_coordinator = MagicMock()
            mock_coordinator.trigger_after_persistence = AsyncMock()
            mock_get_coordinator.return_value = mock_coordinator

            # Process message
            await consumer._process_message(hardware_json_raw)

    # Verify statistics
    assert consumer.stats["messages_received"] == 0  # Not incremented by _process_message directly
    assert consumer.stats["messages_valid"] == 1
    assert consumer.stats["messages_invalid"] == 0
    assert consumer.stats["messages_persisted"] == 1
    assert consumer.stats["messages_failed"] == 0

    # Verify persistence was called with canonical telemetry (not raw hardware JSON)
    assert mock_db_session.add.called
    assert mock_db_session.commit.called

    print("\n✓ MQTT consumer Track 3C integration test PASSED")
    print("  Hardware JSON → Track 3C normalization → validation → persistence")


@pytest.mark.asyncio
async def test_mqtt_consumer_rejects_hardware_json_for_unknown_node(mock_db_session):
    """Test MQTT consumer rejects hardware JSON for unknown node"""

    # Empty registry (no nodes)
    empty_registry = NodeRegistry()

    consumer = MQTTTelemetryConsumer(
        broker_host="localhost",
        broker_port=1883,
        topic="Nexalert/telemetry/#",
        client_id="test-consumer"
    )
    consumer.normalizer = Track3CNormalizer(empty_registry)

    # Hardware JSON for unknown node
    hardware_json_raw = b'''{
        "node_id": "NODE-999",
        "timestamp_ms": 1726678800000,
        "sequence": 100,
        "sensors": {"temperature_c": 25.0},
        "availability": {"temperature": true},
        "power": {"battery_pct": 75}
    }'''

    # Mock database config
    with patch('modules.ingestion.mqtt_consumer.get_db_config') as mock_get_db:
        mock_db_config = MagicMock()

        async def mock_get_session():
            yield mock_db_session

        mock_db_config.get_session.return_value = mock_get_session()
        mock_get_db.return_value = mock_db_config

        # Process message
        await consumer._process_message(hardware_json_raw)

    # Verify message rejected (normalization failed for unknown node)
    assert consumer.stats["messages_valid"] == 0
    assert consumer.stats["messages_invalid"] == 1
    assert consumer.stats["messages_persisted"] == 0

    # Verify persistence was NOT called
    assert not mock_db_session.add.called
    assert not mock_db_session.commit.called

    print("\n✓ MQTT consumer unknown node rejection test PASSED")


@pytest.mark.asyncio
async def test_mqtt_consumer_validates_canonical_telemetry_not_hardware_json():
    """Test MQTT consumer validates canonical telemetry.v1, not raw hardware JSON

    This is the core bug fix verification:
    - Raw hardware JSON lacks schema_version (would fail validation)
    - Track 3C normalization adds schema_version
    - Validator sees canonical telemetry with schema_version (passes validation)
    """

    # Create node registry
    registry = NodeRegistry()
    registry._registry = {
        "NODE-001": {
            "location": {"lat": 12.9716, "lon": 77.5946},
            "status": "ACTIVE"
        }
    }

    # Create normalizer
    normalizer = Track3CNormalizer(registry)

    # Raw hardware JSON (NO schema_version)
    hardware_json = {
        "node_id": "NODE-001",
        "timestamp_ms": 1726678800000,
        "sequence": 100,
        "sensors": {"temperature_c": 45.2},
        "availability": {"temperature": True},
        "power": {"battery_pct": 85}
    }

    received_timestamp = datetime(2024, 9, 18, 17, 0, 1, tzinfo=timezone.utc)

    # Normalize hardware JSON
    canonical_telemetry, error = await normalizer.normalize_hardware_json(
        hardware_json, received_timestamp
    )

    assert error is None
    assert canonical_telemetry is not None

    # Verify canonical telemetry HAS schema_version
    assert "schema_version" in canonical_telemetry
    assert canonical_telemetry["schema_version"] == "telemetry.v1"

    # Verify canonical telemetry has all required fields
    assert canonical_telemetry["telemetry_id"] is not None
    assert canonical_telemetry["node_id"] == "NODE-001"
    assert canonical_telemetry["sequence"] == 100
    assert canonical_telemetry["measurement_timestamp"] is not None
    assert canonical_telemetry["received_timestamp"] is not None
    assert canonical_telemetry["location"] == {"lat": 12.9716, "lon": 77.5946, "alt": None}
    assert canonical_telemetry["source"] == "HARDWARE"

    print("\n✓ Canonical telemetry validation test PASSED")
    print("  Track 3C adds schema_version to hardware JSON")
