/**
 * @file evidence.h
 * @brief Evidence (E_h) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Sections 6.1-6.4
 * Reference: reference/python/nexalert_reference/evidence.py
 *
 * Formula: E_h = threshold-based rule matching with core evidence floor
 * Range: [0, 1] or None
 *
 * Core Evidence Floor:
 *   If core_coverage < min_core_coverage → E_h = min(E_h, cap_without_core)
 */

#ifndef NEXALERT_EVIDENCE_H
#define NEXALERT_EVIDENCE_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Configuration (ESP32 constraints)
#define EVIDENCE_MAX_RULES         10    // Maximum evidence rules per hazard
#define EVIDENCE_MAX_SENSOR_NAME   32    // Maximum sensor name length

/**
 * Evidence rule (threshold-based)
 */
typedef struct {
    char sensor[EVIDENCE_MAX_SENSOR_NAME];  // Sensor type identifier
    float threshold_min;                     // Minimum threshold value
    float threshold_max;                     // Maximum threshold value
    float weight;                            // Rule weight [0, 1]
} evidence_rule_t;

/**
 * Core evidence floor configuration
 */
typedef struct {
    float min_core_coverage;    // Minimum core coverage required (PROTOTYPE: 0.5)
    float cap_without_core;     // Max E_h without core evidence (PROTOTYPE: 0.3)
} core_floor_config_t;

/**
 * Evidence configuration
 */
typedef struct {
    evidence_rule_t core_rules[EVIDENCE_MAX_RULES];      // Core evidence rules
    uint8_t core_rule_count;                              // Number of core rules
    evidence_rule_t supporting_rules[EVIDENCE_MAX_RULES]; // Supporting evidence rules
    uint8_t supporting_rule_count;                        // Number of supporting rules
    core_floor_config_t core_floor;                       // Core floor configuration
    bool use_core_floor;                                  // Whether to apply core floor
} evidence_config_t;

/**
 * Sensor reading entry
 */
typedef struct {
    char sensor[EVIDENCE_MAX_SENSOR_NAME];  // Sensor type identifier
    float value;                             // Sensor value (NAN = missing)
} sensor_reading_t;

/**
 * Evidence computation result
 */
typedef struct {
    float e_h;               // Hazard evidence [0, 1]
    bool valid;              // true = computation successful, false = insufficient data
} evidence_result_t;

/**
 * Compute hazard evidence from sensor readings
 *
 * Implements Document 04, Sections 6.1-6.4:
 *   E_h = Σ(w_i × rule_matched_i) / Σ(w_i)
 *   With core floor: If core_coverage < min → E_h = min(E_h, cap)
 *
 * Args:
 *   readings: Array of sensor readings
 *   reading_count: Number of sensor readings
 *   config: Evidence configuration (rules, thresholds, core floor)
 *   epsilon: Zero-division guard (default 1e-9f)
 *
 * Returns:
 *   evidence_result_t:
 *     - e_h in [0, 1] when valid=true
 *     - e_h undefined when valid=false (insufficient data)
 *     - valid=true when at least one sensor available and rules configured
 *     - valid=false when all sensors missing or no rules
 *
 * Missing Handling:
 *   - NAN sensor readings → excluded from computation
 *   - Missing sensors are NOT negative evidence
 *   - If all sensors missing → {valid: false}
 *   - Never convert missing to zero
 *
 * Core Evidence Floor:
 *   - If core_coverage < min_core_coverage → E_h capped at cap_without_core
 *   - Example: Fire without temp/smoke → E_h ≤ 0.3
 *
 * Evidence Aggregation:
 *   - For each sensor: if value in [threshold_min, threshold_max] → contributes weight
 *   - E_h_raw = sum(matched_weights) / sum(all_weights)
 *   - E_h clamped to [0, 1]
 *   - Core floor applied if core coverage insufficient
 *
 * Provenance: ALL threshold values are PROTOTYPE ASSUMPTIONS
 * Validation Status: UNVALIDATED - NOT scientifically authoritative
 * Owner: Phase 5 implementation (requires domain expert validation)
 */
evidence_result_t compute_evidence(
    const sensor_reading_t* readings,
    uint8_t reading_count,
    const evidence_config_t* config,
    float epsilon
);

/**
 * Compute fraction of core evidence sensors available
 *
 * Args:
 *   readings: Array of sensor readings
 *   reading_count: Number of sensor readings
 *   core_rules: Array of core evidence rules
 *   core_rule_count: Number of core rules
 *
 * Returns:
 *   Core coverage in [0, 1]
 *
 * Missing Handling:
 *   - Sensor reading is NAN → unavailable (not counted in coverage)
 *   - Never convert missing to zero
 *
 * Formula:
 *   core_coverage = Σ(w_i × available_i) / Σ(w_i)
 */
float compute_core_coverage(
    const sensor_reading_t* readings,
    uint8_t reading_count,
    const evidence_rule_t* core_rules,
    uint8_t core_rule_count
);

/**
 * Apply core evidence floor to cap E_h when core coverage insufficient
 *
 * Args:
 *   e_h: Raw evidence score [0, 1]
 *   core_coverage: Fraction of core evidence available [0, 1]
 *   min_core_coverage: Minimum core coverage required (PROTOTYPE: 0.5)
 *   cap_without_core: Max E_h without core evidence (PROTOTYPE: 0.3)
 *
 * Returns:
 *   E_h capped by core floor if necessary
 *
 * Core Evidence Floor Logic:
 *   - If core_coverage >= min_core_coverage → no cap (return e_h)
 *   - If core_coverage < min_core_coverage → E_h = min(e_h, cap_without_core)
 *
 * Provenance: min_core_coverage=0.5, cap_without_core=0.3 are PROTOTYPE ASSUMPTIONS
 * Validation Status: UNVALIDATED
 */
float apply_core_floor(
    float e_h,
    float core_coverage,
    float min_core_coverage,
    float cap_without_core
);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_EVIDENCE_H
