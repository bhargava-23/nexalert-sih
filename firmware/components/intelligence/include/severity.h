/**
 * @file severity.h
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
 *
 * Formula: S_h = w_I × I_h + w_T × T_h + w_D × D_h
 * Range: [0, 1] or None
 *
 * CRITICAL INVARIANT: Severity ≠ Probability
 * - S_h measures operational intensity/danger, NOT event likelihood
 * - Deliberately excludes E_h (evidence) to avoid circular dependency
 */

#ifndef NEXALERT_SEVERITY_H
#define NEXALERT_SEVERITY_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Numerical epsilon (matches Python reference)
#define SEVERITY_EPSILON 1e-9f

/**
 * Fire intensity threshold configuration (PROTOTYPE)
 */
typedef struct {
    float temp_low;     // Low temperature threshold (°C, PROTOTYPE: 40.0)
    float temp_high;    // High temperature threshold (°C, PROTOTYPE: 100.0)
    float smoke_low;    // Low smoke threshold ([0,1], PROTOTYPE: 0.2)
    float smoke_high;   // High smoke threshold ([0,1], PROTOTYPE: 0.8)
} fire_intensity_config_t;

/**
 * Flood intensity threshold configuration (PROTOTYPE)
 */
typedef struct {
    float water_low;    // Low water level (m, PROTOTYPE: 0.5)
    float water_high;   // High water level (m, PROTOTYPE: 3.0)
    float rain_low;     // Low rainfall (mm/h, PROTOTYPE: 10.0)
    float rain_high;    // High rainfall (mm/h, PROTOTYPE: 100.0)
} flood_intensity_config_t;

/**
 * Severity weights (must sum to 1.0)
 */
typedef struct {
    float w_I;  // Intensity weight (PROTOTYPE: 0.5)
    float w_T;  // Temporal weight (PROTOTYPE: 0.3)
    float w_D;  // Duration weight (PROTOTYPE: 0.2)
} severity_weights_t;

/**
 * Severity computation result
 */
typedef struct {
    float s_h;      // Severity [0, 1]
    bool valid;     // true = computation successful
} severity_result_t;

/**
 * Compute fire intensity from temperature and smoke sensors
 *
 * Formula:
 *   I_temp = clamp((temp - temp_low) / (temp_high - temp_low), 0, 1)
 *   I_smoke = clamp((smoke - smoke_low) / (smoke_high - smoke_low), 0, 1)
 *   I_h = max(I_temp, I_smoke)
 *
 * Args:
 *   temperature: Temperature reading (°C) or NAN
 *   smoke: Smoke reading [0, 1] or NAN
 *   config: Intensity thresholds or NULL for defaults
 *
 * Returns:
 *   I_h in [0, 1] or NAN if both sensors missing
 *
 * Missing Handling:
 *   - Both NAN → returns NAN
 *   - One NAN → uses the other
 *   - Missing ≠ zero preserved
 *
 * Provenance: ALL thresholds are PROTOTYPE ASSUMPTIONS
 * Validation Status: UNVALIDATED
 */
float compute_fire_intensity(
    float temperature,
    float smoke,
    const fire_intensity_config_t* config
);

/**
 * Compute flood intensity from water level and rainfall sensors
 *
 * Formula:
 *   I_water = clamp((level - water_low) / (water_high - water_low), 0, 1)
 *   I_rain = clamp((rain - rain_low) / (rain_high - rain_low), 0, 1)
 *   I_h = max(I_water, I_rain)
 *
 * Args:
 *   water_level: Water level (m) or NAN
 *   rainfall: Rainfall rate (mm/h) or NAN
 *   config: Intensity thresholds or NULL for defaults
 *
 * Returns:
 *   I_h in [0, 1] or NAN if both sensors missing
 *
 * Missing Handling:
 *   - Both NAN → returns NAN
 *   - One NAN → uses the other
 *   - Missing ≠ zero preserved
 *
 * Provenance: ALL thresholds are PROTOTYPE ASSUMPTIONS
 * Validation Status: UNVALIDATED
 */
float compute_flood_intensity(
    float water_level,
    float rainfall,
    const flood_intensity_config_t* config
);

/**
 * Compute temporal component from rate of change
 *
 * Formula:
 *   rate = abs(current - previous) / time_delta_seconds
 *   T_h = min(rate / max_rate_per_second, 1.0)
 *
 * Args:
 *   current: Current sensor value (hazard-specific units) or NAN
 *   previous: Previous sensor value (same units) or NAN
 *   time_delta_seconds: Time elapsed (seconds) or NAN
 *   max_rate_per_second: Maximum rate for normalization (units/second)
 *   max_age_seconds: Maximum age before stale (seconds, 0 = no limit)
 *
 * Returns:
 *   T_h in [0, 1] or NAN
 *
 * Missing/Edge Cases:
 *   - current is NAN → T_h = NAN
 *   - previous is NAN → T_h = NAN (cannot compute rate)
 *   - time_delta_seconds is NAN → T_h = NAN
 *   - time_delta_seconds <= 0 → T_h = 0.0 (no time elapsed)
 *   - time_delta_seconds > max_age_seconds → T_h = 0.0 (data stale)
 *
 * Provenance: max_rate values are PROTOTYPE ASSUMPTIONS
 * Validation Status: UNVALIDATED
 */
