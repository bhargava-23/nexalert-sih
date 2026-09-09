/**
 * @file quality.c
 * @brief Signal quality (Q_i) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Section 3.2
 * Reference: reference/python/nexalert_reference/quality.py
 *
 * Formula: Q_i = q_integrity × q_stability
 */

#include "quality.h"
#include <math.h>

quality_result_t compute_quality(
    float q_integrity,
    float q_stability
)
{
    quality_result_t result = {
        .q_i = 0.0f,
        .valid = false
    };

    // Preserve missing != zero (Python: if q_integrity is None or q_stability is None)
    if (isnan(q_integrity) || isnan(q_stability)) {
        result.valid = false;
        return result;
    }

    // Validate q_integrity range [0, 1] (Doc 04 Sec 3.2)
    if (q_integrity < 0.0f || q_integrity > 1.0f) {
        result.valid = false;
        return result;
    }

    // Validate q_stability range [0, 1] (Doc 04 Sec 3.2)
    if (q_stability < 0.0f || q_stability > 1.0f) {
        result.valid = false;
        return result;
    }

    // Multiplicative combination (Doc 04 Sec 3.2)
    float q_i = q_integrity * q_stability;

    // Defensive clamp to [0, 1]
    if (q_i < 0.0f) {
        q_i = 0.0f;
    } else if (q_i > 1.0f) {
        q_i = 1.0f;
    }

    result.q_i = q_i;
    result.valid = true;
    return result;
}
