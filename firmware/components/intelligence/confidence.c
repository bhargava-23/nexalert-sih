/**
 * @file confidence.c
 * @brief Confidence (C_h) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Section 7
 * Reference: reference/python/nexalert_reference/confidence.py
 *
 * Components:
 * - C_cov: Coverage confidence (sensor availability)
 * - C_agree: Agreement confidence (variance-based)
 * - C_temp: Temporal confidence (data freshness)
 * - C_base: Baseline confidence (baseline readiness)
 * - C_h: Final weighted combination
 */

#include "confidence.h"
#include <math.h>

// Numerical epsilon (matches Python reference)
#define EPSILON 1e-9f

float compute_coverage(
    const sensor_availability_t* sensors,
    uint8_t sensor_count,
    float epsilon
)
{
    if (sensor_count == 0) {
        return 1.0f;  // No sensors required → full coverage
    }

    float total_weight = 0.0f;
    float available_weight = 0.0f;

    for (uint8_t i = 0; i < sensor_count; i++) {
        total_weight += sensors[i].weight;
        if (sensors[i].available) {
            available_weight += sensors[i].weight;
        }
    }

    // Zero denominator guard
    if (total_weight < epsilon) {
        return 1.0f;  // All weights zero → full coverage
    }

    return available_weight / total_weight;
}

float compute_agreement(
    const evidence_group_t* groups,
    uint8_t group_count,
    float k_v,
    float epsilon
)
{
    if (group_count == 0) {
        return 1.0f;  // No groups → no disagreement
    }

    // Collect valid (non-NAN) groups
    uint8_t valid_count = 0;
    for (uint8_t i = 0; i < group_count; i++) {
        if (!isnan(groups[i].evidence)) {
            valid_count++;
        }
    }

    // No valid groups or single group → perfect agreement
    if (valid_count == 0 || valid_count == 1) {
        return 1.0f;
    }

    // Compute weighted mean: ē = Σ(v_g × e_g) / Σ(v_g)
    float sum_weight = 0.0f;
    float sum_weighted_evidence = 0.0f;

    for (uint8_t i = 0; i < group_count; i++) {
        if (!isnan(groups[i].evidence)) {
            sum_weight += groups[i].weight;
            sum_weighted_evidence += groups[i].weight * groups[i].evidence;
        }
    }

    // Zero denominator guard
    if (sum_weight < epsilon) {
        return 1.0f;
    }

    float mean_evidence = sum_weighted_evidence / sum_weight;

    // Zero-mean case: all agree on near-zero
    if (fabsf(mean_evidence) < epsilon) {
        return 1.0f;
    }

    // Compute weighted variance: V_e = Σ(v_g × (e_g - ē)²) / Σ(v_g)
    float sum_weighted_variance = 0.0f;

    for (uint8_t i = 0; i < group_count; i++) {
        if (!isnan(groups[i].evidence)) {
            float deviation = groups[i].evidence - mean_evidence;
            sum_weighted_variance += groups[i].weight * (deviation * deviation);
        }
    }

    float variance = sum_weighted_variance / sum_weight;

    // Agreement formula: C_agree = exp(-k_v × V_e)
    float c_agree = expf(-k_v * variance);

    return c_agree;
}

float compute_temporal(
    float telemetry_age_seconds,
    float max_age_seconds
)
{
    // Missing temporal information
    if (isnan(telemetry_age_seconds)) {
        return 0.0f;
    }

    // Invalid age (clock error or future timestamp)
    if (telemetry_age_seconds < 0.0f) {
        return 0.0f;
    }

    // Stale data
    if (telemetry_age_seconds > max_age_seconds) {
        return 0.0f;
    }

    // Formula: C_temp = max(0, 1 - age / max_age)
    float c_temp = 1.0f - (telemetry_age_seconds / max_age_seconds);

    // Clamp to [0, 1]
    if (c_temp < 0.0f) {
        c_temp = 0.0f;
    } else if (c_temp > 1.0f) {
        c_temp = 1.0f;
    }

    return c_temp;
}

float compute_baseline_confidence(
    baseline_state_t baseline_state
)
{
    // Baseline state confidence mapping (PROTOTYPE)
    switch (baseline_state) {
        case BASELINE_READY:
            return 1.0f;  // Full confidence
        case BASELINE_LEARNING:
            return 0.7f;  // Building baseline
        case BASELINE_RECOVERING:
            return 0.6f;  // Post-event recovery
        case BASELINE_FROZEN:
            return 0.5f;  // Frozen during event
        case BASELINE_INITIALIZING:
            return 0.3f;  // Insufficient data
        default:
            return 0.3f;  // Unknown state → low confidence
    }
}

confidence_result_t compute_confidence(
    float c_cov,
    float c_agree,
    float c_temp,
    float c_base,
    const confidence_weights_t* weights,
    float epsilon
)
{
    confidence_result_t result = {
        .c_h = 0.0f,
        .valid = false
    };

    // Validate weights
    if (weights == NULL) {
        return result;
    }

    // Validate weight sum (must be 1.0 ± epsilon)
    float weight_sum = weights->coverage + weights->agreement + weights->temporal + weights->baseline;
    if (fabsf(weight_sum - 1.0f) > epsilon) {
        return result;  // Invalid weight sum
    }

    // Validate component ranges [0, 1]
    if (c_cov < 0.0f || c_cov > 1.0f ||
        c_agree < 0.0f || c_agree > 1.0f ||
        c_temp < 0.0f || c_temp > 1.0f ||
        c_base < 0.0f || c_base > 1.0f) {
        return result;  // Invalid component values
    }

    // Compute weighted combination
    // C_h = w_c × C_cov + w_a × C_agree + w_t × C_temp + w_b × C_base
    float c_h = (weights->coverage * c_cov) +
                (weights->agreement * c_agree) +
                (weights->temporal * c_temp) +
                (weights->baseline * c_base);

    // Clamp to [0, 1] (should already be in range, but safety guard)
    if (c_h < 0.0f) {
        c_h = 0.0f;
    } else if (c_h > 1.0f) {
        c_h = 1.0f;
    }

    result.c_h = c_h;
    result.valid = true;

    return result;
}

confidence_weights_t confidence_default_weights(void)
{
    confidence_weights_t weights = {
        .coverage = 0.3f,
        .agreement = 0.3f,
        .temporal = 0.2f,
        .baseline = 0.2f
    };

    return weights;
}
