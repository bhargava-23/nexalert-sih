/**
 * @file calibration_store.c
 * @brief NVS-based calibration storage implementation
 *
 * Per Decision C2: Calibration is versioned provisioning artifact.
 * Stores per-node, per-sensor calibration coefficients in ESP32 NVS.
 */

#include "calibration_store.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_log.h"
#include <string.h>

static const char *TAG = "calibration_store";
static const char *NVS_NAMESPACE = "calibration";

// NVS key format: "type_id" (e.g., "0_temp", "0_humid")
#define MAX_KEY_LEN 16

esp_err_t calibration_store_init(void)
{
    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        // NVS partition was truncated, erase and reinitialize
        ESP_LOGW(TAG, "NVS initialization failed, erasing...");
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }

    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "NVS init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "Calibration store initialized");
    return ESP_OK;
}

/**
 * Generate NVS key from sensor type and ID
 */
static void make_nvs_key(sensor_type_t type, const char* sensor_id, char* key_out)
{
    snprintf(key_out, MAX_KEY_LEN, "%d_%s", (int)type, sensor_id);
}

esp_err_t calibration_load(sensor_type_t type, const char* sensor_id, calibration_t* cal)
{
    if (sensor_id == NULL || cal == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    char key[MAX_KEY_LEN];
    make_nvs_key(type, sensor_id, key);

    nvs_handle_t handle;
    esp_err_t ret = nvs_open(NVS_NAMESPACE, NVS_READONLY, &handle);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Failed to open NVS: %s", esp_err_to_name(ret));
        cal->valid = false;
        return ret;
    }

    // Read calibration blob
    size_t required_size = sizeof(calibration_t);
    ret = nvs_get_blob(handle, key, cal, &required_size);
    nvs_close(handle);

    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "Loaded calibration for %s: offset=%.4f, scale=%.4f, version=%u",
                 sensor_id, cal->offset, cal->scale, cal->version);
        cal->valid = true;
        return ESP_OK;
    } else if (ret == ESP_ERR_NVS_NOT_FOUND) {
        ESP_LOGI(TAG, "No calibration found for %s", sensor_id);
        cal->valid = false;
        cal->offset = 0.0f;
        cal->scale = 1.0f;
        cal->version = 0;
        return ESP_ERR_NOT_FOUND;
    } else {
        ESP_LOGE(TAG, "Failed to load calibration for %s: %s", sensor_id, esp_err_to_name(ret));
        cal->valid = false;
        return ret;
    }
}

esp_err_t calibration_save(sensor_type_t type, const char* sensor_id, const calibration_t* cal)
{
    if (sensor_id == NULL || cal == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    char key[MAX_KEY_LEN];
    make_nvs_key(type, sensor_id, key);

    nvs_handle_t handle;
    esp_err_t ret = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &handle);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to open NVS for write: %s", esp_err_to_name(ret));
        return ret;
    }

    // Write calibration blob
    ret = nvs_set_blob(handle, key, cal, sizeof(calibration_t));
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to write calibration: %s", esp_err_to_name(ret));
        nvs_close(handle);
        return ret;
    }

    // Commit
    ret = nvs_commit(handle);
    nvs_close(handle);

    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "Saved calibration for %s: offset=%.4f, scale=%.4f, version=%u",
                 sensor_id, cal->offset, cal->scale, cal->version);
    } else {
        ESP_LOGE(TAG, "Failed to commit calibration: %s", esp_err_to_name(ret));
    }

    return ret;
}

esp_err_t calibration_clear_all(void)
{
    nvs_handle_t handle;
    esp_err_t ret = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &handle);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to open NVS for erase: %s", esp_err_to_name(ret));
        return ret;
    }

    ret = nvs_erase_all(handle);
    if (ret == ESP_OK) {
        ret = nvs_commit(handle);
    }

    nvs_close(handle);

    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "Cleared all calibrations");
    } else {
        ESP_LOGE(TAG, "Failed to clear calibrations: %s", esp_err_to_name(ret));
    }

    return ret;
}
