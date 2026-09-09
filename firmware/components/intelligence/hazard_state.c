/**
 * @file hazard_state.c
 * @brief Hazard State Machine implementation for NexAlert edge intelligence
 *
 * Specification: Document 04, Section 10
 * Reference: reference/python/nexalert_reference/state_machine.py
 *
 * Deterministic hazard state tracking with hysteresis and persistence.
 */

#include "hazard_state.h"
#include <math.h>
#include <string.h>
#include <stdio.h>

// Helper: Check if value is valid (not NAN)
static inline bool is_valid(float value) {
    return !isnan(value);
}

information_condition_t compute_information_condition(
    float confidence,
    float core_coverage,
    const char* baseline_status,
    const state_machine_config_t* config,
    float epsilon
)
{
    // INITIALIZING baseline → UNKNOWN
    if (baseline_status != NULL && strcmp(baseline_status, "INITIALIZING") == 0) {
        return INFO_CONDITION_UNKNOWN;
    }

    // Missing confidence or core_coverage → UNKNOWN
    if (!is_valid(confidence) || !is_valid(core_coverage)) {
        return INFO_CONDITION_UNKNOWN;
    }

    // UNKNOWN: C_h < 0.4 OR core_coverage < 0.5
    if (confidence < config->degraded_confidence_min ||
        core_coverage < config->degraded_core_coverage_min) {
        return INFO_CONDITION_UNKNOWN;
    }

    // GOOD: C_h >= 0.7 AND core_coverage >= 0.8
    if (confidence >= config->good_confidence_min &&
        core_coverage >= config->good_core_coverage_min) {
        return INFO_CONDITION_GOOD;
    }

    // DEGRADED: between UNKNOWN and GOOD
    return INFO_CONDITION_DEGRADED;
}

