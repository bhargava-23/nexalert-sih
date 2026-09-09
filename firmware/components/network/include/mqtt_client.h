/**
 * @file mqtt_client.h
 * @brief MQTT publisher for NexAlert telemetry
 *
 * Publishes telemetry envelopes to local Mosquitto broker on Raspberry Pi.
 * Topic: Nexalert/telemetry/node1 (locked format)
 * QoS: 1 (at least once delivery)
 */

#ifndef NEXALERT_MQTT_CLIENT_H
#define NEXALERT_MQTT_CLIENT_H

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * MQTT configuration
 */
typedef struct {
    const char* broker_host;     // MQTT broker hostname/IP
    uint16_t broker_port;        // MQTT broker port (default 1883)
    const char* node_id;         // Node ID for topic generation
} mqtt_config_t;

/**
 * Initialize MQTT client
 *
 * @param config MQTT configuration
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t mqtt_client_init(const mqtt_config_t* config);

/**
 * Publish telemetry JSON to MQTT
 *
 * Topic: Nexalert/telemetry/node1 (locked format)
 * QoS: 1 (at least once delivery)
 *
 * @param json_payload Telemetry envelope JSON string
 * @return ESP_OK on success, ESP_FAIL if not connected
 */
esp_err_t mqtt_publish_telemetry(const char* json_payload);

/**
 * Check if MQTT client is connected
 *
 * @return true if connected, false otherwise
 */
bool mqtt_is_connected(void);

/**
 * Deinitialize MQTT client
 *
 * @return ESP_OK on success
 */
esp_err_t mqtt_client_deinit(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_MQTT_CLIENT_H
