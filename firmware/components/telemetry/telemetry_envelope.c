/**
 * @file telemetry_envelope.c
 * @brief Canonical NexAlert telemetry envelope generation (LOCKED contract)
 *
 * Implements schemas/telemetry-envelope.schema.json.
 * Preserves missing != zero invariant via JSON null serialization.
 */

#include "telemetry_envelope.h"
#include "cJSON.h"
#include "esp_log.h"
#include "esp_timer.h"
#include <string.h>
#include <time.h>
#include <math.h>

static const char *TAG = "telemetry";

// Module state
static struct {
    bool initialized;
    char node_id[32];
    float latitude;
    float longitude;
    float altitude;
    uint32_t sequence;
} telem_state = {0};

esp_err_t telemetry_envelope_init(const telemetry_config_t* config)
{
    if (config == NULL || config->node_id == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    strncpy(telem_state.node_id, config->node_id, sizeof(telem_state.node_id) - 1);
    telem_state.latitude = config->latitude;
    telem_state.longitude = config->longitude;
    telem_state.altitude = config->altitude;
    telem_state.sequence = 0;
    telem_state.initialized = true;

    ESP_LOGI(TAG, "Initialized for node %s at %.6f,%.6f",
             telem_state.node_id, telem_state.latitude, telem_state.longitude);

    return ESP_OK;
}

/**
 * Generate ULID (simplified: timestamp + random)
 */
static void generate_ulid(char* out, size_t len)
{
    uint64_t timestamp_ms = esp_timer_get_time() / 1000;
    uint32_t random = esp_random();
    snprintf(out, len, "%016llX%010X", timestamp_ms, random);
}

/**
 * Format ISO 8601 timestamp
 */
static void format_iso8601(char* out, size_t len)
{
    time_t now = time(NULL);
    struct tm timeinfo;
    gmtime_r(&now, &timeinfo);
    strftime(out, len, "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
}

/**
 * Add numeric field as null or number
 * CRITICAL: Preserves missing != zero invariant
 */
static void add_nullable_number(cJSON* obj, const char* key, float value)
{
    if (isnan(value)) {
        cJSON_AddNullToObject(obj, key);
    } else {
        cJSON_AddNumberToObject(obj, key, value);
    }
}

/**
 * Add boolean field as null or boolean
 */
static void add_nullable_bool(cJSON* obj, const char* key, bool value, bool present)
{
    if (!present) {
        cJSON_AddNullToObject(obj, key);
    } else {
        cJSON_AddBoolToObject(obj, key, value);
    }
}

esp_err_t telemetry_envelope_generate(
    const measurements_t* measurements,
    const diagnostics_t* diagnostics,
    const power_t* power,
    char** out_json)
{
    if (!telem_state.initialized || out_json == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    // Create JSON root object
    cJSON* root = cJSON_CreateObject();
    if (root == NULL) {
        return ESP_ERR_NO_MEM;
    }

    // Schema version (LOCKED)
    cJSON_AddStringToObject(root, "schema_version", "telemetry.v1");

    // Telemetry ID (ULID)
    char telemetry_id[32];
    generate_ulid(telemetry_id, sizeof(telemetry_id));
    cJSON_AddStringToObject(root, "telemetry_id", telemetry_id);

    // Node ID
    cJSON_AddStringToObject(root, "node_id", telem_state.node_id);

    // Sequence (monotonic)
    cJSON_AddNumberToObject(root, "sequence", telem_state.sequence++);

    // Timestamps
    char timestamp[32];
    format_iso8601(timestamp, sizeof(timestamp));
    cJSON_AddStringToObject(root, "measurement_timestamp", timestamp);
    cJSON_AddStringToObject(root, "received_timestamp", timestamp); // Will be overwritten by backend

    // Location
    cJSON* location = cJSON_CreateObject();
    cJSON_AddNumberToObject(location, "lat", telem_state.latitude);
    cJSON_AddNumberToObject(location, "lon", telem_state.longitude);
    add_nullable_number(location, "alt", telem_state.altitude);
    cJSON_AddItemToObject(root, "location", location);

    // Measurements (CRITICAL: missing != zero via null)
    if (measurements != NULL) {
        cJSON* meas = cJSON_CreateObject();
        add_nullable_number(meas, "temp_c", measurements->temp_c);
        add_nullable_number(meas, "humidity_pct", measurements->humidity_pct);
        add_nullable_number(meas, "pressure_hpa", measurements->pressure_hpa);
        add_nullable_number(meas, "pm25_ug_m3", measurements->pm25_ug_m3);
        add_nullable_number(meas, "pm10_ug_m3", measurements->pm10_ug_m3);
        cJSON_AddItemToObject(root, "measurements", meas);
    } else {
        cJSON_AddObjectToObject(root, "measurements");
    }

    // Diagnostics (Per Document 04, Section 3.1)
    if (diagnostics != NULL) {
        cJSON* diag = cJSON_CreateObject();
        if (diagnostics->uptime_s > 0) {
            cJSON_AddNumberToObject(diag, "uptime_s", diagnostics->uptime_s);
        } else {
            cJSON_AddNullToObject(diag, "uptime_s");
        }
        add_nullable_bool(diag, "self_test_passed", diagnostics->self_test_passed, true);
        add_nullable_number(diag, "comm_integrity", diagnostics->comm_integrity);
        add_nullable_bool(diag, "calibration_valid", diagnostics->calibration_valid, true);
        add_nullable_number(diag, "stability_index", diagnostics->stability_index);
        cJSON_AddItemToObject(root, "diagnostics", diag);
    } else {
        cJSON_AddObjectToObject(root, "diagnostics");
    }

    // Power
    if (power != NULL) {
        cJSON* pwr = cJSON_CreateObject();
        add_nullable_number(pwr, "battery_pct", power->battery_pct);
        add_nullable_number(pwr, "battery_voltage", power->battery_voltage);
        add_nullable_number(pwr, "solar_current", power->solar_current);
        cJSON_AddItemToObject(root, "power", pwr);
    } else {
        cJSON_AddObjectToObject(root, "power");
    }

    // Source (LOCKED: "HARDWARE" for ESP32)
    cJSON_AddStringToObject(root, "source", "HARDWARE");

    // Serialize to JSON string
    *out_json = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);

    if (*out_json == NULL) {
        ESP_LOGE(TAG, "JSON serialization failed");
        return ESP_ERR_NO_MEM;
    }

    ESP_LOGD(TAG, "Generated telemetry envelope, sequence=%u", telem_state.sequence - 1);
    return ESP_OK;
}

uint32_t telemetry_envelope_get_sequence(void)
{
    return telem_state.sequence;
}
