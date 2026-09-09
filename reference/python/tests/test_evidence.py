"""
Evidence reference implementation tests.

Test coverage:
- Nominal evidence computation
- Core evidence floor behavior
- Missing sensor handling
- Threshold boundary cases
- Configuration validation
- Multi-hazard independence
- Zero-denominator behavior

Specification: Document 04, Sections 6.1-6.4
"""
import pytest
from nexalert_reference.evidence import (
    compute_evidence,
    compute_core_coverage,
    apply_core_floor,
    validate_evidence_config
)


class TestComputeEvidence:
    """Test evidence computation with various sensor configurations."""

    def test_fire_nominal(self):
        """Fire evidence with both core sensors matching thresholds."""
        config = {
            "core_evidence": [
                {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 0.5},
                {"sensor": "smoke", "threshold_min": 0.3, "threshold_max": 1.0, "weight": 0.3}
            ],
            "supporting_evidence": [
                {"sensor": "humidity", "threshold_min": 0.0, "threshold_max": 0.3, "weight": 0.1}
            ],
            "core_evidence_floor": {"min_core_coverage": 0.5, "cap_without_core": 0.3}
        }

        sensor_readings = {
            "temperature": 80.0,
            "smoke": 0.6,
            "humidity": 0.2
        }

        e_h = compute_evidence("fire", sensor_readings, config)

        # All sensors match: (0.5 + 0.3 + 0.1) / (0.5 + 0.3 + 0.1) = 0.9 / 0.9 = 1.0
        assert e_h is not None
        assert 0.99 <= e_h <= 1.01

    def test_fire_core_missing(self):
        """Fire evidence with one core sensor missing - should be capped."""
        config = {
            "core_evidence": [
                {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 0.5},
                {"sensor": "smoke", "threshold_min": 0.3, "threshold_max": 1.0, "weight": 0.3}
            ],
            "core_evidence_floor": {"min_core_coverage": 0.5, "cap_without_core": 0.3}
        }

        sensor_readings = {
            "temperature": None,  # Core sensor missing
            "smoke": 0.6
        }

        e_h = compute_evidence("fire", sensor_readings, config)

        # Core coverage = 0.3 / 0.8 = 0.375 < 0.5, so E_h capped at 0.3
        assert e_h is not None
        assert e_h == pytest.approx(0.3, abs=1e-6)

    def test_fire_supporting_only(self):
        """Fire evidence with only supporting evidence (no core) - should be capped."""
        config = {
            "core_evidence": [
                {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 0.5},
                {"sensor": "smoke", "threshold_min": 0.3, "threshold_max": 1.0, "weight": 0.3}
            ],
            "supporting_evidence": [
                {"sensor": "humidity", "threshold_min": 0.0, "threshold_max": 0.3, "weight": 0.1}
            ],
            "core_evidence_floor": {"min_core_coverage": 0.5, "cap_without_core": 0.3}
        }

        sensor_readings = {
            "temperature": None,
            "smoke": None,
            "humidity": 0.2
        }

        e_h = compute_evidence("fire", sensor_readings, config)

        # Core coverage = 0.0, E_h capped at 0.3
        # Raw E_h would be 0.1 / 0.9 ≈ 0.111, capped at 0.3
        assert e_h is not None
        assert e_h <= 0.3

    def test_fire_threshold_boundary(self):
        """Fire evidence with sensor exactly at threshold boundary."""
        config = {
            "core_evidence": [
                {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 0.5}
            ],
            "core_evidence_floor": {"min_core_coverage": 0.5, "cap_without_core": 0.3}
        }

        # Test exact threshold_min
        sensor_readings = {"temperature": 60.0}
        e_h = compute_evidence("fire", sensor_readings, config)
        assert e_h == pytest.approx(1.0, abs=1e-6)

        # Test exact threshold_max
        sensor_readings = {"temperature": 150.0}
        e_h = compute_evidence("fire", sensor_readings, config)
        assert e_h == pytest.approx(1.0, abs=1e-6)

        # Test just below threshold_min (sensor available but doesn't match)
        sensor_readings = {"temperature": 59.9}
        e_h = compute_evidence("fire", sensor_readings, config)
        assert e_h == pytest.approx(0.0, abs=1e-6)  # No match = zero evidence

        # Test just above threshold_max (sensor available but doesn't match)
        sensor_readings = {"temperature": 150.1}
        e_h = compute_evidence("fire", sensor_readings, config)
        assert e_h == pytest.approx(0.0, abs=1e-6)  # No match = zero evidence

    def test_fire_all_missing(self):
        """Fire evidence with all sensors missing - should return None."""
        config = {
            "core_evidence": [
                {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 0.5},
                {"sensor": "smoke", "threshold_min": 0.3, "threshold_max": 1.0, "weight": 0.3}
            ]
        }

        sensor_readings = {
            "temperature": None,
            "smoke": None
        }

        e_h = compute_evidence("fire", sensor_readings, config)

        assert e_h is None, "All sensors missing should return None"

    def test_flood_nominal(self):
        """Flood evidence with water level and rainfall matching."""
        config = {
            "core_evidence": [
                {"sensor": "water_level", "threshold_min": 2.0, "threshold_max": 10.0, "weight": 0.6},
                {"sensor": "rainfall", "threshold_min": 30.0, "threshold_max": 200.0, "weight": 0.3}
            ],
            "core_evidence_floor": {"min_core_coverage": 0.5, "cap_without_core": 0.4}
        }

        sensor_readings = {
            "water_level": 2.5,
            "rainfall": 50.0
        }

        e_h = compute_evidence("flood", sensor_readings, config)

        # Both match: (0.6 + 0.3) / (0.6 + 0.3) = 1.0
        assert e_h is not None
        assert e_h == pytest.approx(1.0, abs=1e-6)

    def test_multi_hazard_independence(self):
        """Verify fire and flood evidence remain independent from same telemetry."""
        # Same sensor readings, different hazard configurations
        sensor_readings = {
            "temperature": 80.0,
            "smoke": 0.6,
            "water_level": 2.5,
            "rainfall": 50.0
        }

        fire_config = {
            "core_evidence": [
                {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 0.5},
                {"sensor": "smoke", "threshold_min": 0.3, "threshold_max": 1.0, "weight": 0.3}
            ]
        }

        flood_config = {
            "core_evidence": [
                {"sensor": "water_level", "threshold_min": 2.0, "threshold_max": 10.0, "weight": 0.6},
                {"sensor": "rainfall", "threshold_min": 30.0, "threshold_max": 200.0, "weight": 0.3}
            ]
        }

        e_h_fire = compute_evidence("fire", sensor_readings, fire_config)
        e_h_flood = compute_evidence("flood", sensor_readings, flood_config)

        # Both should compute independently
        assert e_h_fire is not None
        assert e_h_flood is not None
        # Fire uses temp/smoke, flood uses water_level/rainfall
        assert e_h_fire == pytest.approx(1.0, abs=1e-6)
        assert e_h_flood == pytest.approx(1.0, abs=1e-6)

    def test_partial_threshold_match(self):
        """Some sensors match thresholds, some don't."""
        config = {
            "core_evidence": [
                {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 0.5},
                {"sensor": "smoke", "threshold_min": 0.3, "threshold_max": 1.0, "weight": 0.3}
            ],
            "supporting_evidence": [
                {"sensor": "humidity", "threshold_min": 0.0, "threshold_max": 0.3, "weight": 0.1}
            ]
        }

        sensor_readings = {
            "temperature": 80.0,   # Matches
            "smoke": 0.1,          # Below threshold (doesn't match)
            "humidity": 0.5        # Above threshold (doesn't match)
        }

        e_h = compute_evidence("fire", sensor_readings, config)

        # Only temperature matches: 0.5 / 0.9 ≈ 0.556
        assert e_h is not None
        assert e_h == pytest.approx(0.5 / 0.9, abs=1e-6)

    def test_zero_denominator(self):
        """No sensors configured for hazard - should return None."""
        config = {
            "core_evidence": [],
            "supporting_evidence": []
        }

        sensor_readings = {"temperature": 80.0}

        e_h = compute_evidence("fire", sensor_readings, config)

        assert e_h is None, "No configured sensors should return None"


