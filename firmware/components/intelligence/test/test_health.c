/**
 * @file test_health.c
 * @brief Reference parity tests for H_i (sensor health) calculation
 *
 * Tests embedded C implementation against Python reference:
 * reference/python/nexalert_reference/health.py
 *
 * Validates:
 * - Hard failure gate (F_i=1 forces H_i=0)
 * - Weighted sum computation
 * - Missing diagnostics handling (preserves missing != zero)
 * - Weight validation (must sum to 1)
 * - Diagnostic range validation [0, 1]
 */

#include "health.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <stdbool.h>

// Test tolerance (matches Python EPSILON = 1e-9, but use 1e-6 for float precision)
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
 * Test 1: Basic weighted sum (Python reference case)
 *
 * Python equivalent:
 *   diagnostics = {"uptime": 0.8, "self_test": 1.0, "stability": 0.9}
 *   weights = {"uptime": 0.3, "self_test": 0.4, "stability": 0.3}
 *   H_i = 0.3*0.8 + 0.4*1.0 + 0.3*0.9 = 0.91
 */
void test_basic_weighted_sum(void)
{
    printf("\nTest 1: Basic weighted sum\n");

    health_diagnostic_t diagnostics[] = {
        {"uptime", 0.8f, 0.3f},
        {"self_test", 1.0f, 0.4f},
        {"stability", 0.9f, 0.3f}
    };

    health_result_t result = compute_health(diagnostics, 3, false);

    ASSERT_TRUE(result.complete, "Computation complete");
    ASSERT_FALSE(result.hard_failure, "No hard failure");
    ASSERT_FLOAT_EQ(0.91f, result.h_i, "H_i = 0.91");
}

/**
 * Test 2: Hard failure gate (Python reference case)
 *
 * Python equivalent:
 *   hard_failure = True
 *   H_i = 0.0 (forced by F_i=1)
 */
void test_hard_failure_gate(void)
{
    printf("\nTest 2: Hard failure gate\n");

    health_diagnostic_t diagnostics[] = {
        {"uptime", 0.9f, 0.5f},
        {"self_test", 0.8f, 0.5f}
    };

    health_result_t result = compute_health(diagnostics, 2, true);

    ASSERT_TRUE(result.complete, "Computation complete");
    ASSERT_TRUE(result.hard_failure, "Hard failure set");
    ASSERT_FLOAT_EQ(0.0f, result.h_i, "H_i = 0.0 (forced)");
}

/**
 * Test 3: Missing diagnostics (Python reference case)
 *
 * Python equivalent:
 *   diagnostics = {"uptime": 0.8}  # missing "self_test"
 *   weights = {"uptime": 0.5, "self_test": 0.5}
 *   Returns (None, False) to preserve missing != zero
 */
void test_missing_diagnostics(void)
{
    printf("\nTest 3: Missing diagnostics\n");

    health_diagnostic_t diagnostics[] = {
        {"uptime", 0.8f, 0.5f}
        // Missing second diagnostic (only 1 of 2 provided)
    };

    // This test simulates incomplete diagnostics by not providing full weight coverage
    // In practice, missing diagnostics would be detected by application logic
    health_result_t result = compute_health(diagnostics, 1, false);

    // With only one diagnostic and weight=0.5, sum != 1, so incomplete
    ASSERT_FALSE(result.complete, "Computation incomplete (missing diagnostic)");
}

/**
 * Test 4: Invalid weight sum (Python reference case)
 *
 * Python equivalent:
 *   weights = {"uptime": 0.3, "self_test": 0.5}  # sum = 0.8 != 1
 *   Raises ValueError per Doc 04 Sec 3.1
 */
void test_invalid_weight_sum(void)
{
    printf("\nTest 4: Invalid weight sum\n");

    health_diagnostic_t diagnostics[] = {
        {"uptime", 0.8f, 0.3f},
        {"self_test", 1.0f, 0.5f}  // Sum = 0.8 != 1
    };

    health_result_t result = compute_health(diagnostics, 2, false);

    ASSERT_FALSE(result.complete, "Computation incomplete (invalid weights)");
}

