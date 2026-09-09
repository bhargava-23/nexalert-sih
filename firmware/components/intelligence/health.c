/**
 * @file health.c
 * @brief Sensor health (H_i) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Section 3.1
 * Reference: reference/python/nexalert_reference/health.py
 *
 * Formula: H_i^soft = Σ_j w_ij · D_ij,  H_i = 0 if F_i=1 else H_i^soft
 *
 * PHASE 4: Missing diagnostics behavior preserves missing != zero
 */

#include "health.h"
#include <math.h>
#include <string.h>

// Epsilon for floating-point comparisons (matches Python EPSILON = 1e-9)
#define EPSILON 1e-9f

bool validate_health_weights(
    const health_diagnostic_t* diagnostics,
    uint8_t num_diagnostics
)
{
    if (diagnostics == NULL || num_diagnostics == 0) {
        return false;
    }

    // Sum weights
    float weight_sum = 0.0f;
    for (uint8_t i = 0; i < num_diagnostics; i++) {
        weight_sum += diagnostics[i].weight;
    }

    // Validate weights sum to 1 within epsilon (Doc 04 Sec 3.1)
    return (weight_sum >= (1.0f - EPSILON) && weight_sum <= (1.0f + EPSILON));
}

health_result_t compute_health(
    const health_diagnostic_t* diagnostics,
    uint8_t num_diagnostics,
    bool hard_failure
)
{
    health_result_t result = {
        .h_i = 0.0f,
        .complete = false,
        .hard_failure = hard_failure
    };

    // Hard failure gate (Doc 04 Sec 3.1: F_i=1 forces H_i=0)
    if (hard_failure) {
        result.h_i = 0.0f;
        result.complete = true;  // Hard failure is a complete result
        return result;
    }

    // Validate inputs
    if (diagnostics == NULL || num_diagnostics == 0) {
        // No diagnostics = incomplete (PHASE 4: missing != zero)
        result.complete = false;
        return result;
    }

    // Validate weights sum to 1 (Doc 04 Sec 3.1)
    if (!validate_health_weights(diagnostics, num_diagnostics)) {
        // Invalid weights = incomplete computation
        result.complete = false;
        return result;
    }

    // Compute weighted sum H_i^soft = Σ_j w_ij · D_ij
    float h_soft = 0.0f;
    for (uint8_t i = 0; i < num_diagnostics; i++) {
        float d_ij = diagnostics[i].value;
        float w_ij = diagnostics[i].weight;

        // Validate D_ij range [0, 1] (Doc 04 Sec 3.1: normalized)
        if (d_ij < 0.0f || d_ij > 1.0f) {
            // Out-of-range diagnostic = incomplete computation
            result.complete = false;
            return result;
        }

        h_soft += w_ij * d_ij;
    }

    // Clamp to [0, 1] (defensive, should already be in range)
    if (h_soft < 0.0f) {
        h_soft = 0.0f;
    } else if (h_soft > 1.0f) {
        h_soft = 1.0f;
    }

    result.h_i = h_soft;
    result.complete = true;
    return result;
}
