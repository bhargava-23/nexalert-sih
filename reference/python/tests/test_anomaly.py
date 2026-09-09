"""
Tests for anomaly (A_i, A_node, A_h) reference implementation.

Specification: Document 04, Sections 4.2, 4.3
"""
import pytest
from nexalert_reference.anomaly import (
    compute_individual_anomaly,
    compute_node_aggregate_anomaly,
    compute_hazard_specific_anomaly,
    EPSILON
)


class TestComputeIndividualAnomaly:
    """Test individual anomaly A_i computation."""

    def test_zero_z_score(self):
        """Test z_score = 0 → A_i ≈ 0 (no anomaly)."""
        a_i = compute_individual_anomaly(0.0, lambda_param=2.0, z_cap=5.0)
        assert a_i == pytest.approx(0.0, abs=1e-9)

    def test_moderate_anomaly(self):
        """Test moderate z_score → moderate A_i."""
        a_i = compute_individual_anomaly(2.0, lambda_param=2.0, z_cap=5.0)

        # A_i = 1 - exp(-2.0 / 2.0) = 1 - exp(-1.0) ≈ 0.632
        assert a_i == pytest.approx(0.632121, rel=1e-3)

    def test_high_anomaly(self):
        """Test high z_score capped at z_cap."""
        # z_score = 10.0 > z_cap = 5.0, so clamped to 5.0
        a_i = compute_individual_anomaly(10.0, lambda_param=2.0, z_cap=5.0)

        # A_i = 1 - exp(-5.0 / 2.0) = 1 - exp(-2.5) ≈ 0.917
        assert a_i == pytest.approx(0.917915, rel=1e-3)

    def test_missing_z_score(self):
        """Test None z_score → None A_i (preserve missing != zero)."""
        a_i = compute_individual_anomaly(None, lambda_param=2.0, z_cap=5.0)
        assert a_i is None

    def test_negative_z_score(self):
        """Test symmetry: A_i(-z) = A_i(z)."""
        a_i_pos = compute_individual_anomaly(2.0, lambda_param=2.0, z_cap=5.0)
        a_i_neg = compute_individual_anomaly(-2.0, lambda_param=2.0, z_cap=5.0)

        assert a_i_pos == pytest.approx(a_i_neg)

    def test_boundary_at_z_cap(self):
        """Test z_score exactly at z_cap."""
        a_i = compute_individual_anomaly(5.0, lambda_param=2.0, z_cap=5.0)

        # Should equal high_anomaly test (clamped to z_cap)
        assert a_i == pytest.approx(0.917915, rel=1e-3)

    def test_invalid_lambda_param(self):
        """Test validation: lambda_param must be > 0."""
        with pytest.raises(ValueError, match="lambda_param must be > 0"):
            compute_individual_anomaly(2.0, lambda_param=0.0, z_cap=5.0)

        with pytest.raises(ValueError, match="lambda_param must be > 0"):
            compute_individual_anomaly(2.0, lambda_param=-1.0, z_cap=5.0)

    def test_invalid_z_cap(self):
        """Test validation: z_cap must be > 0."""
        with pytest.raises(ValueError, match="z_cap must be > 0"):
            compute_individual_anomaly(2.0, lambda_param=2.0, z_cap=0.0)

        with pytest.raises(ValueError, match="z_cap must be > 0"):
            compute_individual_anomaly(2.0, lambda_param=2.0, z_cap=-1.0)

    def test_asymptotic_behavior(self):
        """Test A_i approaches 1.0 at high |z|."""
        a_i_5 = compute_individual_anomaly(5.0, lambda_param=2.0, z_cap=5.0)
        a_i_10 = compute_individual_anomaly(10.0, lambda_param=2.0, z_cap=5.0)

        # Both capped at z_cap=5.0, should be identical
        assert a_i_5 == pytest.approx(a_i_10)

        # Should be close to 1.0
        assert a_i_5 > 0.9


class TestComputeNodeAggregateAnomaly:
    """Test node aggregate anomaly A_node computation."""

    def test_weighted_average(self):
        """Test reliability-weighted averaging."""
        anomalies = {"temp": 0.8, "smoke": 0.6}
        reliabilities = {"temp": 0.9, "smoke": 0.7}

        a_node = compute_node_aggregate_anomaly(anomalies, reliabilities)

        # A_node = (0.9*0.8 + 0.7*0.6) / (0.9 + 0.7)
        #        = (0.72 + 0.42) / 1.6 = 1.14 / 1.6 = 0.7125
        assert a_node == pytest.approx(0.7125)

    def test_missing_anomaly(self):
        """Test missing A_i excluded from computation."""
        anomalies = {"temp": 0.8, "smoke": None}
        reliabilities = {"temp": 0.9, "smoke": 0.7}

        a_node = compute_node_aggregate_anomaly(anomalies, reliabilities)

        # Only temp contributes
        # A_node = 0.9 * 0.8 / 0.9 = 0.8
        assert a_node == pytest.approx(0.8)

    def test_missing_reliability(self):
        """Test missing R_i excluded from computation."""
        anomalies = {"temp": 0.8, "smoke": 0.6}
        reliabilities = {"temp": 0.9, "smoke": None}

        a_node = compute_node_aggregate_anomaly(anomalies, reliabilities)

        # Only temp contributes
        assert a_node == pytest.approx(0.8)

    def test_all_missing(self):
        """Test all sensors missing → None."""
        anomalies = {"temp": None, "smoke": None}
        reliabilities = {"temp": 0.9, "smoke": 0.7}

        a_node = compute_node_aggregate_anomaly(anomalies, reliabilities)

        assert a_node is None

    def test_empty_dict(self):
        """Test empty anomalies dict → None."""
        a_node = compute_node_aggregate_anomaly({}, {})
        assert a_node is None

    def test_zero_denominator(self):
        """Test epsilon guard when sum(R_i) ≈ 0."""
        anomalies = {"temp": 0.8}
        reliabilities = {"temp": 1e-10}  # Much smaller than epsilon

        a_node = compute_node_aggregate_anomaly(anomalies, reliabilities)

        # weight_sum < epsilon → returns None
        assert a_node is None

    def test_partial_missing(self):
        """Test some sensors missing, others valid."""
        anomalies = {"temp": 0.8, "smoke": None, "pm25": 0.7}
        reliabilities = {"temp": 0.9, "smoke": 0.7, "pm25": 0.8}

        a_node = compute_node_aggregate_anomaly(anomalies, reliabilities)

        # Only temp and pm25 contribute
        # A_node = (0.9*0.8 + 0.8*0.7) / (0.9 + 0.8)
        #        = (0.72 + 0.56) / 1.7 = 0.753
        assert a_node == pytest.approx(0.7529, rel=1e-3)

    def test_out_of_range_anomaly(self):
        """Test validation: A_i must be in [0, 1]."""
        anomalies = {"temp": 1.5}  # Out of range
        reliabilities = {"temp": 0.9}

        with pytest.raises(ValueError, match="out of range"):
            compute_node_aggregate_anomaly(anomalies, reliabilities)

    def test_out_of_range_reliability(self):
        """Test validation: R_i must be in [0, 1]."""
        anomalies = {"temp": 0.8}
        reliabilities = {"temp": 1.2}  # Out of range

        with pytest.raises(ValueError, match="out of range"):
            compute_node_aggregate_anomaly(anomalies, reliabilities)


