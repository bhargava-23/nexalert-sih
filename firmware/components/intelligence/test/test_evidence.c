/**
 * @file test_evidence.c
 * @brief Reference parity tests for evidence (E_h) calculation
 *
 * Tests embedded C implementation against Python reference:
 * reference/python/nexalert_reference/evidence.py
 *
 * Validates:
 * - Threshold-based rule matching
 * - Core evidence floor
 * - Missing sensor handling
 * - Configuration-driven evidence computation
 */

#include "evidence.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <stdbool.h>
#include <string.h>

// Test tolerance (float32 precision)
#define TEST_EPSILON 1e-6f

// Test result tracking
static int tests_passed = 0;
static int tests_failed = 0;

/**
 * Assert helpers
 */
#define ASSERT_FLOAT_EQ(expected, actual, message) do { \
    if (fabsf((expected) - (actual)) <= TEST_EPSILON) { \
        tests_passed++; \
        printf("  ✓ %s\n", message); \
    } else { \
        tests_failed++; \
        printf("  ✗ %s: expected %.6f, got %.6f\n", message, (expected), (actual)); \
    } \
} while(0)

#define ASSERT_TRUE(condition, message) do { \
    if (condition) { \
        tests_passed++; \
        printf("  ✓ %s\n", message); \
    } else { \
        tests_failed++; \
        printf("  ✗ %s: condition false\n", message); \
    } \
} while(0)

#define ASSERT_FALSE(condition, message) do { \
    if (!(condition)) { \
        tests_passed++; \
        printf("  ✓ %s\n", message); \
    } else { \
        tests_failed++; \
        printf("  ✗ %s: condition true\n", message); \
    } \
} while(0)

/**
 * Test 1: Fire nominal evidence (Python reference case)
 *
 * Python equivalent:
 *   config = {
 *     "core_evidence": [
 *       {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 0.5},
 *       {"sensor": "smoke", "threshold_min": 0.3, "threshold_max": 1.0, "weight": 0.3}
 *     ],
 *     "supporting_evidence": [],
 *     "core_evidence_floor": {"min_core_coverage": 0.5, "cap_without_core": 0.3}
 *   }
 *   readings = {"temperature": 80.0, "smoke": 0.6}
 *   E_h = (0.5 + 0.3) / (0.5 + 0.3) = 1.0 (both core sensors match)
 */
