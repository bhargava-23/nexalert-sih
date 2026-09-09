/**
 * @file test_hazard_state.c
 * @brief Reference parity tests for hazard state machine
 *
 * Tests embedded C implementation against Python reference:
 * reference/python/nexalert_reference/state_machine.py
 *
 * Validates:
 * - State transitions (all legal transitions)
 * - Hysteresis boundaries
 * - Persistence counters
 * - Fast escalation paths
 * - Information condition computation
 * - Baseline freeze behavior
 * - Missing value handling
 */

#include "hazard_state.h"
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

#define ASSERT_EQ(expected, actual, message) do { \
    if ((expected) == (actual)) { \
        tests_passed++; \
        printf("  ✓ %s\n", message); \
    } else { \
        tests_failed++; \
        printf("  ✗ %s: expected %d, got %d\n", message, (expected), (actual)); \
    } \
} while(0)

/**
 * Test 1: Initial state - starts NORMAL
 */
void test_initial_state(void)
{
    printf("\nTest 1: Initial state - starts NORMAL\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.1f, .C_h = 0.8f, .S_h = 0.1f,
        .R_h = 0.1f, .A_h = 0.1f, .T_h = 0.1f,
        .core_coverage = 0.9f
    };

    state_transition_t result = update_state(
        HAZARD_STATE_NORMAL, &intel, "READY",
        1000.0f, 0, NAN, &config, HAZARD_STATE_EPSILON
    );

    ASSERT_EQ(HAZARD_STATE_NORMAL, result.new_state, "Remains NORMAL with low metrics");
    ASSERT_EQ(HAZARD_STATE_NORMAL, result.prev_state, "Previous state NORMAL");
}

/**
 * Test 2: NORMAL → WATCH via risk threshold
 */
void test_normal_to_watch_via_risk(void)
{
    printf("\nTest 2: NORMAL → WATCH via risk threshold\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.1f, .C_h = 0.8f, .S_h = 0.1f,
        .R_h = 0.35f,  // Above watch threshold (0.3)
        .A_h = 0.1f, .T_h = 0.1f,
        .core_coverage = 0.9f
    };

    state_transition_t result = update_state(
        HAZARD_STATE_NORMAL, &intel, "READY",
        1000.0f, 0, NAN, &config, HAZARD_STATE_EPSILON
    );

    ASSERT_EQ(HAZARD_STATE_WATCH, result.new_state, "Transitions to WATCH");
    ASSERT_EQ(HAZARD_STATE_NORMAL, result.prev_state, "Previous state NORMAL");
}

/**
 * Test 3: NORMAL → WATCH via anomaly threshold
 */
void test_normal_to_watch_via_anomaly(void)
{
    printf("\nTest 3: NORMAL → WATCH via anomaly threshold\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.1f, .C_h = 0.8f, .S_h = 0.1f,
        .R_h = 0.1f,
        .A_h = 0.55f,  // Above watch threshold (0.5)
        .T_h = 0.1f,
        .core_coverage = 0.9f
    };

    state_transition_t result = update_state(
        HAZARD_STATE_NORMAL, &intel, "READY",
        1000.0f, 0, NAN, &config, HAZARD_STATE_EPSILON
    );

    ASSERT_EQ(HAZARD_STATE_WATCH, result.new_state, "Transitions to WATCH via anomaly");
}

/**
 * Test 4: WATCH → SUSPECTED with persistence
 */
void test_watch_to_suspected(void)
{
    printf("\nTest 4: WATCH → SUSPECTED with persistence\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.45f,  // Above suspected threshold (0.4)
        .C_h = 0.8f, .S_h = 0.5f,
        .R_h = 0.35f, .A_h = 0.55f, .T_h = 0.5f,
        .core_coverage = 0.9f
    };

    // Sample 1: counter = 0 → 1
    state_transition_t result = update_state(
        HAZARD_STATE_WATCH, &intel, "READY",
        1000.0f, 0, NAN, &config, HAZARD_STATE_EPSILON
    );
    ASSERT_EQ(HAZARD_STATE_WATCH, result.new_state, "Sample 1: still WATCH");
    ASSERT_EQ(1, result.persistence_counter, "Counter = 1");

    // Sample 2: counter = 1 → 2
    result = update_state(
        HAZARD_STATE_WATCH, &intel, "READY",
        1001.0f, 1, NAN, &config, HAZARD_STATE_EPSILON
    );
    ASSERT_EQ(HAZARD_STATE_WATCH, result.new_state, "Sample 2: still WATCH");
    ASSERT_EQ(2, result.persistence_counter, "Counter = 2");

    // Sample 3: counter = 2 → 3, transition
    result = update_state(
        HAZARD_STATE_WATCH, &intel, "READY",
        1002.0f, 2, NAN, &config, HAZARD_STATE_EPSILON
    );
    ASSERT_EQ(HAZARD_STATE_SUSPECTED, result.new_state, "Sample 3: transitions to SUSPECTED");
    ASSERT_EQ(0, result.persistence_counter, "Counter reset to 0");
}

