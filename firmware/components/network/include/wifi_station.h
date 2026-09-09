/**
 * @file wifi_station.h
 * @brief Wi-Fi station mode for NexAlert nodes
 *
 * Connects to local Wi-Fi network to reach Raspberry Pi MQTT broker.
 */

#ifndef NEXALERT_WIFI_STATION_H
#define NEXALERT_WIFI_STATION_H

#include "esp_err.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Wi-Fi configuration (NexAlert-specific, avoids ESP-IDF wifi_config_t collision)
 */
typedef struct {
    const char* ssid;            // Wi-Fi SSID
    const char* password;        // Wi-Fi password
} nexalert_wifi_config_t;

/**
 * Initialize Wi-Fi station mode and connect
 *
 * @param config Wi-Fi configuration
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t wifi_station_init(const nexalert_wifi_config_t* config);

/**
 * Check if Wi-Fi is connected
 *
 * @return true if connected, false otherwise
 */
bool wifi_is_connected(void);

/**
 * Get IP address
 *
 * @param ip_str Output buffer for IP address string (min 16 bytes)
 * @return ESP_OK if connected and IP available
 */
esp_err_t wifi_get_ip(char* ip_str, size_t len);

/**
 * Deinitialize Wi-Fi station
 *
 * @return ESP_OK on success
 */
esp_err_t wifi_station_deinit(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_WIFI_STATION_H
