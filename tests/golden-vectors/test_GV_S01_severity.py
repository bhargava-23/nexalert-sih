"""
GV-S01: Severity golden vectors.

Specification: Document 04, Section 8
Validates S_h reference implementation against deterministic test cases.

PHASE 5 ITERATION 5: Severity golden vectors.
"""

import json
import pytest
from pathlib import Path

# Import reference implementation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "reference" / "python"))

from nexalert_reference.severity import compute_severity


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

def test_GV_S01_fire_nominal(load_gv, assert_close):
    """GV-S01-1: Fire with all components nominal."""
    input_data, expected_data = load_gv("GV_S01_fire_nominal")

    s_h = compute_severity(
        i_h=input_data["i_h"],
        t_h=input_data["t_h"],
        d_h=input_data["d_h"],
        weights=input_data["weights"]
    )

    assert_close(s_h, expected_data["S_h"])


def test_GV_S01_fire_high_intensity(load_gv, assert_close):
    """GV-S01-2: High intensity fire."""
    input_data, expected_data = load_gv("GV_S01_fire_high_intensity")

    s_h = compute_severity(
        i_h=input_data["i_h"],
        t_h=input_data["t_h"],
        d_h=input_data["d_h"],
        weights=input_data["weights"]
    )

    assert_close(s_h, expected_data["S_h"])


def test_GV_S01_fire_rapid_escalation(load_gv, assert_close):
    """GV-S01-3: Rapid escalation fire."""
    input_data, expected_data = load_gv("GV_S01_fire_rapid_escalation")

    s_h = compute_severity(
        i_h=input_data["i_h"],
        t_h=input_data["t_h"],
        d_h=input_data["d_h"],
        weights=input_data["weights"]
    )

    assert_close(s_h, expected_data["S_h"])


def test_GV_S01_fire_long_duration(load_gv, assert_close):
    """GV-S01-4: Long duration fire."""
    input_data, expected_data = load_gv("GV_S01_fire_long_duration")

    s_h = compute_severity(
        i_h=input_data["i_h"],
        t_h=input_data["t_h"],
        d_h=input_data["d_h"],
        weights=input_data["weights"]
    )

    assert_close(s_h, expected_data["S_h"])


def test_GV_S01_fire_intensity_only(load_gv, assert_close):
    """GV-S01-5: Intensity only, temporal and duration missing."""
    input_data, expected_data = load_gv("GV_S01_fire_intensity_only")

    s_h = compute_severity(
        i_h=input_data["i_h"],
        t_h=input_data["t_h"],
        d_h=input_data["d_h"],
        weights=input_data["weights"]
    )

    assert_close(s_h, expected_data["S_h"])


def test_GV_S01_fire_partial_missing(load_gv, assert_close):
    """GV-S01-6: One component missing - reweighting."""
    input_data, expected_data = load_gv("GV_S01_fire_partial_missing")

    s_h = compute_severity(
        i_h=input_data["i_h"],
        t_h=input_data["t_h"],
        d_h=input_data["d_h"],
        weights=input_data["weights"]
    )

    assert_close(s_h, expected_data["S_h"])


def test_GV_S01_fire_all_missing(load_gv, assert_close):
    """GV-S01-7: All components missing - returns None."""
    input_data, expected_data = load_gv("GV_S01_fire_all_missing")

    s_h = compute_severity(
        i_h=input_data["i_h"],
        t_h=input_data["t_h"],
        d_h=input_data["d_h"],
        weights=input_data["weights"]
    )

    assert_close(s_h, expected_data["S_h"])


def test_GV_S01_multi_hazard(load_gv, assert_close):
    """GV-S01-8: Multi-hazard independence - fire and flood separate."""
    input_data, expected_data = load_gv("GV_S01_multi_hazard")

    # Compute flood severity
    flood_s_h = compute_severity(
        i_h=input_data["flood_i_h"],
        t_h=input_data["flood_t_h"],
        d_h=input_data["flood_d_h"],
        weights=input_data["weights"]
    )

    # Compute fire severity
    fire_s_h = compute_severity(
        i_h=input_data["fire_i_h"],
        t_h=input_data["fire_t_h"],
        d_h=input_data["fire_d_h"],
        weights=input_data["weights"]
    )

    assert_close(flood_s_h, expected_data["flood_S_h"])
    assert_close(fire_s_h, expected_data["fire_S_h"])


def test_GV_S01_zero_weights(load_gv, assert_close):
    """GV-S01-9: Edge case with zero weight on one component."""
    input_data, expected_data = load_gv("GV_S01_zero_weights")

    s_h = compute_severity(
        i_h=input_data["i_h"],
        t_h=input_data["t_h"],
        d_h=input_data["d_h"],
        weights=input_data["weights"]
    )

    assert_close(s_h, expected_data["S_h"])
