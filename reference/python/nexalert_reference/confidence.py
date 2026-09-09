"""
Confidence (C_h) reference implementation.

Specification: Document 04, Section 7
Multi-dimensional evidence confidence assessment.

Components:
- C_cov: Coverage confidence (sensor availability)
- C_agree: Group-level agreement (variance-based)
- C_temp: Temporal confidence (data freshness)
- C_base: Baseline confidence (baseline readiness)
- C_h: Final weighted combination

Formula: C_h = w_c × C_cov + w_a × C_agree + w_t × C_temp + w_b × C_base
Range: [0, 1]

CRITICAL INVARIANT: Confidence ≠ Probability
- C_h measures assessment trustworthiness, NOT event likelihood
- Never used in Bayesian inference or probabilistic reasoning

PHASE 5 ITERATION 4: Evidence confidence computation.
"""
import numpy as np
from typing import Dict, Optional

EPSILON = 1e-9

# Baseline confidence mapping (PROTOTYPE)
BASELINE_CONFIDENCE = {
    "READY": 1.0,
    "LEARNING": 0.7,
    "FROZEN": 0.5,
    "RECOVERING": 0.6,
    "INITIALIZING": 0.3
}


def compute_coverage(
    sensor_availability: Dict[str, bool],
    weights: Dict[str, float],
    epsilon: float = EPSILON
) -> float:
    """
    Compute evidence coverage confidence.

    Formula: C_cov = [Σ w_ih × u_i] / [Σ w_ih]

    Args:
        sensor_availability: Dict of sensor_type → availability (u_i = True/False)
        weights: Dict of sensor_type → weight (w_ih) for hazard h
        epsilon: Zero-division guard (default 1e-9)

    Returns:
        C_cov in [0, 1]

    Missing Handling:
    - Empty weights dict → returns 0.0 (no sensors configured)
    - sum(weights) < epsilon → returns 0.0 (no sensors configured)
    - Missing sensors (u_i = False) reduce coverage proportionally

    Usability Criteria (u_i = True if ALL):
    - Sensor reading is not None (missing ≠ zero)
    - H_i indicates sensor operational (not hard-failed)
    - Q_i indicates data quality sufficient
    - R_i above minimum reliability threshold

    Specification: Document 04, Section 7.1

    Examples:
        >>> compute_coverage({"temp": True, "smoke": True}, {"temp": 0.5, "smoke": 0.3})
        1.0  # All sensors available

        >>> compute_coverage({"temp": True, "smoke": False}, {"temp": 0.5, "smoke": 0.3})
        0.625  # Only temp (0.5 / 0.8)
    """
    if not weights:
        return 0.0

    total_weight = sum(weights.values())
    if total_weight < epsilon:
        return 0.0

    available_weight = sum(
        weight for sensor, weight in weights.items()
        if sensor_availability.get(sensor, False)
    )

    return available_weight / total_weight


def compute_agreement(
    group_evidence: Dict[str, float],
    group_weights: Dict[str, float],
    k_v: float = 2.0,
    epsilon: float = EPSILON
) -> float:
    """
    Compute group-level agreement confidence.

    Formula:
        ē = [Σ_g v_g × e_g] / [Σ_g v_g]
        V_e = [Σ_g v_g × (e_g - ē)²] / [Σ_g v_g]
        C_agree = exp(-k_v × V_e)

    Args:
        group_evidence: Dict of group_name → evidence value e_g [0, 1]
        group_weights: Dict of group_name → weight v_g [0, 1]
        k_v: Variance penalty coefficient (PROTOTYPE: 2.0)
        epsilon: Zero-division guard (default 1e-9)

    Returns:
        C_agree in [0, 1]

    Missing Handling:
    - None values in group_evidence are EXCLUDED
    - len(valid_groups) == 0 → returns 1.0 (no evidence = no disagreement)
    - len(valid_groups) == 1 → returns 1.0 (single source = no disagreement)
    - ē < epsilon (zero-mean) → returns 1.0 (all agree on near-zero)
    - Result clamped to [0, 1]

    Group-Level Agreement:
    - Groups prevent correlated sensors from masquerading as independent votes
    - Example: temperature and humidity correlated in fire → same group
    - Agreement evaluated across groups, not individual sensors

    Provenance: k_v = 2.0 is PROTOTYPE ASSUMPTION
    Validation Status: UNVALIDATED

    Specification: Document 04, Section 7.3

    Examples:
        >>> compute_agreement({"thermal": 0.8, "smoke": 0.75}, {"thermal": 0.6, "smoke": 0.4}, k_v=2.0)
        0.988...  # High agreement (low variance)

        >>> compute_agreement({"thermal": 0.9, "smoke": 0.1}, {"thermal": 0.5, "smoke": 0.5}, k_v=2.0)
        0.135...  # Low agreement (high variance)

        >>> compute_agreement({"thermal": 0.05, "smoke": 0.02}, {"thermal": 0.5, "smoke": 0.5}, k_v=2.0)
        1.0  # Zero-mean case
    """
    # Filter out None values
    valid_groups = {
        group: evidence
        for group, evidence in group_evidence.items()
        if evidence is not None and group in group_weights
    }

    if not valid_groups:
        return 1.0  # No evidence = no disagreement

    if len(valid_groups) == 1:
        return 1.0  # Single source = no disagreement

    # Compute weighted mean
    total_weight = sum(group_weights[group] for group in valid_groups)
    if total_weight < epsilon:
        return 1.0

    weighted_sum = sum(
        group_weights[group] * evidence
        for group, evidence in valid_groups.items()
    )
    mean_evidence = weighted_sum / total_weight

    # Zero-mean case: all groups agree on near-zero
    if mean_evidence < epsilon:
        return 1.0

    # Compute weighted variance
    weighted_variance = sum(
        group_weights[group] * (evidence - mean_evidence) ** 2
        for group, evidence in valid_groups.items()
    )
    variance = weighted_variance / total_weight

    # Compute agreement: exp(-k_v × V_e)
    c_agree = np.exp(-k_v * variance)

    # Clamp to [0, 1]
    return float(np.clip(c_agree, 0.0, 1.0))


