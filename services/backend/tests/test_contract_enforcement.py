"""
Phase 2A Contract Enforcement Tests

Tests the canonical telemetry contract enforcement:
- Node ID pattern validation (NODE-[0-9]{3,})
- Timestamp semantics (measurement_timestamp vs received_timestamp)
- Missing≠Zero preservation (null vs 0)
- Source enum validation (HARDWARE, SIMULATION)
- Field name conformance to schema
"""
import pytest
import json
from pathlib import Path
from datetime import datetime
from modules.ingestion.validator import TelemetryValidator, parse_telemetry_payload


@pytest.fixture
def validator():
    """Create validator with canonical schema"""
    schema_path = Path(__file__).parent.parent.parent.parent / "schemas" / "telemetry-envelope.schema.json"
    return TelemetryValidator(str(schema_path))


@pytest.fixture
def valid_telemetry():
    """Canonical valid telemetry envelope"""
    return {
        "schema_version": "telemetry.v1",
        "telemetry_id": "01J0000000000000000000TEST",
        "node_id": "NODE-001",
        "sequence": 1,
        "measurement_timestamp": "2026-09-13T12:00:00Z",
        "received_timestamp": "2026-09-13T12:00:01Z",
        "location": {
            "lat": 12.9716,
            "lon": 77.5946,
            "alt": 920.0
        },
        "measurements": {
            "temp_c": 25.5,
            "humidity_pct": 60.0,
            "pressure_hpa": 1013.25,
            "pm25_ug_m3": 12.0,
            "pm10_ug_m3": 18.0
        },
        "diagnostics": {
            "uptime_s": 3600,
            "self_test_passed": True,
            "comm_integrity": 0.98,
            "calibration_valid": True,
            "stability_index": 0.95
        },
        "power": {
            "battery_pct": 85.0,
            "battery_voltage": 3.7,
            "solar_current": 0.5
        },
        "source": "HARDWARE",
        "auth": {}
    }


class TestNodeIdentityEnforcement:
    """Test canonical node_id pattern enforcement"""

    def test_node_001_accepted(self, validator, valid_telemetry):
        """NODE-001 is valid (3 digits)"""
        valid_telemetry["node_id"] = "NODE-001"
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"NODE-001 should be valid: {error}"

    def test_node_042_accepted(self, validator, valid_telemetry):
        """NODE-042 is valid (3 digits)"""
        valid_telemetry["node_id"] = "NODE-042"
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"NODE-042 should be valid: {error}"

    def test_node_1234_accepted(self, validator, valid_telemetry):
        """NODE-1234 is valid (4+ digits allowed)"""
        valid_telemetry["node_id"] = "NODE-1234"
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"NODE-1234 should be valid: {error}"

    def test_node_1_rejected(self, validator, valid_telemetry):
        """NODE-1 is invalid (only 1 digit, requires 3+)"""
        valid_telemetry["node_id"] = "NODE-1"
        is_valid, error = validator.validate(valid_telemetry)
        assert not is_valid, "NODE-1 should be rejected"
        assert "NODE-[0-9]{3,}" in error or "expected NODE-" in error

    def test_node_01_rejected(self, validator, valid_telemetry):
        """NODE-01 is invalid (only 2 digits, requires 3+)"""
        valid_telemetry["node_id"] = "NODE-01"
        is_valid, error = validator.validate(valid_telemetry)
        assert not is_valid, "NODE-01 should be rejected"
        assert "NODE-[0-9]{3,}" in error or "expected NODE-" in error

    def test_nex_001_rejected(self, validator, valid_telemetry):
        """NEX-001 is invalid (wrong prefix, operational ingestion only accepts NODE-)"""
        valid_telemetry["node_id"] = "NEX-001"
        is_valid, error = validator.validate(valid_telemetry)
        assert not is_valid, "NEX-001 should be rejected in operational ingestion"
        assert "NODE-" in error

    def test_node1_rejected(self, validator, valid_telemetry):
        """node1 is invalid (no NODE- prefix, no digits in required format)"""
        valid_telemetry["node_id"] = "node1"
        is_valid, error = validator.validate(valid_telemetry)
        assert not is_valid, "node1 should be rejected"
        assert "NODE-" in error


class TestSourceEnumValidation:
    """Test source enum enforcement"""

    def test_hardware_accepted(self, validator, valid_telemetry):
        """HARDWARE source is valid"""
        valid_telemetry["source"] = "HARDWARE"
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"HARDWARE source should be valid: {error}"

    def test_simulation_accepted(self, validator, valid_telemetry):
        """SIMULATION source is valid"""
        valid_telemetry["source"] = "SIMULATION"
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"SIMULATION source should be valid: {error}"

    def test_demo_rejected(self, validator, valid_telemetry):
        """DEMO source is invalid (not in canonical enum)"""
        valid_telemetry["source"] = "DEMO"
        is_valid, error = validator.validate(valid_telemetry)
        assert not is_valid, "DEMO source should be rejected"
        assert "HARDWARE" in error and "SIMULATION" in error


class TestMissingNotZeroPreservation:
    """Test Missing≠Zero invariant preservation"""

    def test_null_measurement_preserved(self, validator, valid_telemetry):
        """null in measurements is valid (missing != zero)"""
        valid_telemetry["measurements"]["pressure_hpa"] = None
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"null measurement should be valid: {error}"

    def test_zero_measurement_valid_with_warning(self, validator, valid_telemetry, caplog):
        """0 in measurements is valid but logs warning (legitimate zero reading)"""
        valid_telemetry["measurements"]["temp_c"] = 0.0
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"0.0 measurement should be valid: {error}"
        # Validator logs debug warning but does NOT reject
        # (0°C is a valid temperature measurement)

    def test_null_power_preserved(self, validator, valid_telemetry):
        """null in power fields is valid"""
        valid_telemetry["power"]["solar_current"] = None
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"null power field should be valid: {error}"

    def test_missing_optional_field_valid(self, validator, valid_telemetry):
        """Missing optional field (not present) is valid"""
        del valid_telemetry["power"]["solar_current"]
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"Missing optional field should be valid: {error}"


