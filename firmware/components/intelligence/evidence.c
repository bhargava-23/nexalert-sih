/**
 * @file evidence.c
 * @brief Evidence (E_h) calculation for NexAlert edge intelligence
 *
 * Specification: Document 04, Sections 6.1-6.4
 * Reference: reference/python/nexalert_reference/evidence.py
 *
 * Formula: E_h = threshold-based rule matching with core evidence floor
 */

#include "evidence.h"
#include <math.h>
#include <string.h>

// Numerical epsilon (matches Python reference)
#define EPSILON 1e-9f

/**
 * Helper: Find sensor reading by name
 */
static const sensor_reading_t* find_sensor(
    const char* sensor_name,
    const sensor_reading_t* readings,
    uint8_t reading_count
)
{
    for (uint8_t i = 0; i < reading_count; i++) {
        if (strcmp(readings[i].sensor, sensor_name) == 0) {
            return &readings[i];
        }
    }
    return NULL;
}

evidence_result_t compute_evidence(
    const sensor_reading_t* readings,
    uint8_t reading_count,
    const evidence_config_t* config,
    float epsilon
)
{
    evidence_result_t result = {
        .e_h = 0.0f,
        .valid = false
    };

    // Validate configuration
    if (config == NULL || readings == NULL) {
        return result;
    }

    uint8_t total_rule_count = config->core_rule_count + config->supporting_rule_count;
    if (total_rule_count == 0) {
        return result;  // No sensors configured for hazard
    }

    // Compute evidence from rule matching
    float matched_weight = 0.0f;
    float total_weight = 0.0f;
    uint8_t available_sensor_count = 0;

    // Process core rules
    for (uint8_t i = 0; i < config->core_rule_count; i++) {
        const evidence_rule_t* rule = &config->core_rules[i];
        total_weight += rule->weight;

        // Find sensor reading
        const sensor_reading_t* reading = find_sensor(rule->sensor, readings, reading_count);
        if (reading != NULL && !isnan(reading->value)) {
            available_sensor_count++;
            // Check if matches threshold
            if (reading->value >= rule->threshold_min && reading->value <= rule->threshold_max) {
                matched_weight += rule->weight;
            }
        }
    }

    // Process supporting rules
    for (uint8_t i = 0; i < config->supporting_rule_count; i++) {
        const evidence_rule_t* rule = &config->supporting_rules[i];
        total_weight += rule->weight;

        // Find sensor reading
        const sensor_reading_t* reading = find_sensor(rule->sensor, readings, reading_count);
        if (reading != NULL && !isnan(reading->value)) {
            available_sensor_count++;
            // Check if matches threshold
            if (reading->value >= rule->threshold_min && reading->value <= rule->threshold_max) {
                matched_weight += rule->weight;
            }
        }
    }

    // Check if all sensors missing
    if (available_sensor_count == 0) {
        return result;  // All sensors missing
    }

    // Check for zero denominator
    if (total_weight < epsilon) {
        return result;
    }

    // Compute raw evidence
    float e_h_raw = matched_weight / total_weight;

    // Apply core evidence floor if configured
    float e_h;
    if (config->use_core_floor && config->core_rule_count > 0) {
        float core_coverage = compute_core_coverage(
            readings,
            reading_count,
            config->core_rules,
            config->core_rule_count
        );

        e_h = apply_core_floor(
            e_h_raw,
            core_coverage,
            config->core_floor.min_core_coverage,
            config->core_floor.cap_without_core
        );
    } else {
        e_h = e_h_raw;
    }

    // Clamp to [0, 1]
    if (e_h < 0.0f) {
        e_h = 0.0f;
    } else if (e_h > 1.0f) {
        e_h = 1.0f;
    }

    result.e_h = e_h;
    result.valid = true;

    return result;
}

float compute_core_coverage(
    const sensor_reading_t* readings,
    uint8_t reading_count,
    const evidence_rule_t* core_rules,
    uint8_t core_rule_count
)
{
    if (core_rule_count == 0) {
        return 1.0f;  // No core sensors required
    }

    float total_core_weight = 0.0f;
    float available_core_weight = 0.0f;

    for (uint8_t i = 0; i < core_rule_count; i++) {
        const evidence_rule_t* rule = &core_rules[i];
        total_core_weight += rule->weight;

        // Find sensor reading
        const sensor_reading_t* reading = find_sensor(rule->sensor, readings, reading_count);
        if (reading != NULL && !isnan(reading->value)) {
            available_core_weight += rule->weight;
        }
    }

    if (total_core_weight == 0.0f) {
        return 1.0f;
    }

    return available_core_weight / total_core_weight;
}

float apply_core_floor(
    float e_h,
    float core_coverage,
    float min_core_coverage,
    float cap_without_core
)
{
    if (core_coverage >= min_core_coverage) {
        return e_h;  // Core coverage sufficient
    } else {
        // Cap evidence when core coverage insufficient
        return (e_h < cap_without_core) ? e_h : cap_without_core;
    }
}
