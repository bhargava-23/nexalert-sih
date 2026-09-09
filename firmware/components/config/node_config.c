/**
 * @file node_config.c
 * @brief Centralized configuration implementation with NVS persistence
 *
 * PROTOTYPE/DEMO configuration with UNVALIDATED intelligence thresholds.
 */

#include "node_config.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_log.h"
#include <string.h>
#include <math.h>

static const char *TAG = "node_config";
static const char *NVS_NAMESPACE = "nexalert";
static const char *NVS_KEY = "config";

node_config_complete_t node_config_default(void)
{
    node_config_complete_t config = {
        // Node identity
        .identity = {
            .node_id = "node1",
            .latitude = 12.9716,      // Bangalore coordinates (DEMO)
            .longitude = 77.5946,
            .altitude = 920.0f,
        },

        // Sampling configuration
        .sampling = {
            .interval_ms = 5000,      // 5 seconds
            .warmup_ms = 2000,        // 2 seconds sensor warmup
        },

        // MQTT configuration (LOCKED TOPIC FORMAT)
        .mqtt = {
            .broker_host = "192.168.1.100",  // DEMO: Raspberry Pi local IP
            .broker_port = 1883,
            .topic = "Nexalert/telemetry/node1",  // LOCKED canonical format
            .tls_enabled = false,
            .username = "",           // No auth for local broker
            .password = "",
            .keepalive_s = 60,
            .timeout_ms = 5000,
        },

        // Buffer configuration
        .buffer = {
            .capacity = 100,
            .enabled = true,
        },

        // Heartbeat configuration
        .heartbeat = {
            .interval_ms = 30000,     // 30 seconds
            .enabled = true,
        },

        // Calibration (DEMO values)
        .calibration = {
            .K_temp = 1.0f,
            .K_humidity = 1.0f,
            .K_pressure = 1.0f,
        },

        // Intelligence configuration (PROTOTYPE - UNVALIDATED)
        .intelligence = {
            // Baseline
            .baseline_window = 120,
            .baseline_alpha = 0.1f,

            // Anomaly
            .anomaly_lambda = 0.05f,
            .anomaly_z_cap = 5.0f,

            // Confidence weights
            .confidence_w_cov = 0.3f,
            .confidence_w_agree = 0.3f,
            .confidence_w_temp = 0.2f,
            .confidence_w_base = 0.2f,

            // Severity weights
            .severity_w_intensity = 0.5f,
            .severity_w_temporal = 0.3f,
            .severity_w_duration = 0.2f,

            // Risk weights
            .risk_w_evidence = 0.4f,
            .risk_w_severity = 0.4f,
            .risk_w_temporal = 0.2f,

            // State machine thresholds (from Python reference)
            .watch_risk_enter = 0.3f,
            .watch_anomaly_enter = 0.5f,
            .suspected_evidence_enter = 0.4f,
            .confirmed_evidence_enter = 0.7f,
            .confirmed_confidence_min = 0.6f,
            .critical_severity_enter = 0.85f,
            .critical_risk_enter = 0.9f,

            // Persistence counters
            .watch_persistence = 1,
            .suspected_persistence = 3,
            .confirmed_persistence = 5,
            .critical_persistence = 1,
            .resolved_persistence = 10,

            // Hysteresis values
            .watch_risk_exit = 0.25f,
            .suspected_evidence_exit = 0.35f,
            .confirmed_evidence_exit = 0.65f,
            .critical_severity_exit = 0.80f,
            .critical_risk_exit = 0.85f,
        },

        // Logging
        .logging = {
            .log_level = 3,  // ESP_LOG_INFO
        },
    };

    return config;
}

