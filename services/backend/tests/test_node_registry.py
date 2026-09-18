"""Unit tests for Node Registry

Tests the node registry loader for Track 3C normalization
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from modules.ingestion.node_registry import NodeRegistry, initialize_registry, get_registry
from db.models import Node


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
            "POINT(77.5946 12.9716)",  # location (WKT)
            12.9716, 77.5946, 920.0
        ),
        MockRow(
            "NODE-002", "ACTIVE", "1.0.0",
            "POINT(67.8901 23.4567)",
            23.4567, 67.8901, None  # No altitude
        ),
        MockRow(
            "NODE-003", "INACTIVE", "0.9.0",
            None, None, None, None  # No location
        )
    ]


@pytest.mark.asyncio
async def test_registry_load_from_db(mock_db_session, mock_nodes):
    """Test loading registry from database"""
    registry = NodeRegistry()

    # Mock query result
    mock_result = MagicMock()
    mock_result.all.return_value = mock_nodes
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    await registry.load_from_db(mock_db_session)

    assert registry.size() == 3

    # NODE-001: valid location with altitude
    node1 = registry.get_node_info("NODE-001")
    assert node1 is not None
    assert node1["status"] == "ACTIVE"
    assert node1["firmware_version"] == "1.0.0"
    assert node1["location"]["lat"] == 12.9716
    assert node1["location"]["lon"] == 77.5946
    assert node1["location"]["alt"] == 920.0

    # NODE-002: valid location without altitude
    node2 = registry.get_node_info("NODE-002")
    assert node2 is not None
    assert node2["location"]["lat"] == 23.4567
    assert node2["location"]["lon"] == 67.8901
    assert "alt" not in node2["location"]

    # NODE-003: no location (normalization will fail)
    node3 = registry.get_node_info("NODE-003")
    assert node3 is not None
    assert node3["status"] == "INACTIVE"
    assert node3["location"] is None


@pytest.mark.asyncio
async def test_registry_get_location(mock_db_session, mock_nodes):
    """Test getting location from registry"""
    registry = NodeRegistry()

    mock_result = MagicMock()
    mock_result.all.return_value = mock_nodes
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    await registry.load_from_db(mock_db_session)

    # Valid location
    loc1 = registry.get_location("NODE-001")
    assert loc1 is not None
    assert loc1["lat"] == 12.9716
    assert loc1["lon"] == 77.5946
    assert loc1["alt"] == 920.0

    # Valid location without altitude
    loc2 = registry.get_location("NODE-002")
    assert loc2 is not None
    assert "alt" not in loc2

    # No location
    loc3 = registry.get_location("NODE-003")
    assert loc3 is None

    # Unknown node
    loc_unknown = registry.get_location("NODE-999")
    assert loc_unknown is None


@pytest.mark.asyncio
async def test_registry_empty_on_error(mock_db_session):
    """Test registry remains empty on database error"""
    registry = NodeRegistry()

    # Simulate database error
    mock_db_session.execute = AsyncMock(side_effect=Exception("DB connection failed"))

    await registry.load_from_db(mock_db_session)

    assert registry.size() == 0


def test_registry_clear():
    """Test clearing registry"""
    registry = NodeRegistry()

    # Manually populate registry
    registry._registry = {
        "NODE-001": {"location": {"lat": 12.34, "lon": 56.78}}
    }
    assert registry.size() == 1

    registry.clear()
    assert registry.size() == 0


def test_global_registry_initialize():
    """Test global registry initialization"""
    # Initialize
    registry = initialize_registry()
    assert registry is not None
    assert registry.size() == 0

    # Get same instance
    registry2 = get_registry()
    assert registry2 is registry


def test_global_registry_not_initialized():
    """Test get_registry raises when not initialized"""
    # Clear global registry
    import modules.ingestion.node_registry as reg_module
    reg_module._global_registry = None

    with pytest.raises(RuntimeError, match="not initialized"):
        get_registry()
