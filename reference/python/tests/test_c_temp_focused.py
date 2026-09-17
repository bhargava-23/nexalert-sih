"""
Track 4: Focused C_temp semantic verification test

Tests the exact repository semantics for temporal confidence:
C_temp = max(0, 1 - age / max_age)

Where age = t_now - t_measurement

Validates:
1. age = 0 → C_temp = 1.0 (maximum confidence)
2. age = max_age → C_temp = 0.0 (zero confidence)
3. age > max_age → C_temp = 0.0 (stale data)
4. age = max_age/2 → C_temp = 0.5 (50% confidence)
5. age < 0 → ValueError (clock error)
6. age = None → C_temp = 0.0 (missing temporal info)
"""

import pytest
from nexalert_reference.confidence import compute_temporal


class TestTemporalConfidenceSemantics:
    """Focused tests proving C_temp repository semantics"""

    def test_zero_age_maximum_confidence(self):
        """Age = 0 seconds → C_temp = 1.0 (measurements just acquired)"""
        age_seconds = 0.0
        max_age = 300.0

        result = compute_temporal(age_seconds, max_age)

        assert result == 1.0, f"Expected 1.0 for zero age, got {result}"

    def test_max_age_zero_confidence(self):
        """Age = max_age → C_temp = 0.0 (stale boundary)"""
        age_seconds = 300.0
        max_age = 300.0

        result = compute_temporal(age_seconds, max_age)

        assert result == 0.0, f"Expected 0.0 for age=max_age, got {result}"

    def test_beyond_max_age_zero_confidence(self):
        """Age > max_age → C_temp = 0.0 (stale data)"""
        age_seconds = 400.0
        max_age = 300.0

        result = compute_temporal(age_seconds, max_age)

        assert result == 0.0, f"Expected 0.0 for age > max_age, got {result}"

    def test_half_max_age_reduced_confidence(self):
        """Age = max_age/2 → C_temp = 0.5 (50% confidence decay)"""
        age_seconds = 150.0
        max_age = 300.0

        result = compute_temporal(age_seconds, max_age)

        expected = 1.0 - (150.0 / 300.0)
        assert abs(result - expected) < 1e-6, f"Expected {expected} for age=150s, got {result}"

    def test_quarter_max_age_linear_decay(self):
        """Age = max_age/4 → C_temp = 0.75 (75% confidence)"""
        age_seconds = 75.0
        max_age = 300.0

        result = compute_temporal(age_seconds, max_age)

        expected = 1.0 - (75.0 / 300.0)
        assert abs(result - expected) < 1e-6, f"Expected {expected} for age=75s, got {result}"

    def test_negative_age_error(self):
        """Age < 0 → ValueError (clock error or future timestamp)"""
        age_seconds = -10.0
        max_age = 300.0

        with pytest.raises(ValueError, match="Negative telemetry age"):
            compute_temporal(age_seconds, max_age)

    def test_none_age_zero_confidence(self):
        """Age = None → C_temp = 0.0 (missing temporal information)"""
        age_seconds = None
        max_age = 300.0

        result = compute_temporal(age_seconds, max_age)

        assert result == 0.0, f"Expected 0.0 for None age, got {result}"

    def test_small_nonzero_age(self):
        """Age = 1 second → C_temp ≈ 0.9967 (very fresh)"""
        age_seconds = 1.0
        max_age = 300.0

        result = compute_temporal(age_seconds, max_age)

        expected = 1.0 - (1.0 / 300.0)
        assert abs(result - expected) < 1e-6, f"Expected {expected} for age=1s, got {result}"

    def test_processing_delay_age(self):
        """Age = 0.1 seconds (100ms processing delay) → C_temp ≈ 0.9997"""
        age_seconds = 0.1
        max_age = 300.0

        result = compute_temporal(age_seconds, max_age)

        expected = 1.0 - (0.1 / 300.0)
        assert abs(result - expected) < 1e-6, f"Expected {expected} for age=100ms, got {result}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
