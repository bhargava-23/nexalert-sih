"""
Health (H_i) reference implementation.

Specification: Document 04, Section 3.1
Formula: H_i^soft = Σ_j w_ij · D_ij,  H_i = 0 if F_i=1 else H_i^soft
Range: [0, 1]

PHASE 4 DECISION (human-approved): Missing diagnostics behavior not specified in Document 04.
This implementation preserves missingness and signals incomplete diagnostics explicitly.
See "Phase 4 Decisions" section. Must be documented in DECISIONS.md.
"""
import numpy as np
from typing import Dict, Optional, Tuple

EPSILON = 1e-9


def compute_health(
    diagnostics: Dict[str, float],
    weights: Dict[str, float],
    hard_failure: bool = False
) -> Tuple[Optional[float], bool]:
    """
    Compute sensor health H_i.

    Args:
        diagnostics: D_ij values (normalized 0-1), keys match weights
        weights: w_ij values (must sum to 1)
        hard_failure: F_i flag (True forces H_i = 0)

    Returns:
        (H_i or None, diagnostics_complete: bool)
        - H_i in [0,1] when all required diagnostics present
        - None when diagnostics incomplete (preserves missing != zero)
        - diagnostics_complete flag indicates if computation used full weight set

    Specification: Document 04, Section 3.1

    Invariants:
        - Hard failure F_i=1 forces H_i=0 (Doc 04 Sec 3.1)
        - Missing diagnostics are NOT treated as zero (IMPLEMENTATION_CONSTITUTION.md Sec 3)
        - Weights must sum to 1 within epsilon (Doc 04 Sec 3.1)
        - All D_ij must be in [0, 1] (Doc 04 Sec 3.1)

    PHASE 4 DECISION (human-approved): Document 04 does not specify missing diagnostic behavior.
    Returns (None, False) for incomplete diagnostics per approved Phase 4 decision,
    preserving missing != zero and signaling degraded information explicitly.
    Decision documented in "Phase 4 Decisions" section; must record in DECISIONS.md.
    """
    # Hard failure gate (Doc 04 Sec 3.1)
    if hard_failure:
        return (0.0, True)  # F_i=1 forces H_i=0

    # Validate weights sum to 1
    weight_sum = sum(weights.values())
    if not (1.0 - EPSILON <= weight_sum <= 1.0 + EPSILON):
        raise ValueError(f"Weights must sum to 1 per Doc 04 Sec 3.1, got {weight_sum}")

    # Check for missing diagnostics
    missing_keys = set(weights.keys()) - set(diagnostics.keys())
    if missing_keys:
        # PHASE 4 DECISION (human-approved): Doc 04 does not specify missing diagnostic behavior.
        # Return None to preserve missing != zero per approved decision, signal incomplete with flag.
        return (None, False)

    # Compute weighted sum H_i^soft
    h_soft = 0.0
    for key, w_ij in weights.items():
        d_ij = diagnostics[key]

        # Validate D_ij range (Doc 04 Sec 3.1: normalized)
        if not (0.0 <= d_ij <= 1.0):
            raise ValueError(f"Diagnostic {key}={d_ij} out of range [0,1] per Doc 04 Sec 3.1")

        h_soft += w_ij * d_ij

    # Clamp to [0, 1] (defensive)
    h_i = np.clip(h_soft, 0.0, 1.0)

    return (float(h_i), True)
