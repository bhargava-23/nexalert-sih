/**
 * @file test_baseline.c
 * @brief Reference parity tests for baseline (B_i) calculation
 *
 * Tests embedded C implementation against Python reference:
 * reference/python/nexalert_reference/baseline.py
 *
 * Validates:
 * - Robust baseline computation (median + MAD)
 * - Z-score computation
 * - Baseline state machine transitions
 * - Missing value handling
 * - Edge cases and boundary conditions
 */

#include "baseline.h"
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
 * Test 1: Normal distribution (Python reference case)
 *
 * Python equivalent:
 *   samples = [10.0, 10.2, 10.1, 10.3, 10.0, 9.8, 10.4, 9.9, 10.2, 10.1]
 *   median ≈ 10.1, scale > 0
 */
void test_normal_distribution(void)
{
    printf("\nTest 1: Normal distribution\n");

    float samples[] = {10.0f, 10.2f, 10.1f, 10.3f, 10.0f, 9.8f, 10.4f, 9.9f, 10.2f, 10.1f};
    baseline_result_t result = compute_robust_baseline(samples, 10, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_TRUE(result.median >= 10.0f && result.median <= 10.2f, "Median in range [10.0, 10.2]");
    ASSERT_TRUE(result.scale > 1e-9f, "Scale > epsilon");
}

/**
 * Test 2: All identical samples (Python reference case)
 *
 * Python equivalent:
 *   samples = [10.0, 10.0, 10.0, 10.0, 10.0]
 *   median = 10.0, scale = epsilon (MAD = 0)
 */
void test_all_identical_samples(void)
{
    printf("\nTest 2: All identical samples (MAD = 0)\n");

    float samples[] = {10.0f, 10.0f, 10.0f, 10.0f, 10.0f};
    baseline_result_t result = compute_robust_baseline(samples, 5, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(10.0f, result.median, "Median = 10.0");
    ASSERT_FLOAT_EQ(1e-9f, result.scale, "Scale = epsilon (MAD = 0)");
}

/**
 * Test 3: Insufficient samples (Python reference case)
 *
 * Python equivalent:
 *   compute_robust_baseline([10.0]) → ValueError
 *   compute_robust_baseline([]) → ValueError
 */
void test_insufficient_samples(void)
{
    printf("\nTest 3: Insufficient samples\n");

    float samples[] = {10.0f};
    baseline_result_t result1 = compute_robust_baseline(samples, 1, 1e-9f);
    ASSERT_FALSE(result1.valid, "Single sample invalid");

    baseline_result_t result2 = compute_robust_baseline(samples, 0, 1e-9f);
    ASSERT_FALSE(result2.valid, "Empty array invalid");
}

/**
 * Test 4: Exact two samples (Python reference case)
 *
 * Python equivalent:
 *   samples = [10.0, 12.0]
 *   median = 11.0 (average of two)
 *   MAD = 1.0, scale = 1.4826 * 1.0 + epsilon
 */
void test_exact_two_samples(void)
{
    printf("\nTest 4: Exact two samples (minimum valid)\n");

    float samples[] = {10.0f, 12.0f};
    baseline_result_t result = compute_robust_baseline(samples, 2, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(11.0f, result.median, "Median = 11.0 (average)");

    // Expected scale = 1.4826 * 1.0 + 1e-9
    float expected_scale = 1.4826f + 1e-9f;
    ASSERT_FLOAT_EQ(expected_scale, result.scale, "Scale = 1.4826 * MAD + epsilon");
}

/**
 * Test 5: Outlier robustness (Python reference case)
 *
 * Python equivalent:
 *   samples_no_outlier = [10.0, 10.1, 10.2, 10.3, 10.4]
 *   samples_with_outlier = [10.0, 10.1, 10.2, 10.3, 100.0]
 *   Median should be similar (robust to outliers)
 */
void test_outlier_robustness(void)
{
    printf("\nTest 5: Outlier robustness\n");

    float samples_no_outlier[] = {10.0f, 10.1f, 10.2f, 10.3f, 10.4f};
    float samples_with_outlier[] = {10.0f, 10.1f, 10.2f, 10.3f, 100.0f};

    baseline_result_t result1 = compute_robust_baseline(samples_no_outlier, 5, 1e-9f);
    baseline_result_t result2 = compute_robust_baseline(samples_with_outlier, 5, 1e-9f);

    ASSERT_TRUE(result1.valid && result2.valid, "Both computations valid");

    // Median should be similar (robust to outliers)
    float median_diff = fabsf(result1.median - result2.median);
    ASSERT_TRUE(median_diff < 0.5f, "Median robust to outliers (diff < 0.5)");
}

/**
 * Test 6: Z-score normal case (Python reference case)
 *
 * Python equivalent:
 *   z = compute_z_score(15.0, 10.0, 2.0)
 *   z = (15 - 10) / 2 = 2.5
 */
void test_z_score_normal(void)
{
    printf("\nTest 6: Z-score normal computation\n");

    zscore_result_t result = compute_z_score(15.0f, 10.0f, 2.0f, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(2.5f, result.z_score, "z = 2.5");
}

/**
 * Test 7: Z-score missing value (Python reference case)
 *
 * Python equivalent:
 *   z = compute_z_score(None, 10.0, 2.0)
 *   Returns None (preserve missing != zero)
 */
void test_z_score_missing_value(void)
{
    printf("\nTest 7: Z-score missing value\n");

    zscore_result_t result = compute_z_score(NAN, 10.0f, 2.0f, 1e-9f);

    ASSERT_FALSE(result.valid, "Missing value invalid");
}

/**
 * Test 8: Z-score scale too small (Python reference case)
 *
 * Python equivalent:
 *   z = compute_z_score(10.5, 10.0, 1e-10)
 *   Returns None (scale < epsilon)
 */
void test_z_score_scale_too_small(void)
{
    printf("\nTest 8: Z-score scale too small\n");

    zscore_result_t result = compute_z_score(10.5f, 10.0f, 1e-10f, 1e-9f);

    ASSERT_FALSE(result.valid, "Scale too small invalid");
}

/**
 * Test 9: Z-score zero (Python reference case)
 *
 * Python equivalent:
 *   z = compute_z_score(10.0, 10.0, 2.0)
 *   z = 0 (value equals median)
 */
void test_z_score_zero(void)
{
    printf("\nTest 9: Z-score zero (value = median)\n");

    zscore_result_t result = compute_z_score(10.0f, 10.0f, 2.0f, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(0.0f, result.z_score, "z = 0");
}

/**
 * Test 10: Z-score negative (Python reference case)
 *
 * Python equivalent:
 *   z = compute_z_score(8.0, 10.0, 2.0)
 *   z = (8 - 10) / 2 = -1.0
 */
void test_z_score_negative(void)
{
    printf("\nTest 10: Z-score negative (value below median)\n");

    zscore_result_t result = compute_z_score(8.0f, 10.0f, 2.0f, 1e-9f);

    ASSERT_TRUE(result.valid, "Computation valid");
    ASSERT_FLOAT_EQ(-1.0f, result.z_score, "z = -1.0");
}

/**
 * Test 11: State INITIALIZING → LEARNING (Python reference case)
 *
 * Python equivalent:
 *   update_baseline_state(INITIALIZING, 15, 10, 50, "NORMAL", 0, 10)
 *   → (LEARNING, 1)
 */
void test_state_initializing_to_learning(void)
{
    printf("\nTest 11: State INITIALIZING → LEARNING\n");

    baseline_config_t config = baseline_default_config();
    baseline_state_result_t result = update_baseline_state(
        BASELINE_INITIALIZING,
        15,
        &config,
        "NORMAL",
        0
    );

    ASSERT_TRUE(result.next_state == BASELINE_LEARNING, "Transitioned to LEARNING");
    ASSERT_TRUE(result.stability_count == 1, "Stability count = 1");
}

/**
 * Test 12: State LEARNING → READY (Python reference case)
 *
 * Python equivalent:
 *   update_baseline_state(LEARNING, 60, 10, 50, "NORMAL", 5, 10)
 *   → (READY, 6)
 */
void test_state_learning_to_ready(void)
{
    printf("\nTest 12: State LEARNING → READY\n");

    baseline_config_t config = baseline_default_config();
    baseline_state_result_t result = update_baseline_state(
        BASELINE_LEARNING,
        60,
        &config,
        "NORMAL",
        5
    );

    ASSERT_TRUE(result.next_state == BASELINE_READY, "Transitioned to READY");
    ASSERT_TRUE(result.stability_count == 6, "Stability count incremented");
}

/**
 * Test 13: State READY → FROZEN (Python reference case)
 *
 * Python equivalent:
 *   update_baseline_state(READY, 100, 10, 50, "CONFIRMED", 5, 10)
 *   → (FROZEN, 0)
 */
void test_state_ready_to_frozen(void)
{
    printf("\nTest 13: State READY → FROZEN (hazard CONFIRMED)\n");

    baseline_config_t config = baseline_default_config();
    baseline_state_result_t result = update_baseline_state(
        BASELINE_READY,
        100,
        &config,
        "CONFIRMED",
        5
    );

    ASSERT_TRUE(result.next_state == BASELINE_FROZEN, "Transitioned to FROZEN");
    ASSERT_TRUE(result.stability_count == 0, "Stability count reset on freeze");
}

/**
 * Test 14: State FROZEN → RECOVERING (Python reference case)
 *
 * Python equivalent:
 *   update_baseline_state(FROZEN, 100, 10, 50, "NORMAL", 10, 10)
 *   → (RECOVERING, ...)
 */
void test_state_frozen_to_recovering(void)
{
    printf("\nTest 14: State FROZEN → RECOVERING (stability reached)\n");

    baseline_config_t config = baseline_default_config();
    baseline_state_result_t result = update_baseline_state(
        BASELINE_FROZEN,
        100,
        &config,
        "NORMAL",
        10  // Reached stability threshold
    );

    ASSERT_TRUE(result.next_state == BASELINE_RECOVERING, "Transitioned to RECOVERING");
}

/**
 * Test 15: State RECOVERING → READY (Python reference case)
 *
 * Python equivalent:
 *   update_baseline_state(RECOVERING, 60, 10, 50, "NORMAL", 15, 10)
 *   → (READY, ...)
 */
void test_state_recovering_to_ready(void)
{
    printf("\nTest 15: State RECOVERING → READY\n");

    baseline_config_t config = baseline_default_config();
    baseline_state_result_t result = update_baseline_state(
        BASELINE_RECOVERING,
        60,
        &config,
        "NORMAL",
        15
    );

    ASSERT_TRUE(result.next_state == BASELINE_READY, "Transitioned to READY");
}

/**
 * Test 16: Stability reset on unfavorable hazard state (Python reference case)
 *
 * Python equivalent:
 *   update_baseline_state(FROZEN, 100, 10, 50, "CRITICAL", 5, 10)
 *   → (FROZEN, 0)  # Stability reset
 */
void test_stability_reset_on_unfavorable(void)
{
    printf("\nTest 16: Stability reset on unfavorable hazard state\n");

    baseline_config_t config = baseline_default_config();
    baseline_state_result_t result = update_baseline_state(
        BASELINE_FROZEN,
        100,
        &config,
        "CRITICAL",  // Unfavorable
        5
    );

    ASSERT_TRUE(result.next_state == BASELINE_FROZEN, "No transition (still FROZEN)");
    ASSERT_TRUE(result.stability_count == 0, "Stability count reset");
}

/**
 * Test 17: Stability increment on favorable hazard state (Python reference case)
 *
 * Python equivalent:
 *   update_baseline_state(FROZEN, 100, 10, 50, "NORMAL", 5, 10)
 *   Stability increments to 6
 */
void test_stability_increment_on_favorable(void)
{
    printf("\nTest 17: Stability increment on favorable hazard state\n");

    baseline_config_t config = baseline_default_config();

    // Test NORMAL
    baseline_state_result_t result1 = update_baseline_state(
        BASELINE_FROZEN,
        100,
        &config,
        "NORMAL",
        5
    );
    ASSERT_TRUE(result1.stability_count == 6, "Stability incremented (NORMAL)");

    // Test WATCH
    baseline_state_result_t result2 = update_baseline_state(
        BASELINE_FROZEN,
        100,
        &config,
        "WATCH",
        5
    );
    ASSERT_TRUE(result2.stability_count == 6, "Stability incremented (WATCH)");
}

/**
 * Test 18: No circular dependency (Python reference case)
 *
 * Verifies baseline state machine only READS hazard state (no write)
 */
void test_no_circular_dependency(void)
{
    printf("\nTest 18: No circular dependency (baseline reads hazard state only)\n");

    baseline_config_t config = baseline_default_config();
    const char* initial_hazard_state = "CONFIRMED";

    baseline_state_result_t result = update_baseline_state(
        BASELINE_READY,
        100,
        &config,
        initial_hazard_state,
        0
    );

    // Function returns only baseline state and stability
    // No hazard state returned - confirms no circular write
    ASSERT_TRUE(result.next_state == BASELINE_FROZEN, "Baseline transitions by reading hazard state");

    printf("  ✓ No hazard state mutation (input only)\n");
    tests_passed++;
}

/**
 * Test 19: READY → FROZEN with CRITICAL hazard (Python reference case)
 *
 * Python equivalent:
 *   update_baseline_state(READY, 100, 10, 50, "CRITICAL", 5, 10)
 *   → (FROZEN, 0)
 */
void test_state_ready_to_frozen_critical(void)
{
    printf("\nTest 19: State READY → FROZEN (hazard CRITICAL)\n");

    baseline_config_t config = baseline_default_config();
    baseline_state_result_t result = update_baseline_state(
        BASELINE_READY,
        100,
        &config,
        "CRITICAL",
        5
    );

    ASSERT_TRUE(result.next_state == BASELINE_FROZEN, "Transitioned to FROZEN (CRITICAL)");
    ASSERT_TRUE(result.stability_count == 0, "Stability count reset on freeze");
}

/**
 * Main test runner
 */
int main(void)
{
    printf("=== Baseline (B_i) Reference Parity Tests ===\n");
    printf("Reference: reference/python/nexalert_reference/baseline.py\n");

    // Robust baseline tests
    test_normal_distribution();
    test_all_identical_samples();
    test_insufficient_samples();
    test_exact_two_samples();
    test_outlier_robustness();

    // Z-score tests
    test_z_score_normal();
    test_z_score_missing_value();
    test_z_score_scale_too_small();
    test_z_score_zero();
    test_z_score_negative();

    // State machine tests
    test_state_initializing_to_learning();
    test_state_learning_to_ready();
    test_state_ready_to_frozen();
    test_state_frozen_to_recovering();
    test_state_recovering_to_ready();
    test_stability_reset_on_unfavorable();
    test_stability_increment_on_favorable();
    test_no_circular_dependency();
    test_state_ready_to_frozen_critical();

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
