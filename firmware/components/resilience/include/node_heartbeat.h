/**
 * @file node_heartbeat.h
 * @brief Lightweight heartbeat and node health reporting
 *
 * Allows coordinator to distinguish:
 * - Healthy node
 * - Stale node
 * - Disconnected node
 * - Degraded sensor
 * - Missing/invalid measurement
 *
 * CRITICAL INVARIANT: No telemetry != Environment normal
 */

#ifndef NEXALERT_NODE_HEARTBEAT_H
#define NEXALERT_NODE_HEARTBEAT_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Node health status
 */
typedef struct {
    uint32_t uptime_s;               // Uptime in seconds
    bool self_test_passed;           // Self-test result
    bool calibration_valid;          // Calibration validity
    bool mqtt_connected;             // MQTT connection status
    uint32_t last_publish_ms;        // Last successful publish timestamp (millis)
    uint16_t buffer_depth;           // Current buffer depth
    uint16_t buffer_capacity;        // Buffer capacity
    uint32_t total_samples;          // Total samples collected
    uint32_t failed_samples;         // Failed sample attempts
    float battery_pct;               // Battery percentage (NAN if unavailable)
    float comm_integrity;            // Communication integrity [0,1] (NAN if unavailable)
} node_health_t;

/**
 * Heartbeat configuration
 */
typedef struct {
    uint32_t interval_ms;            // Heartbeat interval (milliseconds)
    bool enabled;                    // Heartbeat enabled
} heartbeat_config_t;

/**
 * Initialize heartbeat module
 *
 * @param config Heartbeat configuration
 * @return ESP_OK on success
 */
esp_err_t node_heartbeat_init(const heartbeat_config_t* config);

/**
 * Update node health status
 *
 * Should be called periodically to update health metrics.
 *
 * @param health Current node health
 * @return ESP_OK on success
 */
esp_err_t node_heartbeat_update(const node_health_t* health);

/**
 * Generate heartbeat JSON message
 *
 * Returns lightweight heartbeat message with node health status.
 * Includes freshness timestamp to allow coordinator to detect staleness.
 *
 * @param out_json Output JSON string (caller must free with free())
 * @return ESP_OK on success, ESP_ERR_NO_MEM if allocation fails
 */
esp_err_t node_heartbeat_generate(char** out_json);

/**
 * Check if heartbeat is due
 *
 * @return true if heartbeat should be sent, false otherwise
 */
bool node_heartbeat_is_due(void);

/**
 * Reset heartbeat timer (call after successful heartbeat publish)
 *
 * @return ESP_OK on success
 */
esp_err_t node_heartbeat_reset_timer(void);

/**
 * Deinitialize heartbeat module
 *
 * @return ESP_OK on success
 */
esp_err_t node_heartbeat_deinit(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_NODE_HEARTBEAT_H
