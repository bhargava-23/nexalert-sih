/**
 * @file reliability.c
 * @brief Evidence reliability (R_i) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Section 3.3
 * Reference: reference/python/nexalert_reference/reliability.py
 *
 * Formula: R_i = H_i × Q_i × K_i
 */

#include "reliability.h"
#include <math.h>

reliability_result_t compute_reliability(
    float h_i,
    float q_i,
    float k_i
)
{
    reliability_result_t result = {
        .r_i = 0.0f,
        .valid = false
    };

    // Preserve missing != zero (Python: if h_i is None or q_i is None or k_i is None)
    if (isnan(h_i) || isnan(q_i) || isnan(k_i)) {
        result.valid = false;
        return result;
    }

    // Validate h_i range [0, 1] (Doc 04 Sec 3.3)
    if (h_i < 0.0f || h_i > 1.0f) {
        result.valid = false;
        return result;
    }

    // Validate q_i range [0, 1] (Doc 04 Sec 3.3)
    if (q_i < 0.0f || q_i > 1.0f) {
        result.valid = false;
        return result;
    }

    // Validate k_i range [0, 1] (Doc 04 Sec 3.3)
    if (k_i < 0.0f || k_i > 1.0f) {
        result.valid = false;
        return result;
    }

    // Multiplicative trust gate (Doc 04 Sec 3.3)
    // R_i = 0 if any component is 0 (strict trust gate)
    float r_i = h_i * q_i * k_i;

    // Defensive clamp to [0, 1]
    if (r_i < 0.0f) {
        r_i = 0.0f;
    } else if (r_i > 1.0f) {
        r_i = 1.0f;
    }

    result.r_i = r_i;
    result.valid = true;
    return result;
}
