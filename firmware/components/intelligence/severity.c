/**
 * @file severity.c
 * @brief Severity (S_h) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Section 8
 * Reference: reference/python/nexalert_reference/severity.py
 *
 * Components:
 * - I_h: Intensity component (hazard-specific thresholds)
 * - T_h: Temporal component (rate of change)
 * - D_h: Duration component (time above threshold)
 * - S_h: Final weighted combination
 */

#include "severity.h"
#include <math.h>

float compute_fire_intensity(
    float temperature,
    float smoke,
    const fire_intensity_config_t* config
)
{
    fire_intensity_config_t default_config;
    if (config == NULL) {
        default_config = fire_intensity_default_config();
        config = &default_config;
    }

    float intensities[2];
    uint8_t intensity_count = 0;

    // Temperature intensity
    if (!isnan(temperature)) {
        float i_temp;
        if (temperature <= config->temp_low) {
            i_temp = 0.0f;
        } else if (temperature >= config->temp_high) {
            i_temp = 1.0f;
        } else {
            i_temp = (temperature - config->temp_low) / (config->temp_high - config->temp_low);
        }
        intensities[intensity_count++] = i_temp;
    }

    // Smoke intensity
    if (!isnan(smoke)) {
        float i_smoke;
        if (smoke <= config->smoke_low) {
            i_smoke = 0.0f;
        } else if (smoke >= config->smoke_high) {
            i_smoke = 1.0f;
        } else {
            i_smoke = (smoke - config->smoke_low) / (config->smoke_high - config->smoke_low);
        }
        intensities[intensity_count++] = i_smoke;
    }

    // Combined: max of available sensors
    if (intensity_count == 0) {
        return NAN;  // Both missing
    }

    // Return max
    float max_intensity = intensities[0];
    for (uint8_t i = 1; i < intensity_count; i++) {
        if (intensities[i] > max_intensity) {
            max_intensity = intensities[i];
        }
    }

    return max_intensity;
}

float compute_flood_intensity(
    float water_level,
    float rainfall,
    const flood_intensity_config_t* config
)
{
    flood_intensity_config_t default_config;
    if (config == NULL) {
        default_config = flood_intensity_default_config();
        config = &default_config;
    }

    float intensities[2];
    uint8_t intensity_count = 0;

    // Water level intensity
    if (!isnan(water_level)) {
        float i_water;
        if (water_level <= config->water_low) {
            i_water = 0.0f;
        } else if (water_level >= config->water_high) {
            i_water = 1.0f;
        } else {
            i_water = (water_level - config->water_low) / (config->water_high - config->water_low);
        }
        intensities[intensity_count++] = i_water;
    }

    // Rainfall intensity
    if (!isnan(rainfall)) {
        float i_rain;
        if (rainfall <= config->rain_low) {
            i_rain = 0.0f;
        } else if (rainfall >= config->rain_high) {
            i_rain = 1.0f;
        } else {
            i_rain = (rainfall - config->rain_low) / (config->rain_high - config->rain_low);
        }
        intensities[intensity_count++] = i_rain;
    }

    // Combined: max of available sensors
    if (intensity_count == 0) {
        return NAN;  // Both missing
    }

    // Return max
    float max_intensity = intensities[0];
    for (uint8_t i = 1; i < intensity_count; i++) {
        if (intensities[i] > max_intensity) {
            max_intensity = intensities[i];
        }
    }

    return max_intensity;
}

float compute_temporal(
    float current,
    float previous,
    float time_delta_seconds,
    float max_rate_per_second,
    float max_age_seconds
)
{
    // Missing inputs
    if (isnan(current) || isnan(previous) || isnan(time_delta_seconds)) {
        return NAN;
    }

    // Edge case: no time elapsed
    if (time_delta_seconds <= 0.0f) {
        return 0.0f;
    }

    // Edge case: data too stale
    if (max_age_seconds > 0.0f && time_delta_seconds > max_age_seconds) {
        return 0.0f;
    }

    // Compute rate
    float rate = fabsf(current - previous) / time_delta_seconds;

    // Normalize to [0, 1]
    float t_h = rate / max_rate_per_second;
    if (t_h > 1.0f) {
        t_h = 1.0f;
    }

    return t_h;
}

float compute_duration(
    float above_threshold_seconds,
    float max_duration_seconds
)
{
    // Validate configuration
    if (max_duration_seconds <= 0.0f) {
        return NAN;  // Invalid configuration
    }

    // Missing input
    if (isnan(above_threshold_seconds)) {
        return NAN;
    }

    // Validate input
    if (above_threshold_seconds < 0.0f) {
        return NAN;  // Invalid input
    }

    // Normalize to [0, 1]
    float d_h = above_threshold_seconds / max_duration_seconds;
    if (d_h > 1.0f) {
        d_h = 1.0f;
    }

    return d_h;
}

severity_result_t compute_severity(
    float i_h,
    float t_h,
    float d_h,
    const severity_weights_t* weights,
    float epsilon
)
{
    severity_result_t result = {
        .s_h = 0.0f,
        .valid = false
    };

    // Use default weights if not provided
    severity_weights_t default_weights;
    if (weights == NULL) {
        default_weights = severity_default_weights();
        weights = &default_weights;
    }

    // Build component list with weights
    typedef struct {
        float value;
        float weight;
        bool available;
    } component_t;

    component_t components[3] = {
        {i_h, weights->w_I, !isnan(i_h)},
        {t_h, weights->w_T, !isnan(t_h)},
        {d_h, weights->w_D, !isnan(d_h)}
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
    float s_h = weighted_sum / total_weight;

    // Clamp to [0, 1] for numerical safety
    if (s_h < 0.0f) {
        s_h = 0.0f;
    } else if (s_h > 1.0f) {
        s_h = 1.0f;
    }

    result.s_h = s_h;
    result.valid = true;

    return result;
}

bool validate_severity_weights(
    const severity_weights_t* weights,
    float epsilon
)
{
    if (weights == NULL) {
        return false;
    }

    // Check all weights in [0, 1]
    if (weights->w_I < 0.0f || weights->w_I > 1.0f ||
        weights->w_T < 0.0f || weights->w_T > 1.0f ||
        weights->w_D < 0.0f || weights->w_D > 1.0f) {
        return false;
    }

    // Check sum to 1.0 ± epsilon
    float total = weights->w_I + weights->w_T + weights->w_D;
    if (fabsf(total - 1.0f) > epsilon) {
        return false;
    }

    return true;
}

severity_weights_t severity_default_weights(void)
{
    severity_weights_t weights = {
        .w_I = 0.5f,
        .w_T = 0.3f,
        .w_D = 0.2f
    };
    return weights;
}

fire_intensity_config_t fire_intensity_default_config(void)
{
    fire_intensity_config_t config = {
        .temp_low = 40.0f,
        .temp_high = 100.0f,
        .smoke_low = 0.2f,
        .smoke_high = 0.8f
    };
    return config;
}

flood_intensity_config_t flood_intensity_default_config(void)
{
    flood_intensity_config_t config = {
        .water_low = 0.5f,
        .water_high = 3.0f,
        .rain_low = 10.0f,
        .rain_high = 100.0f
    };
    return config;
}
