"""
GV-Q01: Quality computation golden vectors.

Specification: Document 17, Section 4.1 (GV-Q01)
Validates Q_i reference implementation against deterministic test cases.
"""
import pytest
from nexalert_reference.quality import compute_quality


def test_GV_Q01_nominal(load_gv, assert_close_fixture):
    """GV-Q01-01: Fresh and stable."""
    inputs, expected = load_gv("GV_Q01_nominal")

    q_i = compute_quality(
        q_integrity=inputs["q_integrity"],
        q_stability=inputs["q_stability"]
    )

    assert q_i is not None, "Q_i should not be None with complete inputs"
    assert_close_fixture(q_i, expected["Q_i"], label="Q_i nominal")
    assert 0.0 <= q_i <= 1.0, "Q_i out of range [0,1] per Doc 04 Sec 3.2"


def test_GV_Q01_stale(load_gv, assert_close_fixture):
    """GV-Q01-02: Stale data degrades integrity."""
    inputs, expected = load_gv("GV_Q01_stale")

    q_i = compute_quality(
        q_integrity=inputs["q_integrity"],
        q_stability=inputs["q_stability"]
    )

    assert q_i is not None
    assert_close_fixture(q_i, expected["Q_i"], label="Q_i stale")
    assert 0.0 <= q_i <= 1.0
    assert q_i < 1.0, "Stale data must degrade Q_i per Doc 04 Sec 3.2"


def test_GV_Q01_jitter(load_gv, assert_close_fixture):
    """GV-Q01-03: High jitter degrades stability."""
    inputs, expected = load_gv("GV_Q01_jitter")

    q_i = compute_quality(
        q_integrity=inputs["q_integrity"],
        q_stability=inputs["q_stability"]
    )

    assert q_i is not None
    assert_close_fixture(q_i, expected["Q_i"], label="Q_i jitter")
    assert 0.0 <= q_i <= 1.0
    assert q_i < 1.0, "High jitter must degrade Q_i per Doc 04 Sec 3.2"


def test_GV_Q01_degraded(load_gv, assert_close_fixture):
    """GV-Q01-04: Both components degraded."""
    inputs, expected = load_gv("GV_Q01_degraded")

    q_i = compute_quality(
        q_integrity=inputs["q_integrity"],
        q_stability=inputs["q_stability"]
    )

    assert q_i is not None
    assert_close_fixture(q_i, expected["Q_i"], label="Q_i degraded")
    assert 0.0 <= q_i <= 1.0


def test_GV_Q01_missing_integrity():
    """GV-Q01-05: Missing integrity preserves missing != zero."""
    q_i = compute_quality(
        q_integrity=None,
        q_stability=1.0
    )

    assert q_i is None, "Q_i=None preserves missing != zero per IMPLEMENTATION_CONSTITUTION.md Sec 3"


def test_GV_Q01_missing_stability():
    """GV-Q01-06: Missing stability preserves missing != zero."""
    q_i = compute_quality(
        q_integrity=1.0,
        q_stability=None
    )

    assert q_i is None, "Q_i=None preserves missing != zero per IMPLEMENTATION_CONSTITUTION.md Sec 3"


def test_GV_Q01_invalid_integrity_range():
    """GV-Q01-07: Invalid integrity range raises ValueError."""
    with pytest.raises(ValueError, match="q_integrity.*out of range"):
        compute_quality(q_integrity=1.5, q_stability=1.0)


def test_GV_Q01_invalid_stability_range():
    """GV-Q01-08: Invalid stability range raises ValueError."""
    with pytest.raises(ValueError, match="q_stability.*out of range"):
        compute_quality(q_integrity=1.0, q_stability=-0.1)


def test_GV_Q01_multiplicative():
    """GV-Q01-09: Formula Q_i = q_integrity × q_stability."""
    q_i = compute_quality(q_integrity=0.9, q_stability=0.8)

    assert q_i is not None
    assert_close_fixture = lambda a, e, label: None  # Simple check
    # 0.9 × 0.8 = 0.72
    assert abs(q_i - 0.72) < 1e-6, f"Expected 0.72, got {q_i}"
