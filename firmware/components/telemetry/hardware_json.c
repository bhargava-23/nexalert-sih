/**
 * @file hardware_json.c
 * @brief Hardware JSON payload serializer for ESP32 → MQTT transport
 *
 * Track 3A: Implements the EXACT hardware JSON contract from recovered Arduino deployment.
 */

#include "hardware_json.h"
#include "cJSON.h"
#include "esp_log.h"
#include "esp_timer.h"
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <math.h>

static const char *TAG = "hardware_json";

// Module state
static struct {
    bool initialized;
    char node_id[32];
    uint32_t sequence;
} hw_state = {0};

esp_err_t hardware_json_init(const char* node_id)
{
    if (node_id == NULL || strlen(node_id) == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    strncpy(hw_state.node_id, node_id, sizeof(hw_state.node_id) - 1);
    hw_state.node_id[sizeof(hw_state.node_id) - 1] = '\0';
    hw_state.sequence = 0;
    hw_state.initialized = true;

    ESP_LOGI(TAG, "Hardware JSON initialized: node_id=%s", hw_state.node_id);
    return ESP_OK;
}

/**
 * Helper: Add float to JSON object, or null if NAN
 */
static void add_float_or_null(cJSON* obj, const char* key, float value)
{
    if (isnan(value)) {
        cJSON_AddNullToObject(obj, key);
    } else {
        cJSON_AddNumberToObject(obj, key, (double)value);
    }
}

esp_err_t hardware_json_generate(
    const hardware_sensor_readings_t* sensors,
    const hardware_power_t* power,
    char** out_json)
{
    if (!hw_state.initialized || sensors == NULL || power == NULL || out_json == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    // Increment sequence
    hw_state.sequence++;

    // Create root object
    cJSON* root = cJSON_CreateObject();
    if (root == NULL) {
        return ESP_ERR_NO_MEM;
    }

    // node_id
    cJSON_AddStringToObject(root, "node_id", hw_state.node_id);

    // timestamp_ms (Unix milliseconds)
    int64_t timestamp_ms = esp_timer_get_time() / 1000;  // Convert µs to ms
    cJSON_AddNumberToObject(root, "timestamp_ms", (double)timestamp_ms);

    // sequence
    cJSON_AddNumberToObject(root, "sequence", hw_state.sequence);

    // sensors object
    cJSON* sensors_obj = cJSON_AddObjectToObject(root, "sensors");
    if (sensors_obj != NULL) {
        add_float_or_null(sensors_obj, "temperature_c", sensors->temperature_c);
        add_float_or_null(sensors_obj, "humidity_rh", sensors->humidity_rh);
        add_float_or_null(sensors_obj, "pm25_ugm3", sensors->pm25_ugm3);
        add_float_or_null(sensors_obj, "pm10_ugm3", sensors->pm10_ugm3);
        add_float_or_null(sensors_obj, "gas_ppm", sensors->gas_ppm);
        add_float_or_null(sensors_obj, "pressure_hpa", sensors->pressure_hpa);
        add_float_or_null(sensors_obj, "water_level_m", sensors->water_level_m);
        add_float_or_null(sensors_obj, "rainfall_mm_h", sensors->rainfall_mm_h);
        add_float_or_null(sensors_obj, "soil_moisture_vwc_pct", sensors->soil_moisture_vwc_pct);
        add_float_or_null(sensors_obj, "vibration_mps2", sensors->vibration_mps2);
    }

    // availability object (derived from NAN check)
    cJSON* availability_obj = cJSON_AddObjectToObject(root, "availability");
    if (availability_obj != NULL) {
        cJSON_AddBoolToObject(availability_obj, "temperature", !isnan(sensors->temperature_c));
        cJSON_AddBoolToObject(availability_obj, "humidity", !isnan(sensors->humidity_rh));
        cJSON_AddBoolToObject(availability_obj, "pm25", !isnan(sensors->pm25_ugm3));
        cJSON_AddBoolToObject(availability_obj, "pm10", !isnan(sensors->pm10_ugm3));
        cJSON_AddBoolToObject(availability_obj, "gas", !isnan(sensors->gas_ppm));
        cJSON_AddBoolToObject(availability_obj, "pressure", !isnan(sensors->pressure_hpa));
        cJSON_AddBoolToObject(availability_obj, "water_level", !isnan(sensors->water_level_m));
        cJSON_AddBoolToObject(availability_obj, "rainfall", !isnan(sensors->rainfall_mm_h));
        cJSON_AddBoolToObject(availability_obj, "soil_moisture", !isnan(sensors->soil_moisture_vwc_pct));
        cJSON_AddBoolToObject(availability_obj, "vibration", !isnan(sensors->vibration_mps2));
    }

    // power object
    cJSON* power_obj = cJSON_AddObjectToObject(root, "power");
    if (power_obj != NULL) {
        add_float_or_null(power_obj, "battery_pct", power->battery_pct);

        if (power->solar_state != NULL) {
            cJSON_AddStringToObject(power_obj, "solar_state", power->solar_state);
        } else {
            cJSON_AddNullToObject(power_obj, "solar_state");
        }
    }

    // Serialize to JSON string
    *out_json = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);

    if (*out_json == NULL) {
        ESP_LOGE(TAG, "JSON serialization failed");
        return ESP_ERR_NO_MEM;
    }

    ESP_LOGD(TAG, "Generated hardware JSON, sequence=%u, size=%d bytes",
             hw_state.sequence, strlen(*out_json));
    return ESP_OK;
}

uint32_t hardware_json_get_sequence(void)
{
    return hw_state.sequence;
}
