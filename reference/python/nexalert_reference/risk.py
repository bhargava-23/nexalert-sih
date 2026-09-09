"""
Risk (R_h) reference implementation.

Specification: Document 04, Section 9
Operational risk index combining evidence, severity, and temporal components.

Formula: R_h = w_E × E_h + w_S × S_h + w_T × T_h
Range: [0, 1] or None

CRITICAL INVARIANT: Operational Risk ≠ Probability
- R_h measures operational urgency, NOT disaster probability
- Confidence handled separately by state engine (not multiplied into R_h)

PHASE 5 ITERATION 5: Risk computation.

Design Decision:
- D16: Reweight remaining components when some missing (same as severity)

Missing Semantics:
- All components None → R_h = None (cannot compute)
- Some components None → reweight remaining to sum to 1.0
- Never convert None to 0.0 (missing ≠ zero invariant)

Dependency Flow:
- E_h from Iteration 4 (evidence.py)
- S_h from Iteration 5 (severity.py)
- T_h from severity temporal computation
- C_h NOT consumed (handled by state engine, Iteration 6)

Provenance: ALL weight values are PROTOTYPE ASSUMPTIONS
Validation Status: UNVALIDATED - NOT scientifically authoritative
Owner: Phase 5 implementation (requires domain expert takeover)
Config Version: 1.0-prototype
"""

from typing import Optional, Dict

# Numerical constants
EPSILON = 1e-9

# Prototype risk weights (UNVALIDATED)
DEFAULT_RISK_WEIGHTS = {
    'w_E': 0.4,  # Evidence weight
    'w_S': 0.4,  # Severity weight
    'w_T': 0.2   # Temporal/threat weight
}


def compute_risk(
    e_h: Optional[float],
    s_h: Optional[float],
    t_h: Optional[float],
    weights: Optional[Dict[str, float]] = None,
    epsilon: float = EPSILON
) -> Optional[float]:
    """
    Compute operational risk from components with reweighting.

    Specification: Document 04, Section 9.1
    Decision: D16 (component reweighting strategy)

    Args:
        e_h: Evidence component [0, 1] or None (from Iteration 4)
        s_h: Severity component [0, 1] or None (from Iteration 5)
        t_h: Temporal/threat component [0, 1] or None
        weights: {'w_E': float, 'w_S': float, 'w_T': float} or None for defaults
        epsilon: Zero-division guard

    Returns:
        R_h in [0, 1] or None

    Formula (all components available):
        R_h = w_E × E_h + w_S × S_h + w_T × T_h

    Missing Semantics (D16):
        - All None → returns None (cannot compute)
        - Some None → reweight remaining to sum to 1.0
        - Never converts None to 0.0 (missing ≠ zero)

    Preserves Invariants:
        - Missing ≠ zero
        - Risk ≠ probability (R_h is operational urgency, not P(disaster))
        - Confidence separation (C_h NOT multiplied into R_h)
        - Multi-hazard independence

    Dependency Flow:
        E_h (evidence) ← Iteration 4
        S_h (severity) ← Iteration 5
        T_h (temporal) ← Iteration 5 severity computation
        C_h NOT consumed ← Handled by state engine (Iteration 6)

    Examples:
        >>> compute_risk(0.8, 0.7, 0.5)  # All available
        0.69  # 0.4*0.8 + 0.4*0.7 + 0.2*0.5

        >>> compute_risk(0.8, None, 0.5)  # Severity missing
        0.7333  # Reweight: (0.4*0.8 + 0.2*0.5) / (0.4+0.2)

        >>> compute_risk(None, None, None)  # All missing
        None

    Provenance: Default weights are PROTOTYPE ASSUMPTIONS
    Validation Status: UNVALIDATED
    """
    if weights is None:
        weights = DEFAULT_RISK_WEIGHTS

    # Build component list with weights
    components = [
        (e_h, weights['w_E']),
        (s_h, weights['w_S']),
        (t_h, weights['w_T'])
    ]

    # Filter to available components
    available = [(val, w) for val, w in components if val is not None]

    # All missing → None (cannot compute)
    if len(available) == 0:
        return None

    # Sum available weights for renormalization
    total_weight = sum(w for _, w in available)

    # Guard against invalid weight configuration
    if total_weight < epsilon:
        return None

    # Weighted sum with renormalization
    r_h = sum(val * w for val, w in available) / total_weight

    # Clamp to [0, 1] for numerical safety
    return max(0.0, min(1.0, r_h))


def validate_risk_weights(
    weights: Dict[str, float],
    epsilon: float = EPSILON
) -> bool:
    """
    Validate risk weight configuration.

    Args:
        weights: {'w_E': float, 'w_S': float, 'w_T': float}
        epsilon: Tolerance for sum-to-one constraint

    Returns:
        True if valid, False otherwise

    Validation Rules:
        - All weights present: w_E, w_S, w_T
        - All weights in [0, 1]
        - Weights sum to 1.0 ± epsilon

    Examples:
        >>> validate_risk_weights({'w_E': 0.4, 'w_S': 0.4, 'w_T': 0.2})
        True

        >>> validate_risk_weights({'w_E': 0.5, 'w_S': 0.4, 'w_T': 0.2})
        False  # Sum != 1.0

        >>> validate_risk_weights({'w_E': -0.1, 'w_S': 0.6, 'w_T': 0.5})
        False  # Negative weight
    """
    required_keys = {'w_E', 'w_S', 'w_T'}

    # Check all keys present
    if set(weights.keys()) != required_keys:
        return False

    # Check all weights in [0, 1]
    for w in weights.values():
        if w < 0 or w > 1:
            return False

    # Check sum to 1.0 ± epsilon
    total = weights['w_E'] + weights['w_S'] + weights['w_T']
    if abs(total - 1.0) > epsilon:
        return False

    return True