/**
 * Test 5: Diagnostic out of range (Python reference case)
 *
 * Python equivalent:
 *   diagnostics = {"uptime": 1.2}  # out of [0,1]
 *   Raises ValueError per Doc 04 Sec 3.1
 */
void test_diagnostic_out_of_range(void)
{
    printf("\nTest 5: Diagnostic out of range\n");

    health_diagnostic_t diagnostics[] = {
        {"uptime", 1.2f, 0.5f},  // D_ij > 1.0 (invalid)
        {"self_test", 0.8f, 0.5f}
    };

    health_result_t result = compute_health(diagnostics, 2, false);

    ASSERT_FALSE(result.complete, "Computation incomplete (out of range)");
}

/**
 * Test 6: All diagnostics perfect (Python reference case)
 *
 * Python equivalent:
 *   diagnostics = {"uptime": 1.0, "self_test": 1.0}
 *   weights = {"uptime": 0.5, "self_test": 0.5}
 *   H_i = 1.0 (perfect health)
 */
void test_perfect_health(void)
{
    printf("\nTest 6: Perfect health\n");

    health_diagnostic_t diagnostics[] = {
        {"uptime", 1.0f, 0.5f},
        {"self_test", 1.0f, 0.5f}
    };

    health_result_t result = compute_health(diagnostics, 2, false);

    ASSERT_TRUE(result.complete, "Computation complete");
    ASSERT_FLOAT_EQ(1.0f, result.h_i, "H_i = 1.0 (perfect)");
}

/**
 * Test 7: All diagnostics zero (Python reference case)
 *
 * Python equivalent:
 *   diagnostics = {"uptime": 0.0, "self_test": 0.0}
 *   weights = {"uptime": 0.5, "self_test": 0.5}
 *   H_i = 0.0 (complete failure, but not hard failure)
 */
void test_zero_health(void)
{
    printf("\nTest 7: Zero health (soft failure)\n");

    health_diagnostic_t diagnostics[] = {
        {"uptime", 0.0f, 0.5f},
        {"self_test", 0.0f, 0.5f}
    };

    health_result_t result = compute_health(diagnostics, 2, false);

    ASSERT_TRUE(result.complete, "Computation complete");
    ASSERT_FALSE(result.hard_failure, "No hard failure");
    ASSERT_FLOAT_EQ(0.0f, result.h_i, "H_i = 0.0 (soft failure)");
}

/**
 * Test 8: Weight validation helper
 */
void test_weight_validation(void)
{
    printf("\nTest 8: Weight validation helper\n");

    health_diagnostic_t valid_weights[] = {
        {"a", 0.0f, 0.3f},
        {"b", 0.0f, 0.7f}
    };
    ASSERT_TRUE(validate_health_weights(valid_weights, 2), "Valid weights sum to 1");

    health_diagnostic_t invalid_weights[] = {
        {"a", 0.0f, 0.3f},
        {"b", 0.0f, 0.6f}  // Sum = 0.9
    };
    ASSERT_FALSE(validate_health_weights(invalid_weights, 2), "Invalid weights detected");

    ASSERT_FALSE(validate_health_weights(NULL, 2), "NULL diagnostics rejected");
    ASSERT_FALSE(validate_health_weights(valid_weights, 0), "Zero count rejected");
}

/**
 * Main test runner
 */
int main(void)
{
    printf("=== H_i (Sensor Health) Reference Parity Tests ===\n");
    printf("Reference: reference/python/nexalert_reference/health.py\n");

    test_basic_weighted_sum();
    test_hard_failure_gate();
    test_missing_diagnostics();
    test_invalid_weight_sum();
    test_diagnostic_out_of_range();
    test_perfect_health();
    test_zero_health();
    test_weight_validation();

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
