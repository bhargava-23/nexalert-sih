/**
 * @file test_risk.c
 * @brief Reference parity tests for operational risk (R_h) calculation
 *
 * Tests embedded C implementation against Python reference:
 * reference/python/nexalert_reference/risk.py
 *
 * Validates:
 * - Risk computation with all components
 * - Component reweighting when some missing
 * - Missing value handling
 * - Weight validation
 */

#include "risk.h"
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
 * Test 1: Risk - all components available
 *
 * Python equivalent:
 *   compute_risk(0.8, 0.7, 0.5) → 0.69
 *   R_h = 0.4×0.8 + 0.4×0.7 + 0.2×0.5 = 0.70
 */
void test_risk_all_available(void)
{
    printf("\nTest 1: Risk - all components available\n");

    risk_result_t result = compute_risk(0.8f, 0.7f, 0.5f, NULL, RISK_EPSILON);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.70f, result.r_h, "R_h = 0.70");
}

/**
 * Test 2: Risk - severity missing (reweighting)
 *
 * Python equivalent:
 *   compute_risk(0.8, None, 0.5) → 0.733
 *   Reweight: (0.4×0.8 + 0.2×0.5) / (0.4+0.2) = 0.733
 */
void test_risk_severity_missing(void)
{
    printf("\nTest 2: Risk - severity missing (reweighting)\n");

    risk_result_t result = compute_risk(0.8f, NAN, 0.5f, NULL, RISK_EPSILON);

    ASSERT_TRUE(result.valid, "Computation valid");
    // Expected: (0.4×0.8 + 0.2×0.5) / 0.6 = 0.733333
    ASSERT_FLOAT_EQ(0.733333f, result.r_h, "R_h ≈ 0.733 (reweighted)");
}

/**
 * Test 3: Risk - temporal missing (reweighting)
 *
 * Python equivalent:
 *   compute_risk(0.8, 0.7, None) → 0.75
 *   Reweight: (0.4×0.8 + 0.4×0.7) / (0.4+0.4) = 0.75
 */
void test_risk_temporal_missing(void)
{
    printf("\nTest 3: Risk - temporal missing (reweighting)\n");

    risk_result_t result = compute_risk(0.8f, 0.7f, NAN, NULL, RISK_EPSILON);

    ASSERT_TRUE(result.valid, "Computation valid");
    // Expected: (0.4×0.8 + 0.4×0.7) / 0.8 = 0.75
    ASSERT_FLOAT_EQ(0.75f, result.r_h, "R_h = 0.75 (reweighted)");
}

/**
 * Test 4: Risk - evidence missing (reweighting)
 *
 * Python equivalent:
 *   compute_risk(None, 0.7, 0.5) → 0.667
 *   Reweight: (0.4×0.7 + 0.2×0.5) / (0.4+0.2) = 0.633
 */
void test_risk_evidence_missing(void)
{
    printf("\nTest 4: Risk - evidence missing (reweighting)\n");

    risk_result_t result = compute_risk(NAN, 0.7f, 0.5f, NULL, RISK_EPSILON);

    ASSERT_TRUE(result.valid, "Computation valid");
    // Expected: (0.4×0.7 + 0.2×0.5) / 0.6 = 0.633333
    ASSERT_FLOAT_EQ(0.633333f, result.r_h, "R_h ≈ 0.633 (reweighted)");
}

/**
 * Test 5: Risk - all missing
 *
 * Python equivalent:
 *   compute_risk(None, None, None) → None
 */
void test_risk_all_missing(void)
{
    printf("\nTest 5: Risk - all missing\n");

    risk_result_t result = compute_risk(NAN, NAN, NAN, NULL, RISK_EPSILON);

    ASSERT_FALSE(result.valid, "All missing invalid");
}

/**
 * Test 6: Risk - evidence only
 *
 * Python equivalent:
 *   compute_risk(0.8, None, None) → 0.8
 */
void test_risk_evidence_only(void)
{
    printf("\nTest 6: Risk - evidence only\n");

    risk_result_t result = compute_risk(0.8f, NAN, NAN, NULL, RISK_EPSILON);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.8f, result.r_h, "R_h = 0.8 (evidence only)");
}

/**
 * Test 7: Risk - severity only
 *
 * Python equivalent:
 *   compute_risk(None, 0.7, None) → 0.7
 */
void test_risk_severity_only(void)
{
    printf("\nTest 7: Risk - severity only\n");

    risk_result_t result = compute_risk(NAN, 0.7f, NAN, NULL, RISK_EPSILON);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.7f, result.r_h, "R_h = 0.7 (severity only)");
}

/**
 * Test 8: Risk - temporal only
 *
 * Python equivalent:
 *   compute_risk(None, None, 0.5) → 0.5
 */
void test_risk_temporal_only(void)
{
    printf("\nTest 8: Risk - temporal only\n");

    risk_result_t result = compute_risk(NAN, NAN, 0.5f, NULL, RISK_EPSILON);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.5f, result.r_h, "R_h = 0.5 (temporal only)");
}

/**
 * Test 9: Validate weights - valid
 *
 * Python equivalent:
 *   validate_risk_weights({'w_E': 0.4, 'w_S': 0.4, 'w_T': 0.2}) → True
 */
