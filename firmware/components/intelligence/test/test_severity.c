/**
 * @file test_severity.c
 * @brief Reference parity tests for severity (S_h) calculation
 *
 * Tests embedded C implementation against Python reference:
 * reference/python/nexalert_reference/severity.py
 *
 * Validates:
 * - Fire intensity (I_h)
 * - Flood intensity (I_h)
 * - Temporal component (T_h)
 * - Duration component (D_h)
 * - Final severity with reweighting (S_h)
 */

#include "severity.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <stdbool.h>

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

#define ASSERT_NAN(value, message) do { \
    if (isnan(value)) { \
        tests_passed++; \
        printf("  ✓ %s\n", message); \
    } else { \
        tests_failed++; \
        printf("  ✗ %s: expected NAN, got %.6f\n", message, (value)); \
    } \
} while(0)

/**
 * Test 1: Fire intensity - both sensors nominal
 *
 * Python equivalent:
 *   compute_fire_intensity(70.0, 0.6) → 0.5
 *   temp: (70-40)/(100-40) = 0.5
 *   smoke: (0.6-0.2)/(0.8-0.2) = 0.667
 *   max(0.5, 0.667) = 0.667
 */
void test_fire_intensity_nominal(void)
{
    printf("\nTest 1: Fire intensity - both sensors nominal\n");

    float i_h = compute_fire_intensity(70.0f, 0.6f, NULL);

    // Expected: max((70-40)/(100-40), (0.6-0.2)/(0.8-0.2)) = max(0.5, 0.667) = 0.667
    ASSERT_FLOAT_EQ(0.666667f, i_h, "I_h ≈ 0.667");
}

/**
 * Test 2: Fire intensity - temperature only
 *
 * Python equivalent:
 *   compute_fire_intensity(70.0, None) → 0.5
 */
void test_fire_intensity_temp_only(void)
{
    printf("\nTest 2: Fire intensity - temperature only\n");

    float i_h = compute_fire_intensity(70.0f, NAN, NULL);

    ASSERT_FLOAT_EQ(0.5f, i_h, "I_h = 0.5 (temp only)");
}

/**
 * Test 3: Fire intensity - smoke only
 *
 * Python equivalent:
 *   compute_fire_intensity(None, 0.6) → 0.667
 */
void test_fire_intensity_smoke_only(void)
{
    printf("\nTest 3: Fire intensity - smoke only\n");

    float i_h = compute_fire_intensity(NAN, 0.6f, NULL);

    ASSERT_FLOAT_EQ(0.666667f, i_h, "I_h ≈ 0.667 (smoke only)");
}

/**
 * Test 4: Fire intensity - both missing
 *
 * Python equivalent:
 *   compute_fire_intensity(None, None) → None
 */
void test_fire_intensity_both_missing(void)
{
    printf("\nTest 4: Fire intensity - both missing\n");

    float i_h = compute_fire_intensity(NAN, NAN, NULL);

    ASSERT_NAN(i_h, "I_h = NAN (both missing)");
}

/**
 * Test 5: Fire intensity - below threshold
 *
 * Python equivalent:
 *   compute_fire_intensity(30.0, 0.1) → 0.0
 */
void test_fire_intensity_below_threshold(void)
{
    printf("\nTest 5: Fire intensity - below threshold\n");

    float i_h = compute_fire_intensity(30.0f, 0.1f, NULL);

    ASSERT_FLOAT_EQ(0.0f, i_h, "I_h = 0.0 (below threshold)");
}

/**
 * Test 6: Fire intensity - above threshold
 *
 * Python equivalent:
 *   compute_fire_intensity(120.0, 0.9) → 1.0
 */
void test_fire_intensity_above_threshold(void)
{
    printf("\nTest 6: Fire intensity - above threshold\n");

    float i_h = compute_fire_intensity(120.0f, 0.9f, NULL);

    ASSERT_FLOAT_EQ(1.0f, i_h, "I_h = 1.0 (above threshold)");
}

/**
 * Test 7: Flood intensity - both sensors nominal
 *
 * Python equivalent:
 *   compute_flood_intensity(1.5, 50.0) → 0.444
 *   water: (1.5-0.5)/(3.0-0.5) = 0.4
 *   rain: (50-10)/(100-10) = 0.444
 *   max(0.4, 0.444) = 0.444
 */
void test_flood_intensity_nominal(void)
{
    printf("\nTest 7: Flood intensity - both sensors nominal\n");

    float i_h = compute_flood_intensity(1.5f, 50.0f, NULL);

    ASSERT_FLOAT_EQ(0.444444f, i_h, "I_h ≈ 0.444");
}

/**
 * Test 8: Flood intensity - water only
 *
 * Python equivalent:
 *   compute_flood_intensity(2.0, None) → 0.6
 */
void test_flood_intensity_water_only(void)
{
    printf("\nTest 8: Flood intensity - water only\n");

    float i_h = compute_flood_intensity(2.0f, NAN, NULL);

    ASSERT_FLOAT_EQ(0.6f, i_h, "I_h = 0.6 (water only)");
}

