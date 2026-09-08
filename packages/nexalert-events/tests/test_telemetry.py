"""Tests for telemetry envelope schema."""
import pytest
from datetime import datetime, timezone
from nexalert_events.telemetry import (
    TelemetryEnvelope,
    TelemetrySource,
    Location,
    Measurements,
    Diagnostics,
    Power
)


def test_valid_telemetry_envelope():
    """Test valid telemetry envelope parses correctly."""
    envelope = TelemetryEnvelope(
        telemetry_id="01JAAAAAAAAAAAAAAAAAAA0000",
        node_id="NODE-001",
        sequence=42,
        measurement_timestamp=datetime(2026, 9, 7, 7, 45, 18, tzinfo=timezone.utc),
        received_timestamp=datetime(2026, 9, 7, 7, 45, 19, tzinfo=timezone.utc),
        location=Location(lat=13.12, lon=77.58, alt=920.0),
        measurements=Measurements(temperature_c=42.1, pm25_ug_m3=182.0),
        diagnostics=Diagnostics(uptime_s=88211),
        power=Power(battery_percent=71.0),
        source=TelemetrySource.SIMULATION
    )

    assert envelope.telemetry_id == "01JAAAAAAAAAAAAAAAAAAA0000"
    assert envelope.node_id == "NODE-001"
    assert envelope.sequence == 42
    assert envelope.source == TelemetrySource.SIMULATION
    assert envelope.schema_version == "telemetry.v1"


def test_missing_not_zero_measurements():
    """Test that None in measurements is preserved (missing != zero)."""
    measurements = Measurements(temperature_c=25.0, humidity_pct=None)

    assert measurements.temperature_c == 25.0
    assert measurements.humidity_pct is None  # None preserved, not coerced to 0


def test_missing_not_zero_location_alt():
    """Test that None altitude is preserved (missing != zero)."""
    location = Location(lat=13.12, lon=77.58, alt=None)

    assert location.alt is None  # None preserved, not coerced to 0


def test_measurement_timestamp_not_receive_timestamp():
    """Test that measurement_timestamp and received_timestamp are distinct."""
    measurement_ts = datetime(2026, 9, 7, 7, 45, 18, tzinfo=timezone.utc)
    receive_ts = datetime(2026, 9, 7, 7, 45, 19, tzinfo=timezone.utc)

    envelope = TelemetryEnvelope(
        telemetry_id="01JAAAAAAAAAAAAAAAAAAA0001",
        node_id="NODE-002",
        sequence=1,
        measurement_timestamp=measurement_ts,
        received_timestamp=receive_ts,
        location=Location(lat=0, lon=0),
        measurements=Measurements(),
        diagnostics=Diagnostics(),
        power=Power(),
        source=TelemetrySource.HARDWARE
    )

    assert envelope.measurement_timestamp != envelope.received_timestamp
    assert envelope.received_timestamp > envelope.measurement_timestamp


def test_source_enum_validation():
    """Test source enum validates correctly."""
    with pytest.raises(ValueError):
        TelemetryEnvelope(
            telemetry_id="01JAAAAAAAAAAAAAAAAAAA0002",
            node_id="NODE-003",
            sequence=1,
            measurement_timestamp=datetime.now(timezone.utc),
            receive_timestamp=datetime.now(timezone.utc),
            location=Location(lat=0, lon=0),
            measurements=Measurements(),
            diagnostics=Diagnostics(),
            power=Power(),
            source="INVALID_SOURCE"  # type: ignore
        )


def test_location_bounds_validation():
    """Test location latitude/longitude bounds."""
    # Valid bounds
    location = Location(lat=-90, lon=-180)
    assert location.lat == -90
    assert location.lon == -180

    location = Location(lat=90, lon=180)
    assert location.lat == 90
    assert location.lon == 180

    # Invalid latitude
    with pytest.raises(ValueError):
        Location(lat=91, lon=0)

    # Invalid longitude
    with pytest.raises(ValueError):
        Location(lat=0, lon=181)


def test_diagnostics_ranges():
    """Test diagnostic dimension ranges [0,1]."""
    # Valid ranges
    diag = Diagnostics(comm_integrity=0.0, stability_index=1.0)
    assert diag.comm_integrity == 0.0
    assert diag.stability_index == 1.0

    # Invalid range
    with pytest.raises(ValueError):
        Diagnostics(comm_integrity=1.5)
