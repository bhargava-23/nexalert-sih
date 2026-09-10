/**
 * @file test_confidence.c
 * @brief Reference parity tests for confidence (C_h) calculation
 *
 * Tests embedded C implementation against Python reference:
 * reference/python/nexalert_reference/confidence.py
 *
 * Validates:
 * - Coverage confidence (C_cov)
 * - Agreement confidence (C_agree)
 * - Temporal confidence (C_temp)
 * - Baseline confidence (C_base)
 * - Final confidence combination (C_h)
 */

#include "confidence.h"
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
 * Test 1: Coverage - all sensors available
 *
 * Python equivalent:
 *   sensors = [
 *     {"sensor": "temperature", "available": True, "weight": 0.5},
 *     {"sensor": "smoke", "available": True, "weight": 0.3}
 *   ]
 *   C_cov = (0.5 + 0.3) / (0.5 + 0.3) = 1.0
 */
void test_coverage_all_available(void)
{
    printf("\nTest 1: Coverage - all sensors available\n");

    sensor_availability_t sensors[2];
    strcpy(sensors[0].sensor, "temperature");
    sensors[0].available = true;
    sensors[0].weight = 0.5f;

    strcpy(sensors[1].sensor, "smoke");
    sensors[1].available = true;
    sensors[1].weight = 0.3f;

    float c_cov = compute_coverage(sensors, 2, 1e-9f);

    ASSERT_FLOAT_EQ(1.0f, c_cov, "C_cov = 1.0 (all available)");
}

/**
 * Test 2: Coverage - partial availability
 *
 * Python equivalent:
 *   sensors = [
 *     {"sensor": "temperature", "available": True, "weight": 0.5},
 *     {"sensor": "smoke", "available": False, "weight": 0.3}
 *   ]
 *   C_cov = 0.5 / 0.8 = 0.625
 */
void test_coverage_partial(void)
{
    printf("\nTest 2: Coverage - partial availability\n");

    sensor_availability_t sensors[2];
    strcpy(sensors[0].sensor, "temperature");
    sensors[0].available = true;
    sensors[0].weight = 0.5f;

    strcpy(sensors[1].sensor, "smoke");
    sensors[1].available = false;
    sensors[1].weight = 0.3f;

    float c_cov = compute_coverage(sensors, 2, 1e-9f);

    ASSERT_FLOAT_EQ(0.625f, c_cov, "C_cov = 0.625 (partial)");
}

/**
 * Test 3: Coverage - none available
 *
 * Python equivalent:
 *   sensors = [
 *     {"sensor": "temperature", "available": False, "weight": 0.5},
 *     {"sensor": "smoke", "available": False, "weight": 0.3}
 *   ]
 *   C_cov = 0.0 / 0.8 = 0.0
 */
void test_coverage_none_available(void)
{
    printf("\nTest 3: Coverage - none available\n");

    sensor_availability_t sensors[2];
    strcpy(sensors[0].sensor, "temperature");
    sensors[0].available = false;
    sensors[0].weight = 0.5f;

    strcpy(sensors[1].sensor, "smoke");
    sensors[1].available = false;
    sensors[1].weight = 0.3f;

    float c_cov = compute_coverage(sensors, 2, 1e-9f);

    ASSERT_FLOAT_EQ(0.0f, c_cov, "C_cov = 0.0 (none available)");
}

/**
 * Test 4: Coverage - no sensors
 *
 * Python equivalent:
 *   sensors = []
 *   C_cov = 1.0 (no sensors required)
 */
void test_coverage_no_sensors(void)
{
    printf("\nTest 4: Coverage - no sensors\n");

    float c_cov = compute_coverage(NULL, 0, 1e-9f);

    ASSERT_FLOAT_EQ(1.0f, c_cov, "C_cov = 1.0 (no sensors)");
}

/**
 * Test 5: Agreement - perfect agreement
 *
 * Python equivalent:
 *   groups = [
 *     {"group": "thermal", "evidence": 0.8, "weight": 1.0},
 *     {"group": "smoke", "evidence": 0.8, "weight": 1.0}
 *   ]
 *   ē = 0.8, V_e = 0.0
 *   C_agree = exp(-2.0 × 0.0) = 1.0
 */
