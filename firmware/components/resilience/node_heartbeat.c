/**
 * @file node_heartbeat.c
 * @brief Heartbeat implementation for node health monitoring
 *
 * CRITICAL INVARIANT: No telemetry != Environment normal
 */

#include "node_heartbeat.h"
#include "esp_log.h"
#include "esp_timer.h"
#include <string.h>
#include <stdio.h>
#include <math.h>

static const char *TAG = "heartbeat";

/**
 * Heartbeat state
 */
static struct {
    bool initialized;
    bool enabled;
    uint32_t interval_ms;
    uint64_t last_sent_us;       // Last heartbeat sent (microseconds)
    node_health_t current_health;
} hb_state = {0};

esp_err_t node_heartbeat_init(const heartbeat_config_t* config)
{
    if (hb_state.initialized) {
        ESP_LOGW(TAG, "Heartbeat already initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (config == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    hb_state.enabled = config->enabled;
    hb_state.interval_ms = config->interval_ms > 0 ? config->interval_ms : 30000;
    hb_state.last_sent_us = esp_timer_get_time();
    memset(&hb_state.current_health, 0, sizeof(node_health_t));
    hb_state.current_health.battery_pct = NAN;
    hb_state.current_health.comm_integrity = NAN;
    hb_state.initialized = true;

    ESP_LOGI(TAG, "Heartbeat initialized, interval=%lu ms, enabled=%d",
             hb_state.interval_ms, hb_state.enabled);

    return ESP_OK;
}

esp_err_t node_heartbeat_update(const node_health_t* health)
{
    if (!hb_state.initialized || health == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    memcpy(&hb_state.current_health, health, sizeof(node_health_t));
    return ESP_OK;
}

esp_err_t node_heartbeat_generate(char** out_json)
{
    if (!hb_state.initialized || out_json == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    // Allocate JSON buffer (generous for heartbeat)
    char* json = malloc(1024);
    if (json == NULL) {
        ESP_LOGE(TAG, "Failed to allocate heartbeat JSON");
        return ESP_ERR_NO_MEM;
    }

    node_health_t* h = &hb_state.current_health;

    // Build heartbeat JSON
    int len = snprintf(json, 1024,
        "{"
        "\"type\":\"heartbeat\","
        "\"timestamp\":%llu,"
        "\"uptime_s\":%lu,"
        "\"self_test_passed\":%s,"
        "\"calibration_valid\":%s,"
        "\"mqtt_connected\":%s,"
        "\"last_publish_ms\":%lu,"
        "\"buffer_depth\":%u,"
        "\"buffer_capacity\":%u,"
        "\"total_samples\":%lu,"
        "\"failed_samples\":%lu,",
        esp_timer_get_time() / 1000,  // Current timestamp (milliseconds)
        h->uptime_s,
        h->self_test_passed ? "true" : "false",
        h->calibration_valid ? "true" : "false",
        h->mqtt_connected ? "true" : "false",
        h->last_publish_ms,
        h->buffer_depth,
        h->buffer_capacity,
        h->total_samples,
        h->failed_samples
    );

    // Add battery if available
    if (isnan(h->battery_pct)) {
        len += snprintf(json + len, 1024 - len, "\"battery_pct\":null,");
    } else {
        len += snprintf(json + len, 1024 - len, "\"battery_pct\":%.1f,", h->battery_pct);
    }

    // Add comm integrity if available
    if (isnan(h->comm_integrity)) {
        len += snprintf(json + len, 1024 - len, "\"comm_integrity\":null");
    } else {
        len += snprintf(json + len, 1024 - len, "\"comm_integrity\":%.3f", h->comm_integrity);
    }

    len += snprintf(json + len, 1024 - len, "}");

    if (len >= 1024) {
        ESP_LOGW(TAG, "Heartbeat JSON truncated");
    }

    *out_json = json;
    return ESP_OK;
}

bool node_heartbeat_is_due(void)
{
    if (!hb_state.initialized || !hb_state.enabled) {
        return false;
    }

    uint64_t now_us = esp_timer_get_time();
    uint64_t elapsed_ms = (now_us - hb_state.last_sent_us) / 1000;

    return (elapsed_ms >= hb_state.interval_ms);
}

esp_err_t node_heartbeat_reset_timer(void)
{
    if (!hb_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    hb_state.last_sent_us = esp_timer_get_time();
    return ESP_OK;
}

esp_err_t node_heartbeat_deinit(void)
{
    if (!hb_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    memset(&hb_state, 0, sizeof(hb_state));
    ESP_LOGI(TAG, "Heartbeat deinitialized");

    return ESP_OK;
}
