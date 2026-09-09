"""
GV-A02: Aggregate anomaly golden vectors.

Specification: Document 04, Sections 4.2, 4.3 (GV-A02)
Validates A_node and A_h reference implementation against deterministic test cases.
"""
import pytest
from nexalert_reference.anomaly import (
    compute_node_aggregate_anomaly,
    compute_hazard_specific_anomaly
)


def test_GV_A02_node_aggregate(load_gv, assert_close_fixture):
    """GV-A02-01: Node aggregate anomaly A_node."""
    inputs, expected = load_gv("GV_A02_node_aggregate")

    a_node = compute_node_aggregate_anomaly(
        anomalies=inputs["anomalies"],
        reliabilities=inputs["reliabilities"]
    )

    assert a_node is not None
    assert_close_fixture(a_node, expected["A_node"], label="A_node")
    assert 0.0 <= a_node <= 1.0


def test_GV_A02_hazard_specific(load_gv, assert_close_fixture):
    """GV-A02-02: Hazard-specific anomaly A_h."""
    inputs, expected = load_gv("GV_A02_hazard_specific")

    a_h = compute_hazard_specific_anomaly(
        anomalies=inputs["anomalies"],
        reliabilities=inputs["reliabilities"],
        weights=inputs["weights"]
    )

    assert a_h is not None
    assert_close_fixture(a_h, expected["A_h"], label="A_h")
    assert 0.0 <= a_h <= 1.0


def test_GV_A02_missing_anomaly(load_gv, assert_close_fixture):
    """GV-A02-03: Missing anomaly excluded from aggregation."""
    inputs, expected = load_gv("GV_A02_missing_anomaly")

    a_node = compute_node_aggregate_anomaly(
        anomalies=inputs["anomalies"],
        reliabilities=inputs["reliabilities"]
    )

    assert a_node is not None
    assert_close_fixture(a_node, expected["A_node"], label="A_node with missing")
    assert 0.0 <= a_node <= 1.0


def test_GV_A02_missing_reliability(load_gv, assert_close_fixture):
    """GV-A02-04: Missing reliability excluded from aggregation."""
    inputs, expected = load_gv("GV_A02_missing_reliability")

    a_node = compute_node_aggregate_anomaly(
        anomalies=inputs["anomalies"],
        reliabilities=inputs["reliabilities"]
    )

    assert a_node is not None
    assert_close_fixture(a_node, expected["A_node"], label="A_node with missing R_i")
    assert 0.0 <= a_node <= 1.0


def test_GV_A02_partial_missing(load_gv, assert_close_fixture):
    """GV-A02-05: Partial missing sensors in aggregation."""
    inputs, expected = load_gv("GV_A02_partial_missing")

    a_node = compute_node_aggregate_anomaly(
        anomalies=inputs["anomalies"],
        reliabilities=inputs["reliabilities"]
    )

    assert a_node is not None
    assert_close_fixture(a_node, expected["A_node"], label="A_node partial missing")
    assert 0.0 <= a_node <= 1.0


def test_GV_A02_zero_denominator(load_gv):
    """GV-A02-06: Zero denominator returns None."""
    inputs, expected = load_gv("GV_A02_zero_denominator")

    a_node = compute_node_aggregate_anomaly(
        anomalies=inputs["anomalies"],
        reliabilities=inputs["reliabilities"]
    )

    assert a_node is None, "Zero denominator (sum(R_i) < epsilon) must return None"
