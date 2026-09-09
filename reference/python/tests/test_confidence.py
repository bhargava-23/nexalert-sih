"""
Confidence reference implementation tests.

Test coverage:
- Coverage computation
- Agreement computation (zero-mean, single-group, multi-group)
- Temporal confidence (fresh, stale, missing, clock error)
- Baseline confidence (all states, missing)
- Final confidence combination
- Weight validation

Specification: Document 04, Section 7
"""
import pytest
from nexalert_reference.confidence import (
    compute_coverage,
    compute_agreement,
    compute_temporal,
    compute_baseline_confidence,
    compute_confidence,
    validate_confidence_weights,
    BASELINE_CONFIDENCE
)


class TestComputeCoverage:
    """Test coverage confidence computation."""

    def test_all_sensors_available(self):
        """All sensors available."""
        availability = {"temp": True, "smoke": True, "humidity": True}
        weights = {"temp": 0.5, "smoke": 0.3, "humidity": 0.2}

        c_cov = compute_coverage(availability, weights)

        assert c_cov == pytest.approx(1.0, abs=1e-9)

    def test_partial_sensors_available(self):
        """Some sensors available, some missing."""
        availability = {"temp": True, "smoke": False, "humidity": True}
        weights = {"temp": 0.5, "smoke": 0.3, "humidity": 0.2}

        c_cov = compute_coverage(availability, weights)

        # temp (0.5) + humidity (0.2) = 0.7 / 1.0 = 0.7
        assert c_cov == pytest.approx(0.7, abs=1e-6)

    def test_no_sensors_available(self):
        """All sensors unavailable."""
        availability = {"temp": False, "smoke": False}
        weights = {"temp": 0.5, "smoke": 0.3}

        c_cov = compute_coverage(availability, weights)

        assert c_cov == pytest.approx(0.0, abs=1e-9)

    def test_empty_weights(self):
        """Empty weights dict returns 0.0."""
        availability = {"temp": True}
        weights = {}

        c_cov = compute_coverage(availability, weights)

        assert c_cov == pytest.approx(0.0, abs=1e-9)

    def test_sensor_not_in_availability_dict(self):
        """Sensor in weights but not in availability dict treated as unavailable."""
        availability = {"temp": True}
        weights = {"temp": 0.5, "smoke": 0.3}

        c_cov = compute_coverage(availability, weights)

        # Only temp (0.5 / 0.8)
        assert c_cov == pytest.approx(0.625, abs=1e-6)


class TestComputeAgreement:
    """Test agreement confidence computation."""

    def test_high_agreement(self):
        """All groups agree (low variance)."""
        group_evidence = {"thermal": 0.8, "smoke": 0.75, "gas": 0.78}
        group_weights = {"thermal": 0.4, "smoke": 0.3, "gas": 0.3}

        c_agree = compute_agreement(group_evidence, group_weights, k_v=2.0)

        # Low variance → high agreement (close to 1.0)
        assert c_agree > 0.95

    def test_low_agreement(self):
        """Groups disagree (high variance)."""
        group_evidence = {"thermal": 0.9, "smoke": 0.1, "gas": 0.5}
        group_weights = {"thermal": 0.4, "smoke": 0.3, "gas": 0.3}

        c_agree = compute_agreement(group_evidence, group_weights, k_v=2.0)

        # High variance → moderate agreement (variance is not extreme with k_v=2.0)
        assert 0.0 <= c_agree <= 1.0
        assert c_agree < 0.9  # Less than high agreement

    def test_zero_mean_agreement(self):
        """All groups have evidence near zero - should return close to 1.0."""
        group_evidence = {"thermal": 0.02, "smoke": 0.01, "gas": 0.005}
        group_weights = {"thermal": 0.4, "smoke": 0.3, "gas": 0.3}

        c_agree = compute_agreement(group_evidence, group_weights, k_v=2.0)

        # Near-zero mean should have high agreement (close to 1.0)
        assert c_agree > 0.999

    def test_single_group(self):
        """Only one group has evidence - should return 1.0."""
        group_evidence = {"thermal": 0.8, "smoke": None, "gas": None}
        group_weights = {"thermal": 0.4, "smoke": 0.3, "gas": 0.3}

        c_agree = compute_agreement(group_evidence, group_weights, k_v=2.0)

        assert c_agree == pytest.approx(1.0, abs=1e-9)

    def test_all_groups_missing(self):
        """All groups have None evidence - should return 1.0."""
        group_evidence = {"thermal": None, "smoke": None}
        group_weights = {"thermal": 0.5, "smoke": 0.5}

        c_agree = compute_agreement(group_evidence, group_weights, k_v=2.0)

        assert c_agree == pytest.approx(1.0, abs=1e-9)

    def test_missing_group_excluded(self):
        """Groups with None evidence excluded from computation."""
        group_evidence = {"thermal": 0.8, "smoke": 0.75, "gas": None}
        group_weights = {"thermal": 0.4, "smoke": 0.3, "gas": 0.3}

        c_agree = compute_agreement(group_evidence, group_weights, k_v=2.0)

        # Only thermal and smoke contribute
        assert 0.0 <= c_agree <= 1.0
        assert c_agree > 0.95  # Should have high agreement

    def test_result_clamped(self):
        """Result is clamped to [0, 1]."""
        group_evidence = {"thermal": 0.5, "smoke": 0.5}
        group_weights = {"thermal": 0.5, "smoke": 0.5}

        c_agree = compute_agreement(group_evidence, group_weights, k_v=2.0)

        assert 0.0 <= c_agree <= 1.0

    def test_group_not_in_weights(self):
        """Group in evidence but not in weights is excluded."""
        group_evidence = {"thermal": 0.8, "smoke": 0.75, "unknown": 0.5}
        group_weights = {"thermal": 0.6, "smoke": 0.4}

        c_agree = compute_agreement(group_evidence, group_weights, k_v=2.0)

        # Only thermal and smoke contribute
        assert 0.0 <= c_agree <= 1.0


