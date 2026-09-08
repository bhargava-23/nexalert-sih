"""
GV-R01: Reliability computation golden vectors.

Specification: Document 17, Section 4.1 (GV-R01)
Validates R_i reference implementation against deterministic test cases.
"""
import pytest
from nexalert_reference.reliability import compute_reliability


def test_GV_R01_nominal(load_gv, assert_close_fixture):
    """GV-R01-01: All components perfect."""
    inputs, expected = load_gv("GV_R01_nominal")

    r_i = compute_reliability(
        h_i=inputs["h_i"],
        q_i=inputs["q_i"],
        k_i=inputs["k_i"]
    )

    assert r_i is not None, "R_i should not be None with complete inputs"
    assert_close_fixture(r_i, expected["R_i"], label="R_i nominal")
    assert 0.0 <= r_i <= 1.0, "R_i out of range [0,1] per Doc 04 Sec 3.3"


def test_GV_R01_zero_health(load_gv, assert_close_fixture):
    """GV-R01-02: Zero health forces R_i=0."""
    inputs, expected = load_gv("GV_R01_zero_health")

    r_i = compute_reliability(
        h_i=inputs["h_i"],
        q_i=inputs["q_i"],
        k_i=inputs["k_i"]
    )

    assert r_i is not None
    assert_close_fixture(r_i, expected["R_i"], label="R_i zero health")
    assert r_i == 0.0, "Zero health must force R_i=0 per Doc 04 Sec 3.3"


def test_GV_R01_zero_quality(load_gv, assert_close_fixture):
    """GV-R01-03: Zero quality forces R_i=0."""
    inputs, expected = load_gv("GV_R01_zero_quality")

    r_i = compute_reliability(
        h_i=inputs["h_i"],
        q_i=inputs["q_i"],
        k_i=inputs["k_i"]
    )

    assert r_i is not None
    assert_close_fixture(r_i, expected["R_i"], label="R_i zero quality")
    assert r_i == 0.0, "Zero quality must force R_i=0 per Doc 04 Sec 3.3"


def test_GV_R01_zero_calibration(load_gv, assert_close_fixture):
    """GV-R01-04: Zero calibration forces R_i=0."""
    inputs, expected = load_gv("GV_R01_zero_calibration")

    r_i = compute_reliability(
        h_i=inputs["h_i"],
        q_i=inputs["q_i"],
        k_i=inputs["k_i"]
    )

    assert r_i is not None
    assert_close_fixture(r_i, expected["R_i"], label="R_i zero calibration")
    assert r_i == 0.0, "Zero K_i must force R_i=0 per Doc 04 Sec 3.3"


def test_GV_R01_degraded(load_gv, assert_close_fixture):
    """GV-R01-05: All components degraded."""
    inputs, expected = load_gv("GV_R01_degraded")

    r_i = compute_reliability(
        h_i=inputs["h_i"],
        q_i=inputs["q_i"],
        k_i=inputs["k_i"]
    )

    assert r_i is not None
    assert_close_fixture(r_i, expected["R_i"], label="R_i degraded")
    assert 0.0 <= r_i <= 1.0


def test_GV_R01_missing_health():
    """GV-R01-06: Missing health preserves missing != zero."""
    r_i = compute_reliability(
        h_i=None,
        q_i=1.0,
        k_i=1.0
    )

    assert r_i is None, "R_i=None preserves missing != zero per IMPLEMENTATION_CONSTITUTION.md Sec 3"


def test_GV_R01_missing_quality():
    """GV-R01-07: Missing quality preserves missing != zero."""
    r_i = compute_reliability(
        h_i=1.0,
        q_i=None,
        k_i=1.0
    )

    assert r_i is None, "R_i=None preserves missing != zero per IMPLEMENTATION_CONSTITUTION.md Sec 3"


def test_GV_R01_missing_calibration():
    """GV-R01-08: Missing K_i preserves missing != zero."""
    r_i = compute_reliability(
        h_i=1.0,
        q_i=1.0,
        k_i=None
    )

    assert r_i is None, "R_i=None with missing K_i per IMPLEMENTATION_CONSTITUTION.md Sec 3"


def test_GV_R01_invalid_health_range():
    """GV-R01-09: Invalid health range raises ValueError."""
    with pytest.raises(ValueError, match="h_i.*out of range"):
        compute_reliability(h_i=1.5, q_i=1.0, k_i=1.0)


def test_GV_R01_invalid_quality_range():
    """GV-R01-10: Invalid quality range raises ValueError."""
    with pytest.raises(ValueError, match="q_i.*out of range"):
        compute_reliability(h_i=1.0, q_i=-0.1, k_i=1.0)


def test_GV_R01_invalid_calibration_range():
    """GV-R01-11: Invalid K_i range raises ValueError."""
    with pytest.raises(ValueError, match="k_i.*out of range"):
        compute_reliability(h_i=1.0, q_i=1.0, k_i=1.1)


def test_GV_R01_multiplicative():
    """GV-R01-12: Formula R_i = H_i × Q_i × K_i."""
    r_i = compute_reliability(h_i=0.9, q_i=0.8, k_i=0.95)

    assert r_i is not None
    # 0.9 × 0.8 × 0.95 = 0.684
    expected = 0.684
    assert abs(r_i - expected) < 1e-6, f"Expected {expected}, got {r_i}"


def test_GV_R01_k_i_explicit():
    """GV-R01-13: K_i is explicit input, not hard-coded."""
    # Test various K_i values to ensure it's an explicit parameter
    r_i_full = compute_reliability(h_i=1.0, q_i=1.0, k_i=1.0)
    r_i_half = compute_reliability(h_i=1.0, q_i=1.0, k_i=0.5)
    r_i_zero = compute_reliability(h_i=1.0, q_i=1.0, k_i=0.0)

    assert r_i_full == 1.0, "K_i=1.0 should yield R_i=1.0"
    assert r_i_half == 0.5, "K_i=0.5 should yield R_i=0.5"
    assert r_i_zero == 0.0, "K_i=0.0 should yield R_i=0.0"
