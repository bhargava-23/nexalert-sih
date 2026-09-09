/**
 * @file quality.h
 * @brief Signal quality (Q_i) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Section 3.2
 * Formula: Q_i = q_integrity × q_stability
 * Range: [0, 1]
 *
 * Reference: reference/python/nexalert_reference/quality.py
 */

#ifndef NEXALERT_QUALITY_H
#define NEXALERT_QUALITY_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Quality computation result
 */
typedef struct {
    float q_i;                   // Quality value [0, 1] (only valid when valid=true)
    bool valid;                  // true = computation complete, false = missing input
} quality_result_t;

/**
 * Compute signal quality Q_i
 *
 * Implements Document 04, Section 3.2:
 *   Q_i = q_integrity × q_stability
 *
 * Args:
 *   q_integrity: Integrity component [0, 1]
 *                - Decreased by missing samples (Doc 04 Sec 3.2)
 *                - NAN = missing (preserves missing != zero)
 *   q_stability: Stability component [0, 1]
 *                - Decreased by high jitter (Doc 04 Sec 3.2)
 *                - NAN = missing (preserves missing != zero)
 *
 * Returns:
 *   quality_result_t:
 *     - q_i in [0,1] when valid=true
 *     - q_i undefined when valid=false (missing input)
 *     - valid=true when both components present and in range
 *     - valid=false when either component is NAN or out of range
 *
 * Invariants:
 *   - Q_i = 0 means observation unusable (Doc 04 Sec 3.2)
 *   - Missing components NOT treated as zero (IMPLEMENTATION_CONSTITUTION.md Sec 3)
 *   - Both components must be in [0, 1] (Doc 04 Sec 3.2)
 *   - NAN inputs preserve missing != zero
 *
 * Note: This function computes Q_i from pre-computed components.
 * Computation of q_integrity and q_stability is application-specific:
 *   - q_integrity: Based on sample completeness, telemetry validity
 *   - q_stability: Based on signal jitter, variance, consistency
 */
quality_result_t compute_quality(
    float q_integrity,
    float q_stability
);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_QUALITY_H
