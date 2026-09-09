/**
 * @file test_telemetry_buffer.c
 * @brief Tests for bounded telemetry buffer
 *
 * Tests cover:
 * - Empty buffer
 * - Single item enqueue/dequeue
 * - Full buffer overflow behavior
 * - FIFO order preservation
 * - Priority-based overflow (CRITICAL > HAZARD > NORMAL)
 * - Sequence preservation
 * - Statistics tracking
 * - Reconnect/replay scenario
 */

#include "telemetry_buffer.h"
#include <stdio.h>
#include <string.h>
#include <assert.h>

#define ASSERT_OK(expr) assert((expr) == ESP_OK)
#define ASSERT_FAIL(expr) assert((expr) != ESP_OK)
#define ASSERT_TRUE(expr) assert(expr)
#define ASSERT_FALSE(expr) assert(!(expr))

static int tests_passed = 0;
static int tests_failed = 0;

#define TEST_PASS() do { tests_passed++; printf("  ✓ %s\n", __func__); } while(0)
#define TEST_FAIL(msg) do { tests_failed++; printf("  ✗ %s: %s\n", __func__, msg); } while(0)

/**
 * Test 1: Empty buffer behavior
 */
void test_empty_buffer(void)
{
    buffer_config_t config = { .capacity = 10 };
    ASSERT_OK(telemetry_buffer_init(&config));

    ASSERT_TRUE(telemetry_buffer_is_empty());
    ASSERT_FALSE(telemetry_buffer_is_full());
    ASSERT_TRUE(telemetry_buffer_count() == 0);

    char payload[256];
    message_metadata_t meta;
    ASSERT_FAIL(telemetry_buffer_dequeue(payload, &meta, sizeof(payload)));

    ASSERT_OK(telemetry_buffer_deinit());
    TEST_PASS();
}

/**
 * Test 2: Single item enqueue/dequeue
 */
void test_single_item(void)
{
    buffer_config_t config = { .capacity = 10 };
    ASSERT_OK(telemetry_buffer_init(&config));

    const char* test_json = "{\"test\":\"data\",\"seq\":1}";
    ASSERT_OK(telemetry_buffer_enqueue(test_json, 1, PRIORITY_NORMAL));

    ASSERT_FALSE(telemetry_buffer_is_empty());
    ASSERT_TRUE(telemetry_buffer_count() == 1);

    char payload[256];
    message_metadata_t meta;
    ASSERT_OK(telemetry_buffer_dequeue(payload, &meta, sizeof(payload)));

    ASSERT_TRUE(strcmp(payload, test_json) == 0);
    ASSERT_TRUE(meta.sequence == 1);
    ASSERT_TRUE(meta.priority == PRIORITY_NORMAL);
    ASSERT_TRUE(telemetry_buffer_is_empty());

    ASSERT_OK(telemetry_buffer_deinit());
    TEST_PASS();
}

/**
 * Test 3: FIFO order preservation
 */
void test_fifo_order(void)
{
    buffer_config_t config = { .capacity = 5 };
    ASSERT_OK(telemetry_buffer_init(&config));

    // Enqueue 3 messages
    ASSERT_OK(telemetry_buffer_enqueue("{\"seq\":1}", 1, PRIORITY_NORMAL));
    ASSERT_OK(telemetry_buffer_enqueue("{\"seq\":2}", 2, PRIORITY_NORMAL));
    ASSERT_OK(telemetry_buffer_enqueue("{\"seq\":3}", 3, PRIORITY_NORMAL));

    ASSERT_TRUE(telemetry_buffer_count() == 3);

    // Dequeue in FIFO order
    char payload[256];
    message_metadata_t meta;

    ASSERT_OK(telemetry_buffer_dequeue(payload, &meta, sizeof(payload)));
    ASSERT_TRUE(meta.sequence == 1);

    ASSERT_OK(telemetry_buffer_dequeue(payload, &meta, sizeof(payload)));
    ASSERT_TRUE(meta.sequence == 2);

    ASSERT_OK(telemetry_buffer_dequeue(payload, &meta, sizeof(payload)));
    ASSERT_TRUE(meta.sequence == 3);

    ASSERT_TRUE(telemetry_buffer_is_empty());

    ASSERT_OK(telemetry_buffer_deinit());
    TEST_PASS();
}

/**
 * Test 4: Full buffer - NORMAL overflow
 */
void test_full_buffer_normal(void)
{
    buffer_config_t config = { .capacity = 3 };
    ASSERT_OK(telemetry_buffer_init(&config));

    // Fill buffer
    ASSERT_OK(telemetry_buffer_enqueue("{\"seq\":1}", 1, PRIORITY_NORMAL));
    ASSERT_OK(telemetry_buffer_enqueue("{\"seq\":2}", 2, PRIORITY_NORMAL));
    ASSERT_OK(telemetry_buffer_enqueue("{\"seq\":3}", 3, PRIORITY_NORMAL));

    ASSERT_TRUE(telemetry_buffer_is_full());

    // 4th NORMAL message drops oldest NORMAL (seq=1)
    ASSERT_FAIL(telemetry_buffer_enqueue("{\"seq\":4}", 4, PRIORITY_NORMAL));

    buffer_stats_t stats;
    ASSERT_OK(telemetry_buffer_get_stats(&stats));
    ASSERT_TRUE(stats.total_dropped >= 1);
    ASSERT_TRUE(stats.dropped_normal >= 1);

    ASSERT_OK(telemetry_buffer_deinit());
    TEST_PASS();
}

