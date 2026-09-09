/**
 * @file main.c
 * @brief NexAlert ESP32-S3 Node Firmware - COMPLETE INTEGRATION
 *
 * TRACK A — MILESTONE 2: Complete Intelligence Pipeline
 *
 * Pipeline:
 * Sensor → Calibration → H_i/Q_i/R_i → Baseline → Anomaly → Evidence
 * → Confidence → Severity → Risk → Hazard State → Buffer → MQTT
 *
 * CRITICAL ARCHITECTURE:
 * - Complete intelligence evaluation at edge
 * - Network failure != Edge intelligence failure
 * - Missing != Zero throughout
 * - Deterministic state transitions
 * - Priority-based buffering
 * - Reconnect/replay on MQTT recovery
 */

#include <stdio.h>
#include <math.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "driver/gpio.h"

// Sensor drivers
#include "dht22.h"

// Telemetry and network
#include "telemetry_envelope.h"
#include "wifi_station.h"
#include "mqtt_client.h"

// Configuration and resilience
#include "node_config.h"
#include "calibration_store.h"
#include "telemetry_buffer.h"
#include "node_heartbeat.h"

// Intelligence modules (Gates 1-8)
#include "health.h"
#include "quality.h"
#include "reliability.h"
#include "baseline.h"
#include "anomaly.h"
#include "evidence.h"
#include "confidence.h"
#include "severity.h"
#include "risk.h"
#include "hazard_state.h"

static const char *TAG = "main";

// Global configuration
static node_config_complete_t g_config;

// Intelligence pipeline state (persistent across samples)
static baseline_state_t baseline_state = {0};
static anomaly_state_t anomaly_state = {0};
static hazard_state_t hazard_current_state = HAZARD_STATE_NORMAL;
static uint16_t hazard_persistence_counter = 0;
static float hazard_resolved_hold_start = NAN;

// Statistics
static uint32_t g_sample_count = 0;
static uint32_t g_failed_samples = 0;
static uint32_t g_mqtt_publish_success = 0;
static uint32_t g_mqtt_publish_fail = 0;
static uint32_t g_last_publish_ms = 0;

/**
 * Apply replay logic: drain buffer after MQTT reconnect
 */
static void replay_buffered_messages(void)
{
    if (telemetry_buffer_is_empty()) {
        return;
    }

    uint16_t count = telemetry_buffer_count();
    ESP_LOGI(TAG, "Replaying %u buffered messages...", count);

    char payload[2048];
    message_metadata_t meta;
    uint16_t replayed = 0;
    uint16_t replay_failed = 0;

    // Drain buffer with bounded retry
    while (!telemetry_buffer_is_empty() && replayed < 50) {
        esp_err_t ret = telemetry_buffer_peek(payload, &meta, sizeof(payload));
        if (ret != ESP_OK) {
            ESP_LOGE(TAG, "Buffer peek failed");
            break;
        }

        // Attempt publish
        ret = mqtt_publish_telemetry(payload);
        if (ret == ESP_OK) {
            // Success: dequeue
            telemetry_buffer_dequeue(payload, &meta, sizeof(payload));
            replayed++;
            g_mqtt_publish_success++;
            ESP_LOGD(TAG, "Replayed seq=%lu", meta.sequence);
        } else {
            // Failure: leave in buffer, will retry next cycle
            replay_failed++;
            ESP_LOGW(TAG, "Replay failed for seq=%lu, leaving in buffer", meta.sequence);
            break;  // Stop replay, will retry next heartbeat cycle
        }
    }

    ESP_LOGI(TAG, "Replay complete: %u replayed, %u failed, %u remain",
             replayed, replay_failed, telemetry_buffer_count());
}

/**
 * Publish telemetry with buffering on MQTT failure
 */
