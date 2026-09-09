"""
Risk reference implementation tests.

Test coverage:
- Risk computation (nominal, partial missing, all missing)
- Component reweighting when missing
- Weight validation
- Range constraints [0, 1]
- Relationship to severity (S_h as input)
- Relationship to evidence (E_h as input)
- Confidence separation (C_h NOT in R_h)

PHASE 5 ITERATION 5: Risk computation tests.
"""

import pytest
from nexalert_reference.risk import (
    compute_risk,
    validate_risk_weights,
    DEFAULT_RISK_WEIGHTS,
    EPSILON
)


class TestComputeRisk:
    """Test risk computation with reweighting."""

    def test_all_components_available(self):
        """All components present - nominal weighted sum."""
        e_h, s_h, t_h = 0.8, 0.7, 0.5
        weights = {'w_E': 0.4, 'w_S': 0.4, 'w_T': 0.2}

        r_h = compute_risk(e_h, s_h, t_h, weights)

        # Expected: 0.4*0.8 + 0.4*0.7 + 0.2*0.5 = 0.32 + 0.28 + 0.1 = 0.7
        assert r_h is not None
        assert abs(r_h - 0.7) < 1e-6

    def test_evidence_missing(self):
        """Evidence missing - reweight severity and temporal."""
        e_h, s_h, t_h = None, 0.7, 0.5
        weights = {'w_E': 0.4, 'w_S': 0.4, 'w_T': 0.2}

        r_h = compute_risk(e_h, s_h, t_h, weights)

        # Expected: (0.4*0.7 + 0.2*0.5) / (0.4+0.2) = (0.28+0.1)/0.6 = 0.6333...
        assert r_h is not None
        assert abs(r_h - 0.633333333) < 1e-6

    def test_severity_missing(self):
        """Severity missing - reweight evidence and temporal."""
        e_h, s_h, t_h = 0.8, None, 0.5
        weights = {'w_E': 0.4, 'w_S': 0.4, 'w_T': 0.2}

        r_h = compute_risk(e_h, s_h, t_h, weights)

        # Expected: (0.4*0.8 + 0.2*0.5) / (0.4+0.2) = (0.32+0.1)/0.6 = 0.7
        assert r_h is not None
        assert abs(r_h - 0.7) < 1e-6

    def test_temporal_missing(self):
        """Temporal missing - reweight evidence and severity."""
        e_h, s_h, t_h = 0.8, 0.7, None
        weights = {'w_E': 0.4, 'w_S': 0.4, 'w_T': 0.2}

        r_h = compute_risk(e_h, s_h, t_h, weights)

        # Expected: (0.4*0.8 + 0.4*0.7) / (0.4+0.4) = (0.32+0.28)/0.8 = 0.75
        assert r_h is not None
        assert abs(r_h - 0.75) < 1e-6

    def test_two_components_missing(self):
        """Two components missing - single component result."""
        e_h, s_h, t_h = 0.8, None, None

        r_h = compute_risk(e_h, s_h, t_h)

        # Expected: just e_h = 0.8
        assert r_h is not None
        assert abs(r_h - 0.8) < 1e-9

    def test_all_components_missing(self):
        """All components missing - returns None."""
        r_h = compute_risk(None, None, None)

        assert r_h is None

    def test_default_weights(self):
        """Default weights used when not specified."""
        e_h, s_h, t_h = 0.6, 0.5, 0.4

        r_h = compute_risk(e_h, s_h, t_h)

        # Expected with defaults (0.4, 0.4, 0.2): 0.4*0.6 + 0.4*0.5 + 0.2*0.4 = 0.52
        assert r_h is not None
        assert abs(r_h - 0.52) < 1e-6

    def test_range_clamping(self):
        """Values clamped to [0, 1]."""
        # Edge cases at boundaries
        r_h_min = compute_risk(0.0, 0.0, 0.0)
        r_h_max = compute_risk(1.0, 1.0, 1.0)

        assert r_h_min is not None
        assert r_h_min == 0.0
        assert r_h_max is not None
        assert r_h_max == 1.0


class TestValidateRiskWeights:
    """Test weight validation."""

    def test_valid_weights(self):
        """Valid weights sum to 1.0."""
        weights = {'w_E': 0.4, 'w_S': 0.4, 'w_T': 0.2}

        assert validate_risk_weights(weights) is True

    def test_invalid_sum(self):
        """Weights don't sum to 1.0."""
        weights = {'w_E': 0.5, 'w_S': 0.4, 'w_T': 0.2}

        assert validate_risk_weights(weights) is False

    def test_negative_weight(self):
        """Negative weight value."""
        weights = {'w_E': -0.1, 'w_S': 0.6, 'w_T': 0.5}

        assert validate_risk_weights(weights) is False
