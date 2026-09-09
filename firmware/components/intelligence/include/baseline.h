/**
 * @file baseline.h
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
 *
 * Baseline States: INITIALIZING → LEARNING → READY ⇄ FROZEN → RECOVERING
 */

#ifndef NEXALERT_BASELINE_H
#define NEXALERT_BASELINE_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Configuration (PROTOTYPE values from reference)
#define BASELINE_MIN_SAMPLES_INIT      10    // Samples to exit INITIALIZING
#define BASELINE_MIN_SAMPLES_LEARNING  50    // Samples to reach READY
#define BASELINE_RECOVERY_STABILITY    10    // Stability samples for FROZEN → RECOVERING
#define BASELINE_MAX_HISTORY           100   // Maximum bounded history (ESP32 constraint)

/**
 * Baseline state enumeration
 */
typedef enum {
    BASELINE_INITIALIZING,  // Collecting initial samples
    BASELINE_LEARNING,      // Building baseline
    BASELINE_READY,         // Baseline ready for use
    BASELINE_FROZEN,        // Intentionally frozen during hazard event
    BASELINE_RECOVERING     // Post-event recovery
} baseline_state_t;

/**
 * Robust baseline computation result
 */
typedef struct {
    float median;            // Baseline median
    float scale;             // Baseline scale (robust stddev equivalent)
    bool valid;              // true = computation successful, false = insufficient samples
} baseline_result_t;

/**
 * Z-score computation result
 */
typedef struct {
    float z_score;           // Standardized deviation (unbounded)
    bool valid;              // true = computation successful, false = missing/invalid input
} zscore_result_t;

/**
 * Baseline state transition result
 */
typedef struct {
    baseline_state_t next_state;        // Next baseline state
    uint16_t stability_count;           // Updated stability counter
} baseline_state_result_t;

/**
 * Baseline configuration
 */
typedef struct {
    uint16_t min_samples_init;          // Samples to exit INITIALIZING
    uint16_t min_samples_learning;      // Samples to reach READY
    uint16_t recovery_stability_samples; // Stability samples for recovery
    uint16_t max_history;               // Maximum bounded history size
    float epsilon;                      // Numerical epsilon (1e-9f)
} baseline_config_t;

/**
 * Compute robust baseline using median and MAD
 *
 * Implements Document 04, Section 4.1:
 *   median = median(samples)
 *   MAD = median(|samples - median|)
 *   scale = 1.4826 × MAD + ε
 *
 * Args:
 *   samples: Array of valid samples (no NAN values)
 *   count: Number of samples (must be ≥ 2)
 *   epsilon: Numerical epsilon (default 1e-9f)
 *
 * Returns:
 *   baseline_result_t:
 *     - median: Robust center (50th percentile)
 *     - scale: Robust scale (MAD × 1.4826 + ε)
 *     - valid: true if count ≥ 2, false otherwise
 *
 * Invariants:
 *   - Requires at least 2 samples (valid=false if count < 2)
 *   - MAD = 0 (all identical) → scale = ε (prevents divide-by-zero)
 *   - 1.4826 converts MAD to Gaussian-equivalent stddev
 *   - Robust to outliers (median-based, not mean-based)
 *
 * Note: samples array must contain only valid values (no NAN).
 * Caller must filter invalid samples before calling.
 */
baseline_result_t compute_robust_baseline(
    const float* samples,
    uint16_t count,
    float epsilon
);

/**
 * Compute z-score for anomaly detection
 *
 * Implements Document 04, Section 4.1:
 *   z_i = (value - median) / scale
 *
 * Args:
 *   value: Current observation (NAN = missing)
 *   median: Baseline median (from compute_robust_baseline)
 *   scale: Baseline scale (from compute_robust_baseline)
 *   epsilon: Scale threshold for meaningful z-score
 *
 * Returns:
 *   zscore_result_t:
 *     - z_score: Standardized deviation (unbounded)
 *     - valid: true if computation successful, false if missing/invalid
 *
 * Invariants:
 *   - value = NAN → {valid: false} (preserves missing != zero)
 *   - scale < ε → {valid: false} (cannot compute meaningful z-score)
 *   - z_score = 0 means value equals baseline median
 *   - |z_score| = 1 means value is 1 scale unit from median
 *   - Large |z_score| indicates anomaly
 */
zscore_result_t compute_z_score(
    float value,
    float median,
    float scale,
    float epsilon
);

/**
 * Update baseline state machine
 *
 * Implements Document 04, Section 4.1 state transitions:
 *   INITIALIZING → LEARNING → READY ⇄ FROZEN → RECOVERING → READY
 *
 * Args:
 *   current_state: Current baseline state
 *   sample_count: Number of samples collected
 *   config: Baseline configuration (thresholds, parameters)
 *   hazard_state: Current hazard state (INPUT ONLY - no circular write)
 *   hazard_stability_count: Consecutive samples with favorable hazard state
 *
 * Returns:
 *   baseline_state_result_t:
 *     - next_state: Next baseline state
 *     - stability_count: Updated stability counter
 *
 * State Ownership (NO CIRCULAR DEPENDENCY):
 *   - Baseline state machine OWNS baseline state transitions
 *   - Hazard state machine OWNS hazard state transitions
 *   - Baseline READS hazard state as INPUT (no circular write)
 *
 * Freeze/Recovery Logic:
 *   - FREEZE trigger: hazard_state in ["CONFIRMED", "CRITICAL"]
 *   - RECOVERY trigger: hazard_state in ["NORMAL", "WATCH"] AND
 *                      remained there for recovery_stability_samples
 *
 * Stability Counter:
 *   - Increments when hazard_state in ["NORMAL", "WATCH"]
 *   - Resets to 0 when hazard_state NOT in ["NORMAL", "WATCH"]
 *
 * Note: hazard_state is INPUT ONLY (read, never written)
 */
baseline_state_result_t update_baseline_state(
    baseline_state_t current_state,
    uint16_t sample_count,
    const baseline_config_t* config,
    const char* hazard_state,
    uint16_t hazard_stability_count
);

/**
 * Get default baseline configuration (PROTOTYPE)
 *
 * Provenance: PROTOTYPE ASSUMPTIONS
 * Validation Status: UNVALIDATED
 * Configuration Version: 1.0-prototype
 */
baseline_config_t baseline_default_config(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_BASELINE_H