float compute_temporal(
    float current,
    float previous,
    float time_delta_seconds,
    float max_rate_per_second,
    float max_age_seconds
);

/**
 * Compute duration component from time above threshold
 *
 * Formula:
 *   D_h = min(above_threshold_seconds / max_duration_seconds, 1.0)
 *
 * Args:
 *   above_threshold_seconds: Time above threshold (seconds) or NAN
 *   max_duration_seconds: Maximum duration for normalization (seconds)
 *
 * Returns:
 *   D_h in [0, 1] or NAN
 *
 * Missing/Edge Cases:
 *   - above_threshold_seconds is NAN → D_h = NAN (no history)
 *   - above_threshold_seconds == 0 → D_h = 0.0
 *   - above_threshold_seconds < 0 → invalid (returns NAN)
 *   - max_duration_seconds <= 0 → invalid (returns NAN)
 *
 * Provenance: max_duration_seconds is a PROTOTYPE ASSUMPTION
 * Validation Status: UNVALIDATED
 */
float compute_duration(
    float above_threshold_seconds,
    float max_duration_seconds
);

/**
 * Compute severity from components with reweighting
 *
 * Formula (all components available):
 *   S_h = w_I × I_h + w_T × T_h + w_D × D_h
 *
 * Missing Semantics (D16):
 *   - All NAN → returns {valid: false}
 *   - Some NAN → reweight remaining to sum to 1.0
 *   - Never converts NAN to 0.0 (missing ≠ zero)
 *
 * Args:
 *   i_h: Intensity component [0, 1] or NAN
 *   t_h: Temporal component [0, 1] or NAN
 *   d_h: Duration component [0, 1] or NAN
 *   weights: Weight structure (must sum to 1.0) or NULL for defaults
 *   epsilon: Zero-division guard
 *
 * Returns:
 *   severity_result_t:
 *     - s_h in [0, 1] when valid=true
 *     - s_h undefined when valid=false
 *     - valid=true when at least one component available
 *     - valid=false when all components missing
 *
 * Reweighting Example:
 *   - Configured: w_I=0.5, w_T=0.3, w_D=0.2
 *   - I_h=0.8, T_h=NAN, D_h=0.3 (temporal missing)
 *   - Available weights: w_I=0.5, w_D=0.2, sum=0.7
 *   - Reweighted: w_I'=0.5/0.7=0.714, w_D'=0.2/0.7=0.286
 *   - S_h = 0.714×0.8 + 0.286×0.3 = 0.657
 *
 * CRITICAL INVARIANT: Severity ≠ Probability
 *   - S_h measures operational intensity/danger
 *   - NOT event likelihood or disaster probability
 *   - Deliberately excludes E_h to avoid circular dependency
 *
 * Provenance: Default weights are PROTOTYPE ASSUMPTIONS
 * Validation Status: UNVALIDATED
 */
severity_result_t compute_severity(
    float i_h,
    float t_h,
    float d_h,
    const severity_weights_t* weights,
    float epsilon
);

/**
 * Validate severity weight configuration
 *
 * Args:
 *   weights: Weight structure to validate
 *   epsilon: Tolerance for sum-to-one constraint
 *
 * Returns:
 *   true if valid, false otherwise
 *
 * Validation Rules:
 *   - All weights in [0, 1]
 *   - Weights sum to 1.0 ± epsilon
 */
bool validate_severity_weights(
    const severity_weights_t* weights,
    float epsilon
);

/**
 * Get default severity weights (PROTOTYPE)
 *
 * Returns default weight structure:
 *   - w_I: 0.5
 *   - w_T: 0.3
 *   - w_D: 0.2
 *
 * Provenance: PROTOTYPE ASSUMPTIONS
 * Validation Status: UNVALIDATED
 */
severity_weights_t severity_default_weights(void);

/**
 * Get default fire intensity configuration (PROTOTYPE)
 *
 * Returns default thresholds:
 *   - temp_low: 40.0°C
 *   - temp_high: 100.0°C
 *   - smoke_low: 0.2
 *   - smoke_high: 0.8
 *
 * Provenance: PROTOTYPE ASSUMPTIONS
 * Validation Status: UNVALIDATED
 */
fire_intensity_config_t fire_intensity_default_config(void);

/**
 * Get default flood intensity configuration (PROTOTYPE)
 *
 * Returns default thresholds:
 *   - water_low: 0.5m
 *   - water_high: 3.0m
 *   - rain_low: 10.0mm/h
 *   - rain_high: 100.0mm/h
 *
 * Provenance: PROTOTYPE ASSUMPTIONS
 * Validation Status: UNVALIDATED
 */
flood_intensity_config_t flood_intensity_default_config(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_SEVERITY_H
