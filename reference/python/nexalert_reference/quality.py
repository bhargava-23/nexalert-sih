"""
Quality (Q_i) reference implementation.

Specification: Document 04, Section 3.2
Formula: Q_i = q_integrity × q_stability
Range: [0, 1]
"""
import numpy as np
from typing import Optional


def compute_quality(
    q_integrity: Optional[float],
    q_stability: Optional[float]
) -> Optional[float]:
    """
    Compute signal quality Q_i.

    Args:
        q_integrity: Integrity component [0, 1] or None
        q_stability: Stability component [0, 1] or None

    Returns:
        Q_i in [0, 1], or None if either input is None

    Specification: Document 04, Section 3.2

    Invariants:
        - Missing samples decrease q_integrity (Doc 04 Sec 3.2)
        - High jitter decreases q_stability (Doc 04 Sec 3.2)
        - Q_i = 0 means observation unusable
        - None inputs preserve missing != zero (IMPLEMENTATION_CONSTITUTION.md Sec 3)
    """
    # Preserve missing != zero
    if q_integrity is None or q_stability is None:
        return None

    # Validate inputs (Doc 04 Sec 3.2: components in [0,1])
    if not (0.0 <= q_integrity <= 1.0):
        raise ValueError(f"q_integrity={q_integrity} out of range [0,1] per Doc 04 Sec 3.2")
    if not (0.0 <= q_stability <= 1.0):
        raise ValueError(f"q_stability={q_stability} out of range [0,1] per Doc 04 Sec 3.2")

    # Multiplicative combination (Doc 04 Sec 3.2)
    q_i = q_integrity * q_stability

    # Defensive clamp
    q_i = np.clip(q_i, 0.0, 1.0)

    return float(q_i)
