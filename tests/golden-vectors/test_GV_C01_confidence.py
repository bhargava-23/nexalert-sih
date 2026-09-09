"""
GV-C01: Confidence golden vectors.

Specification: Document 04, Section 7
Validates C_h reference implementation against deterministic test cases.

PHASE 5 ITERATION 4: Evidence confidence computation.
"""

import json
import pytest
from pathlib import Path

# Import reference implementation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "reference" / "python"))

from nexalert_reference.confidence import (
    compute_coverage,
    compute_agreement,
    compute_temporal,
    compute_baseline_confidence,
    compute_confidence
)


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

def test_GV_C01_coverage_full(load_gv, assert_close):
    """GV-C01-1: Full coverage - all sensors available."""
    input_data, expected_data = load_gv("GV_C01_coverage_full")

    c_cov = compute_coverage(
        sensor_availability=input_data["sensor_availability"],
        weights=input_data["weights"]
    )

    assert_close(c_cov, expected_data["C_cov"])


def test_GV_C01_coverage_partial(load_gv, assert_close):
    """GV-C01-2: Partial coverage - 60% of sensors available."""
    input_data, expected_data = load_gv("GV_C01_coverage_partial")

    c_cov = compute_coverage(
        sensor_availability=input_data["sensor_availability"],
        weights=input_data["weights"]
    )

    assert_close(c_cov, expected_data["C_cov"])


def test_GV_C01_coverage_none(load_gv, assert_close):
    """GV-C01-3: No coverage - all sensors unavailable."""
    input_data, expected_data = load_gv("GV_C01_coverage_none")

    c_cov = compute_coverage(
        sensor_availability=input_data["sensor_availability"],
        weights=input_data["weights"]
    )

    assert_close(c_cov, expected_data["C_cov"])


def test_GV_C01_agreement_zero_mean(load_gv, assert_close):
    """GV-C01-4: Zero-mean agreement - all groups near zero."""
    input_data, expected_data = load_gv("GV_C01_agreement_zero_mean")

    c_agree = compute_agreement(
        group_evidence=input_data["group_evidence"],
        group_weights=input_data["group_weights"],
        k_v=input_data["k_v"]
    )

    assert_close(c_agree, expected_data["C_agree"])


def test_GV_C01_agreement_single_group(load_gv, assert_close):
    """GV-C01-5: Single group - no disagreement possible."""
    input_data, expected_data = load_gv("GV_C01_agreement_single_group")

    c_agree = compute_agreement(
        group_evidence=input_data["group_evidence"],
        group_weights=input_data["group_weights"],
        k_v=input_data["k_v"]
    )

    assert_close(c_agree, expected_data["C_agree"])


def test_GV_C01_agreement_high(load_gv, assert_close):
    """GV-C01-6: High agreement - low variance."""
    input_data, expected_data = load_gv("GV_C01_agreement_high")

    c_agree = compute_agreement(
        group_evidence=input_data["group_evidence"],
        group_weights=input_data["group_weights"],
        k_v=input_data["k_v"]
    )

    assert_close(c_agree, expected_data["C_agree"])


def test_GV_C01_agreement_low(load_gv, assert_close):
    """GV-C01-7: Low agreement - high variance."""
    input_data, expected_data = load_gv("GV_C01_agreement_low")

    c_agree = compute_agreement(
        group_evidence=input_data["group_evidence"],
        group_weights=input_data["group_weights"],
        k_v=input_data["k_v"]
    )

    assert_close(c_agree, expected_data["C_agree"])


def test_GV_C01_temporal_fresh(load_gv, assert_close):
    """GV-C01-8: Fresh telemetry - within max age."""
    input_data, expected_data = load_gv("GV_C01_temporal_fresh")

    c_temp = compute_temporal(
        telemetry_age_seconds=input_data["telemetry_age_seconds"],
        max_age_seconds=input_data["max_age_seconds"]
    )

    assert_close(c_temp, expected_data["C_temp"])


def test_GV_C01_temporal_stale(load_gv, assert_close):
    """GV-C01-9: Stale telemetry - exceeds max age."""
    input_data, expected_data = load_gv("GV_C01_temporal_stale")

    c_temp = compute_temporal(
        telemetry_age_seconds=input_data["telemetry_age_seconds"],
        max_age_seconds=input_data["max_age_seconds"]
    )

    assert_close(c_temp, expected_data["C_temp"])


def test_GV_C01_temporal_missing(load_gv, assert_close):
    """GV-C01-10: Missing telemetry age."""
    input_data, expected_data = load_gv("GV_C01_temporal_missing")

    c_temp = compute_temporal(
        telemetry_age_seconds=input_data["telemetry_age_seconds"],
        max_age_seconds=input_data["max_age_seconds"]
    )

    assert_close(c_temp, expected_data["C_temp"])


def test_GV_C01_baseline_ready(load_gv, assert_close):
    """GV-C01-11: Baseline state READY."""
    input_data, expected_data = load_gv("GV_C01_baseline_ready")

    c_base = compute_baseline_confidence(
        baseline_state=input_data["baseline_state"]
    )

    assert_close(c_base, expected_data["C_base"])


def test_GV_C01_final_weighted(load_gv, assert_close):
    """GV-C01-12: Final weighted confidence combination."""
    input_data, expected_data = load_gv("GV_C01_final_weighted")

    c_h = compute_confidence(
        c_cov=input_data["c_cov"],
        c_agree=input_data["c_agree"],
        c_temp=input_data["c_temp"],
        c_base=input_data["c_base"],
        weights=input_data["weights"]
    )

    assert_close(c_h, expected_data["C_h"])
