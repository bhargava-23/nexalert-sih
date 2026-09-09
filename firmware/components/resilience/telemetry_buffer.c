/**
 * @file telemetry_buffer.c
 * @brief Bounded local buffer implementation for offline telemetry
 *
 * CRITICAL INVARIANT: Network failure != Edge intelligence failure
 */

#include "telemetry_buffer.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include <string.h>
#include <stdlib.h>

static const char *TAG = "telem_buffer";

// Maximum JSON payload size (generous for telemetry envelope)
#define MAX_PAYLOAD_SIZE 2048

/**
 * Buffered message entry
 */
typedef struct {
    char payload[MAX_PAYLOAD_SIZE];
    message_metadata_t metadata;
    bool occupied;
} buffer_entry_t;

/**
 * Buffer state
 */
static struct {
    bool initialized;
    buffer_entry_t* entries;     // Circular buffer array
    uint16_t capacity;           // Maximum entries
    uint16_t head;               // Write index
    uint16_t tail;               // Read index
    uint16_t count;              // Current count
    buffer_stats_t stats;        // Statistics
    SemaphoreHandle_t mutex;     // Thread safety
} buffer_state = {0};

esp_err_t telemetry_buffer_init(const buffer_config_t* config)
{
    if (buffer_state.initialized) {
        ESP_LOGW(TAG, "Buffer already initialized");
        return ESP_ERR_INVALID_STATE;
    }

    uint16_t capacity = (config != NULL && config->capacity > 0) ?
                        config->capacity : TELEMETRY_BUFFER_DEFAULT_CAPACITY;

    // Allocate buffer array
    buffer_state.entries = calloc(capacity, sizeof(buffer_entry_t));
    if (buffer_state.entries == NULL) {
        ESP_LOGE(TAG, "Failed to allocate buffer (%u entries)", capacity);
        return ESP_ERR_NO_MEM;
    }

    // Create mutex
    buffer_state.mutex = xSemaphoreCreateMutex();
    if (buffer_state.mutex == NULL) {
        free(buffer_state.entries);
        ESP_LOGE(TAG, "Failed to create mutex");
        return ESP_ERR_NO_MEM;
    }

    buffer_state.capacity = capacity;
    buffer_state.head = 0;
    buffer_state.tail = 0;
    buffer_state.count = 0;
    memset(&buffer_state.stats, 0, sizeof(buffer_stats_t));
    buffer_state.stats.capacity = capacity;
    buffer_state.initialized = true;

    ESP_LOGI(TAG, "Buffer initialized, capacity=%u entries (%u KB)",
             capacity, (capacity * sizeof(buffer_entry_t)) / 1024);

    return ESP_OK;
}

/**
 * Find oldest NORMAL priority message for eviction
 * Returns index, or -1 if none found
 */
static int find_oldest_normal(void)
{
    // Scan from tail (oldest) toward head (newest)
    uint16_t idx = buffer_state.tail;
    for (uint16_t i = 0; i < buffer_state.count; i++) {
        if (buffer_state.entries[idx].occupied &&
            buffer_state.entries[idx].metadata.priority == PRIORITY_NORMAL) {
            return idx;
        }
        idx = (idx + 1) % buffer_state.capacity;
    }
    return -1;
}

/**
 * Remove entry at index (does not update head/tail/count)
 */
static void remove_entry_at(uint16_t idx)
{
    buffer_state.entries[idx].occupied = false;
    buffer_state.stats.total_dropped++;

    message_priority_t pri = buffer_state.entries[idx].metadata.priority;
    if (pri == PRIORITY_NORMAL) {
        buffer_state.stats.dropped_normal++;
    } else if (pri == PRIORITY_HAZARD) {
        buffer_state.stats.dropped_hazard++;
    }
}