state_transition_t update_state(
    hazard_state_t current_state,
    const intelligence_inputs_t* intelligence,
    const char* baseline_status,
    float timestamp,
    uint16_t persistence_counter,
    float resolved_hold_start,
    const state_machine_config_t* config,
    float epsilon
)
{
    state_transition_t result = {
        .new_state = current_state,
        .prev_state = current_state,
        .reason = "",
        .persistence_counter = 0,
        .resolved_hold_start = resolved_hold_start,
        .should_freeze_baseline = false,
        .info_condition = INFO_CONDITION_UNKNOWN
    };

    // Compute information condition
    result.info_condition = compute_information_condition(
        intelligence->C_h,
        intelligence->core_coverage,
        baseline_status,
        config,
        epsilon
    );

    // Extract intelligence values
    float E_h = intelligence->E_h;
    float C_h = intelligence->C_h;
    float S_h = intelligence->S_h;
    float R_h = intelligence->R_h;
    float A_h = intelligence->A_h;
    float T_h = intelligence->T_h;
    float core_cov = intelligence->core_coverage;

    hazard_state_t new_state = current_state;
    uint16_t new_counter = persistence_counter;
    bool transition_occurred = false;
    char reason_buffer[256] = "";

    // State transition logic
    switch (current_state) {
        case HAZARD_STATE_NORMAL:
            // NORMAL → WATCH: Risk or anomaly crosses watch threshold
            if ((is_valid(R_h) && R_h >= config->watch_risk_enter) ||
                (is_valid(A_h) && A_h >= config->watch_anomaly_enter)) {
                new_counter++;
                if (new_counter >= config->watch_enter_persistence) {
                    new_state = HAZARD_STATE_WATCH;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "NORMAL → WATCH: Risk/anomaly crosses watch threshold (R_h=%.2f, A_h=%.2f)",
                             is_valid(R_h) ? R_h : 0.0f, is_valid(A_h) ? A_h : 0.0f);
                    transition_occurred = true;
                    new_counter = 0;
                }
            } else {
                new_counter = 0;
            }
            break;

        case HAZARD_STATE_WATCH:
            // WATCH → CONFIRMED (fast path): Very high evidence + severity + confidence + coverage
            if (is_valid(E_h) && E_h >= config->fast_watch_to_confirmed_evidence &&
                is_valid(S_h) && S_h >= config->fast_watch_to_confirmed_severity &&
                is_valid(C_h) && C_h >= config->fast_watch_to_confirmed_confidence &&
                is_valid(core_cov) && core_cov >= config->fast_watch_to_confirmed_core_coverage &&
                result.info_condition != INFO_CONDITION_UNKNOWN) {
                new_counter++;
                if (new_counter >= config->fast_watch_to_confirmed_persistence) {
                    new_state = HAZARD_STATE_CONFIRMED;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "WATCH → CONFIRMED (fast path): E_h=%.2f, S_h=%.2f, C_h=%.2f",
                             E_h, S_h, C_h);
                    transition_occurred = true;
                    new_counter = 0;
                }
            }
            // WATCH → SUSPECTED: Evidence crosses suspected threshold
            else if (is_valid(E_h) && E_h >= config->suspected_evidence_enter) {
                new_counter++;
                if (new_counter >= config->suspected_enter_persistence) {
                    new_state = HAZARD_STATE_SUSPECTED;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "WATCH → SUSPECTED: Evidence crosses suspected threshold (E_h=%.2f)", E_h);
                    transition_occurred = true;
                    new_counter = 0;
                }
            }
            // WATCH → RESOLVED: Evidence and risk below resolution thresholds
            else if (is_valid(E_h) && E_h < config->resolved_evidence_max &&
                     is_valid(R_h) && R_h < config->resolved_risk_max) {
                new_counter++;
                if (new_counter >= config->resolved_enter_persistence) {
                    new_state = HAZARD_STATE_RESOLVED;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "WATCH → RESOLVED: Evidence and risk below resolution thresholds (E_h=%.2f, R_h=%.2f)",
                             E_h, R_h);
                    transition_occurred = true;
                    new_counter = 0;
                    result.resolved_hold_start = timestamp;
                }
            }
            // WATCH → NORMAL (de-escalation via RESOLVED only - blocked)
            else {
                new_counter = 0;
            }
            break;

        case HAZARD_STATE_SUSPECTED:
            // SUSPECTED → CRITICAL (fast path): Extreme severity + temporal + minimum DEGRADED
            if (is_valid(S_h) && S_h >= config->fast_suspected_to_critical_severity &&
                is_valid(T_h) && T_h >= config->fast_suspected_to_critical_temporal &&
                is_valid(C_h) && C_h >= config->fast_suspected_to_critical_confidence &&
                is_valid(core_cov) && core_cov >= config->fast_suspected_to_critical_core_coverage &&
                result.info_condition != INFO_CONDITION_UNKNOWN) {
                new_counter++;
                if (new_counter >= config->critical_enter_persistence) {
                    new_state = HAZARD_STATE_CRITICAL;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "SUSPECTED → CRITICAL (fast path): S_h=%.2f, T_h=%.2f", S_h, T_h);
                    transition_occurred = true;
                    new_counter = 0;
                }
            }
            // SUSPECTED → CONFIRMED: High evidence + confidence + coverage
            else if (is_valid(E_h) && E_h >= config->confirmed_evidence_enter &&
                     is_valid(C_h) && C_h >= config->confirmed_confidence_min &&
                     is_valid(core_cov) && core_cov >= config->confirmed_core_coverage_min &&
                     result.info_condition != INFO_CONDITION_UNKNOWN) {
                new_counter++;
                if (new_counter >= config->confirmed_enter_persistence) {
                    new_state = HAZARD_STATE_CONFIRMED;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "SUSPECTED → CONFIRMED: High evidence + confidence + coverage (E_h=%.2f, C_h=%.2f, core=%.2f)",
                             E_h, C_h, core_cov);
                    transition_occurred = true;
                    new_counter = 0;
                }
            }
            // SUSPECTED → WATCH (de-escalation): Evidence drops below suspected threshold
            else if (is_valid(E_h) && E_h < config->suspected_evidence_exit) {
                new_counter++;
                if (new_counter >= config->deescalate_persistence) {
                    new_state = HAZARD_STATE_WATCH;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "SUSPECTED → WATCH: Evidence drops below threshold (E_h=%.2f)", E_h);
                    transition_occurred = true;
                    new_counter = 0;
                }
            }
            // SUSPECTED → RESOLVED: Evidence and risk below resolution thresholds
            else if (is_valid(E_h) && E_h < config->resolved_evidence_max &&
                     is_valid(R_h) && R_h < config->resolved_risk_max) {
                new_counter++;
                if (new_counter >= config->resolved_enter_persistence) {
                    new_state = HAZARD_STATE_RESOLVED;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "SUSPECTED → RESOLVED: Evidence and risk below resolution thresholds (E_h=%.2f, R_h=%.2f)",
                             E_h, R_h);
                    transition_occurred = true;
                    new_counter = 0;
                    result.resolved_hold_start = timestamp;
                }
            }
            else {
                new_counter = 0;
            }
            break;

        case HAZARD_STATE_CONFIRMED:
            // CONFIRMED → CRITICAL: Extreme severity or risk (any info condition - safety first)
            if ((is_valid(S_h) && S_h >= config->critical_severity_enter) ||
                (is_valid(R_h) && R_h >= config->critical_risk_enter)) {
                new_counter++;
                if (new_counter >= config->critical_enter_persistence) {
                    new_state = HAZARD_STATE_CRITICAL;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "CONFIRMED → CRITICAL: Extreme severity or risk (S_h=%.2f, R_h=%.2f)",
                             is_valid(S_h) ? S_h : 0.0f, is_valid(R_h) ? R_h : 0.0f);
                    transition_occurred = true;
                    new_counter = 0;
                }
            }
            // CONFIRMED → SUSPECTED (de-escalation): Evidence/confidence/coverage drops
            else if ((is_valid(E_h) && E_h < config->confirmed_evidence_exit) ||
                     (is_valid(C_h) && C_h < config->confirmed_confidence_min_exit) ||
                     (is_valid(core_cov) && core_cov < config->confirmed_core_coverage_min_exit)) {
                new_counter++;
                if (new_counter >= config->deescalate_persistence) {
                    new_state = HAZARD_STATE_SUSPECTED;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "CONFIRMED → SUSPECTED: Evidence/confidence/coverage drops (E_h=%.2f, C_h=%.2f, core=%.2f)",
                             is_valid(E_h) ? E_h : 0.0f, is_valid(C_h) ? C_h : 0.0f,
                             is_valid(core_cov) ? core_cov : 0.0f);
                    transition_occurred = true;
                    new_counter = 0;
                }
            }
            // CONFIRMED → RESOLVED: Evidence and risk below resolution thresholds
            else if (is_valid(E_h) && E_h < config->resolved_evidence_max &&
                     is_valid(R_h) && R_h < config->resolved_risk_max) {
                new_counter++;
                if (new_counter >= config->resolved_enter_persistence) {
                    new_state = HAZARD_STATE_RESOLVED;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "CONFIRMED → RESOLVED: Evidence and risk below resolution thresholds (E_h=%.2f, R_h=%.2f)",
                             E_h, R_h);
                    transition_occurred = true;
                    new_counter = 0;
                    result.resolved_hold_start = timestamp;
                }
            }
            else {
                new_counter = 0;
            }
            break;

        case HAZARD_STATE_CRITICAL:
            // CRITICAL → CONFIRMED (de-escalation): Severity and risk drop
            if ((is_valid(S_h) && S_h < config->critical_severity_exit) &&
                (is_valid(R_h) && R_h < config->critical_risk_exit)) {
                new_counter++;
                if (new_counter >= config->deescalate_persistence) {
                    new_state = HAZARD_STATE_CONFIRMED;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "CRITICAL → CONFIRMED: Severity and risk drop (S_h=%.2f, R_h=%.2f)",
                             S_h, R_h);
                    transition_occurred = true;
                    new_counter = 0;
                }
            }
            // CRITICAL → RESOLVED: Evidence and risk below resolution thresholds
            else if (is_valid(E_h) && E_h < config->resolved_evidence_max &&
                     is_valid(R_h) && R_h < config->resolved_risk_max) {
                new_counter++;
                if (new_counter >= config->resolved_enter_persistence) {
                    new_state = HAZARD_STATE_RESOLVED;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "CRITICAL → RESOLVED: Evidence and risk below resolution thresholds (E_h=%.2f, R_h=%.2f)",
                             E_h, R_h);
                    transition_occurred = true;
                    new_counter = 0;
                    result.resolved_hold_start = timestamp;
                }
            }
            else {
                new_counter = 0;
            }
            break;

        case HAZARD_STATE_RESOLVED:
            // RESOLVED → NORMAL: Hold period complete
            if (is_valid(resolved_hold_start) &&
                (timestamp - resolved_hold_start) >= config->resolved_hold_seconds) {
                // Check all metrics still below watch thresholds
                bool still_safe = true;
                if (is_valid(R_h) && R_h >= config->watch_risk_enter) still_safe = false;
                if (is_valid(A_h) && A_h >= config->watch_anomaly_enter) still_safe = false;
                if (is_valid(E_h) && E_h >= config->resolved_evidence_max) still_safe = false;

                if (still_safe) {
                    new_state = HAZARD_STATE_NORMAL;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "RESOLVED → NORMAL: Hold period complete (%.1fs)",
                             timestamp - resolved_hold_start);
                    transition_occurred = true;
                    new_counter = 0;
                    result.resolved_hold_start = NAN;
                } else {
                    // Re-escalation: return to WATCH
                    new_state = HAZARD_STATE_WATCH;
                    snprintf(reason_buffer, sizeof(reason_buffer),
                             "RESOLVED → WATCH: Conditions worsen during hold");
                    transition_occurred = true;
                    new_counter = 0;
                    result.resolved_hold_start = NAN;
                }
            }
            // RESOLVED → WATCH: Re-escalation during hold
            else if ((is_valid(R_h) && R_h >= config->watch_risk_enter) ||
                     (is_valid(A_h) && A_h >= config->watch_anomaly_enter)) {
                new_state = HAZARD_STATE_WATCH;
                snprintf(reason_buffer, sizeof(reason_buffer),
                         "RESOLVED → WATCH: Re-escalation during hold");
                transition_occurred = true;
                new_counter = 0;
                result.resolved_hold_start = NAN;
            }
            break;

        default:
            break;
    }

    // Update result
    result.new_state = new_state;
    result.prev_state = current_state;
    result.persistence_counter = new_counter;
    strncpy(result.reason, reason_buffer, sizeof(result.reason) - 1);
    result.reason[sizeof(result.reason) - 1] = '\0';

    // Determine if baseline should be frozen (post-transition)
    result.should_freeze_baseline = should_freeze_baseline(new_state);

    return result;
}