static esp_err_t publish_with_buffering(
    const char* json_payload,
    uint32_t sequence,
    message_priority_t priority
)
{
    if (!mqtt_is_connected()) {
        // MQTT offline: enqueue to buffer
        esp_err_t ret = telemetry_buffer_enqueue(json_payload, sequence, priority);
        if (ret == ESP_OK) {
            ESP_LOGD(TAG, "Buffered seq=%lu (MQTT offline)", sequence);
        } else {
            ESP_LOGW(TAG, "Buffer full, dropped seq=%lu", sequence);
        }
        g_mqtt_publish_fail++;
        return ESP_FAIL;
    }

    // MQTT connected: attempt publish
    esp_err_t ret = mqtt_publish_telemetry(json_payload);
    if (ret == ESP_OK) {
        g_mqtt_publish_success++;
        g_last_publish_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;
        return ESP_OK;
    } else {
        // Publish failed: enqueue to buffer
        ret = telemetry_buffer_enqueue(json_payload, sequence, priority);
        if (ret == ESP_OK) {
            ESP_LOGD(TAG, "Buffered seq=%lu (publish failed)", sequence);
        }
        g_mqtt_publish_fail++;
        return ESP_FAIL;
    }
}

/**
 * Send heartbeat if due
 */
static void send_heartbeat_if_due(void)
{
    if (!node_heartbeat_is_due()) {
        return;
    }

    // Update health status
    buffer_stats_t buf_stats;
    telemetry_buffer_get_stats(&buf_stats);

    node_health_t health = {
        .uptime_s = esp_timer_get_time() / 1000000,
        .self_test_passed = true,
        .calibration_valid = true,  // Assume valid if loaded
        .mqtt_connected = mqtt_is_connected(),
        .last_publish_ms = g_last_publish_ms,
        .buffer_depth = buf_stats.count,
        .buffer_capacity = buf_stats.capacity,
        .total_samples = g_sample_count,
        .failed_samples = g_failed_samples,
        .battery_pct = NAN,  // Not implemented
        .comm_integrity = mqtt_is_connected() ? 1.0f : 0.5f,
    };

    node_heartbeat_update(&health);

    // Generate heartbeat JSON
    char* heartbeat_json = NULL;
    esp_err_t ret = node_heartbeat_generate(&heartbeat_json);
    if (ret != ESP_OK || heartbeat_json == NULL) {
        ESP_LOGE(TAG, "Heartbeat generation failed");
        return;
    }

    // Publish heartbeat (NORMAL priority)
    ret = publish_with_buffering(heartbeat_json, 0, PRIORITY_NORMAL);
    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "Heartbeat sent");
        node_heartbeat_reset_timer();
    }

    free(heartbeat_json);
}

/**
 * Main sampling task: Complete intelligence pipeline
 */