void test_agreement_perfect(void)
{
    printf("\nTest 5: Agreement - perfect agreement\n");

    evidence_group_t groups[2];
    strcpy(groups[0].group, "thermal");
    groups[0].evidence = 0.8f;
    groups[0].weight = 1.0f;

    strcpy(groups[1].group, "smoke");
    groups[1].evidence = 0.8f;
    groups[1].weight = 1.0f;

    float c_agree = compute_agreement(groups, 2, 2.0f, 1e-9f);

    ASSERT_FLOAT_EQ(1.0f, c_agree, "C_agree = 1.0 (perfect agreement)");
}

/**
 * Test 6: Agreement - moderate disagreement
 *
 * Python equivalent:
 *   groups = [
 *     {"group": "thermal", "evidence": 0.7, "weight": 1.0},
 *     {"group": "smoke", "evidence": 0.5, "weight": 1.0}
 *   ]
 *   ē = 0.6, V_e = 0.02
 *   C_agree = exp(-2.0 × 0.02) = exp(-0.04) ≈ 0.9608
 */
void test_agreement_moderate(void)
{
    printf("\nTest 6: Agreement - moderate disagreement\n");

    evidence_group_t groups[2];
    strcpy(groups[0].group, "thermal");
    groups[0].evidence = 0.7f;
    groups[0].weight = 1.0f;

    strcpy(groups[1].group, "smoke");
    groups[1].evidence = 0.5f;
    groups[1].weight = 1.0f;

    float c_agree = compute_agreement(groups, 2, 2.0f, 1e-9f);

    // Expected: exp(-2.0 × 0.02) = exp(-0.04) ≈ 0.960789
    ASSERT_FLOAT_EQ(0.960789f, c_agree, "C_agree ≈ 0.9608 (moderate disagreement)");
}

/**
 * Test 7: Agreement - single group
 *
 * Python equivalent:
 *   groups = [{"group": "thermal", "evidence": 0.8, "weight": 1.0}]
 *   C_agree = 1.0 (single source, no disagreement)
 */
void test_agreement_single_group(void)
{
    printf("\nTest 7: Agreement - single group\n");

    evidence_group_t groups[1];
    strcpy(groups[0].group, "thermal");
    groups[0].evidence = 0.8f;
    groups[0].weight = 1.0f;

    float c_agree = compute_agreement(groups, 1, 2.0f, 1e-9f);

    ASSERT_FLOAT_EQ(1.0f, c_agree, "C_agree = 1.0 (single group)");
}

/**
 * Test 8: Agreement - missing evidence (NAN)
 *
 * Python equivalent:
 *   groups = [
 *     {"group": "thermal", "evidence": 0.8, "weight": 1.0},
 *     {"group": "smoke", "evidence": None, "weight": 1.0}
 *   ]
 *   Only thermal valid → C_agree = 1.0 (single valid group)
 */
void test_agreement_missing_evidence(void)
{
    printf("\nTest 8: Agreement - missing evidence\n");

    evidence_group_t groups[2];
    strcpy(groups[0].group, "thermal");
    groups[0].evidence = 0.8f;
    groups[0].weight = 1.0f;

    strcpy(groups[1].group, "smoke");
    groups[1].evidence = NAN;  // Missing
    groups[1].weight = 1.0f;

    float c_agree = compute_agreement(groups, 2, 2.0f, 1e-9f);

    ASSERT_FLOAT_EQ(1.0f, c_agree, "C_agree = 1.0 (missing excluded)");
}

/**
 * Test 9: Agreement - zero mean
 *
 * Python equivalent:
 *   groups = [
 *     {"group": "thermal", "evidence": 0.0, "weight": 1.0},
 *     {"group": "smoke", "evidence": 0.0, "weight": 1.0}
 *   ]
 *   ē < epsilon → C_agree = 1.0
 */
void test_agreement_zero_mean(void)
{
    printf("\nTest 9: Agreement - zero mean\n");

    evidence_group_t groups[2];
    strcpy(groups[0].group, "thermal");
    groups[0].evidence = 0.0f;
    groups[0].weight = 1.0f;

    strcpy(groups[1].group, "smoke");
    groups[1].evidence = 0.0f;
    groups[1].weight = 1.0f;

    float c_agree = compute_agreement(groups, 2, 2.0f, 1e-9f);

    ASSERT_FLOAT_EQ(1.0f, c_agree, "C_agree = 1.0 (zero mean)");
}