class TestComputeTemporal:
    """Test temporal confidence computation."""

    def test_fresh_data(self):
        """Fresh telemetry has high confidence."""
        c_temp = compute_temporal(30.0, 300.0)

        # age=30s, max=300s → 1 - 30/300 = 0.9
        assert c_temp == pytest.approx(0.9, abs=1e-6)

    def test_stale_data(self):
        """Stale telemetry has zero confidence."""
        c_temp = compute_temporal(400.0, 300.0)

        assert c_temp == pytest.approx(0.0, abs=1e-9)

    def test_missing_age(self):
        """Missing age returns 0.0."""
        c_temp = compute_temporal(None, 300.0)

        assert c_temp == pytest.approx(0.0, abs=1e-9)

    def test_negative_age_error(self):
        """Negative age raises ValueError (clock error)."""
        with pytest.raises(ValueError, match="Negative telemetry age"):
            compute_temporal(-10.0, 300.0)


class TestComputeBaselineConfidence:
    """Test baseline confidence computation."""

    def test_ready_state(self):
        """READY state has full confidence."""
        c_base = compute_baseline_confidence("READY")

        assert c_base == pytest.approx(1.0, abs=1e-9)

    def test_learning_state(self):
        """LEARNING state has moderate confidence."""
        c_base = compute_baseline_confidence("LEARNING")

        assert c_base == pytest.approx(0.7, abs=1e-9)

    def test_frozen_state(self):
        """FROZEN state has reduced confidence."""
        c_base = compute_baseline_confidence("FROZEN")

        assert c_base == pytest.approx(0.5, abs=1e-9)

    def test_recovering_state(self):
        """RECOVERING state has moderate confidence."""
        c_base = compute_baseline_confidence("RECOVERING")

        assert c_base == pytest.approx(0.6, abs=1e-9)

    def test_initializing_state(self):
        """INITIALIZING state has low confidence."""
        c_base = compute_baseline_confidence("INITIALIZING")

        assert c_base == pytest.approx(0.3, abs=1e-9)

    def test_missing_state(self):
        """Missing state treated as INITIALIZING."""
        c_base = compute_baseline_confidence(None)

        assert c_base == pytest.approx(0.3, abs=1e-9)

    def test_invalid_state_error(self):
        """Invalid state raises ValueError."""
        with pytest.raises(ValueError, match="Invalid baseline state"):
            compute_baseline_confidence("INVALID")


