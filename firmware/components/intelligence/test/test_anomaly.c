/**
 * @file test_anomaly.c
 * @brief Reference parity tests for anomaly (A_i, A_node, A_h) calculation
 *
 * Tests embedded C implementation against Python reference:
 * reference/python/nexalert_reference/anomaly.py
 *
 * Validates:
 * - Individual anomaly computation (A_i)
 * - Node aggregate anomaly (A_node)
 * - Hazard-specific anomaly (A_h)
 * - Missing value handling
 * - Edge cases and boundary conditions
 */

#include "anomaly.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <stdbool.h>

// Test tolerance (float32 precision)
#define TEST_EPSILON 1e-3f  // Relaxed for exp() approximations

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
 * Test 1: Zero z-score (Python reference case)
 *
 * Python equivalent:
 *   A_i = compute_individual_anomaly(0.0, lambda_param=2.0, z_cap=5.0)
 *   A_i ≈ 0.0 (no anomaly)
 */
void test_zero_z_score(void)
{
    printf("\nTest 1: Zero z-score (no anomaly)\n");

    individual_anomaly_result_t result = compute_individual_anomaly(0.0f, 2.0f, 5.0f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.0f, result.a_i, "A_i ≈ 0.0");
}

/**
 * Test 2: Moderate anomaly (Python reference case)
 *
 * Python equivalent:
 *   A_i = compute_individual_anomaly(2.0, lambda_param=2.0, z_cap=5.0)
 *   A_i = 1 - exp(-2.0 / 2.0) = 1 - exp(-1.0) ≈ 0.632
 */
void test_moderate_anomaly(void)
{
    printf("\nTest 2: Moderate anomaly\n");

    individual_anomaly_result_t result = compute_individual_anomaly(2.0f, 2.0f, 5.0f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.632121f, result.a_i, "A_i ≈ 0.632");
}

/**
 * Test 3: High anomaly (z-score capped) (Python reference case)
 *
 * Python equivalent:
 *   A_i = compute_individual_anomaly(10.0, lambda_param=2.0, z_cap=5.0)
 *   z_score = 10.0 > z_cap = 5.0, clamped to 5.0
 *   A_i = 1 - exp(-5.0 / 2.0) ≈ 0.917915
 */
void test_high_anomaly(void)
{
    printf("\nTest 3: High anomaly (z-score capped)\n");

    individual_anomaly_result_t result = compute_individual_anomaly(10.0f, 2.0f, 5.0f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.917915f, result.a_i, "A_i ≈ 0.918 (capped)");
}

/**
 * Test 4: Missing z-score (Python reference case)
 *
 * Python equivalent:
 *   A_i = compute_individual_anomaly(None, lambda_param=2.0, z_cap=5.0)
 *   Returns None (preserve missing != zero)
 */
void test_missing_z_score(void)
{
    printf("\nTest 4: Missing z-score\n");

    individual_anomaly_result_t result = compute_individual_anomaly(NAN, 2.0f, 5.0f);

    ASSERT_FALSE(result.valid, "Missing z-score invalid");
}

/**
 * Test 5: Negative z-score (symmetry) (Python reference case)
 *
 * Python equivalent:
 *   A_i(2.0) == A_i(-2.0) (absolute value)
 */
void test_negative_z_score(void)
{
    printf("\nTest 5: Negative z-score (symmetry)\n");

    individual_anomaly_result_t result_pos = compute_individual_anomaly(2.0f, 2.0f, 5.0f);
    individual_anomaly_result_t result_neg = compute_individual_anomaly(-2.0f, 2.0f, 5.0f);

    ASSERT_TRUE(result_pos.valid && result_neg.valid, "Both computations valid");
    ASSERT_FLOAT_EQ(result_pos.a_i, result_neg.a_i, "A_i(-z) = A_i(z)");
}

/**
 * Test 6: Boundary at z_cap (Python reference case)
 *
 * Python equivalent:
 *   A_i = compute_individual_anomaly(5.0, lambda_param=2.0, z_cap=5.0)
 *   Should equal high_anomaly test (z = z_cap)
 */
void test_boundary_at_z_cap(void)
{
    printf("\nTest 6: Boundary at z_cap\n");

    individual_anomaly_result_t result = compute_individual_anomaly(5.0f, 2.0f, 5.0f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.917915f, result.a_i, "A_i at z_cap ≈ 0.918");
}

/**
 * Test 7: Invalid lambda_param (Python reference case)
 *
 * Python equivalent:
 *   compute_individual_anomaly(2.0, lambda_param=0.0, z_cap=5.0)
 *   Raises ValueError
 */