/**
 * Test 10: Temporal - fresh data
 *
 * Python equivalent:
 *   telemetry_age = 10.0, max_age = 300.0
 *   C_temp = max(0, 1 - 10/300) = 0.9667
 */
void test_temporal_fresh(void)
{
    printf("\nTest 10: Temporal - fresh data\n");

    float c_temp = compute_temporal_confidence(10.0f, 300.0f);

    ASSERT_FLOAT_EQ(0.966667f, c_temp, "C_temp ≈ 0.9667 (fresh)");
}

/**
 * Test 11: Temporal - stale data
 *
 * Python equivalent:
 *   telemetry_age = 400.0, max_age = 300.0
 *   C_temp = max(0, 1 - 400/300) = 0.0
 */
void test_temporal_stale(void)
{
    printf("\nTest 11: Temporal - stale data\n");

    float c_temp = compute_temporal_confidence(400.0f, 300.0f);

    ASSERT_FLOAT_EQ(0.0f, c_temp, "C_temp = 0.0 (stale)");
}

/**
 * Test 12: Temporal - missing age
 *
 * Python equivalent:
 *   telemetry_age = None
 *   C_temp = 0.0
 */
void test_temporal_missing(void)
{
    printf("\nTest 12: Temporal - missing age\n");

    float c_temp = compute_temporal_confidence(NAN, 300.0f);

    ASSERT_FLOAT_EQ(0.0f, c_temp, "C_temp = 0.0 (missing)");
}

/**
 * Test 13: Temporal - invalid age (negative)
 *
 * Python equivalent:
 *   telemetry_age = -10.0
 *   C_temp = 0.0 (clock error)
 */
void test_temporal_invalid(void)
{
    printf("\nTest 13: Temporal - invalid age\n");

    float c_temp = compute_temporal_confidence(-10.0f, 300.0f);

    ASSERT_FLOAT_EQ(0.0f, c_temp, "C_temp = 0.0 (invalid)");
}

/**
 * Test 14: Baseline confidence - READY
 *
 * Python equivalent:
 *   baseline_state = "READY"
 *   C_base = 1.0
 */
void test_baseline_ready(void)
{
    printf("\nTest 14: Baseline confidence - READY\n");

    float c_base = compute_baseline_confidence(BASELINE_READY);

    ASSERT_FLOAT_EQ(1.0f, c_base, "C_base = 1.0 (READY)");
}

/**
 * Test 15: Baseline confidence - LEARNING
 *
 * Python equivalent:
 *   baseline_state = "LEARNING"
 *   C_base = 0.7
 */
void test_baseline_learning(void)
{
    printf("\nTest 15: Baseline confidence - LEARNING\n");

    float c_base = compute_baseline_confidence(BASELINE_LEARNING);

    ASSERT_FLOAT_EQ(0.7f, c_base, "C_base = 0.7 (LEARNING)");
}

/**
 * Test 16: Baseline confidence - INITIALIZING
 *
 * Python equivalent:
 *   baseline_state = "INITIALIZING"
 *   C_base = 0.3
 */
void test_baseline_initializing(void)
{
    printf("\nTest 16: Baseline confidence - INITIALIZING\n");

    float c_base = compute_baseline_confidence(BASELINE_INITIALIZING);

    ASSERT_FLOAT_EQ(0.3f, c_base, "C_base = 0.3 (INITIALIZING)");
}

/**
 * Test 17: Final confidence - nominal case
 *
 * Python equivalent:
 *   C_cov = 1.0, C_agree = 0.9, C_temp = 0.95, C_base = 1.0
 *   weights = {coverage: 0.3, agreement: 0.3, temporal: 0.2, baseline: 0.2}
 *   C_h = 0.3×1.0 + 0.3×0.9 + 0.2×0.95 + 0.2×1.0 = 0.96
 */
void test_confidence_nominal(void)
{
    printf("\nTest 17: Final confidence - nominal case\n");

    confidence_weights_t weights = confidence_default_weights();
    confidence_result_t result = compute_confidence(1.0f, 0.9f, 0.95f, 1.0f, &weights, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.96f, result.c_h, "C_h = 0.96");
}

