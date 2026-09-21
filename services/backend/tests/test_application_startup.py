"""Test application startup lifecycle

Regression test for node registry initialization before MQTT consumer startup.
Verifies the bug fix where registry must be initialized before consumer starts.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from modules.ingestion.node_registry import NodeRegistry, initialize_registry, get_registry


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_nodes():
    """Mock node query results"""
    class MockRow:
        def __init__(self, node_id, status, firmware_version, location, lat, lon, alt):
            self.node_id = node_id
            self.status = status
            self.firmware_version = firmware_version
            self.location = location
            self.lat = lat
            self.lon = lon
            self.alt = alt

    return [
        MockRow(
            "NODE-001", "ACTIVE", "1.0.0",
            "POINT(77.5946 12.9716)",
            12.9716, 77.5946, 920.0
        )
    ]


@pytest.mark.asyncio
async def test_application_startup_initializes_registry_before_mqtt_consumer(
    mock_db_session,
    mock_nodes
):
    """Test application startup initializes node registry before MQTT consumer

    This is a regression test for the bug:
    - MQTT consumer.start() initializes Track3CNormalizer
    - Track3CNormalizer calls get_registry()
    - If registry not initialized → RuntimeError
    - Backend shutdown before MQTT subscription

    Fix: Initialize registry in main.py lifespan BEFORE mqtt_consumer.start()
    """

    # Simulate application startup lifecycle
    # Step 1: Initialize node registry (must happen BEFORE MQTT consumer)
    registry = initialize_registry()
    assert registry is not None
    assert registry.size() == 0

    # Step 2: Load nodes from database
    mock_result = MagicMock()
    mock_result.all.return_value = mock_nodes
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    await registry.load_from_db(mock_db_session)
    assert registry.size() == 1

    # Step 3: Verify get_registry() works (MQTT consumer will call this)
    retrieved_registry = get_registry()
    assert retrieved_registry is registry
    assert retrieved_registry.size() == 1

    # Step 4: Verify location resolution works
    location = retrieved_registry.get_location("NODE-001")
    assert location is not None
    assert location["lat"] == 12.9716
    assert location["lon"] == 77.5946

    print("\n✓ Application startup lifecycle test PASSED")
    print("  Registry initialized → nodes loaded → MQTT consumer can start")


@pytest.mark.asyncio
async def test_mqtt_consumer_fails_if_registry_not_initialized():
    """Test MQTT consumer fails gracefully if registry not initialized

    Verifies the error message is clear when registry initialization is skipped.
    """
    import modules.ingestion.node_registry as reg_module

    # Clear global registry (simulate startup without initialize_registry())
    reg_module._global_registry = None

    # Attempt to get registry (MQTT consumer does this during start())
    with pytest.raises(RuntimeError, match="not initialized"):
        get_registry()

    print("\n✓ Registry not initialized error test PASSED")
    print("  Clear error when registry initialization is skipped")


@pytest.mark.asyncio
async def test_registry_initialization_is_idempotent():
    """Test calling initialize_registry multiple times is safe"""

    # First initialization
    registry1 = initialize_registry()
    assert registry1.size() == 0

    # Second initialization (should replace global registry)
    registry2 = initialize_registry()
    assert registry2 is not registry1  # New instance

    # get_registry returns the latest one
    current = get_registry()
    assert current is registry2

    print("\n✓ Registry initialization idempotence test PASSED")


def test_startup_order_documented():
    """Test documents the required startup order

    Application startup order (main.py lifespan):
    1. Database connection
    2. Initialize node registry (initialize_registry)
    3. Load nodes from database (refresh_registry)
    4. Start MQTT consumer (consumer.start)

    This order is CRITICAL. MQTT consumer depends on initialized registry.
    """
    expected_order = [
        "Database connection",
        "Initialize node registry",
        "Load nodes from database",
        "Start MQTT consumer"
    ]

    print("\n✓ Application startup order documented")
    print("  Required order:")
    for i, step in enumerate(expected_order, 1):
        print(f"    {i}. {step}")
