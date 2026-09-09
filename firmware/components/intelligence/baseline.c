/**
 * @file baseline.c
 * @brief Baseline (B_i) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Section 4.1
 * Reference: reference/python/nexalert_reference/baseline.py
 *
 * Formula:
 *   median = median(samples)
 *   MAD = median(|samples - median|)
 *   scale = 1.4826 × MAD + ε
 *   z_i = (value - median) / scale
 */

#include "baseline.h"
#include <math.h>
#include <string.h>

// Numerical epsilon (matches Python reference)
#define EPSILON 1e-9f

// MAD to Gaussian stddev conversion factor
#define MAD_SCALE_FACTOR 1.4826f

/**
 * Helper: Compute median of float array
 *
 * Note: This function sorts the input array in-place.
 * Caller must provide a working copy if original order must be preserved.
 */
static float compute_median(float* values, uint16_t count)
{
    // Simple insertion sort (adequate for bounded history on ESP32)
    for (uint16_t i = 1; i < count; i++) {
        float key = values[i];
        int16_t j = i - 1;

        while (j >= 0 && values[j] > key) {
            values[j + 1] = values[j];
            j--;
        }
        values[j + 1] = key;
    }

    // Compute median
    if (count % 2 == 0) {
        // Even count: average of two middle values
        return (values[count/2 - 1] + values[count/2]) / 2.0f;
    } else {
        // Odd count: middle value
        return values[count/2];
    }
}

baseline_result_t compute_robust_baseline(
    const float* samples,
    uint16_t count,
    float epsilon
)
{
    baseline_result_t result = {
        .median = 0.0f,
        .scale = 0.0f,
        .valid = false
    };

    // Require at least 2 samples (Python reference constraint)
    if (count < 2) {
        return result;
    }

    // Allocate working buffers (bounded by BASELINE_MAX_HISTORY)
    float working_samples[BASELINE_MAX_HISTORY];
    float absolute_deviations[BASELINE_MAX_HISTORY];

    if (count > BASELINE_MAX_HISTORY) {
        // Safety check: should not happen if caller respects bounds
        count = BASELINE_MAX_HISTORY;
    }

    // Copy samples to working buffer (compute_median sorts in-place)
    memcpy(working_samples, samples, count * sizeof(float));

    // Compute median
    float median = compute_median(working_samples, count);

    // Compute absolute deviations
    for (uint16_t i = 0; i < count; i++) {
        absolute_deviations[i] = fabsf(samples[i] - median);
    }

    // Compute MAD (median of absolute deviations)
    float mad = compute_median(absolute_deviations, count);

    // Convert MAD to scale (Gaussian-equivalent stddev)
    // 1.4826 = 1 / Φ^(-1)(3/4) where Φ is standard normal CDF
    float scale = MAD_SCALE_FACTOR * mad + epsilon;

    result.median = median;
    result.scale = scale;
    result.valid = true;

    return result;
}

zscore_result_t compute_z_score(
    float value,
    float median,
    float scale,
    float epsilon
)
{
    zscore_result_t result = {
        .z_score = 0.0f,
        .valid = false
    };

    // Missing value handling (preserve missing != zero)
    if (isnan(value)) {
        return result;
    }

    // Scale too small (all samples identical or near-identical)
    if (scale < epsilon) {
        return result;
    }

    // Compute standardized deviation
    result.z_score = (value - median) / scale;
    result.valid = true;

    return result;
}

baseline_state_result_t update_baseline_state(
    baseline_state_t current_state,
    uint16_t sample_count,
    const baseline_config_t* config,
    const char* hazard_state,
    uint16_t hazard_stability_count
)
{
    baseline_state_result_t result = {
        .next_state = current_state,
        .stability_count = hazard_stability_count
    };

    // Track stability for recovery
    // Favorable hazard states: "NORMAL", "WATCH"
    // Unfavorable: "SUSPECTED", "CONFIRMED", "CRITICAL", "RESOLVED"
    if (strcmp(hazard_state, "NORMAL") == 0 || strcmp(hazard_state, "WATCH") == 0) {
        result.stability_count++;
    } else {
        result.stability_count = 0;  // Reset when hazard state unfavorable
    }

    // State transitions
    switch (current_state) {
        case BASELINE_INITIALIZING:
            if (sample_count >= config->min_samples_init) {
                result.next_state = BASELINE_LEARNING;
            }
            break;

        case BASELINE_LEARNING:
            if (sample_count >= config->min_samples_learning) {
                result.next_state = BASELINE_READY;
            }
            break;

        case BASELINE_READY:
            // FREEZE trigger: reads hazard state
            if (strcmp(hazard_state, "CONFIRMED") == 0 ||
                strcmp(hazard_state, "CRITICAL") == 0) {
                result.next_state = BASELINE_FROZEN;
                result.stability_count = 0;  // Reset stability counter on freeze
            }
            break;

        case BASELINE_FROZEN:
            // RECOVERY trigger: reads hazard state + stability
            if (result.stability_count >= config->recovery_stability_samples) {
                result.next_state = BASELINE_RECOVERING;
            }
            break;

        case BASELINE_RECOVERING:
            if (sample_count >= config->min_samples_learning) {
                result.next_state = BASELINE_READY;
            }
            break;
    }

    return result;
}

baseline_config_t baseline_default_config(void)
{
    baseline_config_t config = {
        .min_samples_init = BASELINE_MIN_SAMPLES_INIT,
        .min_samples_learning = BASELINE_MIN_SAMPLES_LEARNING,
        .recovery_stability_samples = BASELINE_RECOVERY_STABILITY,
        .max_history = BASELINE_MAX_HISTORY,
        .epsilon = EPSILON
    };

    return config;
}