/**
 * Test 18: Final confidence - degraded coverage
 *
 * Python equivalent:
 *   C_cov = 0.5, C_agree = 1.0, C_temp = 1.0, C_base = 1.0
 *   C_h = 0.3×0.5 + 0.3×1.0 + 0.2×1.0 + 0.2×1.0 = 0.85
 */
void test_confidence_degraded_coverage(void)
{
    printf("\nTest 18: Final confidence - degraded coverage\n");

    confidence_weights_t weights = confidence_default_weights();
    confidence_result_t result = compute_confidence(0.5f, 1.0f, 1.0f, 1.0f, &weights, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.85f, result.c_h, "C_h = 0.85");
}

/**
 * Test 19: Final confidence - invalid weight sum
 *
 * Python equivalent:
 *   weights sum ≠ 1.0 → returns None (invalid)
 */
void test_confidence_invalid_weights(void)
{
    printf("\nTest 19: Final confidence - invalid weight sum\n");

    confidence_weights_t weights = {
        .coverage = 0.4f,
        .agreement = 0.4f,
        .temporal = 0.3f,
        .baseline = 0.2f  // Sum = 1.3 ≠ 1.0
    };

    confidence_result_t result = compute_confidence(1.0f, 1.0f, 1.0f, 1.0f, &weights, 1e-9f);

    ASSERT_FALSE(result.valid, "Invalid weight sum");
}

/**
 * Test 20: Final confidence - component out of range
 *
 * Python equivalent:
 *   C_cov = 1.5 (out of [0, 1]) → returns None (invalid)
 */
void test_confidence_out_of_range(void)
{
    printf("\nTest 20: Final confidence - component out of range\n");

    confidence_weights_t weights = confidence_default_weights();
    confidence_result_t result = compute_confidence(1.5f, 1.0f, 1.0f, 1.0f, &weights, 1e-9f);

    ASSERT_FALSE(result.valid, "Component out of range");
}

/**
 * Test 21: Default weights
 *
 * Python equivalent:
 *   weights = confidence_default_weights()
 *   weights.coverage = 0.3, etc.
 */
void test_default_weights(void)
{
    printf("\nTest 21: Default weights\n");

    confidence_weights_t weights = confidence_default_weights();

    ASSERT_FLOAT_EQ(0.3f, weights.coverage, "coverage = 0.3");
    ASSERT_FLOAT_EQ(0.3f, weights.agreement, "agreement = 0.3");
    ASSERT_FLOAT_EQ(0.2f, weights.temporal, "temporal = 0.2");
    ASSERT_FLOAT_EQ(0.2f, weights.baseline, "baseline = 0.2");
}

/**
 * Test 22: Coverage - weighted availability
 *
 * Python equivalent:
 *   sensors = [
 *     {"sensor": "temp", "available": True, "weight": 0.8},
 *     {"sensor": "smoke", "available": False, "weight": 0.2}
 *   ]
 *   C_cov = 0.8 / 1.0 = 0.8
 */
void test_coverage_weighted(void)
{
    printf("\nTest 22: Coverage - weighted availability\n");

    sensor_availability_t sensors[2];
    strcpy(sensors[0].sensor, "temp");
    sensors[0].available = true;
    sensors[0].weight = 0.8f;

    strcpy(sensors[1].sensor, "smoke");
    sensors[1].available = false;
    sensors[1].weight = 0.2f;

    float c_cov = compute_coverage(sensors, 2, 1e-9f);

    ASSERT_FLOAT_EQ(0.8f, c_cov, "C_cov = 0.8 (weighted)");
}

/**
 * Test 23: Agreement - weighted groups
 *
 * Python equivalent:
 *   groups = [
 *     {"group": "thermal", "evidence": 0.8, "weight": 0.7},
 *     {"group": "smoke", "evidence": 0.6, "weight": 0.3}
 *   ]
 *   ē = (0.7×0.8 + 0.3×0.6) / 1.0 = 0.74
 *   V_e = (0.7×(0.8-0.74)² + 0.3×(0.6-0.74)²) / 1.0 = 0.0084
 *   C_agree = exp(-2.0 × 0.0084) ≈ 0.9833
 */