bool validate_state_machine_config(
    const state_machine_config_t* config,
    float epsilon
)
{
    if (config == NULL) {
        return false;
    }

    // Check all thresholds in [0, 1]
    if (config->watch_risk_enter < 0.0f || config->watch_risk_enter > 1.0f) return false;
    if (config->watch_anomaly_enter < 0.0f || config->watch_anomaly_enter > 1.0f) return false;
    if (config->suspected_evidence_enter < 0.0f || config->suspected_evidence_enter > 1.0f) return false;
    if (config->confirmed_evidence_enter < 0.0f || config->confirmed_evidence_enter > 1.0f) return false;
    if (config->confirmed_confidence_min < 0.0f || config->confirmed_confidence_min > 1.0f) return false;
    if (config->confirmed_core_coverage_min < 0.0f || config->confirmed_core_coverage_min > 1.0f) return false;
    if (config->critical_severity_enter < 0.0f || config->critical_severity_enter > 1.0f) return false;
    if (config->critical_risk_enter < 0.0f || config->critical_risk_enter > 1.0f) return false;

    // Check hysteresis: enter > exit
    if (config->watch_risk_enter <= config->watch_risk_exit + epsilon) return false;
    if (config->suspected_evidence_enter <= config->suspected_evidence_exit + epsilon) return false;
    if (config->confirmed_evidence_enter <= config->confirmed_evidence_exit + epsilon) return false;
    if (config->critical_severity_enter <= config->critical_severity_exit + epsilon) return false;
    if (config->critical_risk_enter <= config->critical_risk_exit + epsilon) return false;

    // Check persistence values >= 1
    if (config->watch_enter_persistence < 1) return false;
    if (config->suspected_enter_persistence < 1) return false;
    if (config->confirmed_enter_persistence < 1) return false;
    if (config->critical_enter_persistence < 1) return false;
    if (config->resolved_enter_persistence < 1) return false;
    if (config->deescalate_persistence < 1) return false;

    // Check RESOLVED hold > 0
    if (config->resolved_hold_seconds <= 0.0f) return false;

    // Check information condition thresholds ordered: good > degraded
    if (config->good_confidence_min <= config->degraded_confidence_min + epsilon) return false;
    if (config->good_core_coverage_min <= config->degraded_core_coverage_min + epsilon) return false;

    return true;
}

