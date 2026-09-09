"""
GV-RK01: Risk golden vectors.

Specification: Document 04, Section 9
Validates R_h reference implementation against deterministic test cases.

PHASE 5 ITERATION 5: Risk golden vectors.
"""

import json
import pytest
from pathlib import Path

# Import reference implementation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "reference" / "python"))

from nexalert_reference.risk import compute_risk


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

def test_GV_RK01_nominal(load_gv, assert_close):
    """GV-RK01-1: All components present - nominal case."""
    input_data, expected_data = load_gv("GV_RK01_nominal")

    r_h = compute_risk(
        e_h=input_data["e_h"],
        s_h=input_data["s_h"],
        t_h=input_data["t_h"],
        weights=input_data["weights"]
    )

    assert_close(r_h, expected_data["R_h"])


def test_GV_RK01_high_evidence(load_gv, assert_close):
    """GV-RK01-2: High evidence, moderate severity."""
    input_data, expected_data = load_gv("GV_RK01_high_evidence")

    r_h = compute_risk(
        e_h=input_data["e_h"],
        s_h=input_data["s_h"],
        t_h=input_data["t_h"],
        weights=input_data["weights"]
    )

    assert_close(r_h, expected_data["R_h"])


def test_GV_RK01_high_severity(load_gv, assert_close):
    """GV-RK01-3: High severity, moderate evidence."""
    input_data, expected_data = load_gv("GV_RK01_high_severity")

    r_h = compute_risk(
        e_h=input_data["e_h"],
        s_h=input_data["s_h"],
        t_h=input_data["t_h"],
        weights=input_data["weights"]
    )

    assert_close(r_h, expected_data["R_h"])


def test_GV_RK01_rapid_threat(load_gv, assert_close):
    """GV-RK01-4: Rapid threat escalation."""
    input_data, expected_data = load_gv("GV_RK01_rapid_threat")

    r_h = compute_risk(
        e_h=input_data["e_h"],
        s_h=input_data["s_h"],
        t_h=input_data["t_h"],
        weights=input_data["weights"]
    )

    assert_close(r_h, expected_data["R_h"])


def test_GV_RK01_evidence_only(load_gv, assert_close):
    """GV-RK01-5: Evidence only, severity and temporal missing."""
    input_data, expected_data = load_gv("GV_RK01_evidence_only")

    r_h = compute_risk(
        e_h=input_data["e_h"],
        s_h=input_data["s_h"],
        t_h=input_data["t_h"],
        weights=input_data["weights"]
    )

    assert_close(r_h, expected_data["R_h"])


def test_GV_RK01_severity_only(load_gv, assert_close):
    """GV-RK01-6: Severity only, evidence and temporal missing."""
    input_data, expected_data = load_gv("GV_RK01_severity_only")

    r_h = compute_risk(
        e_h=input_data["e_h"],
        s_h=input_data["s_h"],
        t_h=input_data["t_h"],
        weights=input_data["weights"]
    )

    assert_close(r_h, expected_data["R_h"])


def test_GV_RK01_partial_missing(load_gv, assert_close):
    """GV-RK01-7: One component missing - reweighting."""
    input_data, expected_data = load_gv("GV_RK01_partial_missing")

    r_h = compute_risk(
        e_h=input_data["e_h"],
        s_h=input_data["s_h"],
        t_h=input_data["t_h"],
        weights=input_data["weights"]
    )

    assert_close(r_h, expected_data["R_h"])


def test_GV_RK01_all_missing(load_gv, assert_close):
    """GV-RK01-8: All components missing - returns None."""
    input_data, expected_data = load_gv("GV_RK01_all_missing")

    r_h = compute_risk(
        e_h=input_data["e_h"],
        s_h=input_data["s_h"],
        t_h=input_data["t_h"],
        weights=input_data["weights"]
    )

    assert_close(r_h, expected_data["R_h"])


def test_GV_RK01_low_confidence_scenario(load_gv, assert_close):
    """GV-RK01-9: Verify confidence NOT multiplied into R_h."""
    input_data, expected_data = load_gv("GV_RK01_low_confidence_scenario")

    # Confidence provided in input but should NOT affect R_h
    r_h = compute_risk(
        e_h=input_data["e_h"],
        s_h=input_data["s_h"],
        t_h=input_data["t_h"],
        weights=input_data["weights"]
    )

    # R_h should be same as nominal, confidence ignored
    assert_close(r_h, expected_data["R_h"])


def test_GV_RK01_multi_hazard(load_gv, assert_close):
    """GV-RK01-10: Multi-hazard independence - fire and flood separate."""
    input_data, expected_data = load_gv("GV_RK01_multi_hazard")

    # Compute flood risk
    flood_r_h = compute_risk(
        e_h=input_data["flood_e_h"],
        s_h=input_data["flood_s_h"],
        t_h=input_data["flood_t_h"],
        weights=input_data["weights"]
    )

    # Compute fire risk
    fire_r_h = compute_risk(
        e_h=input_data["fire_e_h"],
        s_h=input_data["fire_s_h"],
        t_h=input_data["fire_t_h"],
        weights=input_data["weights"]
    )

    assert_close(flood_r_h, expected_data["flood_R_h"])
    assert_close(fire_r_h, expected_data["fire_R_h"])
