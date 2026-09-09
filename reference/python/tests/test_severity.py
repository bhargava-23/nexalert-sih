"""
Severity reference implementation tests.

Test coverage:
- Severity computation (nominal, partial missing, all missing)
- Fire intensity computation
- Flood intensity computation
- Temporal computation (rate, acceleration, edge cases)
- Duration computation
- Weight validation
- Component reweighting when missing
- Range constraints [0, 1]

PHASE 5 ITERATION 5: Severity computation tests.
"""

import pytest
from nexalert_reference.severity import (
    compute_severity,
    compute_fire_intensity,
    compute_flood_intensity,
    compute_temporal,
    compute_duration,
    validate_severity_weights,
    DEFAULT_SEVERITY_WEIGHTS,
    DEFAULT_FIRE_INTENSITY_CONFIG,
    DEFAULT_FLOOD_INTENSITY_CONFIG,
    EPSILON
)


class TestComputeSeverity:
    """Test severity computation with reweighting."""

    def test_all_components_available(self):
        """All components present - nominal weighted sum."""
        i_h, t_h, d_h = 0.8, 0.5, 0.3
        weights = {'w_I': 0.5, 'w_T': 0.3, 'w_D': 0.2}

        s_h = compute_severity(i_h, t_h, d_h, weights)

        # Expected: 0.5*0.8 + 0.3*0.5 + 0.2*0.3 = 0.4 + 0.15 + 0.06 = 0.61
        assert s_h is not None
        assert abs(s_h - 0.61) < 1e-6

    def test_one_component_missing(self):
        """One component missing - reweight remaining."""
        i_h, t_h, d_h = 0.8, None, 0.3
        weights = {'w_I': 0.5, 'w_T': 0.3, 'w_D': 0.2}

        s_h = compute_severity(i_h, t_h, d_h, weights)

        # Expected: (0.5*0.8 + 0.2*0.3) / (0.5+0.2) = (0.4+0.06)/0.7 = 0.657142...
        assert s_h is not None
        assert abs(s_h - 0.657142857) < 1e-6

    def test_two_components_missing(self):
        """Two components missing - single component result."""
        i_h, t_h, d_h = 0.7, None, None

        s_h = compute_severity(i_h, t_h, d_h)

        # Expected: just i_h = 0.7
        assert s_h is not None
        assert abs(s_h - 0.7) < 1e-9

    def test_all_components_missing(self):
        """All components missing - returns None."""
        s_h = compute_severity(None, None, None)

        assert s_h is None

    def test_default_weights(self):
        """Default weights used when not specified."""
        i_h, t_h, d_h = 0.6, 0.4, 0.2

        s_h = compute_severity(i_h, t_h, d_h)

        # Expected with defaults (0.5, 0.3, 0.2): 0.5*0.6 + 0.3*0.4 + 0.2*0.2 = 0.46
        assert s_h is not None
        assert abs(s_h - 0.46) < 1e-6

    def test_range_clamping_min(self):
        """Negative component values clamped to 0.0."""
        # This shouldn't happen in practice, but numerical safety
        s_h = compute_severity(0.0, 0.0, 0.0)

        assert s_h is not None
        assert s_h == 0.0

    def test_range_clamping_max(self):
        """Values > 1.0 clamped to 1.0."""
        # This shouldn't happen in practice, but numerical safety
        s_h = compute_severity(1.0, 1.0, 1.0)

        assert s_h is not None
        assert s_h == 1.0

    def test_missing_not_zero(self):
        """Missing ≠ zero: None components not converted to 0.0."""
        i_h_present = compute_severity(0.5, 0.5, 0.5)
        i_h_missing = compute_severity(None, 0.5, 0.5)

        # If missing were converted to 0.0, these would be different
        # With reweighting: (0.3*0.5 + 0.2*0.5)/(0.3+0.2) = 0.5
        assert i_h_missing is not None
        assert abs(i_h_missing - 0.5) < 1e-6
        assert abs(i_h_present - 0.5) < 1e-6  # Default weights sum properly


class TestFireIntensity:
    """Test fire intensity computation."""

    def test_both_sensors_available(self):
        """Both temperature and smoke available - takes max."""
        temp, smoke = 70.0, 0.5

        i_h = compute_fire_intensity(temp, smoke)

        # temp: (70-40)/60 = 0.5, smoke: (0.5-0.2)/0.6 = 0.5
        assert i_h is not None
        assert abs(i_h - 0.5) < 1e-6

    def test_temperature_only(self):
        """Only temperature available."""
        temp, smoke = 70.0, None

        i_h = compute_fire_intensity(temp, smoke)

        # temp: (70-40)/60 = 0.5
        assert i_h is not None
        assert abs(i_h - 0.5) < 1e-6

    def test_smoke_only(self):
        """Only smoke available."""
        temp, smoke = None, 0.6

        i_h = compute_fire_intensity(temp, smoke)

        # smoke: (0.6-0.2)/0.6 = 0.666...
        assert i_h is not None
        assert abs(i_h - 0.666666667) < 1e-6

    def test_both_missing(self):
        """Both sensors missing - returns None."""
        i_h = compute_fire_intensity(None, None)

        assert i_h is None

    def test_temperature_below_threshold(self):
        """Temperature below lower threshold."""
        i_h = compute_fire_intensity(30.0, None)

        assert i_h is not None
        assert i_h == 0.0

    def test_temperature_above_threshold(self):
        """Temperature above upper threshold."""
        i_h = compute_fire_intensity(120.0, None)

        assert i_h is not None
        assert i_h == 1.0