esp_err_t telemetry_buffer_enqueue(
    const char* json_payload,
    uint32_t sequence,
    message_priority_t priority
)
{
    if (!buffer_state.initialized || json_payload == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    size_t payload_len = strlen(json_payload);
    if (payload_len >= MAX_PAYLOAD_SIZE) {
        ESP_LOGE(TAG, "Payload too large: %u bytes (max %u)", payload_len, MAX_PAYLOAD_SIZE);
        return ESP_ERR_INVALID_SIZE;
    }

    xSemaphoreTake(buffer_state.mutex, portMAX_DELAY);

    // Handle overflow
    if (buffer_state.count >= buffer_state.capacity) {
        if (priority == PRIORITY_CRITICAL) {
            // CRITICAL never dropped, drop oldest NORMAL
            int victim_idx = find_oldest_normal();
            if (victim_idx >= 0) {
                remove_entry_at(victim_idx);
                buffer_state.count--;
                ESP_LOGW(TAG, "Buffer full, dropped NORMAL for CRITICAL (seq=%lu)", sequence);
            } else {
                // No NORMAL to drop, fail
                xSemaphoreGive(buffer_state.mutex);
                ESP_LOGE(TAG, "Buffer full, no NORMAL to drop for CRITICAL");
                return ESP_ERR_NO_MEM;
            }
        } else if (priority == PRIORITY_HAZARD) {
            // HAZARD drops oldest NORMAL if available
            int victim_idx = find_oldest_normal();
            if (victim_idx >= 0) {
                remove_entry_at(victim_idx);
                buffer_state.count--;
                ESP_LOGW(TAG, "Buffer full, dropped NORMAL for HAZARD (seq=%lu)", sequence);
            } else {
                // No NORMAL, drop self
                buffer_state.stats.total_dropped++;
                buffer_state.stats.dropped_hazard++;
                xSemaphoreGive(buffer_state.mutex);
                ESP_LOGW(TAG, "Buffer full, dropped HAZARD (seq=%lu)", sequence);
                return ESP_ERR_NO_MEM;
            }
        } else {
            // NORMAL: drop oldest NORMAL (FIFO)
            int victim_idx = find_oldest_normal();
            if (victim_idx >= 0) {
                remove_entry_at(victim_idx);
                buffer_state.count--;
            } else {
                // All HAZARD/CRITICAL, drop self
                buffer_state.stats.total_dropped++;
                buffer_state.stats.dropped_normal++;
                xSemaphoreGive(buffer_state.mutex);
                ESP_LOGD(TAG, "Buffer full, dropped NORMAL (seq=%lu)", sequence);
                return ESP_ERR_NO_MEM;
            }
        }
    }

    // Enqueue at head
    buffer_entry_t* entry = &buffer_state.entries[buffer_state.head];
    strncpy(entry->payload, json_payload, MAX_PAYLOAD_SIZE - 1);
    entry->payload[MAX_PAYLOAD_SIZE - 1] = '\0';
    entry->metadata.sequence = sequence;
    entry->metadata.timestamp_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;
    entry->metadata.priority = priority;
    entry->metadata.payload_len = payload_len;
    entry->occupied = true;

    buffer_state.head = (buffer_state.head + 1) % buffer_state.capacity;
    buffer_state.count++;
    buffer_state.stats.total_enqueued++;
    buffer_state.stats.count = buffer_state.count;

    xSemaphoreGive(buffer_state.mutex);

    ESP_LOGD(TAG, "Enqueued seq=%lu, priority=%d, count=%u/%u",
             sequence, priority, buffer_state.count, buffer_state.capacity);

    return ESP_OK;
}

esp_err_t telemetry_buffer_peek(
    char* out_payload,
    message_metadata_t* out_metadata,
    size_t max_len
)
{
    if (!buffer_state.initialized || out_payload == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    xSemaphoreTake(buffer_state.mutex, portMAX_DELAY);

    if (buffer_state.count == 0) {
        xSemaphoreGive(buffer_state.mutex);
        return ESP_ERR_NOT_FOUND;
    }

    buffer_entry_t* entry = &buffer_state.entries[buffer_state.tail];
    if (!entry->occupied) {
        xSemaphoreGive(buffer_state.mutex);
        ESP_LOGE(TAG, "Tail entry not occupied (corruption?)");
        return ESP_FAIL;
    }

    strncpy(out_payload, entry->payload, max_len - 1);
    out_payload[max_len - 1] = '\0';

    if (out_metadata != NULL) {
        memcpy(out_metadata, &entry->metadata, sizeof(message_metadata_t));
    }

    xSemaphoreGive(buffer_state.mutex);
    return ESP_OK;
}

esp_err_t telemetry_buffer_dequeue(
    char* out_payload,
    message_metadata_t* out_metadata,
    size_t max_len
)
{
    if (!buffer_state.initialized || out_payload == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    xSemaphoreTake(buffer_state.mutex, portMAX_DELAY);

    if (buffer_state.count == 0) {
        xSemaphoreGive(buffer_state.mutex);
        return ESP_ERR_NOT_FOUND;
    }

    buffer_entry_t* entry = &buffer_state.entries[buffer_state.tail];
    if (!entry->occupied) {
        xSemaphoreGive(buffer_state.mutex);
        ESP_LOGE(TAG, "Tail entry not occupied (corruption?)");
        return ESP_FAIL;
    }

    strncpy(out_payload, entry->payload, max_len - 1);
    out_payload[max_len - 1] = '\0';

    if (out_metadata != NULL) {
        memcpy(out_metadata, &entry->metadata, sizeof(message_metadata_t));
    }

    entry->occupied = false;
    buffer_state.tail = (buffer_state.tail + 1) % buffer_state.capacity;
    buffer_state.count--;
    buffer_state.stats.total_dequeued++;
    buffer_state.stats.count = buffer_state.count;

    xSemaphoreGive(buffer_state.mutex);

    ESP_LOGD(TAG, "Dequeued seq=%lu, count=%u/%u",
             out_metadata ? out_metadata->sequence : 0,
             buffer_state.count, buffer_state.capacity);

    return ESP_OK;
}

esp_err_t telemetry_buffer_clear(void)
{
    if (!buffer_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    xSemaphoreTake(buffer_state.mutex, portMAX_DELAY);

    for (uint16_t i = 0; i < buffer_state.capacity; i++) {
        buffer_state.entries[i].occupied = false;
    }

    buffer_state.head = 0;
    buffer_state.tail = 0;
    buffer_state.count = 0;
    buffer_state.stats.count = 0;

    xSemaphoreGive(buffer_state.mutex);

    ESP_LOGI(TAG, "Buffer cleared");
    return ESP_OK;
}

esp_err_t telemetry_buffer_get_stats(buffer_stats_t* out_stats)
{
    if (!buffer_state.initialized || out_stats == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    xSemaphoreTake(buffer_state.mutex, portMAX_DELAY);
    memcpy(out_stats, &buffer_state.stats, sizeof(buffer_stats_t));
    out_stats->count = buffer_state.count;
    xSemaphoreGive(buffer_state.mutex);

    return ESP_OK;
}

bool telemetry_buffer_is_empty(void)
{
    if (!buffer_state.initialized) {
        return true;
    }

    xSemaphoreTake(buffer_state.mutex, portMAX_DELAY);
    bool empty = (buffer_state.count == 0);
    xSemaphoreGive(buffer_state.mutex);

    return empty;
}

bool telemetry_buffer_is_full(void)
{
    if (!buffer_state.initialized) {
        return false;
    }

    xSemaphoreTake(buffer_state.mutex, portMAX_DELAY);
    bool full = (buffer_state.count >= buffer_state.capacity);
    xSemaphoreGive(buffer_state.mutex);

    return full;
}

uint16_t telemetry_buffer_count(void)
{
    if (!buffer_state.initialized) {
        return 0;
    }

    xSemaphoreTake(buffer_state.mutex, portMAX_DELAY);
    uint16_t count = buffer_state.count;
    xSemaphoreGive(buffer_state.mutex);

    return count;
}

esp_err_t telemetry_buffer_deinit(void)
{
    if (!buffer_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    if (buffer_state.mutex != NULL) {
        vSemaphoreDelete(buffer_state.mutex);
    }

    if (buffer_state.entries != NULL) {
        free(buffer_state.entries);
    }

    memset(&buffer_state, 0, sizeof(buffer_state));
    ESP_LOGI(TAG, "Buffer deinitialized");

    return ESP_OK;
}
