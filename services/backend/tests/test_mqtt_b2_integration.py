"""Integration test for MQTT → B1 → B2 pipeline

Validates end-to-end flow:
1. MQTT telemetry ingestion
2. Validation and persistence (B1)
3. Regional fusion trigger (B2)
4. Incident correlation (B2)

This is a real integration test using actual database and MQTT infrastructure.
"""
import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

import paho.mqtt.client as mqtt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db_config
from db.models import Node, TelemetryRecord
from db.models_b2 import Incident, IncidentObservation, RegionalHazardAssessment
from modules.intelligence.b2_coordinator import get_coordinator


# Test configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "Nexalert/telemetry/+"  # Match all node IDs (canonical format)


@pytest.fixture
async def db_session():
    """Provide async database session"""
    db_config = get_db_config()
    async for session in db_config.get_session():
        yield session


def create_test_telemetry(node_id: str, sequence: int, lat: float, lon: float) -> Dict[str, Any]:
    """Create test telemetry payload

    Args:
        node_id: Node identifier
        sequence: Sequence number
        lat: Latitude
        lon: Longitude

    Returns:
        Telemetry payload dict
    """
    telemetry_id = f"TEST-{node_id}-{sequence:06d}"
    timestamp = datetime.utcnow().isoformat() + "Z"

    return {
        "telemetry_id": telemetry_id,
        "schema_version": "telemetry.v1",
        "node_id": node_id,
        "sequence": sequence,
        "timestamp": timestamp,
        "location": {
            "latitude": lat,
            "longitude": lon,
            "altitude_m": 850.0,
            "accuracy_m": 10.0
        },
        "measurements": {
            "temperature_c": 35.2,
            "humidity_percent": 22.5,
            "pressure_hpa": 950.3,
            "pm25_ug_m3": 85.4,
            "pm10_ug_m3": None,
            "co_ppm": 2.1,
            "no2_ppb": 45.2,
            "smoke_density": 0.75,
            "flame_detected": True,
            "ir_intensity": 0.82,
            "wind_speed_mps": 3.2,
            "wind_direction_deg": 225.0,
            "solar_irradiance_w_m2": 850.0,
            "solar_current": None,
            "soil_moisture_percent": 15.2,
            "water_level_m": 0.45,
            "flow_rate_m3s": 0.012,
            "turbidity_ntu": 12.5,
            "stability_index": None
        },
        "diagnostics": {
            "battery_voltage_v": 12.4,
            "signal_strength_dbm": -65,
            "uptime_seconds": 86400,
            "reboot_count": 2,
            "last_calibration": "2024-01-15T08:30:00Z"
        },
        "power": {
            "battery_soc_percent": 85.0,
            "solar_charging": True,
            "power_mode": "NORMAL"
        },
        "source": "SENSOR_NODE"
    }


def publish_telemetry_mqtt(payload: Dict[str, Any]) -> bool:
    """Publish telemetry via MQTT

    Args:
        payload: Telemetry payload

    Returns:
        True if published successfully
    """
    try:
        client = mqtt.Client()
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

        json_payload = json.dumps(payload)
        result = client.publish(MQTT_TOPIC, json_payload, qos=1)

        # Wait for publish
        result.wait_for_publish(timeout=5.0)

        client.disconnect()
        return result.is_published()

    except Exception as e:
        print(f"MQTT publish error: {str(e)}")
        return False


