/**
 * @file hazard_state.h
 * @brief Hazard State Machine for NexAlert edge intelligence
 *
 * Specification: Document 04, Section 10
 * Reference: reference/python/nexalert_reference/state_machine.py
 *
 * States: NORMAL, WATCH, SUSPECTED, CONFIRMED, CRITICAL, RESOLVED
 * Transitions: Deterministic based on E_h, C_h, S_h, R_h, A_h inputs
 * Hysteresis: Separate enter/exit thresholds prevent flapping
 * Persistence: Sample-count requirements distinguish transient from sustained
 *
 * CRITICAL INVARIANT: UNKNOWN prevents NEW CONFIRMED declarations
 * UNKNOWN information condition prevents NEW CONFIRMED hazard declarations when
 * minimum confidence/coverage gates are not satisfied. However, UNKNOWN does not
 * invalidate an already-established CONFIRMED or CRITICAL hazard; existing hazards
 * may escalate based on valid severity/risk evidence under the safety-first
 * escalation rules.
 */

#ifndef NEXALERT_HAZARD_STATE_H
#define NEXALERT_HAZARD_STATE_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Numerical epsilon
#define HAZARD_STATE_EPSILON 1e-9f

/**
 * Hazard state enumeration
 */
typedef enum {
    HAZARD_STATE_NORMAL = 0,      // No meaningful hazard hypothesis
    HAZARD_STATE_WATCH = 1,       // Something meaningful changing
    HAZARD_STATE_SUSPECTED = 2,   // Hazard plausible but incomplete
    HAZARD_STATE_CONFIRMED = 3,   // Evidence supports credible declaration
    HAZARD_STATE_CRITICAL = 4,    // Urgent/severe/rapidly escalating
    HAZARD_STATE_RESOLVED = 5     // Hazard subsided, sustained safe conditions
} hazard_state_t;

/**
 * Information quality condition (independent of hazard state)
 */
typedef enum {
    INFO_CONDITION_GOOD = 0,      // Sufficient observations available
    INFO_CONDITION_DEGRADED = 1,  // Important limitations but reasoning possible
    INFO_CONDITION_UNKNOWN = 2    // Cannot responsibly characterize situation
} information_condition_t;

/**
 * State machine configuration (all PROTOTYPE values)
 */
typedef struct {
    // Escalation thresholds (enter)
    float watch_risk_enter;
    float watch_anomaly_enter;
    float suspected_evidence_enter;
    float confirmed_evidence_enter;
    float confirmed_confidence_min;
    float confirmed_core_coverage_min;
    float critical_severity_enter;
    float critical_risk_enter;
    float resolved_evidence_max;
    float resolved_risk_max;

    // De-escalation thresholds (exit, with hysteresis)
    float watch_risk_exit;
    float suspected_evidence_exit;
    float confirmed_evidence_exit;
    float confirmed_confidence_min_exit;
    float confirmed_core_coverage_min_exit;
    float critical_severity_exit;
    float critical_risk_exit;

    // Persistence requirements (samples)
    uint8_t watch_enter_persistence;
    uint8_t suspected_enter_persistence;
    uint8_t confirmed_enter_persistence;
    uint8_t critical_enter_persistence;
    uint8_t resolved_enter_persistence;
    uint8_t deescalate_persistence;

    // Fast escalation
    float fast_watch_to_confirmed_evidence;
    float fast_watch_to_confirmed_severity;
    float fast_watch_to_confirmed_confidence;
    float fast_watch_to_confirmed_core_coverage;
    uint8_t fast_watch_to_confirmed_persistence;
    float fast_suspected_to_critical_severity;
    float fast_suspected_to_critical_temporal;
    float fast_suspected_to_critical_confidence;
    float fast_suspected_to_critical_core_coverage;

    // RESOLVED hold
    float resolved_hold_seconds;

    // Information condition thresholds
    float good_confidence_min;
    float good_core_coverage_min;
    float degraded_confidence_min;
    float degraded_core_coverage_min;

    // Staleness
    float max_staleness_seconds;
} state_machine_config_t;

/**
 * Intelligence inputs for state machine
 */
typedef struct {
    float E_h;            // Evidence [0, 1] or NAN
    float C_h;            // Confidence [0, 1] or NAN
    float S_h;            // Severity [0, 1] or NAN
    float R_h;            // Risk [0, 1] or NAN
    float A_h;            // Anomaly [0, 1] or NAN
    float T_h;            // Temporal [0, 1] or NAN
    float core_coverage;  // Core coverage [0, 1] or NAN
} intelligence_inputs_t;