class TestComputeConfidence:
    """Test final confidence computation."""

    def test_perfect_confidence(self):
        """All components perfect."""
        weights = {
            "coverage": 0.3,
            "agreement": 0.3,
            "temporal": 0.2,
            "baseline": 0.2
        }

        c_h = compute_confidence(1.0, 1.0, 1.0, 1.0, weights)

        assert c_h == pytest.approx(1.0, abs=1e-9)

    def test_weighted_combination(self):
        """Weighted combination of components."""
        weights = {
            "coverage": 0.3,
            "agreement": 0.3,
            "temporal": 0.2,
            "baseline": 0.2
        }

        c_h = compute_confidence(0.5, 0.8, 0.9, 0.7, weights)

        # 0.3*0.5 + 0.3*0.8 + 0.2*0.9 + 0.2*0.7 = 0.15 + 0.24 + 0.18 + 0.14 = 0.71
        assert c_h == pytest.approx(0.71, abs=1e-6)

    def test_zero_confidence(self):
        """All components zero."""
        weights = {
            "coverage": 0.3,
            "agreement": 0.3,
            "temporal": 0.2,
            "baseline": 0.2
        }

        c_h = compute_confidence(0.0, 0.0, 0.0, 0.0, weights)

        assert c_h == pytest.approx(0.0, abs=1e-9)

    def test_invalid_component_value(self):
        """Component outside [0, 1] raises ValueError."""
        weights = {
            "coverage": 0.3,
            "agreement": 0.3,
            "temporal": 0.2,
            "baseline": 0.2
        }

        with pytest.raises(ValueError, match="c_cov must be in"):
            compute_confidence(1.5, 0.8, 0.9, 0.7, weights)

    def test_invalid_weight_keys(self):
        """Missing or extra weight keys raise ValueError."""
        weights = {
            "coverage": 0.4,
            "agreement": 0.3,
            "temporal": 0.3
            # Missing baseline
        }

        with pytest.raises(ValueError, match="must have exactly these keys"):
            compute_confidence(1.0, 1.0, 1.0, 1.0, weights)

    def test_weights_dont_sum_to_one(self):
        """Weights not summing to 1.0 raise ValueError."""
        weights = {
            "coverage": 0.3,
            "agreement": 0.3,
            "temporal": 0.3,
            "baseline": 0.3  # Sum = 1.2
        }

        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            compute_confidence(1.0, 1.0, 1.0, 1.0, weights)


class TestValidateConfidenceWeights:
    """Test confidence weight validation."""

    def test_valid_weights(self):
        """Valid weights pass validation."""
        weights = {
            "coverage": 0.3,
            "agreement": 0.3,
            "temporal": 0.2,
            "baseline": 0.2
        }

        assert validate_confidence_weights(weights) is True

    def test_missing_key(self):
        """Missing required key fails validation."""
        weights = {
            "coverage": 0.4,
            "agreement": 0.3,
            "temporal": 0.3
            # Missing baseline
        }

        with pytest.raises(ValueError, match="must have exactly these keys"):
            validate_confidence_weights(weights)

    def test_extra_key(self):
        """Extra key fails validation."""
        weights = {
            "coverage": 0.3,
            "agreement": 0.3,
            "temporal": 0.2,
            "baseline": 0.2,
            "extra": 0.0
        }

        with pytest.raises(ValueError, match="must have exactly these keys"):
            validate_confidence_weights(weights)

    def test_weight_out_of_range(self):
        """Weight outside [0, 1] fails validation."""
        weights = {
            "coverage": 1.5,
            "agreement": 0.3,
            "temporal": 0.2,
            "baseline": 0.2
        }

        with pytest.raises(ValueError, match="must be in \\[0, 1\\]"):
            validate_confidence_weights(weights)

    def test_weights_dont_sum_to_one(self):
        """Weights not summing to 1.0 fail validation."""
        weights = {
            "coverage": 0.3,
            "agreement": 0.3,
            "temporal": 0.3,
            "baseline": 0.3  # Sum = 1.2
        }

        with pytest.raises(ValueError, match="must sum to 1.0"):
            validate_confidence_weights(weights)

    def test_weights_sum_within_epsilon(self):
        """Weights summing to 1.0 within epsilon pass validation."""
        weights = {
            "coverage": 0.3,
            "agreement": 0.3,
            "temporal": 0.2,
            "baseline": 0.2000000001  # Within epsilon
        }

        assert validate_confidence_weights(weights) is True