void test_agreement_weighted(void)
{
    printf("\nTest 23: Agreement - weighted groups\n");

    evidence_group_t groups[2];
    strcpy(groups[0].group, "thermal");
    groups[0].evidence = 0.8f;
    groups[0].weight = 0.7f;

    strcpy(groups[1].group, "smoke");
    groups[1].evidence = 0.6f;
    groups[1].weight = 0.3f;

    float c_agree = compute_agreement(groups, 2, 2.0f, 1e-9f);

    // Expected: exp(-2.0 × 0.0084) ≈ 0.983347
    ASSERT_FLOAT_EQ(0.983347f, c_agree, "C_agree ≈ 0.9833 (weighted)");
}

/**
 * Test 24: Temporal - exact boundary
 *
 * Python equivalent:
 *   telemetry_age = 300.0, max_age = 300.0
 *   C_temp = max(0, 1 - 300/300) = 0.0
 */
void test_temporal_boundary(void)
{
    printf("\nTest 24: Temporal - exact boundary\n");

    float c_temp = compute_temporal_confidence(300.0f, 300.0f);

    ASSERT_FLOAT_EQ(0.0f, c_temp, "C_temp = 0.0 (boundary)");
}

/**
 * Test 25: Baseline confidence - FROZEN
 *
 * Python equivalent:
 *   baseline_state = "FROZEN"
 *   C_base = 0.5
 */
void test_baseline_frozen(void)
{
    printf("\nTest 25: Baseline confidence - FROZEN\n");

    float c_base = compute_baseline_confidence(BASELINE_FROZEN);

    ASSERT_FLOAT_EQ(0.5f, c_base, "C_base = 0.5 (FROZEN)");
}

/**
 * Test 26: Baseline confidence - RECOVERING
 *
 * Python equivalent:
 *   baseline_state = "RECOVERING"
 *   C_base = 0.6
 */
void test_baseline_recovering(void)
{
    printf("\nTest 26: Baseline confidence - RECOVERING\n");

    float c_base = compute_baseline_confidence(BASELINE_RECOVERING);

    ASSERT_FLOAT_EQ(0.6f, c_base, "C_base = 0.6 (RECOVERING)");
}

/**
 * Test 27: Agreement - no groups
 *
 * Python equivalent:
 *   groups = []
 *   C_agree = 1.0 (no groups → no disagreement)
 */
void test_agreement_no_groups(void)
{
    printf("\nTest 27: Agreement - no groups\n");

    float c_agree = compute_agreement(NULL, 0, 2.0f, 1e-9f);

    ASSERT_FLOAT_EQ(1.0f, c_agree, "C_agree = 1.0 (no groups)");
}

/**
 * Test 28: Temporal - very fresh data
 *
 * Python equivalent:
 *   telemetry_age = 0.0, max_age = 300.0
 *   C_temp = max(0, 1 - 0/300) = 1.0
 */
void test_temporal_very_fresh(void)
{
    printf("\nTest 28: Temporal - very fresh data\n");

    float c_temp = compute_temporal_confidence(0.0f, 300.0f);

    ASSERT_FLOAT_EQ(1.0f, c_temp, "C_temp = 1.0 (very fresh)");
}

/**
 * Main test runner
 */
int main(void)
{
    printf("=== Confidence (C_h) Reference Parity Tests ===\n");
    printf("Reference: reference/python/nexalert_reference/confidence.py\n");

    // Coverage tests
    test_coverage_all_available();
    test_coverage_partial();
    test_coverage_none_available();
    test_coverage_no_sensors();
    test_coverage_weighted();

    // Agreement tests
    test_agreement_perfect();
    test_agreement_moderate();
    test_agreement_single_group();
    test_agreement_missing_evidence();
    test_agreement_zero_mean();
    test_agreement_weighted();
    test_agreement_no_groups();

    // Temporal tests
    test_temporal_fresh();
    test_temporal_stale();
    test_temporal_missing();
    test_temporal_invalid();
    test_temporal_boundary();
    test_temporal_very_fresh();

    // Baseline tests
    test_baseline_ready();
    test_baseline_learning();
    test_baseline_initializing();
    test_baseline_frozen();
    test_baseline_recovering();

    // Final confidence tests
    test_confidence_nominal();
    test_confidence_degraded_coverage();
    test_confidence_invalid_weights();
    test_confidence_out_of_range();
    test_default_weights();

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
