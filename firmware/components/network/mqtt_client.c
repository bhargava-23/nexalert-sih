/**
 * @file mqtt_client.c
 * @brief MQTT publisher implementation for NexAlert telemetry
 *
 * Publishes to local Mosquitto broker on Raspberry Pi.
 * Topic: Nexalert/telemetry/node1 (locked format)
 * QoS: 1 (at least once delivery)
 */

#include "mqtt_client.h"
#include "esp_mqtt_client.h"
#include "esp_log.h"
#include <string.h>

static const char *TAG = "mqtt";

// Module state
static struct {
    bool initialized;
    bool connected;
    esp_mqtt_client_handle_t client;
    char topic[64];
} mqtt_state = {0};

/**
 * MQTT event handler
 */
static void mqtt_event_handler(void *handler_args, esp_event_base_t base,
                               int32_t event_id, void *event_data)
{
    esp_mqtt_event_handle_t event = event_data;

    switch ((esp_mqtt_event_id_t)event_id) {
    case MQTT_EVENT_CONNECTED:
        ESP_LOGI(TAG, "MQTT connected");
        mqtt_state.connected = true;
        break;

    case MQTT_EVENT_DISCONNECTED:
        ESP_LOGW(TAG, "MQTT disconnected");
        mqtt_state.connected = false;
        break;

    case MQTT_EVENT_PUBLISHED:
        ESP_LOGD(TAG, "MQTT message published, msg_id=%d", event->msg_id);
        break;

    case MQTT_EVENT_ERROR:
        ESP_LOGE(TAG, "MQTT error");
        if (event->error_handle->error_type == MQTT_ERROR_TYPE_TCP_TRANSPORT) {
            ESP_LOGE(TAG, "TCP transport error");
        }
        mqtt_state.connected = false;
        break;

    default:
        ESP_LOGD(TAG, "MQTT event: %d", event_id);
        break;
    }
}

esp_err_t mqtt_client_init(const mqtt_config_t* config)
{
    if (config == NULL || config->broker_host == NULL || config->node_id == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Build MQTT URI
    char uri[128];
    snprintf(uri, sizeof(uri), "mqtt://%s:%d", config->broker_host, config->broker_port);

    // Use locked topic format: Nexalert/telemetry/node1
    snprintf(mqtt_state.topic, sizeof(mqtt_state.topic),
             "Nexalert/telemetry/%s", config->node_id);

    // Configure MQTT client
    esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = uri,
        .network.timeout_ms = 5000,
        .network.reconnect_timeout_ms = 5000,
        .session.keepalive = 60,
    };

    mqtt_state.client = esp_mqtt_client_init(&mqtt_cfg);
    if (mqtt_state.client == NULL) {
        ESP_LOGE(TAG, "MQTT client init failed");
        return ESP_FAIL;
    }

    // Register event handler
    esp_err_t ret = esp_mqtt_client_register_event(mqtt_state.client,
                                                    ESP_EVENT_ANY_ID,
                                                    mqtt_event_handler,
                                                    NULL);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to register MQTT event handler: %d", ret);
        esp_mqtt_client_destroy(mqtt_state.client);
        return ret;
    }

    // Start client
    ret = esp_mqtt_client_start(mqtt_state.client);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to start MQTT client: %d", ret);
        esp_mqtt_client_destroy(mqtt_state.client);
        return ret;
    }

    mqtt_state.initialized = true;
    ESP_LOGI(TAG, "MQTT client initialized, broker=%s, topic=%s", uri, mqtt_state.topic);

    return ESP_OK;
}

esp_err_t mqtt_publish_telemetry(const char* json_payload)
{
    if (!mqtt_state.initialized || json_payload == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    if (!mqtt_state.connected) {
        ESP_LOGW(TAG, "MQTT not connected, cannot publish");
        return ESP_FAIL;
    }

    // Publish with QoS 1 (at least once delivery)
    int msg_id = esp_mqtt_client_publish(mqtt_state.client,
                                         mqtt_state.topic,
                                         json_payload,
                                         0,  // length (0 = strlen)
                                         1,  // QoS 1
                                         0); // retain

    if (msg_id < 0) {
        ESP_LOGE(TAG, "MQTT publish failed");
        return ESP_FAIL;
    }

    ESP_LOGD(TAG, "Published telemetry, msg_id=%d, size=%d", msg_id, strlen(json_payload));
    return ESP_OK;
}

bool mqtt_is_connected(void)
{
    return mqtt_state.connected;
}

esp_err_t mqtt_client_deinit(void)
{
    if (!mqtt_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    esp_mqtt_client_stop(mqtt_state.client);
    esp_mqtt_client_destroy(mqtt_state.client);

    memset(&mqtt_state, 0, sizeof(mqtt_state));
    ESP_LOGI(TAG, "MQTT client deinitialized");

    return ESP_OK;
}
