/**
 * @file mq2.c
 * @brief MQ-2 gas sensor driver (ADC)
 *
 * MQ-2 combustible gas sensor implementation for ESP32-S3.
 * Matches recovered Arduino deployment behavior.
 *
 * IMPORTANT: Returns RAW ADC value (0-4095), NOT calibrated to ppm.
 * The recovered Arduino deployment published this in a field named "gas_ppm",
 * which is MISLEADING. This driver preserves the raw ADC semantic.
 */

#include "mq2.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_log.h"
#include <math.h>

static const char *TAG = "mq2";

static bool mq2_initialized = false;
static adc_oneshot_unit_handle_t adc1_handle = NULL;
static adc_channel_t mq2_channel;

esp_err_t mq2_init(const mq2_config_t* config)
{
    if (config == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Initialize ADC1
    adc_oneshot_unit_init_cfg_t init_config = {
        .unit_id = ADC_UNIT_1,
    };

    esp_err_t ret = adc_oneshot_new_unit(&init_config, &adc1_handle);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADC1 unit init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Configure ADC channel
    mq2_channel = config->adc_channel;
    adc_oneshot_chan_cfg_t chan_config = {
        .bitwidth = ADC_BITWIDTH_12,  // 0-4095
        .atten = ADC_ATTEN_DB_12,     // 12 dB attenuation, 0-3.3V range (ADC_ATTEN_DB_11 deprecated in ESP-IDF 5.1.7)
    };

    ret = adc_oneshot_config_channel(adc1_handle, mq2_channel, &chan_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADC channel config failed: %s", esp_err_to_name(ret));
        adc_oneshot_del_unit(adc1_handle);
        return ret;
    }

    mq2_initialized = true;
    ESP_LOGI(TAG, "MQ-2 initialized on GPIO%d (ADC1 channel %d)", config->gpio_pin, config->adc_channel);

    return ESP_OK;
}

esp_err_t mq2_read_gas(sensor_reading_t* out)
{
    if (!mq2_initialized || out == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    int adc_raw;
    esp_err_t ret = adc_oneshot_read(adc1_handle, mq2_channel, &adc_raw);

    if (ret != ESP_OK) {
        ESP_LOGD(TAG, "ADC read failed: %s", esp_err_to_name(ret));
        out->valid = false;
        out->value = NAN;
        return ESP_FAIL;
    }

    // Return raw ADC value (0-4095)
    // This is NOT calibrated to ppm or any specific gas concentration
    // The recovered Arduino deployment published this in "gas_ppm" field,
    // but it is NOT actually ppm. It is raw ADC only.
    out->value = (float)adc_raw;
    out->valid = true;

    return ESP_OK;
}

esp_err_t mq2_deinit(void)
{
    if (!mq2_initialized) {
        return ESP_OK;
    }

    if (adc1_handle != NULL) {
        adc_oneshot_del_unit(adc1_handle);
        adc1_handle = NULL;
    }

    mq2_initialized = false;
    ESP_LOGI(TAG, "MQ-2 deinitialized");

    return ESP_OK;
}
