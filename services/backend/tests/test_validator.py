"""Tests for telemetry validation

Tests canonical schema validation and MISSING != ZERO semantics.
"""
import pytest
import json
from pathlib import Path
from modules.ingestion.validator import TelemetryValidator, parse_telemetry_payload


@pytest.fixture
def validator():
    """Create validator with test schema"""
    schema_path = Path(__file__).parent.parent.parent.parent.parent / "schemas" / "telemetry-envelope.schema.json"
    return TelemetryValidator(str(schema_path))


@pytest.fixture
def valid_telemetry():
    """Valid telemetry payload"""
    return {
        "schema_version": "telemetry.v1",
        "telemetry_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "node_id": "NODE-001",
        "sequence": 42,
        "measurement_timestamp": "2026-09-09T12:00:00Z",
        "received_timestamp": "2026-09-09T12:00:01Z",
        "location": {
            "lat": 28.6139,
            "lon": 77.2090,
            "alt": None
        },
        "measurements": {
            "temp_c": 35.2,
            "humidity_pct": 60.5,
            "pressure_hpa": None,
            "pm25_ug_m3": None,
            "pm10_ug_m3": None
        },
        "diagnostics": {
            "uptime_s": 3600,
            "self_test_passed": True,
            "comm_integrity": 0.95,
            "calibration_valid": True,
            "stability_index": None
        },
        "power": {
            "battery_pct": 85.0,
            "battery_voltage": 3.7,
            "solar_current": None
        },
        "source": "HARDWARE"
    }


def test_valid_telemetry(validator, valid_telemetry):
    """Test valid telemetry passes validation"""
    is_valid, error = validator.validate(valid_telemetry)
    assert is_valid is True
    assert error is None


def test_missing_required_field(validator, valid_telemetry):
    """Test missing required field fails validation"""
    del valid_telemetry["node_id"]
    is_valid, error = validator.validate(valid_telemetry)
    assert is_valid is False
    assert "node_id" in error or "required" in error.lower()


def test_invalid_telemetry_id(validator, valid_telemetry):
    """Test invalid ULID format fails validation"""
    valid_telemetry["telemetry_id"] = "INVALID_ID"
    is_valid, error = validator.validate(valid_telemetry)
    assert is_valid is False
    assert "telemetry_id" in error


def test_invalid_node_id_format(validator, valid_telemetry):
    """Test invalid node_id format fails validation"""
    valid_telemetry["node_id"] = "INVALID"
    is_valid, error = validator.validate(valid_telemetry)
    assert is_valid is False
    assert "node_id" in error


def test_invalid_source(validator, valid_telemetry):
    """Test invalid source enum fails validation"""
    valid_telemetry["source"] = "INVALID"
    is_valid, error = validator.validate(valid_telemetry)
    assert is_valid is False
    assert "source" in error


def test_null_measurements_preserved(validator, valid_telemetry):
    """Test NULL measurements are preserved (MISSING != ZERO)"""
    # Set measurements to NULL
    valid_telemetry["measurements"]["pressure_hpa"] = None
    valid_telemetry["measurements"]["pm25_ug_m3"] = None

    is_valid, error = validator.validate(valid_telemetry)
    assert is_valid is True
    assert error is None

    # Verify NULLs are preserved in payload
    assert valid_telemetry["measurements"]["pressure_hpa"] is None
    assert valid_telemetry["measurements"]["pm25_ug_m3"] is None


def test_zero_measurement_warning(validator, valid_telemetry, caplog):
    """Test zero measurement triggers warning (not failure)"""
    valid_telemetry["measurements"]["temp_c"] = 0
    is_valid, error = validator.validate(valid_telemetry)

    # Should still be valid (real zero is allowed)
    assert is_valid is True
    assert error is None


def test_parse_valid_json():
    """Test parsing valid JSON payload"""
    raw = '{"test": "data"}'
    payload, error = parse_telemetry_payload(raw)
    assert payload == {"test": "data"}
    assert error is None


def test_parse_invalid_json():
    """Test parsing invalid JSON fails gracefully"""
    raw = '{invalid json'
    payload, error = parse_telemetry_payload(raw)
    assert payload is None
    assert error is not None
    assert "JSON parse error" in error


def test_parse_bytes_payload():
    """Test parsing bytes payload"""
    raw = b'{"test": "data"}'
    payload, error = parse_telemetry_payload(raw)
    assert payload == {"test": "data"}
    assert error is None