/**
 * Test 5: WATCH → CONFIRMED fast path
 */
void test_watch_to_confirmed_fast_path(void)
{
    printf("\nTest 5: WATCH → CONFIRMED fast path\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.87f,  // Above fast threshold (0.85)
        .C_h = 0.75f,  // Above fast threshold (0.6)
        .S_h = 0.82f,  // Above fast threshold (0.8)
        .R_h = 0.35f, .A_h = 0.55f, .T_h = 0.5f,
        .core_coverage = 0.85f  // Above fast threshold (0.7)
    };

    // Sample 1: counter = 0 → 1
    state_transition_t result = update_state(
        HAZARD_STATE_WATCH, &intel, "READY",
        1000.0f, 0, NAN, &config, HAZARD_STATE_EPSILON
    );
    ASSERT_EQ(HAZARD_STATE_WATCH, result.new_state, "Sample 1: still WATCH");

    // Sample 2: counter = 1 → 2, transition (fast path persistence = 2)
    result = update_state(
        HAZARD_STATE_WATCH, &intel, "READY",
        1001.0f, 1, NAN, &config, HAZARD_STATE_EPSILON
    );
    ASSERT_EQ(HAZARD_STATE_CONFIRMED, result.new_state, "Sample 2: transitions to CONFIRMED (fast path)");
    ASSERT_TRUE(strstr(result.reason, "fast path") != NULL, "Reason contains 'fast path'");
}

/**
 * Test 6: WATCH → CONFIRMED fast path blocked by UNKNOWN
 */
void test_watch_fast_path_blocked_by_unknown(void)
{
    printf("\nTest 6: WATCH → CONFIRMED fast path blocked by UNKNOWN\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.87f,
        .C_h = 0.35f,  // Below DEGRADED threshold → UNKNOWN
        .S_h = 0.82f,
        .R_h = 0.35f, .A_h = 0.55f, .T_h = 0.5f,
        .core_coverage = 0.85f
    };

    // Fast path should be blocked by UNKNOWN information condition
    state_transition_t result = update_state(
        HAZARD_STATE_WATCH, &intel, "READY",
        1000.0f, 5, NAN, &config, HAZARD_STATE_EPSILON
    );

    ASSERT_EQ(HAZARD_STATE_WATCH, result.new_state, "Fast path blocked by UNKNOWN");
    ASSERT_EQ(INFO_CONDITION_UNKNOWN, result.info_condition, "Info condition is UNKNOWN");
}

/**
 * Test 7: SUSPECTED → CONFIRMED with persistence
 */
void test_suspected_to_confirmed(void)
{
    printf("\nTest 7: SUSPECTED → CONFIRMED with persistence\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.75f,  // Above confirmed threshold (0.7)
        .C_h = 0.7f,   // Above confidence min (0.6)
        .S_h = 0.5f,
        .R_h = 0.5f, .A_h = 0.5f, .T_h = 0.5f,
        .core_coverage = 0.8f  // Above coverage min (0.7)
    };

    // Need 5 samples (confirmed_enter_persistence = 5)
    state_transition_t result;
    for (int i = 0; i < 4; i++) {
        result = update_state(
            HAZARD_STATE_SUSPECTED, &intel, "READY",
            1000.0f + i, i, NAN, &config, HAZARD_STATE_EPSILON
        );
        ASSERT_EQ(HAZARD_STATE_SUSPECTED, result.new_state, "Still SUSPECTED");
    }

    // 5th sample: transition
    result = update_state(
        HAZARD_STATE_SUSPECTED, &intel, "READY",
        1004.0f, 4, NAN, &config, HAZARD_STATE_EPSILON
    );
    ASSERT_EQ(HAZARD_STATE_CONFIRMED, result.new_state, "Transitions to CONFIRMED");
}

/**
 * Test 8: SUSPECTED → CONFIRMED blocked by UNKNOWN
 */
