"""
Schema synchronization tests.

Validates that Python Pydantic models synchronize with the authoritative JSON Schema.

Specification: Document 07, Section 7 + Phase 4 Plan Section 1.2
Authoritative Schema: schemas/telemetry-envelope.schema.json
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timezone
import jsonschema
from nexalert_events.telemetry import (
    TelemetryEnvelope,
    TelemetrySource,
    Location,
    Measurements,
    Diagnostics,
    Power
)


@pytest.fixture
def authoritative_schema():
    """Load the authoritative JSON Schema."""
    schema_path = Path(__file__).parents[3] / "schemas" / "telemetry-envelope.schema.json"
    with open(schema_path) as f:
        return json.load(f)


def test_schema_file_exists():
    """Verify authoritative schema file exists."""
    schema_path = Path(__file__).parents[3] / "schemas" / "telemetry-envelope.schema.json"
    assert schema_path.exists(), "Authoritative schema must exist at schemas/telemetry-envelope.schema.json"


def test_valid_envelope_validates_against_schema(authoritative_schema):
    """Test that a valid Pydantic envelope validates against authoritative schema."""
    envelope = TelemetryEnvelope(
        telemetry_id="01JAAAAAAAAAAAAAAAAAAA0000",
        node_id="NODE-001",
        sequence=42,
        measurement_timestamp=datetime(2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc),
        received_timestamp=datetime(2026, 9, 8, 10, 0, 1, tzinfo=timezone.utc),
        location=Location(lat=13.12, lon=77.58, alt=920.0),
        measurements=Measurements(temperature_c=25.5, pm25_ug_m3=45.0),
        diagnostics=Diagnostics(uptime_s=1234, comm_integrity=0.95),
        power=Power(battery_percent=85.0),
        source=TelemetrySource.HARDWARE
    )

    # Convert Pydantic model to dict for JSON Schema validation
    envelope_dict = json.loads(envelope.model_dump_json())

    # Validate against authoritative schema
    jsonschema.validate(instance=envelope_dict, schema=authoritative_schema)


def test_missing_fields_validate_as_null(authoritative_schema):
    """Test that missing/None fields validate correctly against schema."""
    envelope = TelemetryEnvelope(
        telemetry_id="01JAAAAAAAAAAAAAAAAAAA0001",
        node_id="NODE-002",
        sequence=1,
        measurement_timestamp=datetime(2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc),
        received_timestamp=datetime(2026, 9, 8, 10, 0, 1, tzinfo=timezone.utc),
        location=Location(lat=0, lon=0, alt=None),  # alt is None
        measurements=Measurements(temperature_c=None, humidity_pct=None),  # Missing measurements
        diagnostics=Diagnostics(),  # All diagnostics missing
        power=Power(),  # All power fields missing
        source=TelemetrySource.SIMULATION
    )

    envelope_dict = json.loads(envelope.model_dump_json())

    # Validate against authoritative schema
    jsonschema.validate(instance=envelope_dict, schema=authoritative_schema)


def test_schema_version_matches(authoritative_schema):
    """Test that schema_version constant matches."""
    assert authoritative_schema["properties"]["schema_version"]["const"] == "telemetry.v1"

    envelope = TelemetryEnvelope(
        telemetry_id="01JAAAAAAAAAAAAAAAAAAA0002",
        node_id="NODE-003",
        sequence=1,
        measurement_timestamp=datetime(2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc),
        received_timestamp=datetime(2026, 9, 8, 10, 0, 1, tzinfo=timezone.utc),
        location=Location(lat=0, lon=0),
        measurements=Measurements(),
        diagnostics=Diagnostics(),
        power=Power(),
        source=TelemetrySource.HARDWARE
    )

    assert envelope.schema_version == "telemetry.v1"


def test_source_enum_matches(authoritative_schema):
    """Test that source enum values match."""
    schema_source_enum = authoritative_schema["properties"]["source"]["enum"]
    assert set(schema_source_enum) == {"HARDWARE", "SIMULATION"}

    # Verify Python enum matches
    assert TelemetrySource.HARDWARE.value == "HARDWARE"
    assert TelemetrySource.SIMULATION.value == "SIMULATION"


def test_required_fields_match(authoritative_schema):
    """Test that required fields in schema match Pydantic model."""
    schema_required = set(authoritative_schema["required"])
    expected_required = {
        "schema_version",
        "telemetry_id",
        "node_id",
        "sequence",
        "measurement_timestamp",
        "received_timestamp",
        "location",
        "measurements",
        "diagnostics",
        "power",
        "source"
    }

    assert schema_required == expected_required, f"Required fields mismatch: {schema_required ^ expected_required}"


def test_location_bounds_match(authoritative_schema):
    """Test that location bounds match between schema and Python."""
    loc_props = authoritative_schema["properties"]["location"]["properties"]

    assert loc_props["lat"]["minimum"] == -90
    assert loc_props["lat"]["maximum"] == 90
    assert loc_props["lon"]["minimum"] == -180
    assert loc_props["lon"]["maximum"] == 180

    # Verify Pydantic validates these bounds
    with pytest.raises(ValueError):
        Location(lat=91, lon=0)

    with pytest.raises(ValueError):
        Location(lat=0, lon=181)


def test_diagnostics_range_match(authoritative_schema):
    """Test that diagnostic ranges match between schema and Python."""
    diag_props = authoritative_schema["properties"]["diagnostics"]["properties"]

    assert diag_props["comm_integrity"]["minimum"] == 0
    assert diag_props["comm_integrity"]["maximum"] == 1
    assert diag_props["stability_index"]["minimum"] == 0
    assert diag_props["stability_index"]["maximum"] == 1

    # Verify Pydantic validates these ranges
    with pytest.raises(ValueError):
        Diagnostics(comm_integrity=1.5)

    with pytest.raises(ValueError):
        Diagnostics(stability_index=-0.1)


def test_telemetry_id_pattern_match(authoritative_schema):
    """Test that telemetry_id pattern is documented (ULID)."""
    pattern = authoritative_schema["properties"]["telemetry_id"]["pattern"]
    assert pattern == "^[0-9A-HJKMNP-TV-Z]{26}$", "telemetry_id should use ULID pattern"


def test_node_id_pattern_match(authoritative_schema):
    """Test that node_id pattern matches."""
    pattern = authoritative_schema["properties"]["node_id"]["pattern"]
    assert pattern == "^NODE-[0-9]{3,}$"