class TestComputeHazardSpecificAnomaly:
    """Test hazard-specific anomaly A_h computation."""

    def test_hazard_weighted(self):
        """Test hazard-specific weighting."""
        anomalies = {"temp": 0.8, "smoke": 0.6}
        reliabilities = {"temp": 0.9, "smoke": 0.7}
        weights = {"temp": 0.5, "smoke": 0.3}

        a_h = compute_hazard_specific_anomaly(anomalies, reliabilities, weights)

        # A_h = (0.5*0.9*0.8 + 0.3*0.7*0.6) / (0.5*0.9 + 0.3*0.7)
        #     = (0.36 + 0.126) / (0.45 + 0.21)
        #     = 0.486 / 0.66 = 0.7364
        assert a_h == pytest.approx(0.7364, rel=1e-3)

    def test_weights_dont_sum_to_one(self):
        """Test weights are relevance, not probability (don't need to sum to 1)."""
        anomalies = {"temp": 0.8, "smoke": 0.6, "pm25": 0.7}
        reliabilities = {"temp": 0.9, "smoke": 0.7, "pm25": 0.8}
        weights = {"temp": 0.5, "smoke": 0.3, "pm25": 0.3}  # Sum = 1.1

        a_h = compute_hazard_specific_anomaly(anomalies, reliabilities, weights)

        # Should compute without error (weights are relevance)
        assert a_h is not None
        assert 0.0 <= a_h <= 1.0

    def test_missing_anomaly(self):
        """Test missing A_i excluded from hazard computation."""
        anomalies = {"temp": 0.8, "smoke": None}
        reliabilities = {"temp": 0.9, "smoke": 0.7}
        weights = {"temp": 0.5, "smoke": 0.3}

        a_h = compute_hazard_specific_anomaly(anomalies, reliabilities, weights)

        # Only temp contributes
        # A_h = 0.5*0.9*0.8 / (0.5*0.9) = 0.36 / 0.45 = 0.8
        assert a_h == pytest.approx(0.8)

    def test_sensor_not_in_weights(self):
        """Test sensor with no weight excluded."""
        anomalies = {"temp": 0.8, "humidity": 0.5}  # humidity not in weights
        reliabilities = {"temp": 0.9, "humidity": 0.8}
        weights = {"temp": 0.5}  # No weight for humidity

        a_h = compute_hazard_specific_anomaly(anomalies, reliabilities, weights)

        # Only temp contributes (humidity excluded, no weight)
        assert a_h == pytest.approx(0.8)

    def test_empty_weights(self):
        """Test empty weights dict → None."""
        anomalies = {"temp": 0.8}
        reliabilities = {"temp": 0.9}
        weights = {}

        a_h = compute_hazard_specific_anomaly(anomalies, reliabilities, weights)

        assert a_h is None

    def test_all_missing(self):
        """Test all sensors missing → None."""
        anomalies = {"temp": None, "smoke": None}
        reliabilities = {"temp": 0.9, "smoke": 0.7}
        weights = {"temp": 0.5, "smoke": 0.3}

        a_h = compute_hazard_specific_anomaly(anomalies, reliabilities, weights)

        assert a_h is None

    def test_zero_denominator(self):
        """Test epsilon guard when sum(w_ih * R_i) ≈ 0."""
        anomalies = {"temp": 0.8}
        reliabilities = {"temp": 1e-10}  # Very low reliability
        weights = {"temp": 1e-10}  # Very low weight

        a_h = compute_hazard_specific_anomaly(anomalies, reliabilities, weights)

        # weight_sum < epsilon → returns None
        assert a_h is None

    def test_out_of_range_weight(self):
        """Test validation: w_ih must be in [0, 1]."""
        anomalies = {"temp": 0.8}
        reliabilities = {"temp": 0.9}
        weights = {"temp": 1.5}  # Out of range

        with pytest.raises(ValueError, match="out of range"):
            compute_hazard_specific_anomaly(anomalies, reliabilities, weights)
