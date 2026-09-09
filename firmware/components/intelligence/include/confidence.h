/**
 * @file confidence.h
 * @brief Confidence (C_h) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Section 7
 * Reference: reference/python/nexalert_reference/confidence.py
 *
 * Components:
 * - C_cov: Coverage confidence (sensor availability)
 * - C_agree: Group-level agreement (variance-based)
 * - C_temp: Temporal confidence (data freshness)
 * - C_base: Baseline confidence (baseline readiness)
 * - C_h: Final weighted combination
 *
 * Formula: C_h = w_c × C_cov + w_a × C_agree + w_t × C_temp + w_b × C_base
 * Range: [0, 1]
 *
 * CRITICAL INVARIANT: Confidence ≠ Probability
 * - C_h measures assessment trustworthiness, NOT event likelihood
 * - Never used in Bayesian inference or probabilistic reasoning
 */

#ifndef NEXALERT_CONFIDENCE_H
#define NEXALERT_CONFIDENCE_H

#include <stdint.h>
#include <stdbool.h>
#include "baseline.h"

#ifdef __cplusplus
extern "C" {
#endif

// Configuration (ESP32 constraints)
#define CONFIDENCE_MAX_SENSORS     10    // Maximum sensors for coverage
#define CONFIDENCE_MAX_GROUPS      5     // Maximum evidence groups for agreement
#define CONFIDENCE_MAX_SENSOR_NAME 32    // Maximum sensor name length

/**
 * Sensor availability entry (for coverage)
 */
typedef struct {
    char sensor[CONFIDENCE_MAX_SENSOR_NAME];  // Sensor type identifier
    bool available;                            // Availability (u_i = true/false)
    float weight;                              // Sensor weight for this hazard
} sensor_availability_t;

/**
 * Evidence group entry (for agreement)
 */
typedef struct {
    char group[CONFIDENCE_MAX_SENSOR_NAME];  // Group name
    float evidence;                           // Group evidence value [0, 1] (NAN = missing)
    float weight;                             // Group weight
} evidence_group_t;

/**
 * Confidence weights (must sum to 1.0)
 */
typedef struct {
    float coverage;     // w_c (PROTOTYPE: 0.3)
    float agreement;    // w_a (PROTOTYPE: 0.3)
    float temporal;     // w_t (PROTOTYPE: 0.2)
    float baseline;     // w_b (PROTOTYPE: 0.2)
} confidence_weights_t;

/**
 * Confidence computation result
 */
typedef struct {
    float c_h;          // Final confidence [0, 1]
    bool valid;         // true = computation successful
} confidence_result_t;

/**
 * Compute coverage confidence
 *
 * Formula: C_cov = [Σ w_ih × u_i] / [Σ w_ih]
 *
 * Args:
 *   sensors: Array of sensor availability entries
 *   sensor_count: Number of sensors
 *   epsilon: Zero-division guard (default 1e-9f)
 *
 * Returns:
 *   C_cov in [0, 1]
 *
 * Usability Criteria (u_i = true if ALL):
 *   - Sensor reading is not NAN (missing ≠ zero)
 *   - H_i indicates sensor operational (not hard-failed)
 *   - Q_i indicates data quality sufficient
 *   - R_i above minimum reliability threshold
 */
float compute_coverage(
    const sensor_availability_t* sensors,
    uint8_t sensor_count,
    float epsilon
);

/**
 * Compute group-level agreement confidence
 *
 * Formula:
 *   ē = [Σ_g v_g × e_g] / [Σ_g v_g]
 *   V_e = [Σ_g v_g × (e_g - ē)²] / [Σ_g v_g]
 *   C_agree = exp(-k_v × V_e)
 *
 * Args:
 *   groups: Array of evidence group entries
 *   group_count: Number of groups
 *   k_v: Variance penalty coefficient (PROTOTYPE: 2.0)
 *   epsilon: Zero-division guard (default 1e-9f)
 *
 * Returns:
 *   C_agree in [0, 1]
 *
 * Missing Handling:
 *   - NAN values in group evidence are EXCLUDED
 *   - len(valid_groups) == 0 → returns 1.0 (no evidence = no disagreement)
 *   - len(valid_groups) == 1 → returns 1.0 (single source = no disagreement)
 *   - ē < epsilon (zero-mean) → returns 1.0 (all agree on near-zero)
 *
 * Provenance: k_v = 2.0 is PROTOTYPE ASSUMPTION
 */
float compute_agreement(
    const evidence_group_t* groups,
    uint8_t group_count,
    float k_v,
    float epsilon
);

/**
 * Compute temporal confidence based on data freshness
 *
 * Formula: C_temp = max(0, 1 - age / max_age)
 *
 * Args:
 *   telemetry_age_seconds: Age of telemetry (t_now - t_measurement) in seconds
 *                          (NAN = missing, < 0 = clock error)
 *   max_age_seconds: Maximum acceptable age (PROTOTYPE: 300s = 5 minutes)
 *
 * Returns:
 *   C_temp in [0, 1]
 *
 * Missing Handling:
 *   - telemetry_age_seconds is NAN → returns 0.0 (no temporal information)
 *   - age > max_age → returns 0.0 (stale data)
 *   - age < 0 → returns 0.0 (clock error, invalid)
 *
 * Provenance: max_age_seconds = 300 is PROTOTYPE ASSUMPTION
 */
float compute_temporal(
    float telemetry_age_seconds,
    float max_age_seconds
);

/**
 * Compute baseline confidence based on baseline readiness state
 *
 * Formula: C_base = f(baseline_state)
 *
 * Args:
 *   baseline_state: Current baseline state
 *
 * Returns:
 *   C_base in [0, 1]
 *
 * Baseline State Mapping (PROTOTYPE):
 *   - READY: 1.0 (full confidence)
 *   - LEARNING: 0.7 (building baseline)
 *   - RECOVERING: 0.6 (post-event recovery)
 *   - FROZEN: 0.5 (frozen during event)
 *   - INITIALIZING: 0.3 (insufficient data)
 *
 * Provenance: Confidence map values are PROTOTYPE ASSUMPTIONS
 */
float compute_baseline_confidence(
    baseline_state_t baseline_state
);

/**
 * Compute final evidence confidence as weighted combination
 *
 * Formula: C_h = w_c × C_cov + w_a × C_agree + w_t × C_temp + w_b × C_base
 * Constraint: w_c + w_a + w_t + w_b = 1.0
 *
 * Args:
 *   c_cov: Coverage confidence [0, 1]
 *   c_agree: Agreement confidence [0, 1]
 *   c_temp: Temporal confidence [0, 1]
 *   c_base: Baseline confidence [0, 1]
 *   weights: Weight structure (must sum to 1.0 ± epsilon)
 *   epsilon: Weight sum tolerance (default 1e-9f)
 *
 * Returns:
 *   confidence_result_t:
 *     - c_h in [0, 1] when valid=true
 *     - c_h undefined when valid=false (invalid inputs)
 *     - valid=true when all components in [0, 1] and weights sum to 1.0
 *     - valid=false when validation fails
 *
 * CRITICAL INVARIANT: Confidence ≠ Probability
 *   - C_h measures assessment trustworthiness, NOT event likelihood
 *   - Never used in Bayesian inference or probabilistic reasoning
 *   - Not a calibrated probability that the hazard exists
 *   - Expresses quality of evidence assessment under information conditions
 *
 * Default Weights (PROTOTYPE):
 *   - w_coverage = 0.3
 *   - w_agreement = 0.3
 *   - w_temporal = 0.2
 *   - w_baseline = 0.2
 *
 * Provenance: Weight values are PROTOTYPE ASSUMPTIONS
 */
confidence_result_t compute_confidence(
    float c_cov,
    float c_agree,
    float c_temp,
    float c_base,
    const confidence_weights_t* weights,
    float epsilon
);

/**
 * Get default confidence weights (PROTOTYPE)
 *
 * Returns default weight structure:
 *   - coverage: 0.3
 *   - agreement: 0.3
 *   - temporal: 0.2
 *   - baseline: 0.2
 *
 * Provenance: PROTOTYPE ASSUMPTIONS
 * Validation Status: UNVALIDATED
 */
confidence_weights_t confidence_default_weights(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_CONFIDENCE_H