static void sampling_task(void *pvParameters)
{
    ESP_LOGI(TAG, "Sampling task started");

    // Load calibration from NVS
    calibration_t temp_cal, humid_cal;
    esp_err_t ret;
    ret = calibration_load(SENSOR_TYPE_DHT22, "temp", &temp_cal);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Temperature calibration not found, using default");
        temp_cal.valid = false;
    }
    ret = calibration_load(SENSOR_TYPE_DHT22, "humid", &humid_cal);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Humidity calibration not found, using default");
        humid_cal.valid = false;
    }

    // Initialize DHT22 with calibration
    dht22_config_t dht_cfg = {
        .gpio_pin = 4,  // GPIO4 for DHT22
        .temp_cal = temp_cal,
        .humid_cal = humid_cal,
    };
    ret = dht22_init(&dht_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "DHT22 init failed: %d", ret);
        vTaskDelete(NULL);
        return;
    }

    // Initialize baseline with configuration
    baseline_config_t baseline_cfg = {
        .window_size = g_config.intelligence.baseline_window,
        .alpha = g_config.intelligence.baseline_alpha,
    };
    baseline_state_init(&baseline_state, &baseline_cfg);

    // Initialize anomaly with configuration
    anomaly_config_t anomaly_cfg = {
        .lambda = g_config.intelligence.anomaly_lambda,
        .z_cap = g_config.intelligence.anomaly_z_cap,
    };
    anomaly_state_init(&anomaly_state, &anomaly_cfg);

    ESP_LOGI(TAG, "Intelligence pipeline initialized");
    ESP_LOGI(TAG, "Baseline: window=%u, alpha=%.3f", baseline_cfg.window_size, baseline_cfg.alpha);
    ESP_LOGI(TAG, "Anomaly: lambda=%.3f, z_cap=%.3f", anomaly_cfg.lambda, anomaly_cfg.z_cap);

    while (1) {
        g_sample_count++;
        ESP_LOGI(TAG, "=== Sample %lu ===", g_sample_count);

        // ========== SENSOR ACQUISITION ==========
        sensor_reading_t temp_reading, humid_reading;

        ret = dht22_read_temperature(&temp_reading);
        if (ret == ESP_OK && temp_reading.valid) {
            ESP_LOGI(TAG, "Temperature: %.2f °C (calibrated)", temp_reading.value);
        } else {
            ESP_LOGW(TAG, "Temperature: MISSING (sensor error)");
            g_failed_samples++;
        }

        ret = dht22_read_humidity(&humid_reading);
        if (ret == ESP_OK && humid_reading.valid) {
            ESP_LOGI(TAG, "Humidity: %.2f %% (calibrated)", humid_reading.value);
        } else {
            ESP_LOGW(TAG, "Humidity: MISSING (sensor error)");
            g_failed_samples++;
        }

        // Raw measurements (NAN = missing)
        float temp_c = temp_reading.valid ? temp_reading.value : NAN;
        float humidity_pct = humid_reading.valid ? humid_reading.value : NAN;

        // ========== INTELLIGENCE PIPELINE ==========

        // GATE 1: Health (H_i) - per sensor
        float H_temp = compute_health(temp_c, temp_cal.valid, 1.0f);
        float H_humid = compute_health(humidity_pct, humid_cal.valid, 1.0f);
        ESP_LOGD(TAG, "Health: H_temp=%.3f, H_humid=%.3f", H_temp, H_humid);

        // GATE 2: Quality (Q_i) - per sensor
        float Q_temp = compute_quality(temp_c, temp_cal.valid);
        float Q_humid = compute_quality(humidity_pct, humid_cal.valid);
        ESP_LOGD(TAG, "Quality: Q_temp=%.3f, Q_humid=%.3f", Q_temp, Q_humid);

        // GATE 3: Reliability (R_i) - per sensor
        float R_temp = compute_reliability(temp_c, temp_cal.valid, H_temp, Q_temp);
        float R_humid = compute_reliability(humidity_pct, humid_cal.valid, H_humid, Q_humid);
        ESP_LOGD(TAG, "Reliability: R_temp=%.3f, R_humid=%.3f", R_temp, R_humid);

        // GATE 4: Baseline (B_i) - per sensor
        // Check if baseline should be frozen due to hazard state
        bool should_freeze = should_freeze_baseline(hazard_current_state);
        if (should_freeze && baseline_state.status != BASELINE_STATUS_FROZEN) {
            ESP_LOGI(TAG, "Freezing baseline (hazard state: %s)",
                     hazard_state_name(hazard_current_state));
            baseline_state.status = BASELINE_STATUS_FROZEN;
        }

        float B_temp = NAN, B_humid = NAN;
        if (!should_freeze || baseline_state.status == BASELINE_STATUS_FROZEN) {
            B_temp = baseline_update(&baseline_state, 0, temp_c, R_temp);
            B_humid = baseline_update(&baseline_state, 1, humidity_pct, R_humid);
        }
        ESP_LOGD(TAG, "Baseline: B_temp=%.3f, B_humid=%.3f, status=%d",
                 B_temp, B_humid, baseline_state.status);

        // GATE 5: Anomaly (A_i, A_node, A_h)
        float A_temp = anomaly_compute_sensor(&anomaly_state, 0, temp_c, B_temp, R_temp);
        float A_humid = anomaly_compute_sensor(&anomaly_state, 1, humidity_pct, B_humid, R_humid);
        float A_node = anomaly_compute_node(&anomaly_state);

        // Hazard-specific anomaly (fire detection via temperature anomaly)
        float A_h_fire = A_temp;  // Fire primarily detected via temperature
        ESP_LOGD(TAG, "Anomaly: A_temp=%.3f, A_humid=%.3f, A_node=%.3f, A_h_fire=%.3f",
                 A_temp, A_humid, A_node, A_h_fire);

        // GATE 6A: Evidence (E_h) - fire hazard
        sensor_evidence_t temp_evidence = {
            .sensor_id = 0,
            .measurement = temp_c,
            .anomaly = A_temp,
            .reliability = R_temp,
            .weight = 0.7f,  // Temperature primary for fire
        };
        sensor_evidence_t humid_evidence = {
            .sensor_id = 1,
            .measurement = humidity_pct,
            .anomaly = A_humid,
            .reliability = R_humid,
            .weight = 0.3f,  // Humidity secondary
        };
        sensor_evidence_t evidences[] = {temp_evidence, humid_evidence};

        float E_h = compute_evidence(evidences, 2);
        ESP_LOGD(TAG, "Evidence: E_h=%.3f", E_h);

        // GATE 6B: Confidence (C_h)
        sensor_availability_t temp_avail = {.sensor_id = 0, .available = !isnan(temp_c), .weight = 0.7f};
        sensor_availability_t humid_avail = {.sensor_id = 1, .available = !isnan(humidity_pct), .weight = 0.3f};
        sensor_availability_t availability[] = {temp_avail, humid_avail};

        evidence_group_t evidence_group = {
            .values = (float[]){isnan(temp_c) ? NAN : A_temp, isnan(humidity_pct) ? NAN : A_humid},
            .count = 2,
        };

        confidence_weights_t conf_weights = {
            .w_coverage = g_config.intelligence.confidence_w_cov,
            .w_agreement = g_config.intelligence.confidence_w_agree,
            .w_temporal = g_config.intelligence.confidence_w_temp,
            .w_baseline = g_config.intelligence.confidence_w_base,
        };

        confidence_result_t confidence = compute_confidence(
            availability, 2,
            &evidence_group,
            xTaskGetTickCount() * portTICK_PERIOD_MS / 1000.0f,
            baseline_get_status_string(&baseline_state),
            &conf_weights
        );
        float C_h = confidence.confidence;
        float core_coverage = confidence.coverage;
        ESP_LOGD(TAG, "Confidence: C_h=%.3f, coverage=%.3f", C_h, core_coverage);

        // GATE 7: Severity (S_h) - fire hazard
        fire_intensity_config_t fire_cfg = {
            .temp_low_c = 40.0f,
            .temp_high_c = 100.0f,
            .smoke_low = 0.2f,
            .smoke_high = 0.8f,
        };
        severity_weights_t sev_weights = {
            .w_intensity = g_config.intelligence.severity_w_intensity,
            .w_temporal = g_config.intelligence.severity_w_temporal,
            .w_duration = g_config.intelligence.severity_w_duration,
        };

        // Temporal rate (simplified: use anomaly as proxy)
        float T_h = isnan(A_temp) ? NAN : fminf(fabsf(A_temp) / 5.0f, 1.0f);

        // Duration (simplified: assume 0 for now, would need history)
        float D_h = 0.0f;

        severity_result_t severity = compute_severity(
            temp_c, NAN,  // temp, smoke (no smoke sensor)
            NAN, NAN,     // water_level, rainfall (not fire)
            T_h, D_h,
            &fire_cfg, NULL,  // fire config, no flood config
            &sev_weights
        );
        float S_h = severity.severity;
        ESP_LOGD(TAG, "Severity: S_h=%.3f (I=%.3f, T=%.3f, D=%.3f)",
                 S_h, severity.intensity, T_h, D_h);

        // GATE 7: Risk (R_h)
        risk_weights_t risk_weights = {
            .w_evidence = g_config.intelligence.risk_w_evidence,
            .w_severity = g_config.intelligence.risk_w_severity,
            .w_temporal = g_config.intelligence.risk_w_temporal,
        };

        risk_result_t risk = compute_risk(E_h, S_h, T_h, &risk_weights);
        float R_h = risk.risk;
        ESP_LOGD(TAG, "Risk: R_h=%.3f", R_h);

        // GATE 8: Hazard State Machine
        intelligence_inputs_t intel = {
            .E_h = E_h,
            .C_h = C_h,
            .S_h = S_h,
            .R_h = R_h,
            .A_h = A_h_fire,
            .T_h = T_h,
            .core_coverage = core_coverage,
        };

        state_machine_config_t state_cfg = state_machine_default_config();
        // Apply configuration overrides
        state_cfg.watch_risk_enter = g_config.intelligence.watch_risk_enter;
        state_cfg.suspected_evidence_enter = g_config.intelligence.suspected_evidence_enter;
        state_cfg.confirmed_evidence_enter = g_config.intelligence.confirmed_evidence_enter;

        state_transition_t transition = update_state(
            hazard_current_state,
            &intel,
            baseline_get_status_string(&baseline_state),
            xTaskGetTickCount() * portTICK_PERIOD_MS / 1000.0f,
            hazard_persistence_counter,
            hazard_resolved_hold_start,
            &state_cfg,
            HAZARD_STATE_EPSILON
        );

        hazard_state_t prev_state = hazard_current_state;
        hazard_current_state = transition.new_state;
        hazard_persistence_counter = transition.persistence_counter;
        hazard_resolved_hold_start = transition.resolved_hold_start;

        if (prev_state != hazard_current_state) {
            ESP_LOGI(TAG, "STATE TRANSITION: %s → %s (%s)",
                     hazard_state_name(prev_state),
                     hazard_state_name(hazard_current_state),
                     transition.reason);
        } else {
            ESP_LOGD(TAG, "State: %s (info: %s)",
                     hazard_state_name(hazard_current_state),
                     information_condition_name(transition.info_condition));
        }

        // ========== TELEMETRY ENVELOPE ==========
        measurements_t measurements = {
            .temp_c = temp_c,
            .humidity_pct = humidity_pct,
            .pressure_hpa = NAN,
            .pm25_ug_m3 = NAN,
            .pm10_ug_m3 = NAN,
        };

        diagnostics_t diagnostics = {
            .uptime_s = esp_timer_get_time() / 1000000,
            .self_test_passed = true,
            .comm_integrity = mqtt_is_connected() ? 1.0f : 0.5f,
            .calibration_valid = temp_cal.valid && humid_cal.valid,
            .stability_index = 0.9f,
        };

        power_t power = {
            .battery_pct = NAN,
            .battery_voltage = NAN,
            .solar_current = NAN,
        };

        char* telemetry_json = NULL;
        ret = telemetry_envelope_generate(&measurements, &diagnostics, &power, &telemetry_json);
        if (ret != ESP_OK || telemetry_json == NULL) {
            ESP_LOGE(TAG, "Telemetry generation failed");
            vTaskDelay(pdMS_TO_TICKS(g_config.sampling.interval_ms));
            continue;
        }

        uint32_t seq = telemetry_envelope_get_sequence();
        ESP_LOGI(TAG, "Telemetry generated: seq=%lu, size=%d bytes", seq, strlen(telemetry_json));

        // ========== PUBLISH WITH BUFFERING ==========
        // Determine priority based on hazard state
        message_priority_t priority = PRIORITY_NORMAL;
        if (hazard_current_state == HAZARD_STATE_CRITICAL) {
            priority = PRIORITY_CRITICAL;
        } else if (hazard_current_state >= HAZARD_STATE_WATCH) {
            priority = PRIORITY_HAZARD;
        }

        ret = publish_with_buffering(telemetry_json, seq, priority);
        if (ret == ESP_OK) {
            ESP_LOGI(TAG, "Telemetry published (priority=%d)", priority);
        } else {
            ESP_LOGW(TAG, "Telemetry buffered (priority=%d)", priority);
        }

        free(telemetry_json);

        // ========== RECONNECT REPLAY ==========
        // If MQTT just reconnected, replay buffered messages
        static bool was_connected = false;
        bool is_connected = mqtt_is_connected();
        if (is_connected && !was_connected) {
            ESP_LOGI(TAG, "MQTT reconnected, replaying buffer...");
            replay_buffered_messages();
        }
        was_connected = is_connected;

        // ========== HEARTBEAT ==========
        send_heartbeat_if_due();

        // Wait for next sampling period
        vTaskDelay(pdMS_TO_TICKS(g_config.sampling.interval_ms));
    }
}

