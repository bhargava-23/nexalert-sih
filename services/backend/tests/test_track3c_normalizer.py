"""Unit tests for Track 3C hardware JSON normalization

Tests the normalization layer that converts ESP32 hardware JSON to canonical telemetry.v1
"""
import pytest
from datetime import datetime, timezone
from modules.ingestion.track3c_normalizer import Track3CNormalizer
from modules.ingestion.node_registry import NodeRegistry


class MockNodeRegistry:
    """Mock node registry for testing"""

    def __init__(self, nodes=None):
        self.nodes = nodes or {}

    def get_location(self, node_id):
        node_info = self.nodes.get(node_id)
        if node_info is None:
            return None
        return node_info.get("location")


@pytest.fixture
def valid_node_registry():
    """Node registry with valid nodes"""
    return MockNodeRegistry({
        "NODE-001": {
            "location": {"lat": 12.9716, "lon": 77.5946, "alt": 920.0},
            "status": "ACTIVE"
        },
        "NODE-002": {
            "location": {"lat": 23.4567, "lon": 67.8901},
            "status": "ACTIVE"
        }
    })


@pytest.fixture
def registry_missing_location():
    """Node registry with node missing location"""
    return MockNodeRegistry({
        "NODE-003": {
            "location": None,
            "status": "ACTIVE"
        }
    })


@pytest.mark.asyncio
async def test_normalize_valid_hardware_json(valid_node_registry):
    """Test normalization of valid hardware JSON"""
    normalizer = Track3CNormalizer(valid_node_registry)

    hardware_json = {
        "node_id": "NODE-001",
        "timestamp_ms": 1726617600000,  # 2024-09-18T00:00:00Z (Unix timestamp in milliseconds)
        "sequence": 42,
        "sensors": {
            "temperature_c": 45.2,
            "humidity_rh": 15.3,
            "pressure_hpa": 1013.25,
            "gas_ppm": 2345,  # RAW ADC
            "vibration_mps2": 0.15
        },
        "availability": {
            "temperature": True,
            "humidity": True,
            "pressure": True,
            "gas": True,
            "vibration": True
        },
        "power": {
            "battery_pct": 85,
            "solar_state": "CHARGING"
        }
    }

    received_timestamp = datetime(2026, 9, 17, 18, 0, 1, tzinfo=timezone.utc)

    canonical, error = await normalizer.normalize_hardware_json(
        hardware_json, received_timestamp
    )

    assert error is None
    assert canonical is not None
    assert canonical["schema_version"] == "telemetry.v1"
    assert canonical["node_id"] == "NODE-001"
    assert canonical["sequence"] == 42
    assert canonical["measurement_timestamp"] == "2024-09-18T00:00:00Z"
    assert canonical["received_timestamp"] == "2026-09-17T18:00:01Z"
    assert canonical["source"] == "HARDWARE"

    # Location from registry
    assert canonical["location"]["lat"] == 12.9716
    assert canonical["location"]["lon"] == 77.5946
    assert canonical["location"]["alt"] == 920.0

    # Measurements mapping
    measurements = canonical["measurements"]
    assert measurements["temp_c"] == 45.2
    assert measurements["humidity_pct"] == 15.3
    assert measurements["pressure_hpa"] == 1013.25
    assert measurements["gas_adc"] == 2345  # Renamed from gas_ppm
    assert measurements["vibration_mps2"] == 0.15

    # Diagnostics mapping
    diagnostics = canonical["diagnostics"]
    assert diagnostics["sensor_availability"]["temperature"] is True
    assert diagnostics["sensor_availability"]["humidity"] is True
    assert diagnostics["sensor_availability"]["gas"] is True

    # Power mapping
    power = canonical["power"]
    assert power["battery_pct"] == 85
    assert power["solar_state"] == "CHARGING"

    # Telemetry ID generated (ULID format)
    assert len(canonical["telemetry_id"]) == 26