/**
 * State transition result
 */
typedef struct {
    hazard_state_t new_state;              // Resulting hazard state
    hazard_state_t prev_state;             // Previous hazard state
    char reason[256];                       // Human-readable transition reason
    uint16_t persistence_counter;          // Updated persistence counter
    float resolved_hold_start;             // Timestamp when RESOLVED entered (NAN if not)
    bool should_freeze_baseline;           // True if baseline should freeze (post-transition)
    information_condition_t info_condition; // Current information condition
} state_transition_t;

/**
 * Compute information condition from confidence and sensor availability
 *
 * Args:
 *   confidence: Confidence [0, 1] or NAN
 *   core_coverage: Core sensor coverage [0, 1] or NAN
 *   baseline_status: Baseline state ("INITIALIZING", "LEARNING", "READY", "FROZEN", "RECOVERING")
 *   config: State machine configuration
 *   epsilon: Numerical epsilon
 *
 * Returns:
 *   GOOD: C_h >= 0.7 AND core_coverage >= 0.8
 *   DEGRADED: 0.4 <= C_h < 0.7 OR 0.5 <= core_coverage < 0.8
 *   UNKNOWN: C_h < 0.4 OR core_coverage < 0.5 OR baseline INITIALIZING
 */
information_condition_t compute_information_condition(
    float confidence,
    float core_coverage,
    const char* baseline_status,
    const state_machine_config_t* config,
    float epsilon
);

/**
 * Update hazard state based on current intelligence
 *
 * Args:
 *   current_state: Previous hazard state
 *   intelligence: Current intelligence outputs
 *   baseline_status: Current baseline state
 *   timestamp: Current timestamp (seconds)
 *   persistence_counter: Previous persistence counter
 *   resolved_hold_start: Timestamp when RESOLVED entered (NAN if not in RESOLVED)
 *   config: State machine configuration
 *   epsilon: Numerical epsilon
 *
 * Returns:
 *   State transition result with new state, reason, updated counters
 *
 * Deterministic: Same inputs + config → same output
 *
 * CRITICAL INVARIANT: UNKNOWN prevents NEW CONFIRMED declarations
 * - UNKNOWN blocks NORMAL/WATCH/SUSPECTED → CONFIRMED transitions
 * - Existing CONFIRMED/CRITICAL may continue under UNKNOWN (safety-first)
 * - Fast paths bypass persistence ONLY, NOT information gates
 */
state_transition_t update_state(
    hazard_state_t current_state,
    const intelligence_inputs_t* intelligence,
    const char* baseline_status,
    float timestamp,
    uint16_t persistence_counter,
    float resolved_hold_start,
    const state_machine_config_t* config,
    float epsilon
);

/**
 * Validate state machine configuration
 *
 * Args:
 *   config: Configuration to validate
 *   epsilon: Tolerance for threshold validation
 *
 * Returns:
 *   true if valid, false otherwise
 *
 * Validation Rules:
 *   - All thresholds in [0, 1]
 *   - Hysteresis: enter > exit for all transitions
 *   - Persistence values >= 1
 *   - RESOLVED hold > 0
 *   - Information condition thresholds ordered: good > degraded
 */
bool validate_state_machine_config(
    const state_machine_config_t* config,
    float epsilon
);

/**
 * Determine if baseline should be frozen given hazard state
 *
 * Args:
 *   state: Current hazard state
 *
 * Returns:
 *   true if baseline should be frozen (CONFIRMED or CRITICAL), false otherwise
 *
 * Freeze Semantics:
 *   - Freeze when entering CONFIRMED or CRITICAL
 *   - Prevents hazard conditions from corrupting baseline
 *   - Freeze is post-transition operational command (temporal separation)
 *   - No circular dependency: state doesn't consume freeze status
 */
bool should_freeze_baseline(
    hazard_state_t state
);

/**
 * Get default state machine configuration (PROTOTYPE)
 *
 * Returns default configuration with PROTOTYPE threshold values
 *
 * Provenance: PROTOTYPE ASSUMPTIONS
 * Validation Status: UNVALIDATED
 * Config Version: 1.0-prototype
 */
state_machine_config_t state_machine_default_config(void);

/**
 * Get state name as string
 *
 * Args:
 *   state: Hazard state
 *
 * Returns:
 *   String representation of state
 */
const char* hazard_state_name(hazard_state_t state);

/**
 * Get information condition name as string
 *
 * Args:
 *   condition: Information condition
 *
 * Returns:
 *   String representation of information condition
 */
const char* information_condition_name(information_condition_t condition);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_HAZARD_STATE_H
