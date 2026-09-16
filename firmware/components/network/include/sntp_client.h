/**
 * @file sntp_client.h
 * @brief SNTP/NTP client for NexAlert ESP32 nodes
 *
 * Track 3A: Synchronizes wall-clock time from field NTP server.
 *
 * Locked NTP server: 10.42.0.1 (Raspberry Pi field controller)
 */

#ifndef NEXALERT_SNTP_CLIENT_H
#define NEXALERT_SNTP_CLIENT_H

#include "esp_err.h"
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * SNTP configuration
 */
typedef struct {
    const char* ntp_server;      // NTP server hostname/IP (Track 3A: "10.42.0.1")
    uint32_t sync_timeout_ms;    // Synchronization timeout (default 10000ms)
} sntp_config_t;

/**
 * Initialize and start SNTP client
 *
 * Starts SNTP synchronization with the configured NTP server.
 * Does NOT block waiting for sync - call sntp_wait_for_sync() or sntp_is_synced() to check.
 *
 * @param config SNTP configuration
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t sntp_client_init(const sntp_config_t* config);

/**
 * Wait for SNTP synchronization to complete
 *
 * Blocks until time is synchronized or timeout expires.
 *
 * @param timeout_ms Maximum time to wait (milliseconds)
 * @return ESP_OK if synchronized, ESP_ERR_TIMEOUT if timeout expires
 */
esp_err_t sntp_wait_for_sync(uint32_t timeout_ms);

/**
 * Check if SNTP is synchronized
 *
 * @return true if time is synchronized, false otherwise
 */
bool sntp_is_synced(void);

/**
 * Get current Unix timestamp (milliseconds)
 *
 * Returns wall-clock time if synchronized, uptime-based fallback otherwise.
 *
 * @param is_wallclock Output: true if wall-clock, false if uptime fallback (may be NULL)
 * @return Unix timestamp in milliseconds
 */
int64_t sntp_get_timestamp_ms(bool* is_wallclock);

/**
 * Stop SNTP client
 *
 * @return ESP_OK on success
 */
esp_err_t sntp_client_deinit(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_SNTP_CLIENT_H