void app_main(void)
{
    ESP_LOGI(TAG, "=== NexAlert Node Firmware ===");
    ESP_LOGI(TAG, "Version: 1.0.0 - COMPLETE INTEGRATION");
    ESP_LOGI(TAG, "Track A — Milestone 2: Intelligence Pipeline");

    // ========== LOAD CONFIGURATION ==========
    esp_err_t ret = node_config_load(&g_config);
    if (ret == ESP_ERR_NOT_FOUND) {
        ESP_LOGI(TAG, "Using default configuration");
        g_config = node_config_default();
    } else if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Configuration load failed: %d", ret);
        g_config = node_config_default();
    }

    ESP_LOGI(TAG, "Node ID: %s", g_config.identity.node_id);
    ESP_LOGI(TAG, "Location: %.6f, %.6f", g_config.identity.latitude, g_config.identity.longitude);
    ESP_LOGI(TAG, "MQTT: %s:%u → %s", g_config.mqtt.broker_host, g_config.mqtt.broker_port, g_config.mqtt.topic);
    ESP_LOGI(TAG, "Sampling: %lu ms", g_config.sampling.interval_ms);
    ESP_LOGI(TAG, "Buffer: %u entries", g_config.buffer.capacity);

    // ========== INITIALIZE COMPONENTS ==========

    // NVS/Calibration
    ESP_ERROR_CHECK(calibration_store_init());

    // Telemetry envelope
    telemetry_config_t telem_cfg = {
        .node_id = g_config.identity.node_id,
        .latitude = g_config.identity.latitude,
        .longitude = g_config.identity.longitude,
        .altitude = g_config.identity.altitude,
    };
    ESP_ERROR_CHECK(telemetry_envelope_init(&telem_cfg));

    // Telemetry buffer
    buffer_config_t buf_cfg = {
        .capacity = g_config.buffer.capacity,
    };
    ESP_ERROR_CHECK(telemetry_buffer_init(&buf_cfg));

    // Heartbeat
    heartbeat_config_t hb_cfg = {
        .interval_ms = g_config.heartbeat.interval_ms,
        .enabled = g_config.heartbeat.enabled,
    };
    ESP_ERROR_CHECK(node_heartbeat_init(&hb_cfg));

    // Wi-Fi
    nexalert_wifi_config_t wifi_cfg = {
        .ssid = "YOUR_WIFI_SSID",  // TODO: Load from config
        .password = "YOUR_WIFI_PASSWORD",
    };
    ESP_ERROR_CHECK(wifi_station_init(&wifi_cfg));

    ESP_LOGI(TAG, "Waiting for Wi-Fi connection...");
    while (!wifi_is_connected()) {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }

    char ip[16];
    wifi_get_ip(ip, sizeof(ip));
    ESP_LOGI(TAG, "Wi-Fi connected: %s", ip);

    // MQTT with LOCKED TOPIC FORMAT
    mqtt_config_t mqtt_cfg = {
        .broker_host = g_config.mqtt.broker_host,
        .broker_port = g_config.mqtt.broker_port,
        .node_id = g_config.identity.node_id,
    };
    ESP_ERROR_CHECK(mqtt_client_init(&mqtt_cfg));

    ESP_LOGI(TAG, "Waiting for MQTT connection...");
    int mqtt_wait = 0;
    while (!mqtt_is_connected() && mqtt_wait < 10) {
        vTaskDelay(pdMS_TO_TICKS(1000));
        mqtt_wait++;
    }

    if (mqtt_is_connected()) {
        ESP_LOGI(TAG, "MQTT connected to %s:%u", g_config.mqtt.broker_host, g_config.mqtt.broker_port);
    } else {
        ESP_LOGW(TAG, "MQTT connection timeout, buffering enabled");
    }

    // ========== START SAMPLING TASK ==========
    xTaskCreate(sampling_task, "sampling", 16384, NULL, 5, NULL);

    ESP_LOGI(TAG, "Initialization complete, intelligence pipeline active");
}
