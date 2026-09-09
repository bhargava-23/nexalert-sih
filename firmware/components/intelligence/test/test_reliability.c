/**
 * @file test_reliability.c
 * @brief Reference parity tests for R_i (evidence reliability) calculation
 *
 * Tests embedded C implementation against Python reference:
 * reference/python/nexalert_reference/reliability.py
 *
 * Validates:
 * - Multiplicative trust gate R_i = H_i × Q_i × K_i
 * - Missing component handling (preserves missing != zero)
 * - Component range validation [0, 1]
 * - Zero component behavior (strict trust gate)
 * - K_i explicit input (no hardcoded default)
 */

#include "reliability.h"
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

/**
 * Test 1: Basic multiplicative trust gate (Python reference case)
 *
 * Python equivalent:
 *   h_i = 0.9
 *   q_i = 0.8
 *   k_i = 1.0
 *   R_i = 0.9 * 0.8 * 1.0 = 0.72
 */
void test_basic_multiplication(void)
{
    printf("\nTest 1: Basic multiplicative trust gate\n");

    reliability_result_t result = compute_reliability(0.9f, 0.8f, 1.0f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.72f, result.r_i, "R_i = 0.72");
}

/**
 * Test 2: Missing H_i (Python reference case)
 *
 * Python equivalent:
 *   h_i = None
 *   q_i = 0.8
 *   k_i = 1.0
 *   Returns None (preserves missing != zero)
 */
void test_missing_health(void)
{
    printf("\nTest 2: Missing H_i\n");

    reliability_result_t result = compute_reliability(NAN, 0.8f, 1.0f);

    ASSERT_FALSE(result.valid, "Computation invalid (missing H_i)");
}

/**
 * Test 3: Missing Q_i (Python reference case)
 *
 * Python equivalent:
 *   h_i = 0.9
 *   q_i = None
 *   k_i = 1.0
 *   Returns None
 */
void test_missing_quality(void)
{
    printf("\nTest 3: Missing Q_i\n");

    reliability_result_t result = compute_reliability(0.9f, NAN, 1.0f);

    ASSERT_FALSE(result.valid, "Computation invalid (missing Q_i)");
}

/**
 * Test 4: Missing K_i (Python reference case)
 *
 * Python equivalent:
 *   h_i = 0.9
 *   q_i = 0.8
 *   k_i = None
 *   Returns None (NO default K_i per Doc 04 Sec 3.3)
 */
void test_missing_calibration(void)
{
    printf("\nTest 4: Missing K_i (no hardcoded default)\n");

    reliability_result_t result = compute_reliability(0.9f, 0.8f, NAN);

    ASSERT_FALSE(result.valid, "Computation invalid (missing K_i, no default)");
}

/**
 * Test 5: All components missing (Python reference case)
 *
 * Python equivalent:
 *   All None → Returns None
 */
void test_all_missing(void)
{
    printf("\nTest 5: All components missing\n");

    reliability_result_t result = compute_reliability(NAN, NAN, NAN);

    ASSERT_FALSE(result.valid, "Computation invalid (all missing)");
}

/**
 * Test 6: Zero H_i (Python reference case)
 *
 * Python equivalent:
 *   h_i = 0.0
 *   q_i = 0.8
 *   k_i = 1.0
 *   R_i = 0.0 (strict trust gate)
 */
void test_zero_health(void)
{
    printf("\nTest 6: Zero H_i (strict trust gate)\n");

    reliability_result_t result = compute_reliability(0.0f, 0.8f, 1.0f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.0f, result.r_i, "R_i = 0.0 (zero health)");
}

/**
 * Test 7: Zero Q_i (Python reference case)
 *
 * Python equivalent:
 *   h_i = 0.9
 *   q_i = 0.0
 *   k_i = 1.0
 *   R_i = 0.0 (strict trust gate)
 */
void test_zero_quality(void)
{
    printf("\nTest 7: Zero Q_i (strict trust gate)\n");

    reliability_result_t result = compute_reliability(0.9f, 0.0f, 1.0f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.0f, result.r_i, "R_i = 0.0 (zero quality)");
}

/**
 * Test 8: Zero K_i (Python reference case)
 *
 * Python equivalent:
 *   h_i = 0.9
 *   q_i = 0.8
 *   k_i = 0.0
 *   R_i = 0.0 (strict trust gate, invalid calibration)
 */