class TestComputeCoreCoverage:
    """Test core evidence coverage computation."""

    def test_all_core_available(self):
        """All core sensors available."""
        core_rules = [
            {"sensor": "temperature", "weight": 0.5},
            {"sensor": "smoke", "weight": 0.3}
        ]

        sensor_readings = {
            "temperature": 80.0,
            "smoke": 0.6
        }

        coverage = compute_core_coverage(sensor_readings, core_rules)

        assert coverage == pytest.approx(1.0, abs=1e-9)

    def test_partial_core_available(self):
        """Some core sensors missing."""
        core_rules = [
            {"sensor": "temperature", "weight": 0.5},
            {"sensor": "smoke", "weight": 0.3}
        ]

        sensor_readings = {
            "temperature": 80.0,
            "smoke": None  # Missing
        }

        coverage = compute_core_coverage(sensor_readings, core_rules)

        # Only temperature (0.5) out of total (0.8)
        assert coverage == pytest.approx(0.5 / 0.8, abs=1e-6)

    def test_no_core_available(self):
        """All core sensors missing."""
        core_rules = [
            {"sensor": "temperature", "weight": 0.5},
            {"sensor": "smoke", "weight": 0.3}
        ]

        sensor_readings = {
            "temperature": None,
            "smoke": None
        }

        coverage = compute_core_coverage(sensor_readings, core_rules)

        assert coverage == pytest.approx(0.0, abs=1e-9)

    def test_no_core_rules(self):
        """No core evidence rules defined."""
        core_rules = []
        sensor_readings = {"temperature": 80.0}

        coverage = compute_core_coverage(sensor_readings, core_rules)

        assert coverage == pytest.approx(1.0, abs=1e-9)

    def test_sensor_not_in_readings(self):
        """Sensor in rules but not in readings dict."""
        core_rules = [
            {"sensor": "temperature", "weight": 0.5},
            {"sensor": "smoke", "weight": 0.3}
        ]

        sensor_readings = {
            "temperature": 80.0
            # smoke not in dict at all
        }

        coverage = compute_core_coverage(sensor_readings, core_rules)

        # Only temperature available
        assert coverage == pytest.approx(0.5 / 0.8, abs=1e-6)


