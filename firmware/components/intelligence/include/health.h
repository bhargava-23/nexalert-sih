/**
 * @file health.h
 * @brief Sensor health (H_i) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Section 3.1
 * Formula: H_i^soft = Σ_j w_ij · D_ij,  H_i = 0 if F_i=1 else H_i^soft
 * Range: [0, 1]
 *
 * Reference: reference/python/nexalert_reference/health.py
 * PHASE 4: Missing diagnostics behavior preserves missing != zero
 */

#ifndef NEXALERT_HEALTH_H
#define NEXALERT_HEALTH_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Maximum diagnostic dimensions supported
 */
#define HEALTH_MAX_DIAGNOSTICS 8

/**
 * Health diagnostic dimension
 */
typedef struct {
    const char* key;             // Diagnostic key (e.g., "uptime", "self_test")
    float value;                 // D_ij normalized [0, 1]
    float weight;                // w_ij weight (all weights must sum to 1)
} health_diagnostic_t;

/**
 * Health computation result
 */
typedef struct {
    float h_i;                   // Health value [0, 1] (only valid when complete=true)
    bool complete;               // true = all diagnostics present, false = incomplete
    bool hard_failure;           // true = F_i=1 forced H_i=0
} health_result_t;

/**
 * Compute sensor health H_i
 *
 * Implements Document 04, Section 3.1:
 *   H_i^soft = Σ_j w_ij · D_ij
 *   H_i = 0 if F_i=1 else H_i^soft
 *
 * Args:
 *   diagnostics: Array of diagnostic dimensions (D_ij with weights w_ij)
 *   num_diagnostics: Number of diagnostics (must be > 0)
 *   hard_failure: F_i flag (true forces H_i=0)
 *
 * Returns:
 *   health_result_t:
 *     - h_i in [0,1] when complete=true
 *     - h_i undefined when complete=false (missing diagnostics)
 *     - complete=true when all diagnostics present and weights sum to 1
 *     - complete=false when diagnostics incomplete (missing != zero)
 *
 * Invariants:
 *   - Hard failure F_i=1 forces H_i=0 (Doc 04 Sec 3.1)
 *   - Missing diagnostics NOT treated as zero (IMPLEMENTATION_CONSTITUTION.md Sec 3)
 *   - Weights must sum to 1 within epsilon (Doc 04 Sec 3.1)
 *   - All D_ij must be in [0, 1] (Doc 04 Sec 3.1)
 *
 * PHASE 4 DECISION: Missing diagnostic behavior returns complete=false,
 * preserving missing != zero and signaling degraded information explicitly.
 */
health_result_t compute_health(
    const health_diagnostic_t* diagnostics,
    uint8_t num_diagnostics,
    bool hard_failure
);

/**
 * Validate health diagnostic weights sum to 1
 *
 * Args:
 *   diagnostics: Array of diagnostics with weights
 *   num_diagnostics: Number of diagnostics
 *
 * Returns:
 *   true if weights sum to 1 within epsilon, false otherwise
 */
bool validate_health_weights(
    const health_diagnostic_t* diagnostics,
    uint8_t num_diagnostics
);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_HEALTH_H
