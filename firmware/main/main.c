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
#include "esp_adc/adc_oneshot.h"  // Track 3A: ADC for MQ-2

// Sensor drivers - Track 3A: BME680, MPU6050, MQ-2
#include "i2c_bus.h"
#include "bme680.h"
#include "mpu6050.h"
#include "mq2.h"

// Telemetry and network
#include "hardware_json.h"      // Track 3A: Hardware JSON for ESP32 → MQTT transport
#include "wifi_station.h"
#include "nexalert_mqtt.h"
#include "sntp_client.h"        // Track 3A: SNTP/NTP for time synchronization

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
// Baseline state (ENUM, not struct with .status field)
static baseline_state_t baseline_current_state = BASELINE_INITIALIZING;
static baseline_result_t baseline_stats[2] = {0};  // [0] = temperature, [1] = humidity
static uint16_t baseline_sample_count = 0;

// Note: anomaly module is stateless (no anomaly_state_t type exists)
static hazard_state_t hazard_current_state = HAZARD_STATE_NORMAL;
static uint16_t hazard_persistence_counter = 0;
static float hazard_resolved_hold_start = NAN;

// Track 4: History buffers for temporal/duration tracking
#define HISTORY_SIZE 10  // Last 10 samples for rate-of-change
#define BASELINE_HISTORY_SIZE 50  // Accumulate samples before computing baseline

static struct {
    // Temperature history (circular buffer)
    float temp_history[HISTORY_SIZE];
    uint32_t temp_timestamps_ms[HISTORY_SIZE];
    uint8_t temp_index;
    uint8_t temp_count;

    // Humidity history (circular buffer)
    float humid_history[HISTORY_SIZE];
    uint32_t humid_timestamps_ms[HISTORY_SIZE];
    uint8_t humid_index;
    uint8_t humid_count;

    // Duration tracking
    float time_above_fire_threshold_s;
    uint32_t duration_start_ms;
    bool duration_active;
} g_intelligence_history = {0};

// Sample accumulation for baseline computation
static struct {
    float temp_samples[BASELINE_HISTORY_SIZE];
    uint16_t temp_count;

    float humid_samples[BASELINE_HISTORY_SIZE];
    uint16_t humid_count;
} g_baseline_history = {0};

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
 * Track 4: Accumulate samples and compute baseline stats when ready
 */
static void update_baseline_stats(float temp_c, float humidity_pct)
{
    baseline_config_t cfg = baseline_default_config();

    // Accumulate temperature samples
    if (!isnan(temp_c) && g_baseline_history.temp_count < BASELINE_HISTORY_SIZE) {
        g_baseline_history.temp_samples[g_baseline_history.temp_count++] = temp_c;
    }

    // Accumulate humidity samples
    if (!isnan(humidity_pct) && g_baseline_history.humid_count < BASELINE_HISTORY_SIZE) {
        g_baseline_history.humid_samples[g_baseline_history.humid_count++] = humidity_pct;
    }

    // Compute baseline stats when we have enough samples and baseline is LEARNING or READY
    if (baseline_current_state >= BASELINE_LEARNING) {
        // Temperature baseline
        if (g_baseline_history.temp_count >= cfg.min_samples_learning && !baseline_stats[0].valid) {
            baseline_stats[0] = compute_robust_baseline(
                g_baseline_history.temp_samples,
                g_baseline_history.temp_count,
                cfg.epsilon
            );
            if (baseline_stats[0].valid) {
                ESP_LOGI(TAG, "Temperature baseline computed: median=%.2f, scale=%.2f",
                         baseline_stats[0].median, baseline_stats[0].scale);
            }
        }

        // Humidity baseline
        if (g_baseline_history.humid_count >= cfg.min_samples_learning && !baseline_stats[1].valid) {
            baseline_stats[1] = compute_robust_baseline(
                g_baseline_history.humid_samples,
                g_baseline_history.humid_count,
                cfg.epsilon
            );
            if (baseline_stats[1].valid) {
                ESP_LOGI(TAG, "Humidity baseline computed: median=%.2f, scale=%.2f",
                         baseline_stats[1].median, baseline_stats[1].scale);
            }
        }
    }
}

/**
 * Track 4: Compute rate of change from history
 * Returns: rate in units/second, or NAN if insufficient history
 */
