"""
GV-A01: Individual anomaly golden vectors.

Specification: Document 04, Section 4.2 (GV-A01)
Validates A_i reference implementation against deterministic test cases.
"""
import pytest
from nexalert_reference.anomaly import compute_individual_anomaly


def test_GV_A01_zero(load_gv, assert_close_fixture):
    """GV-A01-01: Zero z-score → zero anomaly."""
    inputs, expected = load_gv("GV_A01_zero")

    a_i = compute_individual_anomaly(
        z_score=inputs["z_score"],
        lambda_param=inputs["lambda_param"],
        z_cap=inputs["z_cap"]
    )

    assert a_i is not None
    assert_close_fixture(a_i, expected["A_i"], label="A_i zero")
    assert 0.0 <= a_i <= 1.0


def test_GV_A01_moderate(load_gv, assert_close_fixture):
    """GV-A01-02: Moderate z-score → moderate anomaly."""
    inputs, expected = load_gv("GV_A01_moderate")

    a_i = compute_individual_anomaly(
        z_score=inputs["z_score"],
        lambda_param=inputs["lambda_param"],
        z_cap=inputs["z_cap"]
    )

    assert a_i is not None
    assert_close_fixture(a_i, expected["A_i"], label="A_i moderate")
    assert 0.0 <= a_i <= 1.0


def test_GV_A01_capped(load_gv, assert_close_fixture):
    """GV-A01-03: High z-score capped at z_cap."""
    inputs, expected = load_gv("GV_A01_capped")

    a_i = compute_individual_anomaly(
        z_score=inputs["z_score"],
        lambda_param=inputs["lambda_param"],
        z_cap=inputs["z_cap"]
    )

    assert a_i is not None
    assert_close_fixture(a_i, expected["A_i"], label="A_i capped")
    assert 0.0 <= a_i <= 1.0
    assert a_i > 0.9, "High anomaly should be close to 1.0"


def test_GV_A01_missing_z_score(load_gv):
    """GV-A01-04: Missing z_score preserves missing != zero."""
    inputs, expected = load_gv("GV_A01_missing_z_score")

    a_i = compute_individual_anomaly(
        z_score=inputs["z_score"],
        lambda_param=inputs["lambda_param"],
        z_cap=inputs["z_cap"]
    )

    assert a_i is None, "Missing z_score must return None per missing != zero"


def test_GV_A01_negative_z_score(load_gv, assert_close_fixture):
    """GV-A01-05: Negative z-score symmetry."""
    inputs, expected = load_gv("GV_A01_negative_z_score")

    a_i = compute_individual_anomaly(
        z_score=inputs["z_score"],
        lambda_param=inputs["lambda_param"],
        z_cap=inputs["z_cap"]
    )

    assert a_i is not None
    assert_close_fixture(a_i, expected["A_i"], label="A_i negative")
    assert 0.0 <= a_i <= 1.0


def test_GV_A01_exact_z_cap_boundary(load_gv, assert_close_fixture):
    """GV-A01-06: z_score exactly at z_cap boundary."""
    inputs, expected = load_gv("GV_A01_exact_z_cap_boundary")

    a_i = compute_individual_anomaly(
        z_score=inputs["z_score"],
        lambda_param=inputs["lambda_param"],
        z_cap=inputs["z_cap"]
    )

    assert a_i is not None
    assert_close_fixture(a_i, expected["A_i"], label="A_i at z_cap")
    assert 0.0 <= a_i <= 1.0