esp_err_t node_config_validate(const node_config_complete_t* config)
{
    if (config == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Node ID not empty
    if (strlen(config->identity.node_id) == 0) {
        ESP_LOGE(TAG, "Node ID cannot be empty");
        return ESP_ERR_INVALID_ARG;
    }

    // Sampling interval > 0
    if (config->sampling.interval_ms == 0) {
        ESP_LOGE(TAG, "Sampling interval must be > 0");
        return ESP_ERR_INVALID_ARG;
    }

    // MQTT broker not empty
    if (strlen(config->mqtt.broker_host) == 0) {
        ESP_LOGE(TAG, "MQTT broker host cannot be empty");
        return ESP_ERR_INVALID_ARG;
    }

    // MQTT topic matches canonical format (starts with "Nexalert/telemetry/")
    if (strncmp(config->mqtt.topic, "Nexalert/telemetry/", 19) != 0) {
        ESP_LOGE(TAG, "MQTT topic must start with 'Nexalert/telemetry/' (got: %s)",
                 config->mqtt.topic);
        return ESP_ERR_INVALID_ARG;
    }

    // Buffer capacity reasonable (1-1000)
    if (config->buffer.capacity < 1 || config->buffer.capacity > 1000) {
        ESP_LOGE(TAG, "Buffer capacity out of range: %u (valid: 1-1000)",
                 config->buffer.capacity);
        return ESP_ERR_INVALID_ARG;
    }

    // Intelligence thresholds in [0, 1]
    if (config->intelligence.watch_risk_enter < 0.0f || config->intelligence.watch_risk_enter > 1.0f ||
        config->intelligence.confirmed_evidence_enter < 0.0f || config->intelligence.confirmed_evidence_enter > 1.0f ||
        config->intelligence.critical_severity_enter < 0.0f || config->intelligence.critical_severity_enter > 1.0f) {
        ESP_LOGE(TAG, "Intelligence thresholds must be in [0, 1]");
        return ESP_ERR_INVALID_ARG;
    }

    // Hysteresis: enter > exit
    if (config->intelligence.watch_risk_enter <= config->intelligence.watch_risk_exit ||
        config->intelligence.confirmed_evidence_enter <= config->intelligence.confirmed_evidence_exit ||
        config->intelligence.critical_severity_enter <= config->intelligence.critical_severity_exit) {
        ESP_LOGE(TAG, "Hysteresis violation: enter thresholds must be > exit thresholds");
        return ESP_ERR_INVALID_ARG;
    }

    // Persistence counters >= 1
    if (config->intelligence.watch_persistence < 1 ||
        config->intelligence.suspected_persistence < 1 ||
        config->intelligence.confirmed_persistence < 1) {
        ESP_LOGE(TAG, "Persistence counters must be >= 1");
        return ESP_ERR_INVALID_ARG;
    }

    // Weights should sum to ~1.0 (tolerance 0.01)
    float conf_sum = config->intelligence.confidence_w_cov +
                     config->intelligence.confidence_w_agree +
                     config->intelligence.confidence_w_temp +
                     config->intelligence.confidence_w_base;
    if (fabsf(conf_sum - 1.0f) > 0.01f) {
        ESP_LOGW(TAG, "Confidence weights sum to %.3f (expected ~1.0)", conf_sum);
    }

    float sev_sum = config->intelligence.severity_w_intensity +
                    config->intelligence.severity_w_temporal +
                    config->intelligence.severity_w_duration;
    if (fabsf(sev_sum - 1.0f) > 0.01f) {
        ESP_LOGW(TAG, "Severity weights sum to %.3f (expected ~1.0)", sev_sum);
    }

    float risk_sum = config->intelligence.risk_w_evidence +
                     config->intelligence.risk_w_severity +
                     config->intelligence.risk_w_temporal;
    if (fabsf(risk_sum - 1.0f) > 0.01f) {
        ESP_LOGW(TAG, "Risk weights sum to %.3f (expected ~1.0)", risk_sum);
    }

    return ESP_OK;
}

esp_err_t node_config_load(node_config_complete_t* out_config)
{
    if (out_config == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Open NVS
    nvs_handle_t nvs_handle;
    esp_err_t ret = nvs_open(NVS_NAMESPACE, NVS_READONLY, &nvs_handle);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "NVS not found, using defaults");
        *out_config = node_config_default();
        return ESP_ERR_NOT_FOUND;
    }

    // Read configuration blob
    size_t required_size = sizeof(node_config_complete_t);
    ret = nvs_get_blob(nvs_handle, NVS_KEY, out_config, &required_size);
    nvs_close(nvs_handle);

    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Failed to read config from NVS: %d, using defaults", ret);
        *out_config = node_config_default();
        return ESP_ERR_NOT_FOUND;
    }

    // Validate loaded configuration
    ret = node_config_validate(out_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Loaded config invalid, using defaults");
        *out_config = node_config_default();
        return ESP_ERR_INVALID_ARG;
    }

    ESP_LOGI(TAG, "Configuration loaded from NVS");
    ESP_LOGI(TAG, "  Node ID: %s", out_config->identity.node_id);
    ESP_LOGI(TAG, "  MQTT: %s:%u → %s", out_config->mqtt.broker_host,
             out_config->mqtt.broker_port, out_config->mqtt.topic);
    ESP_LOGI(TAG, "  Buffer: %u entries", out_config->buffer.capacity);

    return ESP_OK;
}

esp_err_t node_config_save(const node_config_complete_t* config)
{
    if (config == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Validate before saving
    esp_err_t ret = node_config_validate(config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Configuration validation failed, not saving");
        return ret;
    }

    // Open NVS
    nvs_handle_t nvs_handle;
    ret = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &nvs_handle);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to open NVS: %d", ret);
        return ret;
    }

    // Write configuration blob
    ret = nvs_set_blob(nvs_handle, NVS_KEY, config, sizeof(node_config_complete_t));
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to write config to NVS: %d", ret);
        nvs_close(nvs_handle);
        return ret;
    }

    // Commit
    ret = nvs_commit(nvs_handle);
    nvs_close(nvs_handle);

    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to commit NVS: %d", ret);
        return ret;
    }

    ESP_LOGI(TAG, "Configuration saved to NVS");
    return ESP_OK;
}

esp_err_t node_config_reset(void)
{
    // Open NVS
    nvs_handle_t nvs_handle;
    esp_err_t ret = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &nvs_handle);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "NVS not found during reset: %d", ret);
        return ESP_OK;  // Already empty
    }

    // Erase configuration key
    ret = nvs_erase_key(nvs_handle, NVS_KEY);
    if (ret != ESP_OK && ret != ESP_ERR_NVS_NOT_FOUND) {
        ESP_LOGE(TAG, "Failed to erase config from NVS: %d", ret);
        nvs_close(nvs_handle);
        return ret;
    }

    // Commit
    ret = nvs_commit(nvs_handle);
    nvs_close(nvs_handle);

    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to commit NVS: %d", ret);
        return ret;
    }

    ESP_LOGI(TAG, "Configuration reset to defaults");
    return ESP_OK;
}