void test_suspected_to_confirmed_blocked_unknown(void)
{
    printf("\nTest 8: SUSPECTED → CONFIRMED blocked by UNKNOWN\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.75f,
        .C_h = 0.35f,  // Below DEGRADED threshold → UNKNOWN
        .S_h = 0.5f,
        .R_h = 0.5f, .A_h = 0.5f, .T_h = 0.5f,
        .core_coverage = 0.8f
    };

    state_transition_t result = update_state(
        HAZARD_STATE_SUSPECTED, &intel, "READY",
        1000.0f, 10, NAN, &config, HAZARD_STATE_EPSILON
    );

    ASSERT_EQ(HAZARD_STATE_SUSPECTED, result.new_state, "Transition blocked by UNKNOWN");
    ASSERT_EQ(INFO_CONDITION_UNKNOWN, result.info_condition, "Info condition is UNKNOWN");
}

/**
 * Test 9: CONFIRMED → CRITICAL
 */
void test_confirmed_to_critical(void)
{
    printf("\nTest 9: CONFIRMED → CRITICAL\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.8f, .C_h = 0.7f,
        .S_h = 0.87f,  // Above critical threshold (0.85)
        .R_h = 0.7f, .A_h = 0.5f, .T_h = 0.7f,
        .core_coverage = 0.8f
    };

    // Immediate transition (critical_enter_persistence = 1)
    state_transition_t result = update_state(
        HAZARD_STATE_CONFIRMED, &intel, "READY",
        1000.0f, 0, NAN, &config, HAZARD_STATE_EPSILON
    );

    ASSERT_EQ(HAZARD_STATE_CRITICAL, result.new_state, "Transitions to CRITICAL");
}

/**
 * Test 10: CONFIRMED → CRITICAL under UNKNOWN (safety-first)
 */
void test_confirmed_to_critical_under_unknown(void)
{
    printf("\nTest 10: CONFIRMED → CRITICAL under UNKNOWN (safety-first)\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.8f,
        .C_h = 0.3f,  // UNKNOWN info condition
        .S_h = 0.87f,  // Above critical threshold
        .R_h = 0.7f, .A_h = 0.5f, .T_h = 0.7f,
        .core_coverage = 0.4f  // Below DEGRADED
    };

    // Safety-first: existing CONFIRMED may escalate to CRITICAL under UNKNOWN
    state_transition_t result = update_state(
        HAZARD_STATE_CONFIRMED, &intel, "READY",
        1000.0f, 0, NAN, &config, HAZARD_STATE_EPSILON
    );

    ASSERT_EQ(HAZARD_STATE_CRITICAL, result.new_state, "Transitions to CRITICAL (safety-first)");
    ASSERT_EQ(INFO_CONDITION_UNKNOWN, result.info_condition, "Info condition is UNKNOWN");
}

/**
 * Test 11: SUSPECTED → CRITICAL fast path
 */
void test_suspected_to_critical_fast_path(void)
{
    printf("\nTest 11: SUSPECTED → CRITICAL fast path\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.6f,
        .C_h = 0.5f,  // Above fast threshold (0.4) → DEGRADED
        .S_h = 0.92f,  // Above fast threshold (0.9)
        .R_h = 0.6f, .A_h = 0.5f,
        .T_h = 0.85f,  // Above fast threshold (0.8)
        .core_coverage = 0.6f  // Above fast threshold (0.5)
    };

    // Immediate transition (persistence = 1)
    state_transition_t result = update_state(
        HAZARD_STATE_SUSPECTED, &intel, "READY",
        1000.0f, 0, NAN, &config, HAZARD_STATE_EPSILON
    );

    ASSERT_EQ(HAZARD_STATE_CRITICAL, result.new_state, "Transitions to CRITICAL (fast path)");
    ASSERT_TRUE(strstr(result.reason, "fast path") != NULL, "Reason contains 'fast path'");
}

/**
 * Test 12: SUSPECTED → CRITICAL fast path blocked by UNKNOWN
 */
void test_suspected_fast_critical_blocked_unknown(void)
{
    printf("\nTest 12: SUSPECTED → CRITICAL fast path blocked by UNKNOWN\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.6f,
        .C_h = 0.3f,  // Below 0.4 → UNKNOWN
        .S_h = 0.92f,
        .R_h = 0.6f, .A_h = 0.5f,
        .T_h = 0.85f,
        .core_coverage = 0.6f
    };

    state_transition_t result = update_state(
        HAZARD_STATE_SUSPECTED, &intel, "READY",
        1000.0f, 5, NAN, &config, HAZARD_STATE_EPSILON
    );

    ASSERT_EQ(HAZARD_STATE_SUSPECTED, result.new_state, "Fast path blocked by UNKNOWN");
}