void test_zero_calibration(void)
{
    printf("\nTest 8: Zero K_i (strict trust gate)\n");

    reliability_result_t result = compute_reliability(0.9f, 0.8f, 0.0f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.0f, result.r_i, "R_i = 0.0 (zero calibration)");
}

/**
 * Test 9: All components zero (Python reference case)
 *
 * Python equivalent:
 *   All 0.0 → R_i = 0.0
 */
void test_all_zero(void)
{
    printf("\nTest 9: All components zero\n");

    reliability_result_t result = compute_reliability(0.0f, 0.0f, 0.0f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.0f, result.r_i, "R_i = 0.0 (all zero)");
}

/**
 * Test 10: Perfect reliability (Python reference case)
 *
 * Python equivalent:
 *   h_i = 1.0
 *   q_i = 1.0
 *   k_i = 1.0
 *   R_i = 1.0 (perfect reliability)
 */
void test_perfect_reliability(void)
{
    printf("\nTest 10: Perfect reliability\n");

    reliability_result_t result = compute_reliability(1.0f, 1.0f, 1.0f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(1.0f, result.r_i, "R_i = 1.0 (perfect)");
}

/**
 * Test 11: H_i out of range (Python reference case)
 *
 * Python equivalent:
 *   h_i = 1.2  # out of [0,1]
 *   Raises ValueError per Doc 04 Sec 3.3
 */
void test_health_out_of_range(void)
{
    printf("\nTest 11: H_i out of range\n");

    reliability_result_t result = compute_reliability(1.2f, 0.8f, 1.0f);

    ASSERT_FALSE(result.valid, "Computation invalid (H_i > 1.0)");
}

/**
 * Test 12: Q_i out of range (Python reference case)
 *
 * Python equivalent:
 *   q_i = -0.1  # out of [0,1]
 *   Raises ValueError per Doc 04 Sec 3.3
 */
void test_quality_out_of_range(void)
{
    printf("\nTest 12: Q_i out of range\n");

    reliability_result_t result = compute_reliability(0.9f, -0.1f, 1.0f);

    ASSERT_FALSE(result.valid, "Computation invalid (Q_i < 0.0)");
}

/**
 * Test 13: K_i out of range (Python reference case)
 *
 * Python equivalent:
 *   k_i = 1.5  # out of [0,1]
 *   Raises ValueError per Doc 04 Sec 3.3
 */
void test_calibration_out_of_range(void)
{
    printf("\nTest 13: K_i out of range\n");

    reliability_result_t result = compute_reliability(0.9f, 0.8f, 1.5f);

    ASSERT_FALSE(result.valid, "Computation invalid (K_i > 1.0)");
}

/**
 * Test 14: Partial calibration (Python reference case)
 *
 * Python equivalent:
 *   h_i = 0.95
 *   q_i = 0.9
 *   k_i = 0.5  # Partially calibrated sensor
 *   R_i = 0.95 * 0.9 * 0.5 = 0.4275
 */
void test_partial_calibration(void)
{
    printf("\nTest 14: Partial calibration (K_i = 0.5)\n");

    reliability_result_t result = compute_reliability(0.95f, 0.9f, 0.5f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.4275f, result.r_i, "R_i = 0.4275");
}

/**
 * Test 15: Low reliability propagation (Python reference case)
 *
 * Python equivalent:
 *   h_i = 0.3
 *   q_i = 0.4
 *   k_i = 0.5
 *   R_i = 0.3 * 0.4 * 0.5 = 0.06 (very low reliability)
 */
void test_low_reliability_propagation(void)
{
    printf("\nTest 15: Low reliability propagation\n");

    reliability_result_t result = compute_reliability(0.3f, 0.4f, 0.5f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.06f, result.r_i, "R_i = 0.06 (low reliability)");
}

/**
 * Main test runner
 */
int main(void)
{
    printf("=== R_i (Evidence Reliability) Reference Parity Tests ===\n");
    printf("Reference: reference/python/nexalert_reference/reliability.py\n");

    test_basic_multiplication();
    test_missing_health();
    test_missing_quality();
    test_missing_calibration();
    test_all_missing();
    test_zero_health();
    test_zero_quality();
    test_zero_calibration();
    test_all_zero();
    test_perfect_reliability();
    test_health_out_of_range();
    test_quality_out_of_range();
    test_calibration_out_of_range();
    test_partial_calibration();
    test_low_reliability_propagation();

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