@pytest.mark.asyncio
async def test_normalize_missing_sensors_preserved(valid_node_registry):
    """Test that missing sensor values remain null (MISSING != ZERO)"""
    normalizer = Track3CNormalizer(valid_node_registry)

    hardware_json = {
        "node_id": "NODE-001",
        "timestamp_ms": 1726617600000,
        "sequence": 43,
        "sensors": {
            "temperature_c": 45.2,
            # humidity missing
            # pressure missing
            # gas missing
            # vibration missing
        },
        "availability": {
            "temperature": True,
            "humidity": False,
            "pressure": False,
            "gas": False,
            "vibration": False
        },
        "power": {
            "battery_pct": 80
            # solar_state missing
        }
    }

    received_timestamp = datetime(2026, 9, 17, 18, 0, 2, tzinfo=timezone.utc)

    canonical, error = await normalizer.normalize_hardware_json(
        hardware_json, received_timestamp
    )

    assert error is None
    assert canonical is not None

    # Present sensor
    assert canonical["measurements"]["temp_c"] == 45.2

    # Missing sensors are null (NOT zero)
    assert canonical["measurements"]["humidity_pct"] is None
    assert canonical["measurements"]["pressure_hpa"] is None
    assert canonical["measurements"]["gas_adc"] is None
    assert canonical["measurements"]["vibration_mps2"] is None

    # Power field present
    assert canonical["power"]["battery_pct"] == 80

    # Missing power field is null
    assert canonical["power"]["solar_state"] is None


@pytest.mark.asyncio
async def test_normalize_unknown_node(valid_node_registry):
    """Test normalization fails for unknown node"""
    normalizer = Track3CNormalizer(valid_node_registry)

    hardware_json = {
        "node_id": "NODE-999",  # Not in registry
        "timestamp_ms": 1726617600000,
        "sequence": 44,
        "sensors": {"temperature_c": 25.0},
        "availability": {"temperature": True},
        "power": {"battery_pct": 75}
    }

    received_timestamp = datetime(2026, 9, 17, 18, 0, 3, tzinfo=timezone.utc)

    canonical, error = await normalizer.normalize_hardware_json(
        hardware_json, received_timestamp
    )

    assert canonical is None
    assert error is not None
    assert "NODE-999" in error
    assert "Unknown node" in error or "missing location" in error


@pytest.mark.asyncio
async def test_normalize_node_missing_location(registry_missing_location):
    """Test normalization fails when node has no location"""
    normalizer = Track3CNormalizer(registry_missing_location)

    hardware_json = {
        "node_id": "NODE-003",  # Has no location in registry
        "timestamp_ms": 1726617600000,
        "sequence": 45,
        "sensors": {"temperature_c": 25.0},
        "availability": {"temperature": True},
        "power": {"battery_pct": 75}
    }

    received_timestamp = datetime(2026, 9, 17, 18, 0, 4, tzinfo=timezone.utc)

    canonical, error = await normalizer.normalize_hardware_json(
        hardware_json, received_timestamp
    )

    assert canonical is None
    assert error is not None
    assert "NODE-003" in error
    assert "location" in error.lower()


@pytest.mark.asyncio
async def test_normalize_missing_required_fields():
    """Test normalization fails when required fields are missing"""
    normalizer = Track3CNormalizer(MockNodeRegistry())

    # Missing node_id
    hardware_json = {
        "timestamp_ms": 1726617600000,
        "sequence": 46,
        "sensors": {},
        "availability": {},
        "power": {}
    }

    received_timestamp = datetime(2026, 9, 17, 18, 0, 5, tzinfo=timezone.utc)

    canonical, error = await normalizer.normalize_hardware_json(
        hardware_json, received_timestamp
    )

    assert canonical is None
    assert error is not None
    assert "node_id" in error


