"""
Reliability (R_i) reference implementation.

Specification: Document 04, Section 3.3
Formula: R_i = H_i × Q_i × K_i
Range: [0, 1]
"""
import numpy as np
from typing import Optional


def compute_reliability(
    h_i: Optional[float],
    q_i: Optional[float],
    k_i: Optional[float]
) -> Optional[float]:
    """
    Compute evidence reliability R_i.

    Args:
        h_i: Sensor health H_i [0, 1] or None
        q_i: Signal quality Q_i [0, 1] or None
        k_i: Calibration validity K_i [0, 1] or None

    Returns:
        R_i in [0, 1], or None if any input is None

    Specification: Document 04, Section 3.3

    Invariants:
        - R_i = 0 if any component is 0 (strict trust gate, Doc 04 Sec 3.3)
        - R_i is NOT double-counted in confidence later (Doc 04 Sec 3.3)
        - K_i is explicit input; NO hard-coded default (calibration from Phase 6)
        - None inputs preserve missing != zero (IMPLEMENTATION_CONSTITUTION.md Sec 3)
    """
    # Preserve missing != zero
    if h_i is None or q_i is None or k_i is None:
        return None

    # Validate inputs (Doc 04 Sec 3.3: all components in [0,1])
    if not (0.0 <= h_i <= 1.0):
        raise ValueError(f"h_i={h_i} out of range [0,1] per Doc 04 Sec 3.3")
    if not (0.0 <= q_i <= 1.0):
        raise ValueError(f"q_i={q_i} out of range [0,1] per Doc 04 Sec 3.3")
    if not (0.0 <= k_i <= 1.0):
        raise ValueError(f"k_i={k_i} out of range [0,1] per Doc 04 Sec 3.3")

    # Multiplicative trust gate (Doc 04 Sec 3.3)
    r_i = h_i * q_i * k_i

    # Defensive clamp
    r_i = np.clip(r_i, 0.0, 1.0)

    return float(r_i)
