"""
Baseline (B_i) reference implementation.

Specification: Document 04, Section 4.1
Formula: Robust baseline using median and MAD (Median Absolute Deviation)
         m_i = median(x_i)
         MAD_i = median(|x_i - m_i|)
         s_i = 1.4826 * MAD_i + epsilon
         z_i = (x_i - m_i) / s_i

Range: z_i is unbounded (standardized score)

PHASE 5: Baseline state machine and robust baseline computation.
"""
import numpy as np
from typing import List, Optional, Tuple
from enum import Enum

EPSILON = 1e-9


class BaselineState(str, Enum):
    """
    Baseline readiness states.

    Specification: Document 04, Section 4.1
    """
    INITIALIZING = "INITIALIZING"  # Collecting initial samples
    LEARNING = "LEARNING"          # Building baseline
    READY = "READY"                # Baseline ready for use
    FROZEN = "FROZEN"              # Intentionally frozen during event
    RECOVERING = "RECOVERING"      # Post-event recovery


def compute_robust_baseline(
    samples: List[float],
    epsilon: float = EPSILON
) -> Tuple[float, float]:
    """
    Compute robust baseline using median and MAD.

    Args:
        samples: Historical samples (minimum 2 required)
        epsilon: Zero-division guard (default 1e-9)

    Returns:
        (median, scale) where scale = 1.4826 * MAD + epsilon

    Raises:
        ValueError: If len(samples) < 2

    Missing Handling:
    - samples list cannot contain None (filtered upstream)
    - len(samples) < 2: raises ValueError
    - MAD = 0 (all samples identical): scale = epsilon (prevents divide-by-zero)

    Mathematical Properties:
    - Median: Robust to outliers, 50th percentile
    - MAD: Robust scale estimator, median of absolute deviations
    - 1.4826: Scale factor for Gaussian equivalence (MAD → stddev)
    - Epsilon guard: Prevents divide-by-zero when all samples identical

    Specification: Document 04, Section 4.1

    Examples:
        >>> compute_robust_baseline([10.0, 10.2, 10.1, 10.3, 10.0])
        (10.1, 0.2223...)

        >>> compute_robust_baseline([10.0, 10.0, 10.0])  # Zero MAD
        (10.0, 1e-9)  # scale = epsilon
    """
    if len(samples) < 2:
        raise ValueError(
            f"Baseline computation requires at least 2 samples, got {len(samples)}"
        )

    # Compute median
    median = float(np.median(samples))

    # Compute MAD (Median Absolute Deviation)
    absolute_deviations = np.abs(np.array(samples) - median)
    mad = float(np.median(absolute_deviations))

    # Convert MAD to scale (Gaussian-equivalent stddev)
    # 1.4826 = 1 / Φ^(-1)(3/4) where Φ is standard normal CDF
    scale = 1.4826 * mad + epsilon

    return (median, scale)


def compute_z_score(
    value: Optional[float],
    median: float,
    scale: float,
    epsilon: float = EPSILON
) -> Optional[float]:
    """
    Compute z-score for anomaly detection.

    Args:
        value: Current observation (or None)
        median: Baseline median
        scale: Baseline scale (from compute_robust_baseline)
        epsilon: Scale threshold for meaningful z-score

    Returns:
        z_i (standardized score) or None if value is None or scale too small

    Missing Handling:
    - value is None → returns None (preserve missing != zero)
    - scale < epsilon → returns None (cannot compute meaningful z-score)

    Mathematical Properties:
    - z_i = (x - median) / scale
    - z_i = 0 means value equals baseline median
    - |z_i| = 1 means value is 1 scale unit from median
    - Large |z_i| indicates anomaly

    Specification: Document 04, Section 4.1

    Examples:
        >>> compute_z_score(15.0, 10.0, 2.0)
        2.5  # Value is 2.5 scale units above median

        >>> compute_z_score(None, 10.0, 2.0)
        None  # Missing value preserved

        >>> compute_z_score(10.0, 10.0, 1e-10)
        None  # Scale too small (< epsilon)
    """
    # Missing value handling
    if value is None:
        return None

    # Scale too small (all samples identical or near-identical)
    if scale < epsilon:
        return None

    # Compute standardized deviation
    z_score = (value - median) / scale

    return float(z_score)