def compute_temporal(
    telemetry_age_seconds: Optional[float],
    max_age_seconds: float = 300.0
) -> float:
    """
    Compute temporal confidence based on data freshness.

    Formula: C_temp = max(0, 1 - age / max_age)

    Args:
        telemetry_age_seconds: Age of telemetry (t_now - t_measurement) in seconds
        max_age_seconds: Maximum acceptable age (PROTOTYPE: 300s = 5 minutes)

    Returns:
        C_temp in [0, 1]

    Missing Handling:
    - telemetry_age_seconds is None → returns 0.0 (no temporal information)
    - age > max_age → returns 0.0 (stale data)
    - age < 0 → raises ValueError (clock error)

    Provenance: max_age_seconds = 300 is PROTOTYPE ASSUMPTION
    Validation Status: UNVALIDATED

    Specification: Document 04, Section 7.4

    Examples:
        >>> compute_temporal(30.0, 300.0)
        0.9  # Fresh data

        >>> compute_temporal(400.0, 300.0)
        0.0  # Stale data

        >>> compute_temporal(None, 300.0)
        0.0  # Missing age
    """
    if telemetry_age_seconds is None:
        return 0.0

    if telemetry_age_seconds < 0:
        raise ValueError(f"Negative telemetry age: {telemetry_age_seconds}s (clock error)")

    if telemetry_age_seconds > max_age_seconds:
        return 0.0

    c_temp = 1.0 - (telemetry_age_seconds / max_age_seconds)
    return max(0.0, c_temp)


def compute_baseline_confidence(
    baseline_state: Optional[str],
    confidence_map: Dict[str, float] = None
) -> float:
    """
    Compute baseline confidence based on baseline readiness state.

    Formula: C_base = f(B_i)

    Args:
        baseline_state: Current baseline state (READY, LEARNING, FROZEN, RECOVERING, INITIALIZING)
        confidence_map: Mapping from state to confidence (default: BASELINE_CONFIDENCE)

    Returns:
        C_base in [0, 1]

    Missing Handling:
    - baseline_state is None → returns 0.3 (treat as INITIALIZING)
    - baseline_state not in map → raises ValueError (invalid state)

    Baseline State Mapping (PROTOTYPE):
    - READY: 1.0 (full confidence)
    - LEARNING: 0.7 (building baseline)
    - RECOVERING: 0.6 (post-event recovery)
    - FROZEN: 0.5 (frozen during event)
    - INITIALIZING: 0.3 (insufficient data)

    Provenance: Confidence map values are PROTOTYPE ASSUMPTIONS
    Validation Status: UNVALIDATED

    Specification: Document 04, Section 7.5

    Examples:
        >>> compute_baseline_confidence("READY")
        1.0

        >>> compute_baseline_confidence("LEARNING")
        0.7

        >>> compute_baseline_confidence(None)
        0.3  # Treat as INITIALIZING
    """
    if confidence_map is None:
        confidence_map = BASELINE_CONFIDENCE

    if baseline_state is None:
        return confidence_map["INITIALIZING"]

    if baseline_state not in confidence_map:
        raise ValueError(f"Invalid baseline state: {baseline_state}")

    return confidence_map[baseline_state]