void test_invalid_lambda_param(void)
{
    printf("\nTest 7: Invalid lambda_param\n");

    individual_anomaly_result_t result1 = compute_individual_anomaly(2.0f, 0.0f, 5.0f);
    ASSERT_FALSE(result1.valid, "lambda_param = 0 invalid");

    individual_anomaly_result_t result2 = compute_individual_anomaly(2.0f, -1.0f, 5.0f);
    ASSERT_FALSE(result2.valid, "lambda_param < 0 invalid");
}

/**
 * Test 8: Invalid z_cap (Python reference case)
 *
 * Python equivalent:
 *   compute_individual_anomaly(2.0, lambda_param=2.0, z_cap=0.0)
 *   Raises ValueError
 */
void test_invalid_z_cap(void)
{
    printf("\nTest 8: Invalid z_cap\n");

    individual_anomaly_result_t result1 = compute_individual_anomaly(2.0f, 2.0f, 0.0f);
    ASSERT_FALSE(result1.valid, "z_cap = 0 invalid");

    individual_anomaly_result_t result2 = compute_individual_anomaly(2.0f, 2.0f, -1.0f);
    ASSERT_FALSE(result2.valid, "z_cap < 0 invalid");
}

/**
 * Test 9: Asymptotic behavior (Python reference case)
 *
 * Python equivalent:
 *   A_i(5.0) == A_i(10.0) (both capped at z_cap=5.0)
 *   A_i > 0.9 (approaches 1.0)
 */
void test_asymptotic_behavior(void)
{
    printf("\nTest 9: Asymptotic behavior (approaches 1.0)\n");

    individual_anomaly_result_t result_5 = compute_individual_anomaly(5.0f, 2.0f, 5.0f);
    individual_anomaly_result_t result_10 = compute_individual_anomaly(10.0f, 2.0f, 5.0f);

    ASSERT_TRUE(result_5.valid && result_10.valid, "Both computations valid");
    ASSERT_FLOAT_EQ(result_5.a_i, result_10.a_i, "A_i(5) = A_i(10) (both capped)");
    ASSERT_TRUE(result_5.a_i > 0.9f, "A_i > 0.9 (close to 1.0)");
}

/**
 * Test 10: Node aggregate weighted average (Python reference case)
 *
 * Python equivalent:
 *   anomalies = {"temp": 0.8, "smoke": 0.6}
 *   reliabilities = {"temp": 0.9, "smoke": 0.7}
 *   A_node = (0.9*0.8 + 0.7*0.6) / (0.9 + 0.7) = 1.14 / 1.6 = 0.7125
 */
void test_node_weighted_average(void)
{
    printf("\nTest 10: Node aggregate weighted average\n");

    sensor_anomaly_t sensors[] = {
        {.a_i = 0.8f, .r_i = 0.9f, .w_ih = NAN},
        {.a_i = 0.6f, .r_i = 0.7f, .w_ih = NAN}
    };

    node_anomaly_result_t result = compute_node_aggregate_anomaly(sensors, 2, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.7125f, result.a_node, "A_node = 0.7125");
}

/**
 * Test 11: Node missing anomaly (Python reference case)
 *
 * Python equivalent:
 *   anomalies = {"temp": 0.8, "smoke": None}
 *   reliabilities = {"temp": 0.9, "smoke": 0.7}
 *   A_node = 0.9 * 0.8 / 0.9 = 0.8
 */
void test_node_missing_anomaly(void)
{
    printf("\nTest 11: Node missing anomaly\n");

    sensor_anomaly_t sensors[] = {
        {.a_i = 0.8f, .r_i = 0.9f, .w_ih = NAN},
        {.a_i = NAN, .r_i = 0.7f, .w_ih = NAN}  // Missing A_i
    };

    node_anomaly_result_t result = compute_node_aggregate_anomaly(sensors, 2, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.8f, result.a_node, "A_node = 0.8 (only temp contributes)");
}

/**
 * Test 12: Node missing reliability (Python reference case)
 *
 * Python equivalent:
 *   anomalies = {"temp": 0.8, "smoke": 0.6}
 *   reliabilities = {"temp": 0.9, "smoke": None}
 *   A_node = 0.9 * 0.8 / 0.9 = 0.8
 */
void test_node_missing_reliability(void)
{
    printf("\nTest 12: Node missing reliability\n");

    sensor_anomaly_t sensors[] = {
        {.a_i = 0.8f, .r_i = 0.9f, .w_ih = NAN},
        {.a_i = 0.6f, .r_i = NAN, .w_ih = NAN}  // Missing R_i
    };

    node_anomaly_result_t result = compute_node_aggregate_anomaly(sensors, 2, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.8f, result.a_node, "A_node = 0.8 (only temp contributes)");
}

