"""
GV-E01: Evidence golden vectors.

Specification: Document 04, Sections 6.1-6.4
Validates E_h reference implementation against deterministic test cases.

PHASE 5 ITERATION 4: Hazard-specific evidence computation.
"""

import json
import pytest
from pathlib import Path

# Import reference implementation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "reference" / "python"))

from nexalert_reference.evidence import compute_evidence


# Fixture for loading golden vectors
@pytest.fixture
def load_gv():
    """Load golden vector input and expected output."""
    def _load(name: str):
        base_path = Path(__file__).parent
        input_path = base_path / "inputs" / f"{name}.json"
        expected_path = base_path / "expected" / f"{name}.json"

        with open(input_path) as f:
            input_data = json.load(f)
        with open(expected_path) as f:
            expected_data = json.load(f)

        return input_data, expected_data
    return _load


# Fixture for close comparison with tolerance
@pytest.fixture
def assert_close():
    """Assert two float values are close within tolerance."""
    def _assert_close(actual, expected, rtol=1e-6, atol=1e-9):
        if expected is None:
            assert actual is None, f"Expected None but got {actual}"
        else:
            assert actual is not None, f"Expected {expected} but got None"
            diff = abs(actual - expected)
            tolerance = atol + rtol * abs(expected)
            assert diff <= tolerance, f"Expected {expected}, got {actual}, diff {diff} > tolerance {tolerance}"
    return _assert_close


# Test cases

def test_GV_E01_fire_nominal(load_gv, assert_close):
    """GV-E01-1: Nominal fire evidence with both core sensors matching."""
    input_data, expected_data = load_gv("GV_E01_fire_nominal")

    e_h = compute_evidence(
        hazard_type=input_data["hazard_type"],
        sensor_readings=input_data["sensor_readings"],
        evidence_config=input_data["evidence_config"]
    )

    assert_close(e_h, expected_data["E_h"])


def test_GV_E01_fire_core_missing(load_gv, assert_close):
    """GV-E01-2: One core sensor missing - core floor applied."""
    input_data, expected_data = load_gv("GV_E01_fire_core_missing")

    e_h = compute_evidence(
        hazard_type=input_data["hazard_type"],
        sensor_readings=input_data["sensor_readings"],
        evidence_config=input_data["evidence_config"]
    )

    assert_close(e_h, expected_data["E_h"])


def test_GV_E01_fire_supporting_only(load_gv, assert_close):
    """GV-E01-3: Only supporting evidence, no core - heavily capped."""
    input_data, expected_data = load_gv("GV_E01_fire_supporting_only")

    e_h = compute_evidence(
        hazard_type=input_data["hazard_type"],
        sensor_readings=input_data["sensor_readings"],
        evidence_config=input_data["evidence_config"]
    )

    assert_close(e_h, expected_data["E_h"])


def test_GV_E01_fire_all_missing(load_gv, assert_close):
    """GV-E01-4: All sensors missing - returns None."""
    input_data, expected_data = load_gv("GV_E01_fire_all_missing")

    e_h = compute_evidence(
        hazard_type=input_data["hazard_type"],
        sensor_readings=input_data["sensor_readings"],
        evidence_config=input_data["evidence_config"]
    )

    assert_close(e_h, expected_data["E_h"])


def test_GV_E01_fire_threshold_boundary(load_gv, assert_close):
    """GV-E01-5: Sensor exactly at threshold boundary."""
    input_data, expected_data = load_gv("GV_E01_fire_threshold_boundary")

    e_h = compute_evidence(
        hazard_type=input_data["hazard_type"],
        sensor_readings=input_data["sensor_readings"],
        evidence_config=input_data["evidence_config"]
    )

    assert_close(e_h, expected_data["E_h"])


def test_GV_E01_flood_nominal(load_gv, assert_close):
    """GV-E01-6: Nominal flood evidence."""
    input_data, expected_data = load_gv("GV_E01_flood_nominal")

    e_h = compute_evidence(
        hazard_type=input_data["hazard_type"],
        sensor_readings=input_data["sensor_readings"],
        evidence_config=input_data["evidence_config"]
    )

    assert_close(e_h, expected_data["E_h"])


def test_GV_E01_multi_hazard(load_gv, assert_close):
    """GV-E01-7: Multi-hazard independence - same telemetry, different E_h."""
    input_data, expected_data = load_gv("GV_E01_multi_hazard")

    # Fire evidence
    fire_e_h = compute_evidence(
        hazard_type="fire",
        sensor_readings=input_data["sensor_readings"],
        evidence_config=input_data["fire_config"]
    )

    # Flood evidence
    flood_e_h = compute_evidence(
        hazard_type="flood",
        sensor_readings=input_data["sensor_readings"],
        evidence_config=input_data["flood_config"]
    )

    assert_close(fire_e_h, expected_data["fire_E_h"])
    assert_close(flood_e_h, expected_data["flood_E_h"])


def test_GV_E01_core_floor_applied(load_gv, assert_close):
    """GV-E01-8: Core coverage at minimum threshold."""
    input_data, expected_data = load_gv("GV_E01_core_floor_applied")

    e_h = compute_evidence(
        hazard_type=input_data["hazard_type"],
        sensor_readings=input_data["sensor_readings"],
        evidence_config=input_data["evidence_config"]
    )

    assert_close(e_h, expected_data["E_h"])


def test_GV_E01_partial_match(load_gv, assert_close):
    """GV-E01-9: Some sensors match thresholds, some don't."""
    input_data, expected_data = load_gv("GV_E01_partial_match")

    e_h = compute_evidence(
        hazard_type=input_data["hazard_type"],
        sensor_readings=input_data["sensor_readings"],
        evidence_config=input_data["evidence_config"]
    )

    assert_close(e_h, expected_data["E_h"])


def test_GV_E01_zero_denominator(load_gv, assert_close):
    """GV-E01-10: No sensors configured for hazard."""
    input_data, expected_data = load_gv("GV_E01_zero_denominator")

    e_h = compute_evidence(
        hazard_type=input_data["hazard_type"],
        sensor_readings=input_data["sensor_readings"],
        evidence_config=input_data["evidence_config"]
    )

    assert_close(e_h, expected_data["E_h"])