@pytest.mark.asyncio
async def test_normalize_gas_ppm_to_gas_adc_mapping(valid_node_registry):
    """Test that gas_ppm (RAW ADC) is correctly mapped to gas_adc"""
    normalizer = Track3CNormalizer(valid_node_registry)

    hardware_json = {
        "node_id": "NODE-001",
        "timestamp_ms": 1726617600000,
        "sequence": 47,
        "sensors": {
            "gas_ppm": 4095  # Maximum RAW ADC value (NOT calibrated ppm)
        },
        "availability": {"gas": True},
        "power": {"battery_pct": 90}
    }

    received_timestamp = datetime(2026, 9, 17, 18, 0, 6, tzinfo=timezone.utc)

    canonical, error = await normalizer.normalize_hardware_json(
        hardware_json, received_timestamp
    )

    assert error is None
    assert canonical is not None

    # gas_ppm → gas_adc (semantic fix, value preserved)
    assert canonical["measurements"]["gas_adc"] == 4095
    assert "gas_ppm" not in canonical["measurements"]  # Renamed field


@pytest.mark.asyncio
async def test_normalize_optional_altitude(valid_node_registry):
    """Test that optional altitude is included when present"""
    normalizer = Track3CNormalizer(valid_node_registry)

    hardware_json = {
        "node_id": "NODE-001",  # Has altitude in registry
        "timestamp_ms": 1726617600000,
        "sequence": 48,
        "sensors": {"temperature_c": 25.0},
        "availability": {"temperature": True},
        "power": {"battery_pct": 85}
    }

    received_timestamp = datetime(2026, 9, 17, 18, 0, 7, tzinfo=timezone.utc)

    canonical, error = await normalizer.normalize_hardware_json(
        hardware_json, received_timestamp
    )

    assert error is None
    assert canonical["location"]["alt"] == 920.0

    # NODE-002 has no altitude
    hardware_json["node_id"] = "NODE-002"
    hardware_json["sequence"] = 49

    canonical, error = await normalizer.normalize_hardware_json(
        hardware_json, received_timestamp
    )

    assert error is None
    assert canonical["location"].get("alt") is None


@pytest.mark.asyncio
async def test_normalize_all_sensor_types(valid_node_registry):
    """Test normalization with all sensor types"""
    normalizer = Track3CNormalizer(valid_node_registry)

    hardware_json = {
        "node_id": "NODE-001",
        "timestamp_ms": 1726617600000,
        "sequence": 50,
        "sensors": {
            "temperature_c": 30.5,
            "humidity_rh": 65.0,
            "pressure_hpa": 1013.25,
            "gas_ppm": 1500,
            "vibration_mps2": 0.08,
            "pm25_ugm3": 35.2,
            "pm10_ugm3": 50.1,
            "water_level_m": 1.2,
            "rainfall_mm_h": 5.5,
            "soil_moisture_vwc_pct": 25.0
        },
        "availability": {
            "temperature": True,
            "humidity": True,
            "pressure": True,
            "gas": True,
            "vibration": True,
            "pm25": True,
            "pm10": True,
            "water_level": True,
            "rainfall": True,
            "soil_moisture": True
        },
        "power": {
            "battery_pct": 95,
            "solar_state": "CHARGING"
        }
    }

    received_timestamp = datetime(2026, 9, 17, 18, 0, 8, tzinfo=timezone.utc)

    canonical, error = await normalizer.normalize_hardware_json(
        hardware_json, received_timestamp
    )

    assert error is None
    assert canonical is not None

    measurements = canonical["measurements"]
    assert measurements["temp_c"] == 30.5
    assert measurements["humidity_pct"] == 65.0
    assert measurements["pressure_hpa"] == 1013.25
    assert measurements["gas_adc"] == 1500
    assert measurements["vibration_mps2"] == 0.08
    assert measurements["pm25_ug_m3"] == 35.2
    assert measurements["pm10_ug_m3"] == 50.1
    assert measurements["water_level_m"] == 1.2
    assert measurements["rainfall_mm_h"] == 5.5
    assert measurements["soil_moisture_vwc_pct"] == 25.0

    # All sensors available
    avail = canonical["diagnostics"]["sensor_availability"]
    assert avail["temperature"] is True
    assert avail["humidity"] is True
    assert avail["gas"] is True
    assert avail["pm25"] is True
    assert avail["water_level"] is True
    assert avail["soil_moisture"] is True