void test_fire_nominal(void)
{
    printf("\nTest 1: Fire nominal evidence\n");

    evidence_config_t config = {0};

    // Core evidence rules
    strcpy(config.core_rules[0].sensor, "temperature");
    config.core_rules[0].threshold_min = 60.0f;
    config.core_rules[0].threshold_max = 150.0f;
    config.core_rules[0].weight = 0.5f;

    strcpy(config.core_rules[1].sensor, "smoke");
    config.core_rules[1].threshold_min = 0.3f;
    config.core_rules[1].threshold_max = 1.0f;
    config.core_rules[1].weight = 0.3f;

    config.core_rule_count = 2;
    config.supporting_rule_count = 0;

    config.use_core_floor = true;
    config.core_floor.min_core_coverage = 0.5f;
    config.core_floor.cap_without_core = 0.3f;

    sensor_reading_t readings[2];
    strcpy(readings[0].sensor, "temperature");
    readings[0].value = 80.0f;
    strcpy(readings[1].sensor, "smoke");
    readings[1].value = 0.6f;

    evidence_result_t result = compute_evidence(readings, 2, &config, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(1.0f, result.e_h, "E_h = 1.0 (both core sensors match)");
}

/**
 * Test 2: Fire core missing (Python reference case)
 *
 * Python equivalent:
 *   readings = {"temperature": None, "smoke": 0.6}
 *   Core coverage = 0.3 / 0.8 = 0.375 < 0.5
 *   E_h_raw = 0.3 / 0.8 = 0.375
 *   E_h = min(0.375, 0.3) = 0.3 (capped by core floor)
 */
void test_fire_core_missing(void)
{
    printf("\nTest 2: Fire core missing (temperature unavailable)\n");

    evidence_config_t config = {0};

    strcpy(config.core_rules[0].sensor, "temperature");
    config.core_rules[0].threshold_min = 60.0f;
    config.core_rules[0].threshold_max = 150.0f;
    config.core_rules[0].weight = 0.5f;

    strcpy(config.core_rules[1].sensor, "smoke");
    config.core_rules[1].threshold_min = 0.3f;
    config.core_rules[1].threshold_max = 1.0f;
    config.core_rules[1].weight = 0.3f;

    config.core_rule_count = 2;
    config.supporting_rule_count = 0;

    config.use_core_floor = true;
    config.core_floor.min_core_coverage = 0.5f;
    config.core_floor.cap_without_core = 0.3f;

    sensor_reading_t readings[1];
    strcpy(readings[0].sensor, "smoke");
    readings[0].value = 0.6f;

    evidence_result_t result = compute_evidence(readings, 1, &config, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.3f, result.e_h, "E_h = 0.3 (capped by core floor)");
}

/**
 * Test 3: Fire supporting only (Python reference case)
 *
 * Python equivalent:
 *   config with supporting rules
 *   readings = {"humidity": 0.2}  # Only supporting sensor
 *   Core coverage = 0.0 < 0.5
 *   E_h_raw = 0.1 / 0.1 = 1.0
 *   E_h = min(1.0, 0.3) = 0.3 (capped by core floor)
 */
void test_fire_supporting_only(void)
{
    printf("\nTest 3: Fire supporting only (no core sensors)\n");

    evidence_config_t config = {0};

    strcpy(config.core_rules[0].sensor, "temperature");
    config.core_rules[0].threshold_min = 60.0f;
    config.core_rules[0].threshold_max = 150.0f;
    config.core_rules[0].weight = 0.5f;

    strcpy(config.core_rules[1].sensor, "smoke");
    config.core_rules[1].threshold_min = 0.3f;
    config.core_rules[1].threshold_max = 1.0f;
    config.core_rules[1].weight = 0.3f;

    config.core_rule_count = 2;

    strcpy(config.supporting_rules[0].sensor, "humidity");
    config.supporting_rules[0].threshold_min = 0.0f;
    config.supporting_rules[0].threshold_max = 0.3f;
    config.supporting_rules[0].weight = 0.1f;

    config.supporting_rule_count = 1;

    config.use_core_floor = true;
    config.core_floor.min_core_coverage = 0.5f;
    config.core_floor.cap_without_core = 0.3f;

    sensor_reading_t readings[1];
    strcpy(readings[0].sensor, "humidity");
    readings[0].value = 0.2f;

    evidence_result_t result = compute_evidence(readings, 1, &config, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.3f, result.e_h, "E_h = 0.3 (capped, no core sensors)");
}

/**
 * Test 4: Threshold boundary (Python reference case)
 *
 * Python equivalent:
 *   readings = {"temperature": 60.0}  # Exactly at threshold_min
 *   Should match threshold
 */
void test_threshold_boundary(void)
{
    printf("\nTest 4: Threshold boundary (exact match)\n");

    evidence_config_t config = {0};

    strcpy(config.core_rules[0].sensor, "temperature");
    config.core_rules[0].threshold_min = 60.0f;
    config.core_rules[0].threshold_max = 150.0f;
    config.core_rules[0].weight = 1.0f;

    config.core_rule_count = 1;
    config.supporting_rule_count = 0;
    config.use_core_floor = false;

    sensor_reading_t readings[1];
    strcpy(readings[0].sensor, "temperature");
    readings[0].value = 60.0f;  // Exactly at threshold_min

    evidence_result_t result = compute_evidence(readings, 1, &config, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(1.0f, result.e_h, "E_h = 1.0 (matches threshold)");
}

/**
 * Test 5: All missing (Python reference case)
 *
 * Python equivalent:
 *   readings = {"temperature": None, "smoke": None}
 *   Returns None (all sensors missing)
 */
void test_all_missing(void)
{
    printf("\nTest 5: All sensors missing\n");

    evidence_config_t config = {0};

    strcpy(config.core_rules[0].sensor, "temperature");
    config.core_rules[0].threshold_min = 60.0f;
    config.core_rules[0].threshold_max = 150.0f;
    config.core_rules[0].weight = 0.5f;

    config.core_rule_count = 1;
    config.supporting_rule_count = 0;
    config.use_core_floor = false;

    sensor_reading_t readings[1];
    strcpy(readings[0].sensor, "temperature");
    readings[0].value = NAN;  // Missing

    evidence_result_t result = compute_evidence(readings, 1, &config, 1e-9f);

    ASSERT_FALSE(result.valid, "All missing invalid");
}

/**
 * Test 6: Partial threshold match (Python reference case)
 *
 * Python equivalent:
 *   readings = {"temperature": 80.0, "smoke": 0.1}
 *   temperature matches (60-150), smoke doesn't match (0.3-1.0)
 *   E_h = 0.5 / 0.8 = 0.625
 */
void test_partial_threshold_match(void)
{
    printf("\nTest 6: Partial threshold match\n");

    evidence_config_t config = {0};

    strcpy(config.core_rules[0].sensor, "temperature");
    config.core_rules[0].threshold_min = 60.0f;
    config.core_rules[0].threshold_max = 150.0f;
    config.core_rules[0].weight = 0.5f;

    strcpy(config.core_rules[1].sensor, "smoke");
    config.core_rules[1].threshold_min = 0.3f;
    config.core_rules[1].threshold_max = 1.0f;
    config.core_rules[1].weight = 0.3f;

    config.core_rule_count = 2;
    config.supporting_rule_count = 0;
    config.use_core_floor = false;

    sensor_reading_t readings[2];
    strcpy(readings[0].sensor, "temperature");
    readings[0].value = 80.0f;  // Matches
    strcpy(readings[1].sensor, "smoke");
    readings[1].value = 0.1f;  // Doesn't match

    evidence_result_t result = compute_evidence(readings, 2, &config, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.625f, result.e_h, "E_h = 0.625 (partial match)");
}

/**
 * Test 7: Zero denominator (Python reference case)
 *
 * Python equivalent:
 *   config with all weights = 0
 *   Returns None (zero denominator)
 */
void test_zero_denominator(void)
{
    printf("\nTest 7: Zero denominator (all weights zero)\n");

    evidence_config_t config = {0};

    strcpy(config.core_rules[0].sensor, "temperature");
    config.core_rules[0].threshold_min = 60.0f;
    config.core_rules[0].threshold_max = 150.0f;
    config.core_rules[0].weight = 0.0f;  // Zero weight

    config.core_rule_count = 1;
    config.supporting_rule_count = 0;
    config.use_core_floor = false;

    sensor_reading_t readings[1];
    strcpy(readings[0].sensor, "temperature");
    readings[0].value = 80.0f;

    evidence_result_t result = compute_evidence(readings, 1, &config, 1e-9f);

    ASSERT_FALSE(result.valid, "Zero denominator invalid");
}

/**
 * Test 8: Core coverage all available (Python reference case)
 *
 * Python equivalent:
 *   compute_core_coverage({"temperature": 80.0, "smoke": 0.6}, core_rules)
 *   = 1.0 (both available)
 */
void test_core_coverage_all_available(void)
{
    printf("\nTest 8: Core coverage all available\n");

    evidence_rule_t core_rules[2];
    strcpy(core_rules[0].sensor, "temperature");
    core_rules[0].weight = 0.5f;
    strcpy(core_rules[1].sensor, "smoke");
    core_rules[1].weight = 0.3f;

    sensor_reading_t readings[2];
    strcpy(readings[0].sensor, "temperature");
    readings[0].value = 80.0f;
    strcpy(readings[1].sensor, "smoke");
    readings[1].value = 0.6f;

    float coverage = compute_core_coverage(readings, 2, core_rules, 2);

    ASSERT_FLOAT_EQ(1.0f, coverage, "Core coverage = 1.0");
}

/**
 * Test 9: Core coverage partial (Python reference case)
 *
 * Python equivalent:
 *   compute_core_coverage({"temperature": 80.0, "smoke": None}, core_rules)
 *   = 0.5 / 0.8 = 0.625 (only temperature available)
 */
void test_core_coverage_partial(void)
{
    printf("\nTest 9: Core coverage partial\n");

    evidence_rule_t core_rules[2];
    strcpy(core_rules[0].sensor, "temperature");
    core_rules[0].weight = 0.5f;
    strcpy(core_rules[1].sensor, "smoke");
    core_rules[1].weight = 0.3f;

    sensor_reading_t readings[1];
    strcpy(readings[0].sensor, "temperature");
    readings[0].value = 80.0f;

    float coverage = compute_core_coverage(readings, 1, core_rules, 2);

    ASSERT_FLOAT_EQ(0.625f, coverage, "Core coverage = 0.625");
}

/**
 * Test 10: Core coverage none available (Python reference case)
 *
 * Python equivalent:
 *   compute_core_coverage({"temperature": None, "smoke": None}, core_rules)
 *   = 0.0 (none available)
 */
void test_core_coverage_none(void)
{
    printf("\nTest 10: Core coverage none available\n");

    evidence_rule_t core_rules[2];
    strcpy(core_rules[0].sensor, "temperature");
    core_rules[0].weight = 0.5f;
    strcpy(core_rules[1].sensor, "smoke");
    core_rules[1].weight = 0.3f;

    sensor_reading_t readings[2];
    strcpy(readings[0].sensor, "temperature");
    readings[0].value = NAN;
    strcpy(readings[1].sensor, "smoke");
    readings[1].value = NAN;

    float coverage = compute_core_coverage(readings, 2, core_rules, 2);

    ASSERT_FLOAT_EQ(0.0f, coverage, "Core coverage = 0.0");
}

/**
 * Test 11: Apply core floor - sufficient coverage (Python reference case)
 *
 * Python equivalent:
 *   apply_core_floor(0.8, 1.0, 0.5, 0.3)
 *   = 0.8 (core coverage sufficient, no cap)
 */
void test_apply_floor_sufficient(void)
{
    printf("\nTest 11: Apply core floor - sufficient coverage\n");

    float e_h = apply_core_floor(0.8f, 1.0f, 0.5f, 0.3f);

    ASSERT_FLOAT_EQ(0.8f, e_h, "E_h = 0.8 (no cap)");
}

/**
 * Test 12: Apply core floor - insufficient coverage (Python reference case)
 *
 * Python equivalent:
 *   apply_core_floor(0.8, 0.3, 0.5, 0.3)
 *   = 0.3 (core coverage insufficient, capped)
 */
void test_apply_floor_insufficient(void)
{
    printf("\nTest 12: Apply core floor - insufficient coverage\n");

    float e_h = apply_core_floor(0.8f, 0.3f, 0.5f, 0.3f);

    ASSERT_FLOAT_EQ(0.3f, e_h, "E_h = 0.3 (capped)");
}

/**
 * Test 13: Apply core floor - below cap anyway (Python reference case)
 *
 * Python equivalent:
 *   apply_core_floor(0.2, 0.3, 0.5, 0.3)
 *   = 0.2 (below cap anyway)
 */
void test_apply_floor_below_cap(void)
{
    printf("\nTest 13: Apply core floor - below cap anyway\n");

    float e_h = apply_core_floor(0.2f, 0.3f, 0.5f, 0.3f);

    ASSERT_FLOAT_EQ(0.2f, e_h, "E_h = 0.2 (below cap)");
}

/**
 * Main test runner
 */
int main(void)
{
    printf("=== Evidence (E_h) Reference Parity Tests ===\n");
    printf("Reference: reference/python/nexalert_reference/evidence.py\n");

    // Evidence computation tests
    test_fire_nominal();
    test_fire_core_missing();
    test_fire_supporting_only();
    test_threshold_boundary();
    test_all_missing();
    test_partial_threshold_match();
    test_zero_denominator();

    // Core coverage tests
    test_core_coverage_all_available();
    test_core_coverage_partial();
    test_core_coverage_none();

    // Core floor tests
    test_apply_floor_sufficient();
    test_apply_floor_insufficient();
    test_apply_floor_below_cap();

    printf("\n=== Test Summary ===\n");
    printf("Passed: %d\n", tests_passed);
    printf("Failed: %d\n", tests_failed);

    if (tests_failed == 0) {
        printf("\n✓ ALL TESTS PASSED\n");
        return 0;
    } else {
        printf("\n✗ SOME TESTS FAILED\n");
        return 1;
    }
}