/**
 * Test 13: Node all missing (Python reference case)
 *
 * Python equivalent:
 *   anomalies = {"temp": None, "smoke": None}
 *   Returns None
 */
void test_node_all_missing(void)
{
    printf("\nTest 13: Node all missing\n");

    sensor_anomaly_t sensors[] = {
        {.a_i = NAN, .r_i = 0.9f, .w_ih = NAN},
        {.a_i = NAN, .r_i = 0.7f, .w_ih = NAN}
    };

    node_anomaly_result_t result = compute_node_aggregate_anomaly(sensors, 2, 1e-9f);

    ASSERT_FALSE(result.valid, "All missing invalid");
}

/**
 * Test 14: Node empty array (Python reference case)
 *
 * Python equivalent:
 *   compute_node_aggregate_anomaly({}, {})
 *   Returns None
 */
void test_node_empty_array(void)
{
    printf("\nTest 14: Node empty array\n");

    node_anomaly_result_t result = compute_node_aggregate_anomaly(NULL, 0, 1e-9f);

    ASSERT_FALSE(result.valid, "Empty array invalid");
}

/**
 * Test 15: Node zero denominator (Python reference case)
 *
 * Python equivalent:
 *   anomalies = {"temp": 0.8}
 *   reliabilities = {"temp": 1e-10}  # Much smaller than epsilon
 *   Returns None (weight_sum < epsilon)
 */
void test_node_zero_denominator(void)
{
    printf("\nTest 15: Node zero denominator\n");

    sensor_anomaly_t sensors[] = {
        {.a_i = 0.8f, .r_i = 1e-10f, .w_ih = NAN}
    };

    node_anomaly_result_t result = compute_node_aggregate_anomaly(sensors, 1, 1e-9f);

    ASSERT_FALSE(result.valid, "Zero denominator invalid");
}

/**
 * Test 16: Node partial missing (Python reference case)
 *
 * Python equivalent:
 *   anomalies = {"temp": 0.8, "smoke": None, "pm25": 0.7}
 *   reliabilities = {"temp": 0.9, "smoke": 0.7, "pm25": 0.8}
 *   A_node = (0.9*0.8 + 0.8*0.7) / (0.9 + 0.8) = 1.28 / 1.7 ≈ 0.7529
 */
void test_node_partial_missing(void)
{
    printf("\nTest 16: Node partial missing\n");

    sensor_anomaly_t sensors[] = {
        {.a_i = 0.8f, .r_i = 0.9f, .w_ih = NAN},
        {.a_i = NAN, .r_i = 0.7f, .w_ih = NAN},  // Missing
        {.a_i = 0.7f, .r_i = 0.8f, .w_ih = NAN}
    };

    node_anomaly_result_t result = compute_node_aggregate_anomaly(sensors, 3, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.7529f, result.a_node, "A_node ≈ 0.753");
}

/**
 * Test 17: Hazard weighted (Python reference case)
 *
 * Python equivalent:
 *   anomalies = {"temp": 0.8, "smoke": 0.6}
 *   reliabilities = {"temp": 0.9, "smoke": 0.7}
 *   weights = {"temp": 0.5, "smoke": 0.3}
 *   A_h = (0.5*0.9*0.8 + 0.3*0.7*0.6) / (0.5*0.9 + 0.3*0.7)
 *       = 0.486 / 0.66 ≈ 0.7364
 */
void test_hazard_weighted(void)
{
    printf("\nTest 17: Hazard-specific weighting\n");

    sensor_anomaly_t sensors[] = {
        {.a_i = 0.8f, .r_i = 0.9f, .w_ih = 0.5f},
        {.a_i = 0.6f, .r_i = 0.7f, .w_ih = 0.3f}
    };

    hazard_anomaly_result_t result = compute_hazard_specific_anomaly(sensors, 2, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.7364f, result.a_h, "A_h ≈ 0.736");
}

/**
 * Test 18: Hazard missing anomaly (Python reference case)
 *
 * Python equivalent:
 *   anomalies = {"temp": 0.8, "smoke": None}
 *   reliabilities = {"temp": 0.9, "smoke": 0.7}
 *   weights = {"temp": 0.5, "smoke": 0.3}
 *   A_h = 0.5*0.9*0.8 / (0.5*0.9) = 0.8
 */