class TestApplyCoreFloor:
    """Test core evidence floor application."""

    def test_sufficient_coverage_no_cap(self):
        """Core coverage sufficient - no cap applied."""
        e_h = apply_core_floor(0.8, 1.0, 0.5, 0.3)
        assert e_h == pytest.approx(0.8, abs=1e-9)

    def test_insufficient_coverage_capped(self):
        """Core coverage insufficient - E_h capped."""
        e_h = apply_core_floor(0.8, 0.3, 0.5, 0.3)
        assert e_h == pytest.approx(0.3, abs=1e-9)

    def test_below_cap_unchanged(self):
        """E_h already below cap - unchanged."""
        e_h = apply_core_floor(0.2, 0.3, 0.5, 0.3)
        assert e_h == pytest.approx(0.2, abs=1e-9)

    def test_boundary_at_min_coverage(self):
        """Core coverage exactly at minimum."""
        e_h = apply_core_floor(0.8, 0.5, 0.5, 0.3)
        assert e_h == pytest.approx(0.8, abs=1e-9)  # No cap

    def test_boundary_just_below_min_coverage(self):
        """Core coverage just below minimum."""
        e_h = apply_core_floor(0.8, 0.49, 0.5, 0.3)
        assert e_h == pytest.approx(0.3, abs=1e-9)  # Capped


class TestValidateEvidenceConfig:
    """Test evidence configuration validation."""

    def test_valid_config(self):
        """Valid configuration passes validation."""
        config = {
            "core_evidence": [
                {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 0.5}
            ],
            "supporting_evidence": [
                {"sensor": "humidity", "threshold_min": 0.0, "threshold_max": 0.3, "weight": 0.1}
            ],
            "core_evidence_floor": {"min_core_coverage": 0.5, "cap_without_core": 0.3}
        }

        assert validate_evidence_config(config) is True

    def test_empty_config(self):
        """Empty configuration fails validation."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_evidence_config({})

    def test_no_rules(self):
        """Configuration with no evidence rules fails."""
        config = {
            "core_evidence": [],
            "supporting_evidence": []
        }

        with pytest.raises(ValueError, match="at least one evidence rule"):
            validate_evidence_config(config)

    def test_missing_required_field(self):
        """Rule missing required field fails validation."""
        config = {
            "core_evidence": [
                {"sensor": "temperature", "threshold_min": 60.0, "weight": 0.5}
                # Missing threshold_max
            ]
        }

        with pytest.raises(ValueError, match="missing required field"):
            validate_evidence_config(config)

    def test_invalid_weight(self):
        """Weight outside [0, 1] fails validation."""
        config = {
            "core_evidence": [
                {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 1.5}
            ]
        }

        with pytest.raises(ValueError, match="weight must be in"):
            validate_evidence_config(config)

    def test_invalid_thresholds(self):
        """threshold_min > threshold_max fails validation."""
        config = {
            "core_evidence": [
                {"sensor": "temperature", "threshold_min": 150.0, "threshold_max": 60.0, "weight": 0.5}
            ]
        }

        with pytest.raises(ValueError, match="threshold_min.*>.*threshold_max"):
            validate_evidence_config(config)

    def test_invalid_core_floor_missing_field(self):
        """Core floor missing required field fails."""
        config = {
            "core_evidence": [
                {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 0.5}
            ],
            "core_evidence_floor": {"min_core_coverage": 0.5}  # Missing cap_without_core
        }

        with pytest.raises(ValueError, match="missing required field"):
            validate_evidence_config(config)

    def test_invalid_core_floor_out_of_range(self):
        """Core floor parameters outside [0, 1] fail validation."""
        config = {
            "core_evidence": [
                {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 0.5}
            ],
            "core_evidence_floor": {"min_core_coverage": 1.5, "cap_without_core": 0.3}
        }

        with pytest.raises(ValueError, match="must be in \\[0, 1\\]"):
            validate_evidence_config(config)
