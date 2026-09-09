/**
 * @file telemetry_buffer.h
 * @brief Bounded local buffer for telemetry when MQTT/Wi-Fi unavailable
 *
 * CRITICAL INVARIANT: Network failure != Edge intelligence failure
 * The node continues sensing and evaluating intelligence while disconnected.
 *
 * Design:
 * - Bounded capacity (no unbounded malloc)
 * - Deterministic memory usage
 * - FIFO behavior with explicit overflow handling
 * - Sequence preservation for replay
 * - Priority handling for critical hazard events
 */

#ifndef NEXALERT_TELEMETRY_BUFFER_H
#define NEXALERT_TELEMETRY_BUFFER_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

// Buffer capacity (configurable via node_config)
#define TELEMETRY_BUFFER_DEFAULT_CAPACITY 100

/**
 * Message priority for overflow handling
 */
typedef enum {
    PRIORITY_NORMAL = 0,      // Regular telemetry
    PRIORITY_HAZARD = 1,      // Hazard state transition (WATCH+)
    PRIORITY_CRITICAL = 2,    // Critical hazard (CRITICAL state)
} message_priority_t;

/**
 * Buffered message metadata
 */
typedef struct {
    uint32_t sequence;           // Telemetry sequence number
    uint32_t timestamp_ms;       // Local timestamp (millis since boot)
    message_priority_t priority; // Message priority
    uint16_t payload_len;        // JSON payload length
} message_metadata_t;

/**
 * Buffer configuration
 */
typedef struct {
    uint16_t capacity;           // Maximum buffered messages (bounded)
} buffer_config_t;

/**
 * Buffer statistics
 */
typedef struct {
    uint16_t count;              // Current buffered count
    uint16_t capacity;           // Maximum capacity
    uint32_t total_enqueued;     // Total messages enqueued (lifetime)
    uint32_t total_dequeued;     // Total messages dequeued (lifetime)
    uint32_t total_dropped;      // Total messages dropped due to overflow
    uint32_t dropped_normal;     // Normal priority dropped
    uint32_t dropped_hazard;     // Hazard priority dropped
} buffer_stats_t;

/**
 * Initialize telemetry buffer
 *
 * @param config Buffer configuration (NULL = default)
 * @return ESP_OK on success, ESP_ERR_NO_MEM if allocation fails
 */
esp_err_t telemetry_buffer_init(const buffer_config_t* config);

/**
 * Enqueue telemetry message
 *
 * Overflow behavior:
 * - PRIORITY_CRITICAL: Never dropped, always enqueued (oldest NORMAL dropped if full)
 * - PRIORITY_HAZARD: Drop oldest NORMAL if full, drop self if no NORMAL available
 * - PRIORITY_NORMAL: Drop oldest NORMAL if full (FIFO)
 *
 * @param json_payload JSON telemetry envelope (copied into buffer)
 * @param sequence Telemetry sequence number
 * @param priority Message priority
 * @return ESP_OK on success, ESP_ERR_NO_MEM if buffer full and cannot drop
 */
esp_err_t telemetry_buffer_enqueue(
    const char* json_payload,
    uint32_t sequence,
    message_priority_t priority
);

/**
 * Peek oldest message without removing
 *
 * @param out_payload Output buffer for JSON (must be >= max message size)
 * @param out_metadata Output message metadata
 * @param max_len Maximum output buffer length
 * @return ESP_OK on success, ESP_ERR_NOT_FOUND if buffer empty
 */
esp_err_t telemetry_buffer_peek(
    char* out_payload,
    message_metadata_t* out_metadata,
    size_t max_len
);

/**
 * Dequeue oldest message (removes from buffer)
 *
 * @param out_payload Output buffer for JSON
 * @param out_metadata Output message metadata
 * @param max_len Maximum output buffer length
 * @return ESP_OK on success, ESP_ERR_NOT_FOUND if buffer empty
 */
esp_err_t telemetry_buffer_dequeue(
    char* out_payload,
    message_metadata_t* out_metadata,
    size_t max_len
);

/**
 * Clear all buffered messages
 *
 * @return ESP_OK on success
 */
esp_err_t telemetry_buffer_clear(void);

/**
 * Get buffer statistics
 *
 * @param out_stats Output statistics
 * @return ESP_OK on success
 */
esp_err_t telemetry_buffer_get_stats(buffer_stats_t* out_stats);

/**
 * Check if buffer is empty
 *
 * @return true if empty, false otherwise
 */
bool telemetry_buffer_is_empty(void);

/**
 * Check if buffer is full
 *
 * @return true if full, false otherwise
 */
bool telemetry_buffer_is_full(void);

/**
 * Get current buffer depth
 *
 * @return Number of buffered messages
 */
uint16_t telemetry_buffer_count(void);

/**
 * Deinitialize buffer and free resources
 *
 * @return ESP_OK on success
 */
esp_err_t telemetry_buffer_deinit(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_TELEMETRY_BUFFER_H