bool should_freeze_baseline(
    hazard_state_t state
)
{
    return (state == HAZARD_STATE_CONFIRMED || state == HAZARD_STATE_CRITICAL);
}

state_machine_config_t state_machine_default_config(void)
{
    state_machine_config_t config = {
        // Escalation thresholds
        .watch_risk_enter = 0.3f,
        .watch_anomaly_enter = 0.5f,
        .suspected_evidence_enter = 0.4f,
        .confirmed_evidence_enter = 0.7f,
        .confirmed_confidence_min = 0.6f,
        .confirmed_core_coverage_min = 0.7f,
        .critical_severity_enter = 0.85f,
        .critical_risk_enter = 0.9f,
        .resolved_evidence_max = 0.2f,
        .resolved_risk_max = 0.2f,

        // De-escalation thresholds (hysteresis)
        .watch_risk_exit = 0.25f,
        .suspected_evidence_exit = 0.35f,
        .confirmed_evidence_exit = 0.65f,
        .confirmed_confidence_min_exit = 0.55f,
        .confirmed_core_coverage_min_exit = 0.65f,
        .critical_severity_exit = 0.80f,
        .critical_risk_exit = 0.85f,

        // Persistence requirements
        .watch_enter_persistence = 1,
        .suspected_enter_persistence = 3,
        .confirmed_enter_persistence = 5,
        .critical_enter_persistence = 1,
        .resolved_enter_persistence = 10,
        .deescalate_persistence = 3,

        // Fast escalation
        .fast_watch_to_confirmed_evidence = 0.85f,
        .fast_watch_to_confirmed_severity = 0.8f,
        .fast_watch_to_confirmed_confidence = 0.6f,
        .fast_watch_to_confirmed_core_coverage = 0.7f,
        .fast_watch_to_confirmed_persistence = 2,
        .fast_suspected_to_critical_severity = 0.9f,
        .fast_suspected_to_critical_temporal = 0.8f,
        .fast_suspected_to_critical_confidence = 0.4f,
        .fast_suspected_to_critical_core_coverage = 0.5f,

        // RESOLVED hold
        .resolved_hold_seconds = 300.0f,  // 5 minutes

        // Information condition
        .good_confidence_min = 0.7f,
        .good_core_coverage_min = 0.8f,
        .degraded_confidence_min = 0.4f,
        .degraded_core_coverage_min = 0.5f,

        // Staleness
        .max_staleness_seconds = 60.0f
    };

    return config;
}

const char* hazard_state_name(hazard_state_t state)
{
    switch (state) {
        case HAZARD_STATE_NORMAL: return "NORMAL";
        case HAZARD_STATE_WATCH: return "WATCH";
        case HAZARD_STATE_SUSPECTED: return "SUSPECTED";
        case HAZARD_STATE_CONFIRMED: return "CONFIRMED";
        case HAZARD_STATE_CRITICAL: return "CRITICAL";
        case HAZARD_STATE_RESOLVED: return "RESOLVED";
        default: return "UNKNOWN";
    }
}

const char* information_condition_name(information_condition_t condition)
{
    switch (condition) {
        case INFO_CONDITION_GOOD: return "GOOD";
        case INFO_CONDITION_DEGRADED: return "DEGRADED";
        case INFO_CONDITION_UNKNOWN: return "UNKNOWN";
        default: return "UNKNOWN";
    }
}