void test_validate_weights_valid(void)
{
    printf("\nTest 9: Validate weights - valid\n");

    risk_weights_t weights = risk_default_weights();
    bool valid = validate_risk_weights(&weights, RISK_EPSILON);

    ASSERT_TRUE(valid, "Default weights valid");
}

/**
 * Test 10: Validate weights - invalid sum
 *
 * Python equivalent:
 *   validate_risk_weights({'w_E': 0.5, 'w_S': 0.4, 'w_T': 0.2}) → False
 */
void test_validate_weights_invalid_sum(void)
{
    printf("\nTest 10: Validate weights - invalid sum\n");

    risk_weights_t weights = {
        .w_E = 0.5f,
        .w_S = 0.4f,
        .w_T = 0.2f  // Sum = 1.1
    };
    bool valid = validate_risk_weights(&weights, RISK_EPSILON);

    ASSERT_FALSE(valid, "Invalid sum rejected");
}

/**
 * Test 11: Validate weights - negative weight
 *
 * Python equivalent:
 *   validate_risk_weights({'w_E': -0.1, 'w_S': 0.6, 'w_T': 0.5}) → False
 */
void test_validate_weights_negative(void)
{
    printf("\nTest 11: Validate weights - negative weight\n");

    risk_weights_t weights = {
        .w_E = -0.1f,
        .w_S = 0.6f,
        .w_T = 0.5f
    };
    bool valid = validate_risk_weights(&weights, RISK_EPSILON);

    ASSERT_FALSE(valid, "Negative weight rejected");
}

/**
 * Test 12: Default weights
 */
void test_default_weights(void)
{
    printf("\nTest 12: Default weights\n");

    risk_weights_t weights = risk_default_weights();

    ASSERT_FLOAT_EQ(0.4f, weights.w_E, "w_E = 0.4");
    ASSERT_FLOAT_EQ(0.4f, weights.w_S, "w_S = 0.4");
    ASSERT_FLOAT_EQ(0.2f, weights.w_T, "w_T = 0.2");
}

/**
 * Test 13: Risk - high urgency scenario
 *
 * Python equivalent:
 *   compute_risk(0.9, 0.8, 0.7) → 0.82
 */
void test_risk_high_urgency(void)
{
    printf("\nTest 13: Risk - high urgency scenario\n");

    risk_result_t result = compute_risk(0.9f, 0.8f, 0.7f, NULL, RISK_EPSILON);

    ASSERT_TRUE(result.valid, "Computation valid");
    // Expected: 0.4×0.9 + 0.4×0.8 + 0.2×0.7 = 0.82
    ASSERT_FLOAT_EQ(0.82f, result.r_h, "R_h = 0.82 (high urgency)");
}

/**
 * Test 14: Risk - low urgency scenario
 *
 * Python equivalent:
 *   compute_risk(0.2, 0.1, 0.05) → 0.13
 */
void test_risk_low_urgency(void)
{
    printf("\nTest 14: Risk - low urgency scenario\n");

    risk_result_t result = compute_risk(0.2f, 0.1f, 0.05f, NULL, RISK_EPSILON);

    ASSERT_TRUE(result.valid, "Computation valid");
    // Expected: 0.4×0.2 + 0.4×0.1 + 0.2×0.05 = 0.13
    ASSERT_FLOAT_EQ(0.13f, result.r_h, "R_h = 0.13 (low urgency)");
}

/**
 * Test 15: Risk - boundary values (all zero)
 *
 * Python equivalent:
 *   compute_risk(0.0, 0.0, 0.0) → 0.0
 */
void test_risk_all_zero(void)
{
    printf("\nTest 15: Risk - boundary values (all zero)\n");

    risk_result_t result = compute_risk(0.0f, 0.0f, 0.0f, NULL, RISK_EPSILON);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.0f, result.r_h, "R_h = 0.0 (all zero)");
}

/**
 * Test 16: Risk - boundary values (all one)
 *
 * Python equivalent:
 *   compute_risk(1.0, 1.0, 1.0) → 1.0
 */
void test_risk_all_one(void)
{
    printf("\nTest 16: Risk - boundary values (all one)\n");

    risk_result_t result = compute_risk(1.0f, 1.0f, 1.0f, NULL, RISK_EPSILON);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(1.0f, result.r_h, "R_h = 1.0 (all one)");
}

/**
 * Main test runner
 */
int main(void)
{
    printf("=== Operational Risk (R_h) Reference Parity Tests ===\n");
    printf("Reference: reference/python/nexalert_reference/risk.py\n");

    // Risk computation tests
    test_risk_all_available();
    test_risk_severity_missing();
    test_risk_temporal_missing();
    test_risk_evidence_missing();
    test_risk_all_missing();
    test_risk_evidence_only();
    test_risk_severity_only();
    test_risk_temporal_only();

    // Weight validation tests
    test_validate_weights_valid();
    test_validate_weights_invalid_sum();
    test_validate_weights_negative();
    test_default_weights();

    // Scenario tests
    test_risk_high_urgency();
    test_risk_low_urgency();
    test_risk_all_zero();
    test_risk_all_one();

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
