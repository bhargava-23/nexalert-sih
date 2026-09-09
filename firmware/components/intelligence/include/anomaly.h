/**
 * @file anomaly.h
 * @brief Anomaly (A_i, A_node, A_h) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Sections 4.2, 4.3
 * Reference: reference/python/nexalert_reference/anomaly.py
 *
 * Formulas:
 *   A_i = 1 - exp(-min(|z_i|, z_cap) / lambda)
 *   A_node = Σ(R_i × A_i) / (Σ(R_i) + ε)
 *   A_h = Σ(w_ih × R_i × A_i) / (Σ(w_ih × R_i) + ε)
 *
 * Range: [0, 1]
 */

#ifndef NEXALERT_ANOMALY_H
#define NEXALERT_ANOMALY_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Configuration (PROTOTYPE values from reference)
#define ANOMALY_LAMBDA_DEFAULT  2.0f    // Exponential decay rate
#define ANOMALY_Z_CAP_DEFAULT   5.0f    // Z-score saturation threshold
#define ANOMALY_MAX_SENSORS     10      // Maximum sensors per node (ESP32 constraint)

/**
 * Individual anomaly computation result
 */
typedef struct {
    float a_i;               // Individual anomaly [0, 1]
    bool valid;              // true = computation successful, false = missing/invalid input
} individual_anomaly_result_t;

/**
 * Node aggregate anomaly computation result
 */
typedef struct {
    float a_node;            // Node aggregate anomaly [0, 1]
    bool valid;              // true = computation successful, false = missing/invalid input
} node_anomaly_result_t;

/**
 * Hazard-specific anomaly computation result
 */
typedef struct {
    float a_h;               // Hazard-specific anomaly [0, 1]
    bool valid;              // true = computation successful, false = missing/invalid input
} hazard_anomaly_result_t;

/**
 * Sensor anomaly entry (for node/hazard aggregation)
 */
typedef struct {
    float a_i;               // Individual anomaly (NAN = missing)
    float r_i;               // Reliability (NAN = missing)
    float w_ih;              // Hazard-specific weight (NAN = not applicable for this hazard)
} sensor_anomaly_t;

/**
 * Compute individual anomaly A_i from z-score
 *
 * Implements Document 04, Section 4.2:
 *   A_i = 1 - exp(-min(|z_i|, z_cap) / lambda)
 *
 * Args:
 *   z_score: Standardized deviation (from compute_z_score)
 *            - NAN = missing (preserve missing != zero)
 *   lambda_param: Exponential decay rate (default 2.0, PROTOTYPE)
 *   z_cap: Z-score saturation threshold (default 5.0, PROTOTYPE)
 *
 * Returns:
 *   individual_anomaly_result_t:
 *     - a_i in [0, 1] when valid=true
 *     - a_i undefined when valid=false (missing input)
 *     - valid=true when z_score is valid
 *     - valid=false when z_score = NAN
 *
 * Invariants:
 *   - A_i(z) = A_i(-z) (symmetry: absolute value)
 *   - A_i → 0 as z → 0 (no anomaly)
 *   - A_i → 1 as |z| → ∞ (strong anomaly, saturates at z_cap)
 *   - lambda_param must be > 0
 *   - z_cap must be > 0
 *   - Missing z_score → {valid: false} (preserve missing != zero)
 *
 * Configuration (PROTOTYPE):
 *   - lambda_param = 2.0 (UNVALIDATED)
 *   - z_cap = 5.0 (UNVALIDATED)
 *   - Provenance: PROTOTYPE ASSUMPTIONS
 */
individual_anomaly_result_t compute_individual_anomaly(
    float z_score,
    float lambda_param,
    float z_cap
);

/**
 * Compute node aggregate anomaly A_node
 *
 * Implements Document 04, Section 4.3:
 *   A_node = Σ(R_i × A_i) / (Σ(R_i) + ε)
 *
 * Args:
 *   sensors: Array of sensor anomaly entries
 *   count: Number of sensors (max ANOMALY_MAX_SENSORS)
 *   epsilon: Numerical epsilon (default 1e-9f)
 *
 * Returns:
 *   node_anomaly_result_t:
 *     - a_node in [0, 1] when valid=true
 *     - a_node undefined when valid=false (no valid sensors)
 *     - valid=true when at least one sensor has valid A_i and R_i
 *     - valid=false when all sensors missing or weight_sum < ε
 *
 * Invariants:
 *   - Reliability-weighted averaging
 *   - Missing A_i or R_i (NAN) → sensor excluded from computation
 *   - A_i, R_i must be in [0, 1] (validation enforced)
 *   - Σ(R_i) < ε → {valid: false} (no reliable sensors)
 *   - Result in [0, 1] (defensive clamp)
 *
 * Note: sensors array must contain entries for all node sensors.
 * Sensors with NAN A_i or R_i are automatically excluded.
 */
node_anomaly_result_t compute_node_aggregate_anomaly(
    const sensor_anomaly_t* sensors,
    uint8_t count,
    float epsilon
);

/**
 * Compute hazard-specific anomaly A_h
 *
 * Implements Document 04, Section 4.3:
 *   A_h = Σ(w_ih × R_i × A_i) / (Σ(w_ih × R_i) + ε)
 *
 * Args:
 *   sensors: Array of sensor anomaly entries (with w_ih per sensor)
 *   count: Number of sensors (max ANOMALY_MAX_SENSORS)
 *   epsilon: Numerical epsilon (default 1e-9f)
 *
 * Returns:
 *   hazard_anomaly_result_t:
 *     - a_h in [0, 1] when valid=true
 *     - a_h undefined when valid=false (no valid sensors)
 *     - valid=true when at least one sensor has valid A_i, R_i, w_ih
 *     - valid=false when all sensors missing or weight_sum < ε
 *
 * Invariants:
 *   - Hazard-specific weighted averaging
 *   - Missing A_i, R_i, or w_ih (NAN) → sensor excluded from computation
 *   - A_i, R_i, w_ih must be in [0, 1] (validation enforced)
 *   - w_ih are relevance weights (don't need to sum to 1.0)
 *   - Σ(w_ih × R_i) < ε → {valid: false} (no weighted reliable sensors)
 *   - Result in [0, 1] (defensive clamp)
 *
 * Note: sensors array must contain w_ih for each sensor.
 * Set w_ih = NAN for sensors not relevant to this hazard type.
 */
hazard_anomaly_result_t compute_hazard_specific_anomaly(
    const sensor_anomaly_t* sensors,
    uint8_t count,
    float epsilon
);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_ANOMALY_H