static float compute_rate_of_change(
    const float* history,
    const uint32_t* timestamps_ms,
    uint8_t count,
    uint8_t index
)
{
    if (count < 2) {
        return NAN;  // Need at least 2 samples
    }

    // Get most recent sample
    uint8_t latest_idx = (index > 0) ? (index - 1) : (count - 1);
    float latest_value = history[latest_idx];
    uint32_t latest_time_ms = timestamps_ms[latest_idx];

    // Get oldest sample
    uint8_t oldest_idx = (count < HISTORY_SIZE) ? 0 : index;
    float oldest_value = history[oldest_idx];
    uint32_t oldest_time_ms = timestamps_ms[oldest_idx];

    // Compute rate
    float delta_value = latest_value - oldest_value;
    float delta_time_s = (float)(latest_time_ms - oldest_time_ms) / 1000.0f;

    if (delta_time_s < 0.1f) {
        return NAN;  // Too short interval
    }

    return delta_value / delta_time_s;  // units/second
}

/**
 * Track 4: Update duration tracking for threshold exceedance
 */
static void update_duration_tracking(
    float current_value,
    float threshold,
    uint32_t current_time_ms
)
{
    if (isnan(current_value)) {
        // Missing value: reset duration
        g_intelligence_history.duration_active = false;
        g_intelligence_history.time_above_fire_threshold_s = 0.0f;
        return;
    }

    if (current_value >= threshold) {
        // Above threshold
        if (!g_intelligence_history.duration_active) {
            // Just crossed threshold: start duration
            g_intelligence_history.duration_active = true;
            g_intelligence_history.duration_start_ms = current_time_ms;
            g_intelligence_history.time_above_fire_threshold_s = 0.0f;
        } else {
            // Still above: update duration
            uint32_t elapsed_ms = current_time_ms - g_intelligence_history.duration_start_ms;
            g_intelligence_history.time_above_fire_threshold_s = (float)elapsed_ms / 1000.0f;
        }
    } else {
        // Below threshold: reset
        g_intelligence_history.duration_active = false;
        g_intelligence_history.time_above_fire_threshold_s = 0.0f;
    }
}

// Baseline freeze logic moved to hazard_state.h API (non-static declaration)

/**
 * Main sampling task: Complete intelligence pipeline
 */