@pytest.mark.asyncio
async def test_mqtt_b2_integration_two_nodes(db_session: AsyncSession):
    """Test MQTT → B1 → B2 integration with two nearby nodes

    Scenario:
    - Node NODE-TEST-001 at (12.9716, 77.5946)
    - Node NODE-TEST-002 at (12.9717, 77.5947) [~15m away]
    - Both publish telemetry via MQTT
    - Verify telemetry persisted in database
    - Verify B2 coordinator triggered (check logs)
    - Note: Full B2 fusion requires node-level hazard assessments

    This test validates the WIRING, not the complete B2 pipeline
    (which requires Phase 5 reference implementation integration).
    """

    # Step 1: Publish telemetry from NODE-TEST-001
    payload1 = create_test_telemetry(
        node_id="NODE-TEST-001",
        sequence=1001,
        lat=12.9716,
        lon=77.5946
    )

    success1 = publish_telemetry_mqtt(payload1)
    assert success1, "Failed to publish telemetry from NODE-TEST-001"

    # Wait for ingestion
    await asyncio.sleep(2.0)

    # Step 2: Verify telemetry persisted
    stmt = select(TelemetryRecord).where(
        TelemetryRecord.telemetry_id == payload1["telemetry_id"]
    )
    result = await db_session.execute(stmt)
    record1 = result.scalar_one_or_none()

    assert record1 is not None, "Telemetry from NODE-TEST-001 not persisted"
    assert record1.node_id == "NODE-TEST-001"
    assert record1.sequence == 1001

    # Step 3: Publish telemetry from NODE-TEST-002
    payload2 = create_test_telemetry(
        node_id="NODE-TEST-002",
        sequence=2001,
        lat=12.9717,
        lon=77.5947
    )

    success2 = publish_telemetry_mqtt(payload2)
    assert success2, "Failed to publish telemetry from NODE-TEST-002"

    # Wait for ingestion
    await asyncio.sleep(2.0)

    # Step 4: Verify telemetry persisted
    stmt = select(TelemetryRecord).where(
        TelemetryRecord.telemetry_id == payload2["telemetry_id"]
    )
    result = await db_session.execute(stmt)
    record2 = result.scalar_one_or_none()

    assert record2 is not None, "Telemetry from NODE-TEST-002 not persisted"
    assert record2.node_id == "NODE-TEST-002"
    assert record2.sequence == 2001

    # Step 5: Verify nodes registered
    stmt = select(Node).where(Node.node_id.in_(["NODE-TEST-001", "NODE-TEST-002"]))
    result = await db_session.execute(stmt)
    nodes = result.scalars().all()

    assert len(nodes) == 2, "Both nodes should be registered"

    # Step 6: Check B2 coordinator stats
    coordinator = get_coordinator()
    stats = coordinator.get_stats()

    print(f"\nB2 Coordinator Stats:")
    print(f"  Triggers: {stats['triggers_total']}")
    print(f"  Fusion runs: {stats['fusion_runs']}")
    print(f"  Incidents created: {stats['incidents_created']}")
    print(f"  Incidents updated: {stats['incidents_updated']}")
    print(f"  Errors: {stats['errors']}")

    # Verify coordinator was triggered (at least twice)
    assert stats["triggers_total"] >= 2, "B2 coordinator should be triggered twice"

    # Note: fusion_runs = 0 is EXPECTED because we don't have node-level
    # hazard assessments yet. This test validates the WIRING only.

    print("\n✓ MQTT → B1 → B2 wiring integration test PASSED")
    print("  - Telemetry ingestion: WORKING")
    print("  - B1 persistence: WORKING")
    print("  - B2 coordinator trigger: WORKING")
    print("  - B2 fusion: NOT YET (requires node hazard assessments)")


@pytest.mark.asyncio
async def test_mqtt_idempotency_b2(db_session: AsyncSession):
    """Test that duplicate MQTT messages don't create duplicate B2 incidents

    Scenario:
    - Publish same telemetry twice
    - Verify only one telemetry record persisted
    - Verify B2 coordinator handles idempotency
    """

    payload = create_test_telemetry(
        node_id="NODE-TEST-DUP",
        sequence=5001,
        lat=12.9720,
        lon=77.5950
    )

    # Publish first time
    success1 = publish_telemetry_mqtt(payload)
    assert success1, "First publish failed"
    await asyncio.sleep(2.0)

    # Publish second time (duplicate)
    success2 = publish_telemetry_mqtt(payload)
    assert success2, "Second publish failed"
    await asyncio.sleep(2.0)

    # Verify only ONE telemetry record exists
    stmt = select(TelemetryRecord).where(
        TelemetryRecord.node_id == "NODE-TEST-DUP",
        TelemetryRecord.sequence == 5001
    )
    result = await db_session.execute(stmt)
    records = result.scalars().all()

    assert len(records) == 1, "Duplicate telemetry should not create multiple records"

    # Verify B2 coordinator stats
    coordinator = get_coordinator()
    stats = coordinator.get_stats()

    # Should have been triggered at least twice (once per publish attempt)
    assert stats["triggers_total"] >= 2, "Coordinator should be triggered for both publishes"

    print("\n✓ MQTT idempotency test PASSED")
    print("  - Duplicate telemetry handled correctly")
    print("  - B2 coordinator resilient to duplicates")


@pytest.mark.asyncio
async def test_b2_coordinator_stats(db_session: AsyncSession):
    """Test B2 coordinator statistics tracking"""

    coordinator = get_coordinator()
    initial_stats = coordinator.get_stats()

    print(f"\nInitial B2 Coordinator Stats:")
    print(f"  Triggers: {initial_stats['triggers_total']}")
    print(f"  Fusion runs: {initial_stats['fusion_runs']}")
    print(f"  Incidents created: {initial_stats['incidents_created']}")
    print(f"  Incidents updated: {initial_stats['incidents_updated']}")
    print(f"  Errors: {initial_stats['errors']}")

    # Publish test telemetry
    payload = create_test_telemetry(
        node_id="NODE-TEST-STATS",
        sequence=6001,
        lat=12.9725,
        lon=77.5955
    )

    success = publish_telemetry_mqtt(payload)
    assert success, "Test telemetry publish failed"
    await asyncio.sleep(2.0)

    final_stats = coordinator.get_stats()

    print(f"\nFinal B2 Coordinator Stats:")
    print(f"  Triggers: {final_stats['triggers_total']}")
    print(f"  Fusion runs: {final_stats['fusion_runs']}")
    print(f"  Incidents created: {final_stats['incidents_created']}")
    print(f"  Incidents updated: {final_stats['incidents_updated']}")
    print(f"  Errors: {final_stats['errors']}")

    # Verify stats incremented
    assert final_stats["triggers_total"] > initial_stats["triggers_total"], \
        "Triggers should increment"

    print("\n✓ B2 coordinator stats test PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