/**
 * Test 9: Temporal - nominal rate
 *
 * Python equivalent:
 *   compute_temporal(70.0, 60.0, 60.0, 0.167) → 1.0
 *   rate = abs(70-60)/60 = 0.167
 *   T_h = min(0.167/0.167, 1.0) = 1.0
 */
void test_temporal_nominal(void)
{
    printf("\nTest 9: Temporal - nominal rate\n");

    float t_h = compute_temporal(70.0f, 60.0f, 60.0f, 0.167f, 0.0f);

    ASSERT_FLOAT_EQ(1.0f, t_h, "T_h = 1.0");
}

/**
 * Test 10: Temporal - slower rate
 *
 * Python equivalent:
 *   compute_temporal(65.0, 60.0, 120.0, 0.167) → 0.25
 *   rate = abs(65-60)/120 = 0.0417
 *   T_h = 0.0417/0.167 = 0.25
 */
void test_temporal_slower(void)
{
    printf("\nTest 10: Temporal - slower rate\n");

    float t_h = compute_temporal(65.0f, 60.0f, 120.0f, 0.167f, 0.0f);

    ASSERT_FLOAT_EQ(0.25f, t_h, "T_h = 0.25");
}

/**
 * Test 11: Temporal - missing current
 *
 * Python equivalent:
 *   compute_temporal(None, 60.0, 60.0, 0.167) → None
 */
void test_temporal_missing_current(void)
{
    printf("\nTest 11: Temporal - missing current\n");

    float t_h = compute_temporal(NAN, 60.0f, 60.0f, 0.167f, 0.0f);

    ASSERT_NAN(t_h, "T_h = NAN (current missing)");
}

/**
 * Test 12: Temporal - no time elapsed
 *
 * Python equivalent:
 *   compute_temporal(70.0, 60.0, 0.0, 0.167) → 0.0
 */
void test_temporal_no_time(void)
{
    printf("\nTest 12: Temporal - no time elapsed\n");

    float t_h = compute_temporal(70.0f, 60.0f, 0.0f, 0.167f, 0.0f);

    ASSERT_FLOAT_EQ(0.0f, t_h, "T_h = 0.0 (no time)");
}

/**
 * Test 13: Temporal - data stale
 *
 * Python equivalent:
 *   compute_temporal(70.0, 60.0, 400.0, 0.167, 300.0) → 0.0
 */
void test_temporal_stale(void)
{
    printf("\nTest 13: Temporal - data stale\n");

    float t_h = compute_temporal(70.0f, 60.0f, 400.0f, 0.167f, 300.0f);

    ASSERT_FLOAT_EQ(0.0f, t_h, "T_h = 0.0 (stale)");
}

/**
 * Test 14: Duration - nominal
 *
 * Python equivalent:
 *   compute_duration(1800.0, 3600.0) → 0.5
 */
void test_duration_nominal(void)
{
    printf("\nTest 14: Duration - nominal\n");

    float d_h = compute_duration(1800.0f, 3600.0f);

    ASSERT_FLOAT_EQ(0.5f, d_h, "D_h = 0.5");
}

/**
 * Test 15: Duration - exceeds max
 *
 * Python equivalent:
 *   compute_duration(5400.0, 3600.0) → 1.0
 */
void test_duration_exceeds_max(void)
{
    printf("\nTest 15: Duration - exceeds max\n");

    float d_h = compute_duration(5400.0f, 3600.0f);

    ASSERT_FLOAT_EQ(1.0f, d_h, "D_h = 1.0 (exceeds max)");
}

/**
 * Test 16: Duration - zero
 *
 * Python equivalent:
 *   compute_duration(0.0, 3600.0) → 0.0
 */
void test_duration_zero(void)
{
    printf("\nTest 16: Duration - zero\n");

    float d_h = compute_duration(0.0f, 3600.0f);

    ASSERT_FLOAT_EQ(0.0f, d_h, "D_h = 0.0");
}

/**
 * Test 17: Duration - missing
 *
 * Python equivalent:
 *   compute_duration(None, 3600.0) → None
 */
void test_duration_missing(void)
{
    printf("\nTest 17: Duration - missing\n");

    float d_h = compute_duration(NAN, 3600.0f);

    ASSERT_NAN(d_h, "D_h = NAN (missing)");
}

/**
 * Test 18: Severity - all components available
 *
 * Python equivalent:
 *   compute_severity(0.8, 0.5, 0.3) → 0.59
 *   S_h = 0.5×0.8 + 0.3×0.5 + 0.2×0.3 = 0.61
 */
void test_severity_all_available(void)
{
    printf("\nTest 18: Severity - all components available\n");

    severity_result_t result = compute_severity(0.8f, 0.5f, 0.3f, NULL, SEVERITY_EPSILON);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.61f, result.s_h, "S_h = 0.61");
}