void test_hazard_missing_anomaly(void)
{
    printf("\nTest 18: Hazard missing anomaly\n");

    sensor_anomaly_t sensors[] = {
        {.a_i = 0.8f, .r_i = 0.9f, .w_ih = 0.5f},
        {.a_i = NAN, .r_i = 0.7f, .w_ih = 0.3f}  // Missing A_i
    };

    hazard_anomaly_result_t result = compute_hazard_specific_anomaly(sensors, 2, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.8f, result.a_h, "A_h = 0.8 (only temp contributes)");
}

/**
 * Test 19: Hazard sensor not in weights (Python reference case)
 *
 * Python equivalent:
 *   anomalies = {"temp": 0.8, "humidity": 0.5}
 *   reliabilities = {"temp": 0.9, "humidity": 0.8}
 *   weights = {"temp": 0.5}  # No weight for humidity
 *   A_h = 0.8 (only temp contributes)
 */
void test_hazard_sensor_not_in_weights(void)
{
    printf("\nTest 19: Hazard sensor not in weights\n");

    sensor_anomaly_t sensors[] = {
        {.a_i = 0.8f, .r_i = 0.9f, .w_ih = 0.5f},
        {.a_i = 0.5f, .r_i = 0.8f, .w_ih = NAN}  // No weight (NAN)
    };

    hazard_anomaly_result_t result = compute_hazard_specific_anomaly(sensors, 2, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.8f, result.a_h, "A_h = 0.8 (humidity excluded)");
}

/**
 * Test 20: Hazard empty weights (Python reference case)
 *
 * Python equivalent:
 *   weights = {}
 *   Returns None
 */
void test_hazard_empty_weights(void)
{
    printf("\nTest 20: Hazard empty weights\n");

    sensor_anomaly_t sensors[] = {
        {.a_i = 0.8f, .r_i = 0.9f, .w_ih = NAN}  // No weights
    };

    hazard_anomaly_result_t result = compute_hazard_specific_anomaly(sensors, 1, 1e-9f);

    ASSERT_FALSE(result.valid, "Empty weights invalid");
}

/**
 * Test 21: Hazard all missing (Python reference case)
 *
 * Python equivalent:
 *   anomalies = {"temp": None, "smoke": None}
 *   Returns None
 */
void test_hazard_all_missing(void)
{
    printf("\nTest 21: Hazard all missing\n");

    sensor_anomaly_t sensors[] = {
        {.a_i = NAN, .r_i = 0.9f, .w_ih = 0.5f},
        {.a_i = NAN, .r_i = 0.7f, .w_ih = 0.3f}
    };

    hazard_anomaly_result_t result = compute_hazard_specific_anomaly(sensors, 2, 1e-9f);

    ASSERT_FALSE(result.valid, "All missing invalid");
}

/**
 * Test 22: Hazard zero denominator (Python reference case)
 *
 * Python equivalent:
 *   anomalies = {"temp": 0.8}
 *   reliabilities = {"temp": 1e-10}
 *   weights = {"temp": 1e-10}
 *   Returns None (weight_sum < epsilon)
 */
void test_hazard_zero_denominator(void)
{
    printf("\nTest 22: Hazard zero denominator\n");

    sensor_anomaly_t sensors[] = {
        {.a_i = 0.8f, .r_i = 1e-10f, .w_ih = 1e-10f}
    };

    hazard_anomaly_result_t result = compute_hazard_specific_anomaly(sensors, 1, 1e-9f);

    ASSERT_FALSE(result.valid, "Zero denominator invalid");
}

/**
 * Main test runner
 */
int main(void)
{
    printf("=== Anomaly (A_i, A_node, A_h) Reference Parity Tests ===\n");
    printf("Reference: reference/python/nexalert_reference/anomaly.py\n");

    // Individual anomaly tests
    test_zero_z_score();
    test_moderate_anomaly();
    test_high_anomaly();
    test_missing_z_score();
    test_negative_z_score();
    test_boundary_at_z_cap();
    test_invalid_lambda_param();
    test_invalid_z_cap();
    test_asymptotic_behavior();

    // Node aggregate tests
    test_node_weighted_average();
    test_node_missing_anomaly();
    test_node_missing_reliability();
    test_node_all_missing();
    test_node_empty_array();
    test_node_zero_denominator();
    test_node_partial_missing();

    // Hazard-specific tests
    test_hazard_weighted();
    test_hazard_missing_anomaly();
    test_hazard_sensor_not_in_weights();
    test_hazard_empty_weights();
    test_hazard_all_missing();
    test_hazard_zero_denominator();

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