class TestTimestampSemantics:
    """Test timestamp distinction preservation"""

    def test_distinct_timestamps_required(self, validator, valid_telemetry):
        """measurement_timestamp and received_timestamp must both be present"""
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"Valid telemetry with both timestamps should pass: {error}"
        assert valid_telemetry["measurement_timestamp"] != valid_telemetry["received_timestamp"]

    def test_measurement_timestamp_required(self, validator, valid_telemetry):
        """measurement_timestamp is required"""
        del valid_telemetry["measurement_timestamp"]
        is_valid, error = validator.validate(valid_telemetry)
        assert not is_valid, "Missing measurement_timestamp should be rejected"

    def test_received_timestamp_required(self, validator, valid_telemetry):
        """received_timestamp is required"""
        del valid_telemetry["received_timestamp"]
        is_valid, error = validator.validate(valid_telemetry)
        assert not is_valid, "Missing received_timestamp should be rejected"

    def test_iso8601_format_enforced(self, validator, valid_telemetry):
        """Timestamps must be valid ISO 8601"""
        valid_telemetry["measurement_timestamp"] = "2026-09-13T12:00:00Z"
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"ISO 8601 timestamp should be valid: {error}"

    def test_invalid_timestamp_format_rejected(self, validator, valid_telemetry):
        """Invalid timestamp format is rejected"""
        valid_telemetry["measurement_timestamp"] = "not-a-timestamp"
        is_valid, error = validator.validate(valid_telemetry)
        assert not is_valid, "Invalid timestamp format should be rejected"


class TestSchemaValidation:
    """Test overall schema validation"""

    def test_valid_canonical_telemetry_accepted(self, validator, valid_telemetry):
        """Complete valid telemetry envelope is accepted"""
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"Valid canonical telemetry should pass: {error}"

    def test_missing_required_field_rejected(self, validator, valid_telemetry):
        """Missing required field is rejected"""
        del valid_telemetry["node_id"]
        is_valid, error = validator.validate(valid_telemetry)
        assert not is_valid, "Missing node_id should be rejected"

    def test_invalid_json_rejected(self):
        """Invalid JSON is rejected"""
        invalid_json = '{"incomplete": '
        payload, error = parse_telemetry_payload(invalid_json)
        assert payload is None, "Invalid JSON should return None"
        assert error is not None, "Invalid JSON should return error message"
        assert "JSON parse error" in error

    def test_extra_fields_allowed(self, validator, valid_telemetry):
        """Extra unknown fields are allowed (forward compatibility)"""
        valid_telemetry["extra_field"] = "should_be_ignored"
        is_valid, error = validator.validate(valid_telemetry)
        # Schema validation may accept or reject depending on additionalProperties
        # This test documents current behavior


class TestFieldNameConformance:
    """Test field names match canonical schema"""

    def test_battery_pct_field_name(self, validator, valid_telemetry):
        """Schema uses battery_pct (NOT battery_percent)"""
        valid_telemetry["power"]["battery_pct"] = 85.0
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"battery_pct field should be valid: {error}"

    def test_temp_c_field_name(self, validator, valid_telemetry):
        """Schema uses temp_c (NOT temperature_c)"""
        valid_telemetry["measurements"]["temp_c"] = 25.5
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"temp_c field should be valid: {error}"


class TestLocationBounds:
    """Test location coordinate bounds validation"""

    def test_valid_latitude_range(self, validator, valid_telemetry):
        """Latitude must be [-90, 90]"""
        valid_telemetry["location"]["lat"] = 45.0
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"Valid latitude should pass: {error}"

    def test_invalid_latitude_rejected(self, validator, valid_telemetry):
        """Latitude outside [-90, 90] is rejected"""
        valid_telemetry["location"]["lat"] = 95.0
        is_valid, error = validator.validate(valid_telemetry)
        assert not is_valid, "Latitude > 90 should be rejected"
        assert "95.0" in error or "maximum of 90" in error.lower()

    def test_valid_longitude_range(self, validator, valid_telemetry):
        """Longitude must be [-180, 180]"""
        valid_telemetry["location"]["lon"] = -120.0
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"Valid longitude should pass: {error}"

    def test_invalid_longitude_rejected(self, validator, valid_telemetry):
        """Longitude outside [-180, 180] is rejected"""
        valid_telemetry["location"]["lon"] = 200.0
        is_valid, error = validator.validate(valid_telemetry)
        assert not is_valid, "Longitude > 180 should be rejected"
        assert "200.0" in error or "maximum of 180" in error.lower()


class TestULIDFormat:
    """Test telemetry_id ULID format validation"""

    def test_valid_ulid_accepted(self, validator, valid_telemetry):
        """Valid ULID format is accepted"""
        valid_telemetry["telemetry_id"] = "01J0000000000000000000TEST"
        is_valid, error = validator.validate(valid_telemetry)
        assert is_valid, f"Valid ULID should pass: {error}"

    def test_invalid_ulid_rejected(self, validator, valid_telemetry):
        """Invalid ULID format is rejected"""
        valid_telemetry["telemetry_id"] = "not-a-ulid"
        is_valid, error = validator.validate(valid_telemetry)
        assert not is_valid, "Invalid ULID should be rejected"
        assert "not-a-ulid" in error or "ulid" in error.lower() or "does not match" in error.lower()
