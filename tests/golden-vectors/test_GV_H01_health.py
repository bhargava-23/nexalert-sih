"""
GV-H01: Health computation golden vectors.

Specification: Document 17, Section 4.1 (GV-H01)
Validates H_i reference implementation against deterministic test cases.
"""
import pytest
from nexalert_reference.health import compute_health


def test_GV_H01_nominal(load_gv, assert_close_fixture):
    """GV-H01-01: All diagnostics nominal."""
    inputs, expected = load_gv("GV_H01_nominal")

    h_i, complete = compute_health(
        diagnostics=inputs["diagnostics"],
        weights=inputs["weights"],
        hard_failure=False
    )

    assert complete, "Diagnostics should be complete"
    assert h_i is not None, "H_i should not be None with complete diagnostics"
    assert_close_fixture(h_i, expected["H_i"], label="H_i nominal")
    assert 0.0 <= h_i <= 1.0, "H_i out of range [0,1] per Doc 04 Sec 3.1"


def test_GV_H01_hard_failure():
    """GV-H01-02: Hard failure forces H_i=0."""
    diagnostics = {"self_test_passed": 1.0, "comm_integrity": 1.0,
                   "calibration_valid": 1.0, "stability_index": 1.0}
    weights = {"self_test_passed": 0.3, "comm_integrity": 0.3,
               "calibration_valid": 0.2, "stability_index": 0.2}

    h_i, complete = compute_health(
        diagnostics=diagnostics,
        weights=weights,
        hard_failure=True
    )

    assert h_i == 0.0, "Hard failure must force H_i=0 per Doc 04 Sec 3.1"


def test_GV_H01_degradation(load_gv, assert_close_fixture):
    """GV-H01-03: Weighted degradation."""
    inputs, expected = load_gv("GV_H01_degradation")

    h_i, complete = compute_health(
        diagnostics=inputs["diagnostics"],
        weights=inputs["weights"],
        hard_failure=False
    )

    assert complete, "Diagnostics should be complete"
    assert h_i is not None
    assert_close_fixture(h_i, expected["H_i"], label="H_i degradation")
    assert 0.0 <= h_i <= 1.0
    assert h_i < 1.0, "Degraded health must be < 1.0"


def test_GV_H01_missing_diagnostic():
    """GV-H01-04: Missing diagnostic preserves missing != zero."""
    # Missing stability_index diagnostic
    diagnostics = {"self_test_passed": 1.0, "comm_integrity": 1.0, "calibration_valid": 1.0}
    weights = {"self_test_passed": 0.3, "comm_integrity": 0.3,
               "calibration_valid": 0.2, "stability_index": 0.2}

    h_i, complete = compute_health(
        diagnostics=diagnostics,
        weights=weights,
        hard_failure=False
    )

    assert not complete, "Diagnostics marked incomplete"
    assert h_i is None, "H_i=None preserves missing != zero per IMPLEMENTATION_CONSTITUTION.md Sec 3"
