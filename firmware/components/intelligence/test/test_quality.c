/**
 * @file test_quality.c
 * @brief Reference parity tests for Q_i (signal quality) calculation
 *
 * Tests embedded C implementation against Python reference:
 * reference/python/nexalert_reference/quality.py
 *
 * Validates:
 * - Multiplicative combination Q_i = q_integrity × q_stability
 * - Missing component handling (preserves missing != zero)
 * - Component range validation [0, 1]
 * - Perfect quality (both = 1.0)
 * - Zero quality (either = 0.0)
 */

#include "quality.h"
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
 * Assert helper
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
 * Test 1: Basic multiplicative combination (Python reference case)
 *
 * Python equivalent:
 *   q_integrity = 0.9
 *   q_stability = 0.8
 *   Q_i = 0.9 * 0.8 = 0.72
 */
void test_basic_multiplication(void)
{
    printf("\nTest 1: Basic multiplicative combination\n");

    quality_result_t result = compute_quality(0.9f, 0.8f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.72f, result.q_i, "Q_i = 0.72");
}

/**
 * Test 2: Missing q_integrity (Python reference case)
 *
 * Python equivalent:
 *   q_integrity = None
 *   q_stability = 0.8
 *   Returns None (preserves missing != zero)
 */
void test_missing_integrity(void)
{
    printf("\nTest 2: Missing q_integrity\n");

    quality_result_t result = compute_quality(NAN, 0.8f);

    ASSERT_FALSE(result.valid, "Computation invalid (missing q_integrity)");
}

/**
 * Test 3: Missing q_stability (Python reference case)
 *
 * Python equivalent:
 *   q_integrity = 0.9
 *   q_stability = None
 *   Returns None (preserves missing != zero)
 */
void test_missing_stability(void)
{
    printf("\nTest 3: Missing q_stability\n");

    quality_result_t result = compute_quality(0.9f, NAN);

    ASSERT_FALSE(result.valid, "Computation invalid (missing q_stability)");
}

/**
 * Test 4: Both components missing (Python reference case)
 *
 * Python equivalent:
 *   q_integrity = None
 *   q_stability = None
 *   Returns None
 */
void test_both_missing(void)
{
    printf("\nTest 4: Both components missing\n");

    quality_result_t result = compute_quality(NAN, NAN);

    ASSERT_FALSE(result.valid, "Computation invalid (both missing)");
}

/**
 * Test 5: q_integrity out of range (Python reference case)
 *
 * Python equivalent:
 *   q_integrity = 1.2  # out of [0,1]
 *   Raises ValueError per Doc 04 Sec 3.2
 */
void test_integrity_out_of_range(void)
{
    printf("\nTest 5: q_integrity out of range\n");

    quality_result_t result = compute_quality(1.2f, 0.8f);

    ASSERT_FALSE(result.valid, "Computation invalid (q_integrity > 1.0)");
}

/**
 * Test 6: q_stability out of range (Python reference case)
 *
 * Python equivalent:
 *   q_stability = -0.1  # out of [0,1]
 *   Raises ValueError per Doc 04 Sec 3.2
 */
void test_stability_out_of_range(void)
{
    printf("\nTest 6: q_stability out of range\n");

    quality_result_t result = compute_quality(0.8f, -0.1f);

    ASSERT_FALSE(result.valid, "Computation invalid (q_stability < 0.0)");
}

/**
 * Test 7: Perfect quality (Python reference case)
 *
 * Python equivalent:
 *   q_integrity = 1.0
 *   q_stability = 1.0
 *   Q_i = 1.0 (perfect quality)
 */
void test_perfect_quality(void)
{
    printf("\nTest 7: Perfect quality\n");

    quality_result_t result = compute_quality(1.0f, 1.0f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(1.0f, result.q_i, "Q_i = 1.0 (perfect)");
}

/**
 * Test 8: Zero integrity (Python reference case)
 *
 * Python equivalent:
 *   q_integrity = 0.0
 *   q_stability = 0.8
 *   Q_i = 0.0 (unusable observation)
 */
void test_zero_integrity(void)
{
    printf("\nTest 8: Zero integrity\n");

    quality_result_t result = compute_quality(0.0f, 0.8f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.0f, result.q_i, "Q_i = 0.0 (zero integrity)");
}

/**
 * Test 9: Zero stability (Python reference case)
 *
 * Python equivalent:
 *   q_integrity = 0.9
 *   q_stability = 0.0
 *   Q_i = 0.0 (unusable observation)
 */
void test_zero_stability(void)
{
    printf("\nTest 9: Zero stability\n");

    quality_result_t result = compute_quality(0.9f, 0.0f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.0f, result.q_i, "Q_i = 0.0 (zero stability)");
}

/**
 * Test 10: Both zero (Python reference case)
 *
 * Python equivalent:
 *   q_integrity = 0.0
 *   q_stability = 0.0
 *   Q_i = 0.0
 */
void test_both_zero(void)
{
    printf("\nTest 10: Both components zero\n");

    quality_result_t result = compute_quality(0.0f, 0.0f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.0f, result.q_i, "Q_i = 0.0 (both zero)");
}

/**
 * Test 11: High integrity, low stability (Python reference case)
 *
 * Python equivalent:
 *   q_integrity = 0.95
 *   q_stability = 0.3
 *   Q_i = 0.285 (multiplicative reduces quality)
 */
void test_high_integrity_low_stability(void)
{
    printf("\nTest 11: High integrity, low stability\n");

    quality_result_t result = compute_quality(0.95f, 0.3f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.285f, result.q_i, "Q_i = 0.285");
}

/**
 * Test 12: Low integrity, high stability (Python reference case)
 *
 * Python equivalent:
 *   q_integrity = 0.3
 *   q_stability = 0.95
 *   Q_i = 0.285 (multiplicative reduces quality)
 */
void test_low_integrity_high_stability(void)
{
    printf("\nTest 12: Low integrity, high stability\n");

    quality_result_t result = compute_quality(0.3f, 0.95f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.285f, result.q_i, "Q_i = 0.285");
}

/**
 * Main test runner
 */
int main(void)
{
    printf("=== Q_i (Signal Quality) Reference Parity Tests ===\n");
    printf("Reference: reference/python/nexalert_reference/quality.py\n");

    test_basic_multiplication();
    test_missing_integrity();
    test_missing_stability();
    test_both_missing();
    test_integrity_out_of_range();
    test_stability_out_of_range();
    test_perfect_quality();
    test_zero_integrity();
    test_zero_stability();
    test_both_zero();
    test_high_integrity_low_stability();
    test_low_integrity_high_stability();

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