/**
 * Test 19: Severity - temporal missing (reweighting)
 *
 * Python equivalent:
 *   compute_severity(0.8, None, 0.3) → 0.643
 *   Reweight: (0.5×0.8 + 0.2×0.3) / (0.5+0.2) = 0.657
 */
void test_severity_temporal_missing(void)
{
    printf("\nTest 19: Severity - temporal missing (reweighting)\n");

    severity_result_t result = compute_severity(0.8f, NAN, 0.3f, NULL, SEVERITY_EPSILON);

    ASSERT_TRUE(result.valid, "Computation valid");
    // Expected: (0.5×0.8 + 0.2×0.3) / 0.7 = 0.657143
    ASSERT_FLOAT_EQ(0.657143f, result.s_h, "S_h ≈ 0.657 (reweighted)");
}

/**
 * Test 20: Severity - all missing
 *
 * Python equivalent:
 *   compute_severity(None, None, None) → None
 */
void test_severity_all_missing(void)
{
    printf("\nTest 20: Severity - all missing\n");

    severity_result_t result = compute_severity(NAN, NAN, NAN, NULL, SEVERITY_EPSILON);

    ASSERT_FALSE(result.valid, "All missing invalid");
}

/**
 * Test 21: Validate weights - valid
 *
 * Python equivalent:
 *   validate_severity_weights({'w_I': 0.5, 'w_T': 0.3, 'w_D': 0.2}) → True
 */
void test_validate_weights_valid(void)
{
    printf("\nTest 21: Validate weights - valid\n");

    severity_weights_t weights = severity_default_weights();
    bool valid = validate_severity_weights(&weights, SEVERITY_EPSILON);

    ASSERT_TRUE(valid, "Default weights valid");
}

/**
 * Test 22: Validate weights - invalid sum
 *
 * Python equivalent:
 *   validate_severity_weights({'w_I': 0.6, 'w_T': 0.3, 'w_D': 0.2}) → False
 */
void test_validate_weights_invalid_sum(void)
{
    printf("\nTest 22: Validate weights - invalid sum\n");

    severity_weights_t weights = {
        .w_I = 0.6f,
        .w_T = 0.3f,
        .w_D = 0.2f  // Sum = 1.1
    };
    bool valid = validate_severity_weights(&weights, SEVERITY_EPSILON);

    ASSERT_FALSE(valid, "Invalid sum rejected");
}

/**
 * Test 23: Validate weights - negative weight
 *
 * Python equivalent:
 *   validate_severity_weights({'w_I': -0.1, 'w_T': 0.6, 'w_D': 0.5}) → False
 */
void test_validate_weights_negative(void)
{
    printf("\nTest 23: Validate weights - negative weight\n");

    severity_weights_t weights = {
        .w_I = -0.1f,
        .w_T = 0.6f,
        .w_D = 0.5f
    };
    bool valid = validate_severity_weights(&weights, SEVERITY_EPSILON);

    ASSERT_FALSE(valid, "Negative weight rejected");
}

/**
 * Test 24: Default weights
 */
void test_default_weights(void)
{
    printf("\nTest 24: Default weights\n");

    severity_weights_t weights = severity_default_weights();

    ASSERT_FLOAT_EQ(0.5f, weights.w_I, "w_I = 0.5");
    ASSERT_FLOAT_EQ(0.3f, weights.w_T, "w_T = 0.3");
    ASSERT_FLOAT_EQ(0.2f, weights.w_D, "w_D = 0.2");
}

/**
 * Test 25: Severity - intensity only
 *
 * Python equivalent:
 *   compute_severity(0.8, None, None) → 0.8
 */
void test_severity_intensity_only(void)
{
    printf("\nTest 25: Severity - intensity only\n");

    severity_result_t result = compute_severity(0.8f, NAN, NAN, NULL, SEVERITY_EPSILON);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.8f, result.s_h, "S_h = 0.8 (intensity only)");
}

/**
 * Main test runner
 */
int main(void)
{
    printf("=== Severity (S_h) Reference Parity Tests ===\n");
    printf("Reference: reference/python/nexalert_reference/severity.py\n");

    // Fire intensity tests
    test_fire_intensity_nominal();
    test_fire_intensity_temp_only();
    test_fire_intensity_smoke_only();
    test_fire_intensity_both_missing();
    test_fire_intensity_below_threshold();
    test_fire_intensity_above_threshold();

    // Flood intensity tests
    test_flood_intensity_nominal();
    test_flood_intensity_water_only();

    // Temporal tests
    test_temporal_nominal();
    test_temporal_slower();
    test_temporal_missing_current();
    test_temporal_no_time();
    test_temporal_stale();

    // Duration tests
    test_duration_nominal();
    test_duration_exceeds_max();
    test_duration_zero();
    test_duration_missing();

    // Severity tests
    test_severity_all_available();
    test_severity_temporal_missing();
    test_severity_all_missing();
    test_severity_intensity_only();

    // Weight validation tests
    test_validate_weights_valid();
    test_validate_weights_invalid_sum();
    test_validate_weights_negative();
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
