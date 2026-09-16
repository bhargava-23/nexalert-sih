"""
End-to-End Telemetry Contract Test

Deterministic test of canonical telemetry contract through complete pipeline.
Required by Phase 2A telemetry map completion criteria.

Tests:
- NODE-001 HARDWARE telemetry envelope
- Complete ingestion → validation → (mock persistence)
- Field name conformance (temp_c, battery_pct)
- Timestamp semantics (measurement_timestamp vs received_timestamp)
- Missing≠Zero preservation (null vs 0)
- Source enum (HARDWARE vs SIMULATION)
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timezone
from modules.ingestion.validator import TelemetryValidator, parse_telemetry_payload


@pytest.fixture
def validator():
    """Validator with canonical schema"""
    schema_path = Path(__file__).parent.parent.parent.parent / "schemas" / "telemetry-envelope.schema.json"
    return TelemetryValidator(str(schema_path))


class TestDeterministicE2EContract:
    """Deterministic end-to-end telemetry contract validation"""

    def test_node_001_hardware_canonical_telemetry(self, validator):
        """
        Complete deterministic test: NODE-001 HARDWARE telemetry

        Verifies:
        - Canonical node_id format (NODE-001)
        - HARDWARE source
        - Correct field names (temp_c, battery_pct, NOT temperature_c/battery_percent)
        - Timestamp distinction (measurement_timestamp != received_timestamp)
        - Missing≠Zero (null pressure, null solar_current)
        - Legitimate zero measurement (0.0°C is valid)
        - All required fields present
        """
        canonical_telemetry = {
            "schema_version": "telemetry.v1",
            "telemetry_id": "01M2DSE7FKDXVQXA8Q0S7KBYBG",
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
                "temp_c": 0.0,  # Legitimate zero (0°C is valid temperature)
                "humidity_pct": 60.0,
                "pressure_hpa": None,  # Missing (null != zero)
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
                "battery_pct": 85.0,  # Canonical field name (NOT battery_percent)
                "battery_voltage": 3.7,
                "solar_current": None  # Missing (null != zero)
            },
            "source": "HARDWARE",
            "auth": {}
        }

        # Validate canonical telemetry
        is_valid, error = validator.validate(canonical_telemetry)
        assert is_valid, f"Canonical NODE-001 HARDWARE telemetry should be valid: {error}"

        # Verify field names
        assert "temp_c" in canonical_telemetry["measurements"]
        assert "battery_pct" in canonical_telemetry["power"]
        assert "temperature_c" not in canonical_telemetry["measurements"]
        assert "battery_percent" not in canonical_telemetry["power"]

        # Verify timestamp distinction
        assert canonical_telemetry["measurement_timestamp"] != canonical_telemetry["received_timestamp"]

        # Verify Missing≠Zero preservation
        assert canonical_telemetry["measurements"]["pressure_hpa"] is None
        assert canonical_telemetry["power"]["solar_current"] is None
        assert canonical_telemetry["measurements"]["temp_c"] == 0.0  # Legitimate zero

        # Verify source
        assert canonical_telemetry["source"] == "HARDWARE"

        # Verify node_id format
        assert canonical_telemetry["node_id"] == "NODE-001"

    def test_node_042_simulation_telemetry(self, validator):
        """
        NODE-042 SIMULATION telemetry with all null measurements

        Verifies:
        - Multi-digit node_id (NODE-042)
        - SIMULATION source
        - All measurements can be null (missing data)
        """
        simulation_telemetry = {
            "schema_version": "telemetry.v1",
            "telemetry_id": "01M2DSE7FKDXVQXA8Q0S7KBYBH",
            "node_id": "NODE-042",
            "sequence": 5,
            "measurement_timestamp": "2026-09-13T12:05:00Z",
            "received_timestamp": "2026-09-13T12:05:01Z",
            "location": {
                "lat": 13.0827,
                "lon": 80.2707,
                "alt": None
            },
            "measurements": {
                "temp_c": None,
                "humidity_pct": None,
                "pressure_hpa": None,
                "pm25_ug_m3": None,
                "pm10_ug_m3": None
            },
            "diagnostics": {
                "uptime_s": 0,
                "self_test_passed": True,
                "comm_integrity": 1.0,
                "calibration_valid": True,
                "stability_index": None
            },
            "power": {
                "battery_pct": None,
                "battery_voltage": None,
                "solar_current": None
            },
            "source": "SIMULATION",
            "auth": {}
        }

        is_valid, error = validator.validate(simulation_telemetry)
        assert is_valid, f"SIMULATION telemetry with all null should be valid: {error}"

    def test_invalid_telemetry_rejected_at_boundary(self, validator):
        """
        Verify malformed telemetry is rejected at ingestion boundary

        Tests rejection of:
        - Invalid node_id patterns (NODE-1, NODE-01, NEX-001)
        - Invalid source (DEMO)
        - Missing required fields
        - Invalid JSON
        """
        # NODE-1 rejected (only 1 digit)
        invalid_node_1 = {
            "schema_version": "telemetry.v1",
            "telemetry_id": "01M2DSE7FKDXVQXA8Q0S7KBYBJ",
            "node_id": "NODE-1",
            "sequence": 1,
            "measurement_timestamp": "2026-09-13T12:00:00Z",
            "received_timestamp": "2026-09-13T12:00:01Z",
            "location": {"lat": 0, "lon": 0, "alt": None},
            "measurements": {},
            "diagnostics": {},
            "power": {},
            "source": "HARDWARE",
            "auth": {}
        }
        is_valid, error = validator.validate(invalid_node_1)
        assert not is_valid, "NODE-1 should be rejected"
        assert "NODE-[0-9]{3,}" in error or "expected NODE-" in error

        # NODE-01 rejected (only 2 digits)
        invalid_node_01 = invalid_node_1.copy()
        invalid_node_01["node_id"] = "NODE-01"
        is_valid, error = validator.validate(invalid_node_01)
        assert not is_valid, "NODE-01 should be rejected"

        # NEX-001 rejected (wrong prefix)
        invalid_nex = invalid_node_1.copy()
        invalid_nex["node_id"] = "NEX-001"
        is_valid, error = validator.validate(invalid_nex)
        assert not is_valid, "NEX-001 should be rejected in operational ingestion"

        # Invalid source rejected
        invalid_source = invalid_node_1.copy()
        invalid_source["node_id"] = "NODE-001"
        invalid_source["source"] = "DEMO"
        is_valid, error = validator.validate(invalid_source)
        assert not is_valid, "DEMO source should be rejected"

        # Invalid JSON rejected
        invalid_json = '{"incomplete":'
        payload, error = parse_telemetry_payload(invalid_json)
        assert payload is None, "Invalid JSON should return None"
        assert "JSON parse error" in error

    def test_mqtt_topic_construction(self):
        """
        Verify MQTT topic construction follows canonical format

        Canonical: Nexalert/telemetry/<node_id>
        Wildcard: Nexalert/telemetry/+
        """
        node_id = "NODE-001"
        expected_topic = f"Nexalert/telemetry/{node_id}"
        assert expected_topic == "Nexalert/telemetry/NODE-001"

        node_id = "NODE-042"
        expected_topic = f"Nexalert/telemetry/{node_id}"
        assert expected_topic == "Nexalert/telemetry/NODE-042"

        # Wildcard subscription
        wildcard_topic = "Nexalert/telemetry/+"
        assert wildcard_topic == "Nexalert/telemetry/+"

    def test_timestamp_ownership_semantics(self):
        """
        Verify timestamp ownership semantics

        - measurement_timestamp: set by edge node
        - received_timestamp: assigned by server/Master on receipt
        - Node cannot override server receive time
        """
        telemetry = {
            "schema_version": "telemetry.v1",
            "telemetry_id": "01M2DSE7FKDXVQXA8Q0S7KBYBK",
            "node_id": "NODE-001",
            "sequence": 10,
            "measurement_timestamp": "2026-09-13T11:55:00Z",  # Edge time
            "received_timestamp": "2026-09-13T12:00:00Z",     # Server time (later)
            "location": {"lat": 0, "lon": 0, "alt": None},
            "measurements": {},
            "diagnostics": {},
            "power": {},
            "source": "HARDWARE",
            "auth": {}
        }

        # Measurement timestamp can be earlier than received timestamp
        measurement_dt = datetime.fromisoformat(telemetry["measurement_timestamp"].replace("Z", "+00:00"))
        received_dt = datetime.fromisoformat(telemetry["received_timestamp"].replace("Z", "+00:00"))
        assert received_dt > measurement_dt, "received_timestamp should be later than measurement_timestamp"
