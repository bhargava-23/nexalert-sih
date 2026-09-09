"""
Anomaly (A_i, A_node, A_h) reference implementation.

Specification: Document 04, Sections 4.2, 4.3
Formulas:
  A_i = 1 - exp(-min(|z_i|, z_cap) / lambda)
  A_node = sum(R_i * A_i) / (sum(R_i) + epsilon)
  A_h = sum(w_ih * R_i * A_i) / (sum(w_ih * R_i) + epsilon)

Range: [0, 1]

PHASE 5: Individual, node aggregate, and hazard-specific anomaly detection.
"""
import numpy as np
from typing import Dict, Optional

EPSILON = 1e-9


def compute_individual_anomaly(
    z_score: Optional[float],
    lambda_param: float = 2.0,
    z_cap: float = 5.0
) -> Optional[float]:
    """
    Compute individual anomaly score from z-score.

    Args:
        z_score: Standardized deviation from baseline
        lambda_param: Exponential decay rate (PROTOTYPE: 2.0)
        z_cap: Maximum z-score clipping (PROTOTYPE: 5.0)

    Returns:
        A_i in [0, 1] or None if z_score is None

    Missing Handling:
    - z_score is None → returns None (preserve missing != zero)

    Edge Cases:
    - z_score = 0 → A_i ≈ 0 (no anomaly)
    - |z_score| → ∞ → A_i → 1 (capped at z_cap)
    - lambda_param must be > 0 (validated in configuration)
    - z_cap must be > 0 (validated in configuration)

    Mathematical Properties:
    - Monotonic: Higher |z| → higher A_i
    - Asymptotic: Approaches 1.0 at high |z|
    - Symmetric: A_i(-z) = A_i(z)
    - Smooth: Continuous, differentiable

    Formula: A_i = 1 - exp(-min(|z_i|, z_cap) / lambda)

    Provenance: lambda_param=2.0, z_cap=5.0 are PROTOTYPE ASSUMPTIONS
    Validation Status: UNVALIDATED

    Specification: Document 04, Section 4.2

    Examples:
        >>> compute_individual_anomaly(0.0, 2.0, 5.0)
        0.0  # No anomaly

        >>> compute_individual_anomaly(2.0, 2.0, 5.0)
        0.632...  # Moderate anomaly

        >>> compute_individual_anomaly(10.0, 2.0, 5.0)  # Capped at z_cap
        0.917...  # High anomaly

        >>> compute_individual_anomaly(None, 2.0, 5.0)
        None  # Missing preserved
    """
    # Missing value handling
    if z_score is None:
        return None

    # Validate parameters (defensive - should be validated in configuration)
    if lambda_param <= 0:
        raise ValueError(f"lambda_param must be > 0, got {lambda_param}")
    if z_cap <= 0:
        raise ValueError(f"z_cap must be > 0, got {z_cap}")

    # Clip z-score magnitude
    z_clamped = min(abs(z_score), z_cap)

    # Compute anomaly: 1 - exp(-z / lambda)
    a_i = 1.0 - np.exp(-z_clamped / lambda_param)

    # Clamp to [0, 1] (defensive, should always be in range)
    return float(np.clip(a_i, 0.0, 1.0))


def compute_node_aggregate_anomaly(
    anomalies: Dict[str, float],
    reliabilities: Dict[str, float],
    epsilon: float = EPSILON
) -> Optional[float]:
    """
    Compute reliability-weighted node aggregate anomaly.

    Args:
        anomalies: Dict of sensor_type → A_i values [0, 1]
        reliabilities: Dict of sensor_type → R_i values [0, 1]
        epsilon: Zero-division guard (PROTOTYPE: 1e-9)

    Returns:
        A_node in [0, 1] or None if no valid anomalies

    Missing Handling:
    - If anomalies dict is empty → returns None
    - If any A_i is None → that sensor excluded from computation
    - If any R_i is None → that sensor excluded from computation
    - If all sensors excluded → returns None (preserve missing != zero)
    - If sum(R_i) ≈ 0 (< epsilon) → returns None (no reliable sensors)

    Validation:
    - All A_i values must be in [0, 1]
    - All R_i values must be in [0, 1]
    - Keys in anomalies and reliabilities must match

    Formula: A_node = sum(R_i * A_i) / (sum(R_i) + epsilon)

    Provenance: epsilon=1e-9 is PROTOTYPE ASSUMPTION

    Specification: Document 04, Section 4.2

    Examples:
        >>> anomalies = {"temp": 0.8, "smoke": 0.6}
        >>> reliabilities = {"temp": 0.9, "smoke": 0.7}
        >>> compute_node_aggregate_anomaly(anomalies, reliabilities)
        0.725  # Weighted average

        >>> anomalies = {"temp": 0.8, "smoke": None}
        >>> reliabilities = {"temp": 0.9, "smoke": 0.7}
        >>> compute_node_aggregate_anomaly(anomalies, reliabilities)
        0.8  # Only temp contributes
    """
    if not anomalies:
        return None

    weighted_sum = 0.0
    weight_sum = 0.0

    for sensor_type, a_i in anomalies.items():
        # Skip missing anomalies
        if a_i is None:
            continue

        # Get reliability (skip if missing)
        r_i = reliabilities.get(sensor_type)
        if r_i is None:
            continue

        # Validate ranges
        if not (0.0 <= a_i <= 1.0):
            raise ValueError(f"A_i for {sensor_type} = {a_i} out of range [0, 1]")
        if not (0.0 <= r_i <= 1.0):
            raise ValueError(f"R_i for {sensor_type} = {r_i} out of range [0, 1]")

        # Accumulate weighted sum
        weighted_sum += r_i * a_i
        weight_sum += r_i

    # No valid sensors
    if weight_sum < epsilon:
        return None

    # Compute weighted average
    a_node = weighted_sum / weight_sum

    # Clamp to [0, 1] (defensive)
    return float(np.clip(a_node, 0.0, 1.0))