/**
 * Test 13: CRITICAL → RESOLVED
 */
void test_critical_to_resolved(void)
{
    printf("\nTest 13: CRITICAL → RESOLVED\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.15f,  // Below resolved max (0.2)
        .C_h = 0.7f,
        .S_h = 0.4f,
        .R_h = 0.15f,  // Below resolved max (0.2)
        .A_h = 0.3f, .T_h = 0.3f,
        .core_coverage = 0.8f
    };

    // Need 10 samples (resolved_enter_persistence = 10)
    state_transition_t result;
    for (int i = 0; i < 9; i++) {
        result = update_state(
            HAZARD_STATE_CRITICAL, &intel, "READY",
            1000.0f + i, i, NAN, &config, HAZARD_STATE_EPSILON
        );
        ASSERT_EQ(HAZARD_STATE_CRITICAL, result.new_state, "Still CRITICAL");
    }

    // 10th sample: transition
    result = update_state(
        HAZARD_STATE_CRITICAL, &intel, "READY",
        1009.0f, 9, NAN, &config, HAZARD_STATE_EPSILON
    );
    ASSERT_EQ(HAZARD_STATE_RESOLVED, result.new_state, "Transitions to RESOLVED");
    ASSERT_TRUE(is_valid(result.resolved_hold_start), "RESOLVED hold start set");
}

/**
 * Test 14: RESOLVED → NORMAL after hold
 */
void test_resolved_to_normal(void)
{
    printf("\nTest 14: RESOLVED → NORMAL after hold\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.1f, .C_h = 0.7f, .S_h = 0.1f,
        .R_h = 0.1f, .A_h = 0.3f, .T_h = 0.1f,
        .core_coverage = 0.8f
    };

    float hold_start = 1000.0f;
    float hold_complete = hold_start + config.resolved_hold_seconds + 1.0f;

    state_transition_t result = update_state(
        HAZARD_STATE_RESOLVED, &intel, "READY",
        hold_complete, 0, hold_start, &config, HAZARD_STATE_EPSILON
    );

    ASSERT_EQ(HAZARD_STATE_NORMAL, result.new_state, "Transitions to NORMAL after hold");
}

/**
 * Test 15: Information condition - GOOD
 */
void test_info_condition_good(void)
{
    printf("\nTest 15: Information condition - GOOD\n");

    state_machine_config_t config = state_machine_default_config();

    information_condition_t cond = compute_information_condition(
        0.75f,  // >= 0.7
        0.85f,  // >= 0.8
        "READY",
        &config,
        HAZARD_STATE_EPSILON
    );

    ASSERT_EQ(INFO_CONDITION_GOOD, cond, "Info condition is GOOD");
}

/**
 * Test 16: Information condition - DEGRADED
 */
void test_info_condition_degraded(void)
{
    printf("\nTest 16: Information condition - DEGRADED\n");

    state_machine_config_t config = state_machine_default_config();

    information_condition_t cond = compute_information_condition(
        0.55f,  // 0.4 <= C_h < 0.7
        0.85f,
        "READY",
        &config,
        HAZARD_STATE_EPSILON
    );

    ASSERT_EQ(INFO_CONDITION_DEGRADED, cond, "Info condition is DEGRADED");
}

/**
 * Test 17: Information condition - UNKNOWN (low confidence)
 */
void test_info_condition_unknown_confidence(void)
{
    printf("\nTest 17: Information condition - UNKNOWN (low confidence)\n");

    state_machine_config_t config = state_machine_default_config();

    information_condition_t cond = compute_information_condition(
        0.35f,  // < 0.4
        0.85f,
        "READY",
        &config,
        HAZARD_STATE_EPSILON
    );

    ASSERT_EQ(INFO_CONDITION_UNKNOWN, cond, "Info condition is UNKNOWN");
}

/**
 * Test 18: Information condition - UNKNOWN (baseline INITIALIZING)
 */
void test_info_condition_unknown_baseline(void)
{
    printf("\nTest 18: Information condition - UNKNOWN (baseline INITIALIZING)\n");

    state_machine_config_t config = state_machine_default_config();

    information_condition_t cond = compute_information_condition(
        0.75f,
        0.85f,
        "INITIALIZING",  // Baseline not ready
        &config,
        HAZARD_STATE_EPSILON
    );

    ASSERT_EQ(INFO_CONDITION_UNKNOWN, cond, "Info condition is UNKNOWN (baseline)");
}