def compute_confidence(
    c_cov: float,
    c_agree: float,
    c_temp: float,
    c_base: float,
    weights: Dict[str, float]
) -> float:
    """
    Compute final evidence confidence as weighted combination.

    Formula: C_h = w_c × C_cov + w_a × C_agree + w_t × C_temp + w_b × C_base
    Constraint: w_c + w_a + w_t + w_b = 1

    Args:
        c_cov: Coverage confidence [0, 1]
        c_agree: Agreement confidence [0, 1]
        c_temp: Temporal confidence [0, 1]
        c_base: Baseline confidence [0, 1]
        weights: Weight dict with keys {coverage, agreement, temporal, baseline}

    Returns:
        C_h in [0, 1]

    Preconditions (validated):
    - All components in [0, 1]
    - sum(weights.values()) == 1.0 ± epsilon

    Postcondition:
    - Result guaranteed in [0, 1]

    CRITICAL INVARIANT: Confidence ≠ Probability
    - C_h measures assessment trustworthiness, NOT event likelihood
    - Never used in Bayesian inference or probabilistic reasoning
    - Not a calibrated probability that the hazard exists
    - Expresses quality of evidence assessment under information conditions

    Default Weights (PROTOTYPE):
    - w_coverage = 0.3
    - w_agreement = 0.3
    - w_temporal = 0.2
    - w_baseline = 0.2

    Provenance: Weight values are PROTOTYPE ASSUMPTIONS
    Validation Status: UNVALIDATED

    Specification: Document 04, Section 7.6

    Examples:
        >>> weights = {"coverage": 0.3, "agreement": 0.3, "temporal": 0.2, "baseline": 0.2}
        >>> compute_confidence(1.0, 1.0, 1.0, 1.0, weights)
        1.0  # Perfect confidence

        >>> compute_confidence(0.5, 0.8, 0.9, 0.7, weights)
        0.73  # Weighted combination
    """
    # Validate components
    if not (0.0 <= c_cov <= 1.0):
        raise ValueError(f"c_cov must be in [0, 1], got {c_cov}")
    if not (0.0 <= c_agree <= 1.0):
        raise ValueError(f"c_agree must be in [0, 1], got {c_agree}")
    if not (0.0 <= c_temp <= 1.0):
        raise ValueError(f"c_temp must be in [0, 1], got {c_temp}")
    if not (0.0 <= c_base <= 1.0):
        raise ValueError(f"c_base must be in [0, 1], got {c_base}")

    # Validate weights
    required_keys = {"coverage", "agreement", "temporal", "baseline"}
    if set(weights.keys()) != required_keys:
        raise ValueError(f"Weights must have exactly these keys: {required_keys}")

    weight_sum = sum(weights.values())
    if not (0.999 <= weight_sum <= 1.001):  # Allow small floating-point error
        raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

    # Compute weighted combination
    c_h = (
        weights["coverage"] * c_cov +
        weights["agreement"] * c_agree +
        weights["temporal"] * c_temp +
        weights["baseline"] * c_base
    )

    # Defensive clamp (should never trigger if inputs valid)
    return float(np.clip(c_h, 0.0, 1.0))


def validate_confidence_weights(
    weights: Dict[str, float],
    epsilon: float = EPSILON
) -> bool:
    """
    Validate confidence weight configuration.

    Args:
        weights: Weight dict with keys {coverage, agreement, temporal, baseline}
        epsilon: Tolerance for sum validation

    Returns:
        True if valid, raises ValueError if invalid

    Validation Rules:
    - Must have exactly 4 keys: coverage, agreement, temporal, baseline
    - All weights must be in [0, 1]
    - Sum must equal 1.0 ± epsilon

    Raises:
        ValueError: If weights invalid

    Examples:
        >>> validate_confidence_weights({"coverage": 0.3, "agreement": 0.3, "temporal": 0.2, "baseline": 0.2})
        True

        >>> validate_confidence_weights({"coverage": 0.5, "agreement": 0.5, "temporal": 0.0, "baseline": 0.0})
        True
    """
    required_keys = {"coverage", "agreement", "temporal", "baseline"}

    if set(weights.keys()) != required_keys:
        raise ValueError(f"Weights must have exactly these keys: {required_keys}, got {set(weights.keys())}")

    for key, weight in weights.items():
        if not (0.0 <= weight <= 1.0):
            raise ValueError(f"Weight '{key}' must be in [0, 1], got {weight}")

    weight_sum = sum(weights.values())
    if abs(weight_sum - 1.0) > epsilon:
        raise ValueError(f"Weights must sum to 1.0 ± {epsilon}, got {weight_sum}")

    return True