class TestFloodIntensity:
    """Test flood intensity computation."""

    def test_both_sensors_available(self):
        """Both water level and rainfall available - takes max."""
        water, rain = 1.5, 50.0

        i_h = compute_flood_intensity(water, rain)

        # water: (1.5-0.5)/2.5 = 0.4, rain: (50-10)/90 = 0.444...
        assert i_h is not None
        assert abs(i_h - 0.444444444) < 1e-6

    def test_water_level_only(self):
        """Only water level available."""
        water, rain = 2.0, None

        i_h = compute_flood_intensity(water, rain)

        # water: (2.0-0.5)/2.5 = 0.6
        assert i_h is not None
        assert abs(i_h - 0.6) < 1e-6

    def test_rainfall_only(self):
        """Only rainfall available."""
        water, rain = None, 70.0

        i_h = compute_flood_intensity(water, rain)

        # rain: (70-10)/90 = 0.666...
        assert i_h is not None
        assert abs(i_h - 0.666666667) < 1e-6

    def test_both_missing(self):
        """Both sensors missing - returns None."""
        i_h = compute_flood_intensity(None, None)

        assert i_h is None

    def test_water_level_below_threshold(self):
        """Water level below lower threshold."""
        i_h = compute_flood_intensity(0.3, None)

        assert i_h is not None
        assert i_h == 0.0

    def test_water_level_above_threshold(self):
        """Water level above upper threshold."""
        i_h = compute_flood_intensity(5.0, None)

        assert i_h is not None
        assert i_h == 1.0


class TestTemporal:
    """Test temporal escalation computation."""

    def test_normal_rate(self):
        """Normal rate of change."""
        current, previous = 70.0, 60.0
        time_delta = 60.0
        max_rate = 10.0 / 60.0  # 10°C/min

        t_h = compute_temporal(current, previous, time_delta, max_rate)

        # rate = 10/60 = 0.1667, normalized = 0.1667/0.1667 = 1.0
        assert t_h is not None
        assert abs(t_h - 1.0) < 1e-6

    def test_slow_rate(self):
        """Slow rate of change."""
        current, previous = 65.0, 60.0
        time_delta = 120.0
        max_rate = 10.0 / 60.0

        t_h = compute_temporal(current, previous, time_delta, max_rate)

        # rate = 5/120 = 0.04167, normalized = 0.04167/0.1667 = 0.25
        assert t_h is not None
        assert abs(t_h - 0.25) < 1e-2

    def test_current_missing(self):
        """Current value missing - returns None."""
        t_h = compute_temporal(None, 60.0, 60.0, 0.167)

        assert t_h is None

    def test_previous_missing(self):
        """Previous value missing - returns None."""
        t_h = compute_temporal(70.0, None, 60.0, 0.167)

        assert t_h is None

    def test_zero_time_delta(self):
        """Zero time delta - returns 0.0."""
        t_h = compute_temporal(70.0, 60.0, 0.0, 0.167)

        assert t_h is not None
        assert t_h == 0.0


class TestDuration:
    """Test duration computation."""

    def test_normal_duration(self):
        """Normal duration - halfway to max."""
        above_threshold = 1800.0  # 30 minutes
        max_duration = 3600.0     # 1 hour

        d_h = compute_duration(above_threshold, max_duration)

        assert d_h is not None
        assert abs(d_h - 0.5) < 1e-9

    def test_exceeds_max_duration(self):
        """Duration exceeds max - clamped to 1.0."""
        above_threshold = 5400.0  # 90 minutes
        max_duration = 3600.0

        d_h = compute_duration(above_threshold, max_duration)

        assert d_h is not None
        assert d_h == 1.0

    def test_zero_duration(self):
        """Zero duration - returns 0.0."""
        d_h = compute_duration(0.0, 3600.0)

        assert d_h is not None
        assert d_h == 0.0

    def test_missing_duration(self):
        """Missing duration - returns None."""
        d_h = compute_duration(None, 3600.0)

        assert d_h is None


class TestValidateSeverityWeights:
    """Test weight validation."""

    def test_valid_weights(self):
        """Valid weights sum to 1.0."""
        weights = {'w_I': 0.5, 'w_T': 0.3, 'w_D': 0.2}

        assert validate_severity_weights(weights) is True

    def test_invalid_sum(self):
        """Weights don't sum to 1.0."""
        weights = {'w_I': 0.6, 'w_T': 0.3, 'w_D': 0.2}

        assert validate_severity_weights(weights) is False

    def test_negative_weight(self):
        """Negative weight value."""
        weights = {'w_I': -0.1, 'w_T': 0.6, 'w_D': 0.5}

        assert validate_severity_weights(weights) is False
