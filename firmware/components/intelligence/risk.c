/**
 * @file risk.c
 * @brief Operational Risk (R_h) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Section 9
 * Reference: reference/python/nexalert_reference/risk.py
 *
 * Components:
 * - E_h: Evidence component (from evidence.c)
 * - S_h: Severity component (from severity.c)
 * - T_h: Temporal/threat component (from severity.c)
 * - R_h: Final weighted combination
 */

#include "risk.h"
#include <math.h>

risk_result_t compute_risk(
    float e_h,
    float s_h,
    float t_h,
    const risk_weights_t* weights,
    float epsilon
)
{
    risk_result_t result = {
        .r_h = 0.0f,
        .valid = false
    };

    // Use default weights if not provided
    risk_weights_t default_weights;
    if (weights == NULL) {
        default_weights = risk_default_weights();
        weights = &default_weights;
    }

    // Build component list with weights
    typedef struct {
        float value;
        float weight;
        bool available;
    } component_t;

    component_t components[3] = {
        {e_h, weights->w_E, !isnan(e_h)},
        {s_h, weights->w_S, !isnan(s_h)},
        {t_h, weights->w_T, !isnan(t_h)}
    };

    // Sum available weights for renormalization
    float total_weight = 0.0f;
    float weighted_sum = 0.0f;
    uint8_t available_count = 0;

    for (uint8_t i = 0; i < 3; i++) {
        if (components[i].available) {
            total_weight += components[i].weight;
            weighted_sum += components[i].value * components[i].weight;
            available_count++;
        }
    }

    // All missing → invalid (cannot compute)
    if (available_count == 0) {
        return result;
    }

    // Guard against invalid weight configuration
    if (total_weight < epsilon) {
        return result;
    }

    // Weighted sum with renormalization
    float r_h = weighted_sum / total_weight;

    // Clamp to [0, 1] for numerical safety
    if (r_h < 0.0f) {
        r_h = 0.0f;
    } else if (r_h > 1.0f) {
        r_h = 1.0f;
    }

    result.r_h = r_h;
    result.valid = true;

    return result;
}

bool validate_risk_weights(
    const risk_weights_t* weights,
    float epsilon
)
{
    if (weights == NULL) {
        return false;
    }

    // Check all weights in [0, 1]
    if (weights->w_E < 0.0f || weights->w_E > 1.0f ||
        weights->w_S < 0.0f || weights->w_S > 1.0f ||
        weights->w_T < 0.0f || weights->w_T > 1.0f) {
        return false;
    }

    // Check sum to 1.0 ± epsilon
    float total = weights->w_E + weights->w_S + weights->w_T;
    if (fabsf(total - 1.0f) > epsilon) {
        return false;
    }

    return true;
}

risk_weights_t risk_default_weights(void)
{
    risk_weights_t weights = {
        .w_E = 0.4f,
        .w_S = 0.4f,
        .w_T = 0.2f
    };
    return weights;
}