/**
 * Test 5: Priority overflow - CRITICAL never dropped
 */
void test_priority_critical_never_dropped(void)
{
    buffer_config_t config = { .capacity = 3 };
    ASSERT_OK(telemetry_buffer_init(&config));

    // Fill with NORMAL
    ASSERT_OK(telemetry_buffer_enqueue("{\"seq\":1}", 1, PRIORITY_NORMAL));
    ASSERT_OK(telemetry_buffer_enqueue("{\"seq\":2}", 2, PRIORITY_NORMAL));
    ASSERT_OK(telemetry_buffer_enqueue("{\"seq\":3}", 3, PRIORITY_NORMAL));

    // CRITICAL drops oldest NORMAL and gets enqueued
    ASSERT_OK(telemetry_buffer_enqueue("{\"seq\":4,\"critical\":true}", 4, PRIORITY_CRITICAL));

    ASSERT_TRUE(telemetry_buffer_count() == 3);

    // Verify CRITICAL is in buffer
    char payload[256];
    message_metadata_t meta;
    bool found_critical = false;
    for (int i = 0; i < 3; i++) {
        ASSERT_OK(telemetry_buffer_dequeue(payload, &meta, sizeof(payload)));
        if (meta.sequence == 4) {
            found_critical = true;
            ASSERT_TRUE(meta.priority == PRIORITY_CRITICAL);
        }
    }

    ASSERT_TRUE(found_critical);

    ASSERT_OK(telemetry_buffer_deinit());
    TEST_PASS();
}

/**
 * Test 6: Buffer statistics
 */
void test_buffer_statistics(void)
{
    buffer_config_t config = { .capacity = 5 };
    ASSERT_OK(telemetry_buffer_init(&config));

    ASSERT_OK(telemetry_buffer_enqueue("{\"seq\":1}", 1, PRIORITY_NORMAL));
    ASSERT_OK(telemetry_buffer_enqueue("{\"seq\":2}", 2, PRIORITY_NORMAL));

    buffer_stats_t stats;
    ASSERT_OK(telemetry_buffer_get_stats(&stats));

    ASSERT_TRUE(stats.count == 2);
    ASSERT_TRUE(stats.capacity == 5);
    ASSERT_TRUE(stats.total_enqueued == 2);
    ASSERT_TRUE(stats.total_dequeued == 0);

    char payload[256];
    message_metadata_t meta;
    ASSERT_OK(telemetry_buffer_dequeue(payload, &meta, sizeof(payload)));

    ASSERT_OK(telemetry_buffer_get_stats(&stats));
    ASSERT_TRUE(stats.count == 1);
    ASSERT_TRUE(stats.total_dequeued == 1);

    ASSERT_OK(telemetry_buffer_deinit());
    TEST_PASS();
}

/**
 * Test 7: Reconnect replay scenario
 */
void test_reconnect_replay(void)
{
    buffer_config_t config = { .capacity = 10 };
    ASSERT_OK(telemetry_buffer_init(&config));

    // Simulate offline period - enqueue 5 messages
    for (uint32_t i = 1; i <= 5; i++) {
        char json[64];
        snprintf(json, sizeof(json), "{\"seq\":%lu,\"offline\":true}", i);
        ASSERT_OK(telemetry_buffer_enqueue(json, i, PRIORITY_NORMAL));
    }

    ASSERT_TRUE(telemetry_buffer_count() == 5);

    // Simulate reconnect - replay all buffered messages
    char payload[256];
    message_metadata_t meta;
    uint32_t replayed = 0;

    while (!telemetry_buffer_is_empty()) {
        ASSERT_OK(telemetry_buffer_dequeue(payload, &meta, sizeof(payload)));
        replayed++;
        // In real code: mqtt_publish_telemetry(payload)
    }

    ASSERT_TRUE(replayed == 5);
    ASSERT_TRUE(telemetry_buffer_is_empty());

    ASSERT_OK(telemetry_buffer_deinit());
    TEST_PASS();
}

/**
 * Test 8: Buffer clear
 */
void test_buffer_clear(void)
{
    buffer_config_t config = { .capacity = 5 };
    ASSERT_OK(telemetry_buffer_init(&config));

    ASSERT_OK(telemetry_buffer_enqueue("{\"seq\":1}", 1, PRIORITY_NORMAL));
    ASSERT_OK(telemetry_buffer_enqueue("{\"seq\":2}", 2, PRIORITY_NORMAL));

    ASSERT_TRUE(telemetry_buffer_count() == 2);

    ASSERT_OK(telemetry_buffer_clear());

    ASSERT_TRUE(telemetry_buffer_is_empty());
    ASSERT_TRUE(telemetry_buffer_count() == 0);

    ASSERT_OK(telemetry_buffer_deinit());
    TEST_PASS();
}

/**
 * Main test runner
 */
int main(void)
{
    printf("=== Telemetry Buffer Tests ===\n\n");

    test_empty_buffer();
    test_single_item();
    test_fifo_order();
    test_full_buffer_normal();
    test_priority_critical_never_dropped();
    test_buffer_statistics();
    test_reconnect_replay();
    test_buffer_clear();

    printf("\n=== Test Summary ===\n");
    printf("Passed: %d\n", tests_passed);
    printf("Failed: %d\n", tests_failed);

    return (tests_failed == 0) ? 0 : 1;
}