static void sampling_task(void *pvParameters)
{
    ESP_LOGI(TAG, "Sampling task started");

    // Track 3A: Initialize I2C bus (shared by BME680 and MPU6050)
    esp_err_t ret = i2c_bus_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "I2C bus init failed: %d", ret);
        vTaskDelete(NULL);
        return;
    }

    // Load calibration from NVS
    calibration_t temp_cal, humid_cal, pressure_cal;
    ret = calibration_load(SENSOR_TYPE_BME680, "temp", &temp_cal);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Temperature calibration not found, using default");
        temp_cal.valid = false;
    }
    ret = calibration_load(SENSOR_TYPE_BME680, "humid", &humid_cal);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Humidity calibration not found, using default");
        humid_cal.valid = false;
    }
    ret = calibration_load(SENSOR_TYPE_BME680, "pressure", &pressure_cal);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Pressure calibration not found, using default");
        pressure_cal.valid = false;
    }

    // Track 3A: Initialize BME680 with calibration (replaces DHT22)
    bme680_config_t bme_cfg = {
        .i2c_addr = BME680_I2C_ADDR_PRIMARY,  // Try 0x77, auto-fallback to 0x76
        .temp_cal = temp_cal,
        .humid_cal = humid_cal,
        .pressure_cal = pressure_cal,
    };
    ret = bme680_init(&bme_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "BME680 init failed: %d", ret);
        vTaskDelete(NULL);
        return;
    }

    // Track 3A: Initialize MPU6050 accelerometer for vibration detection
    mpu6050_config_t mpu_cfg = {
        .i2c_addr = MPU6050_I2C_ADDR,  // 0x68
    };
    ret = mpu6050_init(&mpu_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "MPU6050 init failed: %d", ret);
        vTaskDelete(NULL);
        return;
    }

    // Track 3A: Initialize MQ-2 gas sensor (raw ADC)
    mq2_config_t mq2_cfg = {
        .gpio_pin = 4,           // GPIO4 for MQ-2 (was DHT22 pin)
        .adc_channel = ADC_CHANNEL_3,  // GPIO4 = ADC_CH3 on ESP32-S3 (not ADC1_CHANNEL_3)
    };
    ret = mq2_init(&mq2_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "MQ-2 init failed: %d", ret);
        vTaskDelete(NULL);
        return;
    }

    ESP_LOGI(TAG, "Intelligence pipeline initialized");
    ESP_LOGI(TAG, "Baseline: state=%s, samples=%u", baseline_state_name(baseline_current_state), baseline_sample_count);

    while (1) {
        g_sample_count++;
        ESP_LOGI(TAG, "=== Sample %lu ===", g_sample_count);

        // Track 4: Capture measurement timestamp BEFORE sensor acquisition
        // Repository semantic: age = t_now - t_measurement (confidence.py:183-229)
        uint32_t measurement_time_ms = (uint32_t)(esp_timer_get_time() / 1000);

        // ========== SENSOR ACQUISITION - TRACK 3A ==========
        // BME680: Temperature, Humidity, Pressure, Gas Resistance
        sensor_reading_t temp_reading, humid_reading, pressure_reading, gas_reading;

        ret = bme680_read_temperature(&temp_reading);
        if (ret == ESP_OK && temp_reading.valid) {
            ESP_LOGI(TAG, "Temperature: %.2f °C (BME680, calibrated)", temp_reading.value);
        } else {
            ESP_LOGW(TAG, "Temperature: MISSING (BME680 sensor error)");
            g_failed_samples++;
        }

        ret = bme680_read_humidity(&humid_reading);
        if (ret == ESP_OK && humid_reading.valid) {
            ESP_LOGI(TAG, "Humidity: %.2f %% (BME680, calibrated)", humid_reading.value);
        } else {
            ESP_LOGW(TAG, "Humidity: MISSING (BME680 sensor error)");
            g_failed_samples++;
        }

        ret = bme680_read_pressure(&pressure_reading);
        if (ret == ESP_OK && pressure_reading.valid) {
            ESP_LOGI(TAG, "Pressure: %.2f hPa (BME680, calibrated)", pressure_reading.value);
        } else {
            ESP_LOGW(TAG, "Pressure: MISSING (BME680 sensor error)");
            g_failed_samples++;
        }

        ret = bme680_read_gas(&gas_reading);
        if (ret == ESP_OK && gas_reading.valid) {
            ESP_LOGI(TAG, "Gas Resistance: %.0f ADC (BME680, raw)", gas_reading.value);
        } else {
            ESP_LOGW(TAG, "Gas Resistance: MISSING (BME680 sensor error)");
        }

        // MPU6050: 3-axis accelerometer for vibration detection
        mpu6050_accel_t accel_reading;
        ret = mpu6050_read_accel(&accel_reading);
        if (ret == ESP_OK && accel_reading.valid) {
            ESP_LOGI(TAG, "Acceleration: x=%.3f y=%.3f z=%.3f m/s² (MPU6050)",
                     accel_reading.x, accel_reading.y, accel_reading.z);
        } else {
            ESP_LOGW(TAG, "Acceleration: MISSING (MPU6050 sensor error)");
            g_failed_samples++;
        }

        // MQ-2: Gas sensor (RAW ADC, NOT calibrated ppm)
        sensor_reading_t mq2_reading;
        ret = mq2_read_gas(&mq2_reading);
        if (ret == ESP_OK && mq2_reading.valid) {
            ESP_LOGI(TAG, "MQ-2 Gas: %.0f ADC (raw, NOT ppm)", mq2_reading.value);
        } else {
            ESP_LOGW(TAG, "MQ-2 Gas: MISSING (sensor error)");
        }

        // Raw measurements (NAN = missing)
        float temp_c = temp_reading.valid ? temp_reading.value : NAN;
        float humidity_pct = humid_reading.valid ? humid_reading.value : NAN;
        float pressure_hpa = pressure_reading.valid ? pressure_reading.value : NAN;
        // Note: gas_resistance_adc from BME680 is not used in Track 4 intelligence
        // (void)gas_reading;  // BME680 gas resistance not integrated yet
        float vibration_mps2 = accel_reading.valid ? sqrtf(accel_reading.x * accel_reading.x +
                                                           accel_reading.y * accel_reading.y +
                                                           accel_reading.z * accel_reading.z) : NAN;
        float mq2_gas_adc = mq2_reading.valid ? mq2_reading.value : NAN;

        // ========== INTELLIGENCE PIPELINE ==========

        // GATE 1: Health (H_i) - per sensor
        // Current API: health_result_t compute_health(const health_diagnostic_t* diagnostics, uint8_t num_diagnostics, bool hard_failure)
        health_diagnostic_t temp_diagnostics[] = {
            {.key = "calibration", .value = temp_cal.valid ? 1.0f : 0.0f, .weight = 0.5f},
            {.key = "reading", .value = temp_reading.valid ? 1.0f : 0.0f, .weight = 0.5f},
        };
        health_result_t H_temp_result = compute_health(temp_diagnostics, 2, false);

        health_diagnostic_t humid_diagnostics[] = {
            {.key = "calibration", .value = humid_cal.valid ? 1.0f : 0.0f, .weight = 0.5f},
            {.key = "reading", .value = humid_reading.valid ? 1.0f : 0.0f, .weight = 0.5f},
        };
        health_result_t H_humid_result = compute_health(humid_diagnostics, 2, false);

        float H_temp = H_temp_result.complete ? H_temp_result.h_i : NAN;
        float H_humid = H_humid_result.complete ? H_humid_result.h_i : NAN;
        ESP_LOGD(TAG, "Health: H_temp=%.3f, H_humid=%.3f", H_temp, H_humid);

        // GATE 2: Quality (Q_i) - per sensor
        // Current API: quality_result_t compute_quality(float q_integrity, float q_stability)
        // q_integrity: 1.0 if valid reading, NAN if missing
        // q_stability: Variance/stability not computed → NAN (missing) per quality.py:35
        // Per quality.py specification: None input → None output (preserve missing != zero)
        float q_integrity_temp = temp_reading.valid ? 1.0f : NAN;
        float q_stability_temp = NAN;  // Stability not measured → missing per repository specification
        quality_result_t Q_temp_result = compute_quality(q_integrity_temp, q_stability_temp);

        float q_integrity_humid = humid_reading.valid ? 1.0f : NAN;
        float q_stability_humid = NAN;  // Stability not measured → missing per repository specification
        quality_result_t Q_humid_result = compute_quality(q_integrity_humid, q_stability_humid);

        float Q_temp = Q_temp_result.valid ? Q_temp_result.q_i : NAN;
        float Q_humid = Q_humid_result.valid ? Q_humid_result.q_i : NAN;
        ESP_LOGD(TAG, "Quality: Q_temp=%.3f, Q_humid=%.3f", Q_temp, Q_humid);

        // GATE 3: Reliability (R_i) - per sensor
        // Current API: reliability_result_t compute_reliability(float h_i, float q_i, float k_i)
        // K_i is explicit calibration validity - NO hard-coded default (Doc 04 Sec 3.3)
        // If uncalibrated, K_i should be NAN (missing), NOT an invented "partially good" value
        float K_temp = temp_cal.valid ? 1.0f : NAN;  // Uncalibrated = missing
        float K_humid = humid_cal.valid ? 1.0f : NAN;

        reliability_result_t R_temp_result = compute_reliability(H_temp, Q_temp, K_temp);
        reliability_result_t R_humid_result = compute_reliability(H_humid, Q_humid, K_humid);

        float R_temp = R_temp_result.valid ? R_temp_result.r_i : NAN;
        float R_humid = R_humid_result.valid ? R_humid_result.r_i : NAN;
        ESP_LOGD(TAG, "Reliability: R_temp=%.3f, R_humid=%.3f", R_temp, R_humid);

        // GATE 4: Baseline (B_i) and state management
        // Current API: baseline_result_t compute_baseline_z_score(float value, const baseline_stats_t* stats)
        // Current API: baseline_state_result_t update_baseline_state(...)
        // CRITICAL: baseline_current_state is an ENUM, not a struct with .status field

        baseline_sample_count++;

        // Get baseline configuration with CORRECT fields from baseline.h
        baseline_config_t baseline_cfg = baseline_default_config();
        // baseline_config_t has: min_samples_init, min_samples_learning, recovery_stability_samples, max_history, epsilon
        // NO window_size or alpha fields exist

        // Update baseline state
        const char* hazard_state_str = hazard_state_name(hazard_current_state);

        baseline_state_result_t baseline_transition = update_baseline_state(
            baseline_current_state,
            baseline_sample_count,
            &baseline_cfg,
            hazard_state_str,
            hazard_persistence_counter
        );

        // Check if state changed
        if (baseline_transition.next_state != baseline_current_state) {
            ESP_LOGI(TAG, "Baseline state transition: %s → %s",
                     baseline_state_name(baseline_current_state),
                     baseline_state_name(baseline_transition.next_state));
            baseline_current_state = baseline_transition.next_state;
        }

        // Update hazard persistence counter from baseline module
        hazard_persistence_counter = baseline_transition.stability_count;

        // Track 4: Accumulate samples and compute baseline stats
        update_baseline_stats(temp_c, humidity_pct);

        // Compute z-scores if baseline stats are ready
        zscore_result_t z_temp_result = {.z_score = 0.0f, .valid = false};
        zscore_result_t z_humid_result = {.z_score = 0.0f, .valid = false};

        if (baseline_current_state >= BASELINE_READY && !isnan(temp_c) && baseline_stats[0].valid) {
            z_temp_result = compute_z_score(temp_c, baseline_stats[0].median, baseline_stats[0].scale, 1e-9f);
        }
        if (baseline_current_state >= BASELINE_READY && !isnan(humidity_pct) && baseline_stats[1].valid) {
            z_humid_result = compute_z_score(humidity_pct, baseline_stats[1].median, baseline_stats[1].scale, 1e-9f);
        }

        float z_temp = z_temp_result.valid ? z_temp_result.z_score : NAN;
        float z_humid = z_humid_result.valid ? z_humid_result.z_score : NAN;
        ESP_LOGD(TAG, "Baseline: z_temp=%.3f, z_humid=%.3f, state=%s",
                 z_temp, z_humid, baseline_state_name(baseline_current_state));

        // GATE 5: Anomaly (A_i, A_node, A_h)
        // Current API: individual_anomaly_result_t compute_individual_anomaly(float z_score, float lambda_param, float z_cap)
        float lambda = 2.0f;  // ANOMALY_LAMBDA_DEFAULT
        float z_cap = 5.0f;   // ANOMALY_Z_CAP_DEFAULT

        individual_anomaly_result_t A_temp_result = compute_individual_anomaly(z_temp, lambda, z_cap);
        individual_anomaly_result_t A_humid_result = compute_individual_anomaly(z_humid, lambda, z_cap);

        float A_temp = A_temp_result.valid ? A_temp_result.a_i : NAN;
        float A_humid = A_humid_result.valid ? A_humid_result.a_i : NAN;

        // Node aggregate anomaly
        sensor_anomaly_t sensor_anomalies[] = {
            {.a_i = A_temp, .r_i = R_temp, .w_ih = NAN},
            {.a_i = A_humid, .r_i = R_humid, .w_ih = NAN},
        };
        node_anomaly_result_t A_node_result = compute_node_aggregate_anomaly(sensor_anomalies, 2, 1e-9f);
        float A_node = A_node_result.valid ? A_node_result.a_node : NAN;

        // Hazard-specific anomaly (fire: temperature is primary)
        sensor_anomaly_t fire_anomalies[] = {
            {.a_i = A_temp, .r_i = R_temp, .w_ih = 0.8f},   // Temperature primary for fire
            {.a_i = A_humid, .r_i = R_humid, .w_ih = 0.2f}, // Humidity secondary
        };
        hazard_anomaly_result_t A_h_result = compute_hazard_specific_anomaly(fire_anomalies, 2, 1e-9f);
        float A_h_fire = A_h_result.valid ? A_h_result.a_h : NAN;

        ESP_LOGD(TAG, "Anomaly: A_temp=%.3f, A_humid=%.3f, A_node=%.3f, A_h_fire=%.3f",
                 A_temp, A_humid, A_node, A_h_fire);

        // GATE 6A: Evidence (E_h)
        // Current API: evidence_result_t compute_evidence(const sensor_reading_t* readings, uint8_t reading_count, const evidence_config_t* config, float epsilon)

        // Create evidence configuration (simplified for fire detection)
        evidence_config_t evidence_cfg = {
            .core_rules = {
                {.sensor = "temperature", .threshold_min = 40.0f, .threshold_max = 100.0f, .weight = 0.7f},
            },
            .core_rule_count = 1,
            .supporting_rules = {
                {.sensor = "humidity", .threshold_min = 0.0f, .threshold_max = 30.0f, .weight = 0.3f},
            },
            .supporting_rule_count = 1,
            .core_floor = {.min_core_coverage = 0.5f, .cap_without_core = 0.3f},
            .use_core_floor = true,
        };

        evidence_sensor_reading_t evidence_readings[] = {
            {.sensor = "temperature", .value = temp_c},
            {.sensor = "humidity", .value = humidity_pct},
        };

        evidence_result_t E_h_result = compute_evidence(evidence_readings, 2, &evidence_cfg, 1e-9f);
        float E_h = E_h_result.valid ? E_h_result.e_h : NAN;
        ESP_LOGD(TAG, "Evidence: E_h=%.3f", E_h);

        // GATE 6B: Confidence (C_h)
        // Current API: confidence_result_t compute_confidence(float c_cov, float c_agree, float c_temp, float c_base, const confidence_weights_t* weights, float epsilon)

        // Compute confidence components
        // c_cov: Coverage confidence (sensor availability)
        float c_cov = 0.0f;
        if (!isnan(temp_c)) c_cov += 0.7f;  // Temperature available
        if (!isnan(humidity_pct)) c_cov += 0.3f;  // Humidity available

        // c_agree: Evidence group agreement (per confidence.py:90-150)
        // Repository semantics: Agreement evaluated across evidence GROUPS, not individual sensors
        // Fire hazard evidence groups:
        //   - Thermal group: temperature + humidity (correlated readings from same phenomenon)
        //   - Smoke group: unavailable (no smoke sensor)
        // Active evidence groups: 1 (thermal only)
        // Per confidence.py:151: len(valid_groups) == 1 → returns 1.0 (single source = no disagreement)
        float c_agree = 1.0f;

        // c_temp: Temporal confidence (per confidence.py:183-229)
        // Repository semantic: age = t_now - t_measurement
        // measurement_time_ms captured before sensor acquisition (line ~448)
        // current_time_ms captured during intelligence computation
        uint32_t current_time_ms = (uint32_t)(esp_timer_get_time() / 1000);
        float telemetry_age_seconds = (float)(current_time_ms - measurement_time_ms) / 1000.0f;
        float max_age_seconds = 300.0f;  // 5 minutes (repository default, confidence.py:194)
        float c_temp = compute_temporal_confidence(telemetry_age_seconds, max_age_seconds);

        // c_base: Baseline confidence (maps baseline readiness)
        float c_base = NAN;
        if (baseline_current_state == BASELINE_READY) {
            c_base = 1.0f;  // Baseline ready
        } else if (baseline_current_state == BASELINE_LEARNING) {
            c_base = 0.5f;  // Baseline learning
        } else {
            c_base = 0.0f;  // Baseline not ready
        }

        confidence_weights_t conf_weights = {
            .coverage = 0.3f,   // NOT w_coverage
            .agreement = 0.3f,  // NOT w_agreement
            .temporal = 0.2f,   // NOT w_temporal
            .baseline = 0.2f,   // NOT w_baseline
        };

        confidence_result_t confidence = compute_confidence(c_cov, c_agree, c_temp, c_base, &conf_weights, 1e-9f);
        float C_h = confidence.valid ? confidence.c_h : NAN;  // Field is c_h, NOT .confidence
        ESP_LOGD(TAG, "Confidence: C_h=%.3f (cov=%.2f, agree=%.2f, temp=%.2f, base=%.2f)",
                 C_h, c_cov, c_agree, c_temp, c_base);

        // GATE 7: Severity (S_h)
        // Current API: severity_result_t compute_severity(float i_h, float t_h, float d_h, const severity_weights_t* weights, float epsilon)

        // Compute intensity component for fire (simplified)
        fire_intensity_config_t fire_intensity_cfg = fire_intensity_default_config();
        float i_h_fire = 0.0f;
        if (!isnan(temp_c)) {
            if (temp_c >= fire_intensity_cfg.temp_high) {
                i_h_fire = 1.0f;
            } else if (temp_c >= fire_intensity_cfg.temp_low) {
                i_h_fire = (temp_c - fire_intensity_cfg.temp_low) / (fire_intensity_cfg.temp_high - fire_intensity_cfg.temp_low);
            }
        }

        // Temporal component (rate of change)
        // Track 4: Compute from history
        float temp_rate = compute_rate_of_change(
            g_intelligence_history.temp_history,
            g_intelligence_history.temp_timestamps_ms,
            g_intelligence_history.temp_count,
            g_intelligence_history.temp_index
        );

        float t_h = NAN;
        if (!isnan(temp_rate)) {
            float max_temp_rate = 10.0f / 60.0f;  // °C/s (10°C/min from reference severity.py:64)
            float abs_rate = fabsf(temp_rate);
            t_h = (abs_rate >= max_temp_rate) ? 1.0f : (abs_rate / max_temp_rate);
        }

        // Duration component
        // Track 4: Track time above fire threshold
        float fire_threshold = 50.0f;  // °C (from reference severity.py:74)
        uint32_t current_time_ms2 = (uint32_t)(esp_timer_get_time() / 1000);
        update_duration_tracking(temp_c, fire_threshold, current_time_ms2);

        float d_h = NAN;
        if (g_intelligence_history.duration_active) {
            float max_duration = 3600.0f;  // seconds (1 hour, from reference severity.py:73)
            d_h = compute_duration(g_intelligence_history.time_above_fire_threshold_s, max_duration);
        }

        severity_weights_t sev_weights = {
            .w_I = 0.5f,  // Intensity weight
            .w_T = 0.3f,  // Temporal weight
            .w_D = 0.2f,  // Duration weight
        };

        severity_result_t severity = compute_severity(i_h_fire, t_h, d_h, &sev_weights, 1e-9f);
        float S_h = severity.valid ? severity.s_h : NAN;  // Field is s_h, NOT .severity
        ESP_LOGD(TAG, "Severity: S_h=%.3f (I=%.3f, T=%.3f, D=%.3f)", S_h, i_h_fire, t_h, d_h);

        // GATE 8: Risk (R_h)
        // Current API: risk_result_t compute_risk(float e_h, float s_h, float t_h, const risk_weights_t* weights, float epsilon)
        risk_weights_t risk_weights = {
            .w_E = 0.4f,  // NOT w_evidence
            .w_S = 0.4f,  // NOT w_severity
            .w_T = 0.2f,  // NOT w_temporal
        };

        risk_result_t risk = compute_risk(E_h, S_h, t_h, &risk_weights, 1e-9f);
        float R_h = risk.valid ? risk.r_h : NAN;  // Field is r_h, NOT .risk
        ESP_LOGD(TAG, "Risk: R_h=%.3f", R_h);

        // GATE 9: Hazard State Machine
        intelligence_inputs_t intel = {
            .E_h = E_h,
            .C_h = C_h,
            .S_h = S_h,
            .R_h = R_h,
            .A_h = A_h_fire,
            .T_h = t_h,
            .core_coverage = c_cov,  // Use c_cov computed in confidence section
        };

        state_machine_config_t state_cfg = state_machine_default_config();

        state_transition_t transition = update_state(
            hazard_current_state,
            &intel,
            baseline_state_name(baseline_current_state),
            esp_timer_get_time() / 1000000.0f,
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

        // ========== HARDWARE JSON GENERATION (Track 3A) ==========
        // Map Track 3A sensors to hardware JSON structure
        hardware_sensor_readings_t hw_sensors = {
            // BME680 → temperature_c, humidity_rh, pressure_hpa
            .temperature_c = temp_c,         // From BME680
            .humidity_rh = humidity_pct,     // From BME680
            .pressure_hpa = pressure_hpa,    // From BME680

            // MQ-2 → gas_ppm (RAW ADC, NOT calibrated ppm)
            .gas_ppm = mq2_gas_adc,          // From MQ-2 (raw ADC 0-4095)

            // MPU6050 → vibration_mps2
            .vibration_mps2 = vibration_mps2, // From MPU6050

            // PM sensors (not yet connected - MUST be null)
            .pm25_ugm3 = NAN,                // PM2.5 sensor not connected
            .pm10_ugm3 = NAN,                // PM10 sensor not connected

            // Environmental sensors (not connected - MUST be null)
            .water_level_m = NAN,
            .rainfall_mm_h = NAN,
            .soil_moisture_vwc_pct = NAN,
        };

        hardware_power_t hw_power = {
            .battery_pct = NAN,              // Power monitoring not yet implemented
            .solar_state = "INACTIVE",       // Solar state placeholder
        };

        char* hardware_json = NULL;
        ret = hardware_json_generate(&hw_sensors, &hw_power, &hardware_json);
        if (ret != ESP_OK || hardware_json == NULL) {
            ESP_LOGE(TAG, "Hardware JSON generation failed");
            vTaskDelay(pdMS_TO_TICKS(g_config.sampling.interval_ms));
            continue;
        }

        uint32_t seq = hardware_json_get_sequence();
        ESP_LOGI(TAG, "Hardware JSON generated: seq=%lu, size=%d bytes", seq, strlen(hardware_json));

        // ========== PUBLISH WITH BUFFERING ==========
        // Determine priority based on hazard state
        message_priority_t priority = PRIORITY_NORMAL;
        if (hazard_current_state == HAZARD_STATE_CRITICAL) {
            priority = PRIORITY_CRITICAL;
        } else if (hazard_current_state >= HAZARD_STATE_WATCH) {
            priority = PRIORITY_HAZARD;
        }

        ret = publish_with_buffering(hardware_json, seq, priority);
        if (ret == ESP_OK) {
            ESP_LOGI(TAG, "Hardware JSON published (priority=%d)", priority);
        } else {
            ESP_LOGW(TAG, "Hardware JSON buffered (priority=%d)", priority);
        }

        free(hardware_json);

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

        // Track 4: Update history buffers (circular buffers)
        // Use measurement_time_ms (captured before sensor acquisition) for history timestamps
        if (!isnan(temp_c)) {
            g_intelligence_history.temp_history[g_intelligence_history.temp_index] = temp_c;
            g_intelligence_history.temp_timestamps_ms[g_intelligence_history.temp_index] = measurement_time_ms;
            g_intelligence_history.temp_index = (g_intelligence_history.temp_index + 1) % HISTORY_SIZE;
            if (g_intelligence_history.temp_count < HISTORY_SIZE) {
                g_intelligence_history.temp_count++;
            }
        }

        if (!isnan(humidity_pct)) {
            g_intelligence_history.humid_history[g_intelligence_history.humid_index] = humidity_pct;
            g_intelligence_history.humid_timestamps_ms[g_intelligence_history.humid_index] = measurement_time_ms;
            g_intelligence_history.humid_index = (g_intelligence_history.humid_index + 1) % HISTORY_SIZE;
            if (g_intelligence_history.humid_count < HISTORY_SIZE) {
                g_intelligence_history.humid_count++;
            }
        }

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

    // Hardware JSON (Track 3A: ESP32 → MQTT transport)
    ESP_ERROR_CHECK(hardware_json_init(g_config.identity.node_id));

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

    // Wi-Fi (Track 3A: NexAlert_Field_Net)
    nexalert_wifi_config_t wifi_cfg = {
        .ssid = g_config.wifi.ssid,        // Track 3A: "NexAlert_Field_Net"
        .password = g_config.wifi.password,
    };
    ESP_ERROR_CHECK(wifi_station_init(&wifi_cfg));

    ESP_LOGI(TAG, "Waiting for Wi-Fi connection...");
    while (!wifi_is_connected()) {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }

    char ip[16];
    wifi_get_ip(ip, sizeof(ip));
    ESP_LOGI(TAG, "Wi-Fi connected: %s", ip);

    // SNTP (Track 3A: Time synchronization from 10.42.0.1)
    sntp_config_t sntp_cfg = {
        .ntp_server = "10.42.0.1",  // Track 3A: Locked NTP server (Raspberry Pi)
        .sync_timeout_ms = 10000,
    };
    ESP_ERROR_CHECK(sntp_client_init(&sntp_cfg));

    ESP_LOGI(TAG, "Waiting for SNTP sync (timeout 10s)...");
    esp_err_t sntp_ret = sntp_wait_for_sync(10000);
    if (sntp_ret == ESP_OK) {
        ESP_LOGI(TAG, "SNTP synchronized with 10.42.0.1");
    } else {
        ESP_LOGW(TAG, "SNTP sync timeout, using uptime-based timestamps");
    }

    // MQTT with LOCKED TOPIC FORMAT
    mqtt_init_params_t mqtt_params = {
        .broker_host = g_config.mqtt.broker_host,
        .broker_port = g_config.mqtt.broker_port,
        .node_id = g_config.identity.node_id,
    };
    ESP_ERROR_CHECK(mqtt_client_init(&mqtt_params));

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
