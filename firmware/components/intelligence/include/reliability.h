/**
 * @file reliability.h
 * @brief Evidence reliability (R_i) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Section 3.3
 * Formula: R_i = H_i × Q_i × K_i
 * Range: [0, 1]
 *
 * Reference: reference/python/nexalert_reference/reliability.py
 */

#ifndef NEXALERT_RELIABILITY_H
#define NEXALERT_RELIABILITY_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Reliability computation result
 */
typedef struct {
    float r_i;                   // Reliability value [0, 1] (only valid when valid=true)
    bool valid;                  // true = computation complete, false = missing input
} reliability_result_t;

/**
 * Compute evidence reliability R_i
 *
 * Implements Document 04, Section 3.3:
 *   R_i = H_i × Q_i × K_i
 *
 * Args:
 *   h_i: Sensor health H_i [0, 1]
 *        - NAN = missing (preserves missing != zero)
 *   q_i: Signal quality Q_i [0, 1]
 *        - NAN = missing (preserves missing != zero)
 *   k_i: Calibration validity K_i [0, 1]
 *        - NAN = missing (preserves missing != zero)
 *        - IMPORTANT: NO hard-coded default (Doc 04 Sec 3.3)
 *        - K_i is explicit input from calibration subsystem
 *
 * Returns:
 *   reliability_result_t:
 *     - r_i in [0,1] when valid=true
 *     - r_i undefined when valid=false (missing input)
 *     - valid=true when all components present and in range
 *     - valid=false when any component is NAN or out of range
 *
 * Invariants:
 *   - R_i = 0 if any component is 0 (strict trust gate, Doc 04 Sec 3.3)
 *   - R_i is NOT double-counted in confidence later (Doc 04 Sec 3.3)
 *   - K_i is explicit input; NO hard-coded default (calibration from Phase 6)
 *   - Missing components NOT treated as zero (IMPLEMENTATION_CONSTITUTION.md Sec 3)
 *   - All components must be in [0, 1] (Doc 04 Sec 3.3)
 *   - NAN inputs preserve missing != zero
 *
 * Note: This function computes R_i from pre-computed components.
 * Inputs come from:
 *   - h_i: From compute_health() (health.h)
 *   - q_i: From compute_quality() (quality.h)
 *   - k_i: From calibration subsystem (application-specific)
 */
reliability_result_t compute_reliability(
    float h_i,
    float q_i,
    float k_i
);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_RELIABILITY_H
