/**
 * @file risk.h
 * @brief Operational Risk (R_h) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Section 9
 * Reference: reference/python/nexalert_reference/risk.py
 *
 * Components:
 * - E_h: Evidence component (from evidence.c)
 * - S_h: Severity component (from severity.c)
 * - T_h: Temporal/threat component (from severity.c)
 * - R_h: Final weighted combination
 *
 * Formula: R_h = w_E × E_h + w_S × S_h + w_T × T_h
 * Range: [0, 1] or None
 *
 * CRITICAL INVARIANT: Operational Risk ≠ Probability
 * - R_h measures operational urgency, NOT disaster probability
 * - Confidence handled separately by state engine (not multiplied into R_h)
 */

#ifndef NEXALERT_RISK_H
#define NEXALERT_RISK_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Numerical epsilon (matches Python reference)
#define RISK_EPSILON 1e-9f

/**
 * Risk weights (must sum to 1.0)
 */
typedef struct {
    float w_E;  // Evidence weight (PROTOTYPE: 0.4)
    float w_S;  // Severity weight (PROTOTYPE: 0.4)
    float w_T;  // Temporal/threat weight (PROTOTYPE: 0.2)
} risk_weights_t;

/**
 * Risk computation result
 */
typedef struct {
    float r_h;      // Operational risk [0, 1]
    bool valid;     // true = computation successful
} risk_result_t;

/**
 * Compute operational risk from components with reweighting
 *
 * Formula (all components available):
 *   R_h = w_E × E_h + w_S × S_h + w_T × T_h
 *
 * Missing Semantics (D16):
 *   - All NAN → returns {valid: false}
 *   - Some NAN → reweight remaining to sum to 1.0
 *   - Never converts NAN to 0.0 (missing ≠ zero)
 *
 * Args:
 *   e_h: Evidence component [0, 1] or NAN (from evidence.c)
 *   s_h: Severity component [0, 1] or NAN (from severity.c)
 *   t_h: Temporal/threat component [0, 1] or NAN
 *   weights: Weight structure (must sum to 1.0) or NULL for defaults
 *   epsilon: Zero-division guard
 *
 * Returns:
 *   risk_result_t:
 *     - r_h in [0, 1] when valid=true
 *     - r_h undefined when valid=false
 *     - valid=true when at least one component available
 *     - valid=false when all components missing
 *
 * Reweighting Example:
 *   - Configured: w_E=0.4, w_S=0.4, w_T=0.2
 *   - E_h=0.8, S_h=NAN, T_h=0.5 (severity missing)
 *   - Available weights: w_E=0.4, w_T=0.2, sum=0.6
 *   - Reweighted: w_E'=0.4/0.6=0.667, w_T'=0.2/0.6=0.333
 *   - R_h = 0.667×0.8 + 0.333×0.5 = 0.700
 *
 * CRITICAL INVARIANT: Operational Risk ≠ Probability
 *   - R_h measures operational urgency (how soon to respond)
 *   - NOT disaster probability or event likelihood
 *   - Confidence (C_h) handled separately by state engine
 *   - C_h NOT multiplied into R_h
 *
 * Dependency Flow:
 *   E_h (evidence) ← from evidence.c
 *   S_h (severity) ← from severity.c
 *   T_h (temporal) ← from severity.c temporal computation
 *   C_h NOT consumed ← Handled by state engine (Gate 8)
 *
 * Preserves Invariants:
 *   - Missing ≠ zero
 *   - Risk ≠ probability
 *   - Confidence separation
 *   - Multi-hazard independence
 *   - Range [0, 1] for non-None results
 *
 * Provenance: Default weights are PROTOTYPE ASSUMPTIONS
 * Validation Status: UNVALIDATED
 */
risk_result_t compute_risk(
    float e_h,
    float s_h,
    float t_h,
    const risk_weights_t* weights,
    float epsilon
);

/**
 * Validate risk weight configuration
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
bool validate_risk_weights(
    const risk_weights_t* weights,
    float epsilon
);

/**
 * Get default risk weights (PROTOTYPE)
 *
 * Returns default weight structure:
 *   - w_E: 0.4
 *   - w_S: 0.4
 *   - w_T: 0.2
 *
 * Provenance: PROTOTYPE ASSUMPTIONS
 * Validation Status: UNVALIDATED
 */
risk_weights_t risk_default_weights(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_RISK_H