def compute_hazard_specific_anomaly(
    anomalies: Dict[str, float],
    reliabilities: Dict[str, float],
    weights: Dict[str, float],
    epsilon: float = EPSILON
) -> Optional[float]:
    """
    Compute hazard-specific weighted anomaly.

    Args:
        anomalies: Dict of sensor_type → A_i values [0, 1]
        reliabilities: Dict of sensor_type → R_i values [0, 1]
        weights: Dict of sensor_type → w_ih values [0, 1] (PROTOTYPE)
        epsilon: Zero-division guard

    Returns:
        A_h in [0, 1] or None if no valid anomalies

    Missing Handling:
    - Same as compute_node_aggregate_anomaly
    - Additionally: if weights dict is empty → returns None

    Validation:
    - All A_i, R_i, w_ih values must be in [0, 1]
    - Keys must match across all three dicts
    - Weights do NOT need to sum to 1 (hazard-specific relevance, not probability)

    Formula: A_h = sum(w_ih * R_i * A_i) / (sum(w_ih * R_i) + epsilon)

    Provenance: Weights are PROTOTYPE ASSUMPTIONS per hazard type
    Validation Status: UNVALIDATED - requires domain expert review
    Configuration Version: 1.0-prototype

    Example Fire Weights (PROTOTYPE):
    - temperature: 0.5
    - smoke: 0.3
    - pm25: 0.3
    - humidity: 0.1
    (Note: weights sum to 1.2, not 1.0 - this is correct for relevance weighting)

    Specification: Document 04, Section 4.3

    Examples:
        >>> anomalies = {"temp": 0.8, "smoke": 0.6}
        >>> reliabilities = {"temp": 0.9, "smoke": 0.7}
        >>> weights = {"temp": 0.5, "smoke": 0.3}
        >>> compute_hazard_specific_anomaly(anomalies, reliabilities, weights)
        0.744...  # Hazard-weighted

        >>> anomalies = {"temp": 0.8, "smoke": None}
        >>> reliabilities = {"temp": 0.9, "smoke": 0.7}
        >>> weights = {"temp": 0.5, "smoke": 0.3}
        >>> compute_hazard_specific_anomaly(anomalies, reliabilities, weights)
        0.8  # Only temp contributes
    """
    if not anomalies or not weights:
        return None

    weighted_sum = 0.0
    weight_sum = 0.0

    for sensor_type, a_i in anomalies.items():
        # Skip missing anomalies
        if a_i is None:
            continue

        # Get reliability (skip if missing)
        r_i = reliabilities.get(sensor_type)
        if r_i is None:
            continue

        # Get weight (skip if not in weights dict)
        w_ih = weights.get(sensor_type)
        if w_ih is None:
            continue

        # Validate ranges
        if not (0.0 <= a_i <= 1.0):
            raise ValueError(f"A_i for {sensor_type} = {a_i} out of range [0, 1]")
        if not (0.0 <= r_i <= 1.0):
            raise ValueError(f"R_i for {sensor_type} = {r_i} out of range [0, 1]")
        if not (0.0 <= w_ih <= 1.0):
            raise ValueError(f"w_ih for {sensor_type} = {w_ih} out of range [0, 1]")

        # Accumulate weighted sum
        weighted_sum += w_ih * r_i * a_i
        weight_sum += w_ih * r_i

    # No valid sensors
    if weight_sum < epsilon:
        return None

    # Compute weighted average
    a_h = weighted_sum / weight_sum

    # Clamp to [0, 1] (defensive)
    return float(np.clip(a_h, 0.0, 1.0))
