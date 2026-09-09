/**
 * @file anomaly.c
 * @brief Anomaly (A_i, A_node, A_h) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Sections 4.2, 4.3
 * Reference: reference/python/nexalert_reference/anomaly.py
 *
 * Formulas:
 *   A_i = 1 - exp(-min(|z_i|, z_cap) / lambda)
 *   A_node = Σ(R_i × A_i) / (Σ(R_i) + ε)
 *   A_h = Σ(w_ih × R_i × A_i) / (Σ(w_ih × R_i) + ε)
 */

#include "anomaly.h"
#include <math.h>

// Numerical epsilon (matches Python reference)
#define EPSILON 1e-9f

individual_anomaly_result_t compute_individual_anomaly(
    float z_score,
    float lambda_param,
    float z_cap
)
{
    individual_anomaly_result_t result = {
        .a_i = 0.0f,
        .valid = false
    };

    // Missing z_score handling (preserve missing != zero)
    if (isnan(z_score)) {
        return result;
    }

    // Validate lambda_param > 0
    if (lambda_param <= 0.0f) {
        return result;  // Invalid parameter
    }

    // Validate z_cap > 0
    if (z_cap <= 0.0f) {
        return result;  // Invalid parameter
    }

    // Compute A_i = 1 - exp(-min(|z|, z_cap) / lambda)
    float abs_z = fabsf(z_score);
    float capped_z = (abs_z < z_cap) ? abs_z : z_cap;
    float a_i = 1.0f - expf(-capped_z / lambda_param);

    // Defensive clamp to [0, 1]
    if (a_i < 0.0f) {
        a_i = 0.0f;
    } else if (a_i > 1.0f) {
        a_i = 1.0f;
    }

    result.a_i = a_i;
    result.valid = true;

    return result;
}

node_anomaly_result_t compute_node_aggregate_anomaly(
    const sensor_anomaly_t* sensors,
    uint8_t count,
    float epsilon
)
{
    node_anomaly_result_t result = {
        .a_node = 0.0f,
        .valid = false
    };

    if (count == 0 || sensors == NULL) {
        return result;
    }

    float weighted_sum = 0.0f;
    float weight_sum = 0.0f;

    // Compute Σ(R_i × A_i) / Σ(R_i)
    for (uint8_t i = 0; i < count; i++) {
        float a_i = sensors[i].a_i;
        float r_i = sensors[i].r_i;

        // Skip missing values (preserve missing != zero)
        if (isnan(a_i) || isnan(r_i)) {
            continue;
        }

        // Validate ranges [0, 1]
        if (a_i < 0.0f || a_i > 1.0f) {
            return result;  // Invalid A_i
        }
        if (r_i < 0.0f || r_i > 1.0f) {
            return result;  // Invalid R_i
        }

        // Accumulate weighted sum
        weighted_sum += r_i * a_i;
        weight_sum += r_i;
    }

    // No valid sensors or zero denominator
    if (weight_sum < epsilon) {
        return result;
    }

    // Compute weighted average
    float a_node = weighted_sum / weight_sum;

    // Defensive clamp to [0, 1]
    if (a_node < 0.0f) {
        a_node = 0.0f;
    } else if (a_node > 1.0f) {
        a_node = 1.0f;
    }

    result.a_node = a_node;
    result.valid = true;

    return result;
}

hazard_anomaly_result_t compute_hazard_specific_anomaly(
    const sensor_anomaly_t* sensors,
    uint8_t count,
    float epsilon
)
{
    hazard_anomaly_result_t result = {
        .a_h = 0.0f,
        .valid = false
    };

    if (count == 0 || sensors == NULL) {
        return result;
    }

    float weighted_sum = 0.0f;
    float weight_sum = 0.0f;

    // Compute Σ(w_ih × R_i × A_i) / Σ(w_ih × R_i)
    for (uint8_t i = 0; i < count; i++) {
        float a_i = sensors[i].a_i;
        float r_i = sensors[i].r_i;
        float w_ih = sensors[i].w_ih;

        // Skip missing values (preserve missing != zero)
        if (isnan(a_i) || isnan(r_i) || isnan(w_ih)) {
            continue;
        }

        // Validate ranges [0, 1]
        if (a_i < 0.0f || a_i > 1.0f) {
            return result;  // Invalid A_i
        }
        if (r_i < 0.0f || r_i > 1.0f) {
            return result;  // Invalid R_i
        }
        if (w_ih < 0.0f || w_ih > 1.0f) {
            return result;  // Invalid w_ih
        }

        // Accumulate weighted sum
        weighted_sum += w_ih * r_i * a_i;
        weight_sum += w_ih * r_i;
    }

    // No valid sensors or zero denominator
    if (weight_sum < epsilon) {
        return result;
    }

    // Compute weighted average
    float a_h = weighted_sum / weight_sum;

    // Defensive clamp to [0, 1]
    if (a_h < 0.0f) {
        a_h = 0.0f;
    } else if (a_h > 1.0f) {
        a_h = 1.0f;
    }

    result.a_h = a_h;
    result.valid = true;

    return result;
}
