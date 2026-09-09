"""
Tests for baseline (B_i) reference implementation.

Specification: Document 04, Section 4.1
"""
import pytest
import numpy as np
from nexalert_reference.baseline import (
    BaselineState,
    compute_robust_baseline,
    compute_z_score,
    update_baseline_state,
    EPSILON
)


class TestComputeRobustBaseline:
    """Test robust baseline computation using median and MAD."""

    def test_normal_distribution(self):
        """Test baseline with normally distributed samples."""
        samples = [10.0, 10.2, 10.1, 10.3, 10.0, 9.8, 10.4, 9.9, 10.2, 10.1]
        median, scale = compute_robust_baseline(samples)

        # Median should be around 10.1
        assert 10.0 <= median <= 10.2

        # Scale should be positive
        assert scale > 0

        # Scale should be larger than epsilon
        assert scale > EPSILON

    def test_all_identical_samples(self):
        """Test zero MAD case - all samples identical."""
        samples = [10.0, 10.0, 10.0, 10.0, 10.0]
        median, scale = compute_robust_baseline(samples)

        # Median should be exact
        assert median == 10.0

        # Scale should be epsilon (MAD = 0)
        assert scale == EPSILON

    def test_insufficient_samples(self):
        """Test error when fewer than 2 samples."""
        with pytest.raises(ValueError, match="at least 2 samples"):
            compute_robust_baseline([10.0])

        with pytest.raises(ValueError, match="at least 2 samples"):
            compute_robust_baseline([])

    def test_outlier_robustness(self):
        """Test median/MAD robustness to outliers."""
        samples_no_outlier = [10.0, 10.1, 10.2, 10.3, 10.4]
        samples_with_outlier = [10.0, 10.1, 10.2, 10.3, 100.0]  # Extreme outlier

        median1, scale1 = compute_robust_baseline(samples_no_outlier)
        median2, scale2 = compute_robust_baseline(samples_with_outlier)

        # Median should be similar (robust to outliers)
        assert abs(median1 - median2) < 0.5

        # Scale might increase slightly but not dramatically
        assert scale2 < scale1 * 3  # Not affected too much by single outlier

    def test_exact_two_samples(self):
        """Test minimum valid sample count (2 samples)."""
        samples = [10.0, 12.0]
        median, scale = compute_robust_baseline(samples)

        # Median is average of two values
        assert median == 11.0

        # MAD = |10-11| = |12-11| = 1.0
        # scale = 1.4826 * 1.0 + epsilon
        expected_scale = 1.4826 + EPSILON
        assert abs(scale - expected_scale) < 1e-9


class TestComputeZScore:
    """Test z-score computation."""

    def test_normal_z_score(self):
        """Test standard z-score computation."""
        value = 15.0
        median = 10.0
        scale = 2.0

        z = compute_z_score(value, median, scale)

        # z = (15 - 10) / 2 = 2.5
        assert z == pytest.approx(2.5)

    def test_missing_value(self):
        """Test None value handling - preserve missing != zero."""
        z = compute_z_score(None, 10.0, 2.0)

        # Missing value should return None
        assert z is None

    def test_scale_too_small(self):
        """Test handling when scale < epsilon."""
        value = 10.5
        median = 10.0
        scale = 1e-10  # Much smaller than epsilon

        z = compute_z_score(value, median, scale)

        # Cannot compute meaningful z-score
        assert z is None

    def test_zero_z_score(self):
        """Test value equals median."""
        value = 10.0
        median = 10.0
        scale = 2.0

        z = compute_z_score(value, median, scale)

        # z = (10 - 10) / 2 = 0
        assert z == pytest.approx(0.0)

    def test_negative_z_score(self):
        """Test value below median."""
        value = 8.0
        median = 10.0
        scale = 2.0

        z = compute_z_score(value, median, scale)

        # z = (8 - 10) / 2 = -1.0
        assert z == pytest.approx(-1.0)

    def test_scale_exactly_epsilon(self):
        """Test boundary case: scale exactly equals epsilon."""
        value = 10.5
        median = 10.0
        scale = EPSILON

        z = compute_z_score(value, median, scale, epsilon=EPSILON)

        # scale == epsilon, so condition scale < epsilon is False
        # Should compute normally
        z_expected = (10.5 - 10.0) / EPSILON
        assert z == pytest.approx(z_expected)


