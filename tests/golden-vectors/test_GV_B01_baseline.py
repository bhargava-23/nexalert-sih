"""
GV-B01: Baseline computation golden vectors.

Specification: Document 04, Section 4.1 (GV-B01)
Validates B_i reference implementation against deterministic test cases.
"""
import pytest
from nexalert_reference.baseline import (
    BaselineState,
    compute_robust_baseline,
    compute_z_score,
    update_baseline_state
)


def test_GV_B01_robust_median(load_gv, assert_close_fixture):
    """GV-B01-01: Robust baseline with median and MAD."""
    inputs, expected = load_gv("GV_B01_robust_median")

    median, scale = compute_robust_baseline(samples=inputs["samples"])

    assert_close_fixture(median, expected["median"], label="median")
    assert_close_fixture(scale, expected["scale"], label="scale")
    assert scale > 0, "Scale must be positive"


def test_GV_B01_zero_mad(load_gv, assert_close_fixture):
    """GV-B01-02: Zero MAD case (all samples identical)."""
    inputs, expected = load_gv("GV_B01_zero_mad")

    median, scale = compute_robust_baseline(samples=inputs["samples"])

    assert_close_fixture(median, expected["median"], label="median")
    assert_close_fixture(scale, expected["scale"], label="scale (epsilon)")
    assert scale == 1e-9, "Scale equals epsilon when MAD=0"


def test_GV_B01_z_score(load_gv, assert_close_fixture):
    """GV-B01-03: Z-score computation."""
    inputs, expected = load_gv("GV_B01_z_score")

    z_score = compute_z_score(
        value=inputs["value"],
        median=inputs["median"],
        scale=inputs["scale"]
    )

    assert z_score is not None
    assert_close_fixture(z_score, expected["z_score"], label="z_score")


def test_GV_B01_state_init_to_learning(load_gv):
    """GV-B01-04: State transition INITIALIZING → LEARNING."""
    inputs, expected = load_gv("GV_B01_state_init_to_learning")

    next_state, stability = update_baseline_state(
        current_state=BaselineState(inputs["current_state"]),
        sample_count=inputs["sample_count"],
        min_samples_init=inputs["min_samples_init"],
        min_samples_learning=inputs["min_samples_learning"],
        hazard_state=inputs["hazard_state"],
        hazard_state_stability_count=inputs["stability_count"],
        recovery_stability_samples=inputs["recovery_stability_samples"]
    )

    assert next_state == BaselineState(expected["next_state"])
    assert stability == expected["stability"]


def test_GV_B01_state_freeze(load_gv):
    """GV-B01-05: State transition READY → FROZEN."""
    inputs, expected = load_gv("GV_B01_state_freeze")

    next_state, stability = update_baseline_state(
        current_state=BaselineState(inputs["current_state"]),
        sample_count=inputs["sample_count"],
        min_samples_init=inputs["min_samples_init"],
        min_samples_learning=inputs["min_samples_learning"],
        hazard_state=inputs["hazard_state"],
        hazard_state_stability_count=inputs["stability_count"],
        recovery_stability_samples=inputs["recovery_stability_samples"]
    )

    assert next_state == BaselineState(expected["next_state"])
    assert stability == expected["stability"]
    assert stability == 0, "Stability resets on freeze"


def test_GV_B01_insufficient_samples(load_gv):
    """GV-B01-06: Insufficient samples raises ValueError."""
    inputs, expected = load_gv("GV_B01_insufficient_samples")

    with pytest.raises(ValueError, match="at least 2 samples"):
        compute_robust_baseline(samples=inputs["samples"])


def test_GV_B01_missing_value(load_gv):
    """GV-B01-07: Missing value preserves missing != zero."""
    inputs, expected = load_gv("GV_B01_missing_value")

    z_score = compute_z_score(
        value=inputs["value"],
        median=inputs["median"],
        scale=inputs["scale"]
    )

    assert z_score is None, "Missing value must return None per missing != zero"


def test_GV_B01_state_recovery(load_gv):
    """GV-B01-08: State transition FROZEN → RECOVERING."""
    inputs, expected = load_gv("GV_B01_state_recovery")

    next_state, stability = update_baseline_state(
        current_state=BaselineState(inputs["current_state"]),
        sample_count=inputs["sample_count"],
        min_samples_init=inputs["min_samples_init"],
        min_samples_learning=inputs["min_samples_learning"],
        hazard_state=inputs["hazard_state"],
        hazard_state_stability_count=inputs["stability_count"],
        recovery_stability_samples=inputs["recovery_stability_samples"]
    )

    assert next_state == BaselineState(expected["next_state"])
    assert stability == expected["stability"]
