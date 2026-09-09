"""Track C B2→C Integration Test - Simplified Version

Tests the coordinator trigger logic without full database dependency.
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from modules.simulation.c_coordinator import get_c_coordinator


@pytest.mark.asyncio
async def test_b2_to_c_fire_incident_trigger():
    """Test B2 fire incident triggers Track C simulation"""

    # Mock session for coordinator call
    session = MagicMock(spec=AsyncSession)

    # Get coordinator
    c_coord = get_c_coordinator()

    # Reset stats for clean test
    c_coord.stats = {
        "triggers_total": 0,
        "simulations_started": 0,
        "simulations_failed": 0,
        "errors": 0
    }

    # Fire incident data
    incident_id = "test-incident-001"
    incident_data = {
        "hazard_type": "FIRE",
        "centroid_lat": 12.9716,
        "centroid_lon": 77.5946,
        "confidence": 0.95
    }

    # Trigger coordinator
    await c_coord.on_incident_created(session, incident_id, incident_data)

    # Verify stats updated
    stats = c_coord.get_stats()
    assert stats["triggers_total"] == 1, "Should count trigger"
    assert stats["simulations_started"] == 1, "Should start simulation for fire incident"
    assert stats["errors"] == 0, "Should have no errors"

    print("✅ B2→C Fire Incident Trigger Test PASSED")


@pytest.mark.asyncio
async def test_b2_to_c_non_fire_incident_skipped():
    """Test non-FIRE incidents are skipped"""

    session = MagicMock(spec=AsyncSession)
    c_coord = get_c_coordinator()

    # Get current stats
    stats_before = c_coord.get_stats()

    # Non-fire incident
    incident_id = "test-incident-002"
    incident_data = {
        "hazard_type": "FLOOD",
        "centroid_lat": 12.9716,
        "centroid_lon": 77.5946
    }

    # Trigger coordinator
    await c_coord.on_incident_created(session, incident_id, incident_data)

    # Verify skipped
    stats_after = c_coord.get_stats()
    assert stats_after["triggers_total"] == stats_before["triggers_total"] + 1, "Should count trigger"
    assert stats_after["simulations_started"] == stats_before["simulations_started"], "Should NOT start simulation"

    print("✅ B2→C Non-Fire Incident Skip Test PASSED")


@pytest.mark.asyncio
async def test_b2_to_c_missing_location():
    """Test incidents with missing location fail gracefully"""

    session = MagicMock(spec=AsyncSession)
    c_coord = get_c_coordinator()

    stats_before = c_coord.get_stats()

    # Fire incident without location
    incident_id = "test-incident-003"
    incident_data = {
        "hazard_type": "FIRE",
        # Missing centroid_lat and centroid_lon
    }

    # Trigger coordinator - should not crash
    await c_coord.on_incident_created(session, incident_id, incident_data)

    stats_after = c_coord.get_stats()
    assert stats_after["triggers_total"] == stats_before["triggers_total"] + 1
    assert stats_after["simulations_failed"] == stats_before["simulations_failed"] + 1

    print("✅ B2→C Missing Location Test PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