class TestUpdateBaselineState:
    """Test baseline state machine transitions."""

    def test_initializing_to_learning(self):
        """Test INITIALIZING → LEARNING transition."""
        current = BaselineState.INITIALIZING
        sample_count = 15

        next_state, stability = update_baseline_state(
            current_state=current,
            sample_count=sample_count,
            min_samples_init=10,
            min_samples_learning=50,
            hazard_state="NORMAL",
            hazard_state_stability_count=0,
            recovery_stability_samples=10
        )

        assert next_state == BaselineState.LEARNING
        assert stability == 1  # Incremented because hazard_state is NORMAL

    def test_learning_to_ready(self):
        """Test LEARNING → READY transition."""
        current = BaselineState.LEARNING
        sample_count = 60

        next_state, stability = update_baseline_state(
            current_state=current,
            sample_count=sample_count,
            min_samples_init=10,
            min_samples_learning=50,
            hazard_state="NORMAL",
            hazard_state_stability_count=5,
            recovery_stability_samples=10
        )

        assert next_state == BaselineState.READY
        assert stability == 6  # Incremented

    def test_ready_to_frozen(self):
        """Test READY → FROZEN when hazard CONFIRMED."""
        current = BaselineState.READY
        sample_count = 100

        next_state, stability = update_baseline_state(
            current_state=current,
            sample_count=sample_count,
            min_samples_init=10,
            min_samples_learning=50,
            hazard_state="CONFIRMED",
            hazard_state_stability_count=5,
            recovery_stability_samples=10
        )

        assert next_state == BaselineState.FROZEN
        assert stability == 0  # Reset on freeze

    def test_frozen_to_recovering(self):
        """Test FROZEN → RECOVERING after stability period."""
        current = BaselineState.FROZEN
        sample_count = 100

        next_state, stability = update_baseline_state(
            current_state=current,
            sample_count=sample_count,
            min_samples_init=10,
            min_samples_learning=50,
            hazard_state="NORMAL",
            hazard_state_stability_count=10,  # Reached stability threshold
            recovery_stability_samples=10
        )

        assert next_state == BaselineState.RECOVERING

    def test_recovering_to_ready(self):
        """Test RECOVERING → READY after sufficient samples."""
        current = BaselineState.RECOVERING
        sample_count = 60

        next_state, stability = update_baseline_state(
            current_state=current,
            sample_count=sample_count,
            min_samples_init=10,
            min_samples_learning=50,
            hazard_state="NORMAL",
            hazard_state_stability_count=15,
            recovery_stability_samples=10
        )

        assert next_state == BaselineState.READY

    def test_stability_reset_on_unfavorable(self):
        """Test stability counter resets when hazard state unfavorable."""
        current = BaselineState.FROZEN

        next_state, stability = update_baseline_state(
            current_state=current,
            sample_count=100,
            min_samples_init=10,
            min_samples_learning=50,
            hazard_state="CRITICAL",  # Unfavorable
            hazard_state_stability_count=5,
            recovery_stability_samples=10
        )

        assert next_state == BaselineState.FROZEN  # No transition
        assert stability == 0  # Reset

    def test_stability_increment_on_favorable(self):
        """Test stability counter increments on NORMAL/WATCH."""
        current = BaselineState.FROZEN

        # Test NORMAL
        next_state, stability = update_baseline_state(
            current_state=current,
            sample_count=100,
            min_samples_init=10,
            min_samples_learning=50,
            hazard_state="NORMAL",
            hazard_state_stability_count=5,
            recovery_stability_samples=10
        )

        assert stability == 6

        # Test WATCH
        next_state, stability = update_baseline_state(
            current_state=current,
            sample_count=100,
            min_samples_init=10,
            min_samples_learning=50,
            hazard_state="WATCH",
            hazard_state_stability_count=5,
            recovery_stability_samples=10
        )

        assert stability == 6

    def test_no_circular_dependency(self):
        """
        Test that baseline state machine only READS hazard state.

        This test verifies the function signature and behavior:
        - hazard_state is INPUT ONLY (string parameter)
        - Function returns (next_baseline_state, stability) - no hazard state returned
        - No mutation of hazard state
        """
        current = BaselineState.READY
        sample_count = 100
        initial_hazard_state = "CONFIRMED"

        # Call the function
        next_state, stability = update_baseline_state(
            current_state=current,
            sample_count=sample_count,
            min_samples_init=10,
            min_samples_learning=50,
            hazard_state=initial_hazard_state,
            hazard_state_stability_count=0,
            recovery_stability_samples=10
        )

        # Function returns only baseline state and stability
        # No hazard state returned - confirms no circular write
        assert isinstance(next_state, BaselineState)
        assert isinstance(stability, int)

        # Baseline transitions to FROZEN by reading hazard state
        assert next_state == BaselineState.FROZEN