/**
 * Test 19: Baseline freeze - CONFIRMED
 */
void test_baseline_freeze_confirmed(void)
{
    printf("\nTest 19: Baseline freeze - CONFIRMED\n");

    ASSERT_TRUE(should_freeze_baseline(HAZARD_STATE_CONFIRMED), "Freeze at CONFIRMED");
}

/**
 * Test 20: Baseline freeze - CRITICAL
 */
void test_baseline_freeze_critical(void)
{
    printf("\nTest 20: Baseline freeze - CRITICAL\n");

    ASSERT_TRUE(should_freeze_baseline(HAZARD_STATE_CRITICAL), "Freeze at CRITICAL");
}

/**
 * Test 21: Baseline no freeze - WATCH
 */
void test_baseline_no_freeze_watch(void)
{
    printf("\nTest 21: Baseline no freeze - WATCH\n");

    ASSERT_FALSE(should_freeze_baseline(HAZARD_STATE_WATCH), "No freeze at WATCH");
}

/**
 * Test 22: Validate config - valid
 */
void test_validate_config_valid(void)
{
    printf("\nTest 22: Validate config - valid\n");

    state_machine_config_t config = state_machine_default_config();
    bool valid = validate_state_machine_config(&config, HAZARD_STATE_EPSILON);

    ASSERT_TRUE(valid, "Default config is valid");
}

/**
 * Test 23: Validate config - invalid hysteresis
 */
void test_validate_config_invalid_hysteresis(void)
{
    printf("\nTest 23: Validate config - invalid hysteresis\n");

    state_machine_config_t config = state_machine_default_config();
    config.watch_risk_enter = 0.25f;  // Same as exit (no hysteresis)

    bool valid = validate_state_machine_config(&config, HAZARD_STATE_EPSILON);

    ASSERT_FALSE(valid, "Invalid hysteresis rejected");
}

/**
 * Test 24: Persistence counter reset
 */
void test_persistence_counter_reset(void)
{
    printf("\nTest 24: Persistence counter reset\n");

    state_machine_config_t config = state_machine_default_config();
    intelligence_inputs_t intel = {
        .E_h = 0.45f,  // Above suspected threshold
        .C_h = 0.8f, .S_h = 0.5f,
        .R_h = 0.35f, .A_h = 0.55f, .T_h = 0.5f,
        .core_coverage = 0.9f
    };

    // Sample 1: counter = 0 → 1
    state_transition_t result = update_state(
        HAZARD_STATE_WATCH, &intel, "READY",
        1000.0f, 0, NAN, &config, HAZARD_STATE_EPSILON
    );
    ASSERT_EQ(1, result.persistence_counter, "Counter = 1");

    // Sample 2: evidence drops, counter resets
    intel.E_h = 0.3f;  // Below suspected threshold
    result = update_state(
        HAZARD_STATE_WATCH, &intel, "READY",
        1001.0f, 1, NAN, &config, HAZARD_STATE_EPSILON
    );
    ASSERT_EQ(0, result.persistence_counter, "Counter reset to 0");
}

/**
 * Main test runner
 */
int main(void)
{
    printf("=== Hazard State Machine Reference Parity Tests ===\n");
    printf("Reference: reference/python/nexalert_reference/state_machine.py\n");

    // Initial state
    test_initial_state();

    // NORMAL transitions
    test_normal_to_watch_via_risk();
    test_normal_to_watch_via_anomaly();

    // WATCH transitions
    test_watch_to_suspected();
    test_watch_to_confirmed_fast_path();
    test_watch_fast_path_blocked_by_unknown();

    // SUSPECTED transitions
    test_suspected_to_confirmed();
    test_suspected_to_confirmed_blocked_unknown();
    test_suspected_to_critical_fast_path();
    test_suspected_fast_critical_blocked_unknown();

    // CONFIRMED transitions
    test_confirmed_to_critical();
    test_confirmed_to_critical_under_unknown();

    // CRITICAL transitions
    test_critical_to_resolved();

    // RESOLVED transitions
    test_resolved_to_normal();

    // Information condition
    test_info_condition_good();
    test_info_condition_degraded();
    test_info_condition_unknown_confidence();
    test_info_condition_unknown_baseline();

    // Baseline freeze
    test_baseline_freeze_confirmed();
    test_baseline_freeze_critical();
    test_baseline_no_freeze_watch();

    // Configuration validation
    test_validate_config_valid();
    test_validate_config_invalid_hysteresis();

    // Persistence behavior
    test_persistence_counter_reset();

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