def update_baseline_state(
    current_state: BaselineState,
    sample_count: int,
    min_samples_init: int,
    min_samples_learning: int,
    hazard_state: str,
    hazard_state_stability_count: int,
    recovery_stability_samples: int
) -> Tuple[BaselineState, int]:
    """
    State transition logic for baseline readiness.

    Args:
        current_state: Current baseline state
        sample_count: Number of samples collected
        min_samples_init: Samples required to exit INITIALIZING (PROTOTYPE: 10)
        min_samples_learning: Samples required to reach READY (PROTOTYPE: 50)
        hazard_state: Current hazard state (INPUT ONLY - no circular write)
        hazard_state_stability_count: Consecutive samples with favorable hazard state
        recovery_stability_samples: Samples required for FROZEN → RECOVERING

    Returns:
        (next_baseline_state, updated_stability_count)

    State Ownership (NO CIRCULAR DEPENDENCY):
    - Baseline state machine OWNS baseline state transitions
    - Hazard state machine OWNS hazard state transitions
    - Baseline reads hazard state as INPUT (no circular write)

    Freeze/Recovery Logic (PROTOTYPE - REQUIRE APPROVAL):
    - FREEZE trigger: hazard_state in ["CONFIRMED", "CRITICAL"]
    - RECOVERY trigger: hazard_state in ["NORMAL", "WATCH"] AND
                       remained there for recovery_stability_samples consecutive samples

    State Transitions:
    INITIALIZING (sample_count >= min_samples_init) → LEARNING
    LEARNING (sample_count >= min_samples_learning) → READY
    READY (hazard_state in ["CONFIRMED", "CRITICAL"]) → FROZEN
    FROZEN (hazard_state in ["NORMAL", "WATCH"] for N samples) → RECOVERING
    RECOVERING (sample_count >= min_samples_learning) → READY

    During FROZEN:
    - Historical samples retained (not discarded)
    - No baseline recomputation
    - Z-scores computed using frozen median/scale

    During RECOVERING:
    - Samples accumulate
    - Recomputation begins when sample_count >= min_samples_learning

    Stability Counter:
    - Increments when hazard_state in ["NORMAL", "WATCH"]
    - Resets to 0 when hazard_state NOT in ["NORMAL", "WATCH"]

    Specification: Document 04, Section 4.1
    Provenance: State thresholds are PROTOTYPE ASSUMPTIONS
    Configuration Version: 1.0-prototype

    Examples:
        >>> update_baseline_state(BaselineState.INITIALIZING, 15, 10, 50, "NORMAL", 0, 10)
        (BaselineState.LEARNING, 1)

        >>> update_baseline_state(BaselineState.READY, 100, 10, 50, "CONFIRMED", 0, 10)
        (BaselineState.FROZEN, 0)
    """
    next_state = current_state
    stability = hazard_state_stability_count

    # Track stability for recovery
    if hazard_state in ["NORMAL", "WATCH"]:
        stability += 1
    else:
        stability = 0  # Reset when hazard state unfavorable

    # State transitions
    if current_state == BaselineState.INITIALIZING:
        if sample_count >= min_samples_init:
            next_state = BaselineState.LEARNING

    elif current_state == BaselineState.LEARNING:
        if sample_count >= min_samples_learning:
            next_state = BaselineState.READY

    elif current_state == BaselineState.READY:
        # FREEZE trigger: reads hazard state
        if hazard_state in ["CONFIRMED", "CRITICAL"]:
            next_state = BaselineState.FROZEN
            stability = 0  # Reset stability counter on freeze

    elif current_state == BaselineState.FROZEN:
        # RECOVERY trigger: reads hazard state + stability
        if stability >= recovery_stability_samples:
            next_state = BaselineState.RECOVERING

    elif current_state == BaselineState.RECOVERING:
        if sample_count >= min_samples_learning:
            next_state = BaselineState.READY

    return (next_state, stability)
