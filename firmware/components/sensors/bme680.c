/**
 * @file bme680.c
 * @brief BME680 environmental sensor driver (I2C)
 *
 * Bosch BME680 implementation for ESP32-S3.
 * Matches recovered Arduino deployment behavior.
 *
 * NOTE: This is a minimal driver for Track 3A. A production implementation
 * would use the full Bosch BME680 driver library with proper sensor
 * configuration, gas heater control, and compensation algorithms.
 *
 * Track 3A focuses on interface compatibility and build verification.
 * Physical sensor operation requires the actual hardware.
 */

#include "bme680.h"
#include "i2c_bus.h"
#include "esp_log.h"
#include <math.h>

static const char *TAG = "bme680";

// BME680 register addresses (subset for minimal driver)
#define BME680_REG_CHIP_ID          0xD0
#define BME680_REG_STATUS           0x1D
#define BME680_REG_TEMP_MSB         0x22
#define BME680_REG_HUMIDITY_MSB     0x25
#define BME680_REG_PRESSURE_MSB     0x1F
#define BME680_REG_GAS_R_MSB        0x2A

#define BME680_CHIP_ID              0x61

static bool bme680_initialized = false;
static uint8_t bme680_addr = BME680_I2C_ADDR_PRIMARY;
static calibration_t temp_cal;
static calibration_t humid_cal;
static calibration_t pressure_cal;

esp_err_t bme680_init(const bme680_config_t* config)
{
    if (config == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Store calibration
    temp_cal = config->temp_cal;
    humid_cal = config->humid_cal;
    pressure_cal = config->pressure_cal;

    // Try primary address first
    uint8_t chip_id;
    esp_err_t ret = i2c_bus_read(BME680_I2C_ADDR_PRIMARY, BME680_REG_CHIP_ID, &chip_id, 1);

    if (ret == ESP_OK && chip_id == BME680_CHIP_ID) {
        bme680_addr = BME680_I2C_ADDR_PRIMARY;
        ESP_LOGI(TAG, "BME680 found at 0x%02X (chip_id=0x%02X)", bme680_addr, chip_id);
        bme680_initialized = true;
        return ESP_OK;
    }

    // Fallback to secondary address (matches recovered Arduino behavior)
    ret = i2c_bus_read(BME680_I2C_ADDR_SECONDARY, BME680_REG_CHIP_ID, &chip_id, 1);

    if (ret == ESP_OK && chip_id == BME680_CHIP_ID) {
        bme680_addr = BME680_I2C_ADDR_SECONDARY;
        ESP_LOGI(TAG, "BME680 found at 0x%02X (chip_id=0x%02X)", bme680_addr, chip_id);
        bme680_initialized = true;
        return ESP_OK;
    }

    ESP_LOGE(TAG, "BME680 not found at 0x%02X or 0x%02X",
             BME680_I2C_ADDR_PRIMARY, BME680_I2C_ADDR_SECONDARY);
    return ESP_ERR_NOT_FOUND;
}

esp_err_t bme680_read_temperature(sensor_reading_t* out)
{
    if (!bme680_initialized || out == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    // Read temperature registers (simplified - production needs full compensation)
    uint8_t data[3];
    esp_err_t ret = i2c_bus_read(bme680_addr, BME680_REG_TEMP_MSB, data, 3);

    if (ret != ESP_OK) {
        out->valid = false;
        out->value = NAN;
        return ESP_FAIL;
    }

    // Simplified temperature calculation (production needs calibration coefficients)
    // This is a placeholder that returns a plausible value for build verification
    int32_t adc_temp = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4);
    float temp_c = (float)adc_temp / 5120.0f;  // Simplified conversion

    // Apply calibration if valid
    if (temp_cal.valid) {
        temp_c = temp_c * temp_cal.scale + temp_cal.offset;
    }

    out->value = temp_c;
    out->valid = true;

    return ESP_OK;
}

esp_err_t bme680_read_humidity(sensor_reading_t* out)
{
    if (!bme680_initialized || out == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    // Read humidity registers (simplified - production needs full compensation)
    uint8_t data[2];
    esp_err_t ret = i2c_bus_read(bme680_addr, BME680_REG_HUMIDITY_MSB, data, 2);

    if (ret != ESP_OK) {
        out->valid = false;
        out->value = NAN;
        return ESP_FAIL;
    }

    // Simplified humidity calculation (production needs calibration coefficients)
    int32_t adc_humid = (data[0] << 8) | data[1];
    float humidity_pct = (float)adc_humid / 1024.0f;  // Simplified conversion

    // Apply calibration if valid
    if (humid_cal.valid) {
        humidity_pct = humidity_pct * humid_cal.scale + humid_cal.offset;
    }

    // Clamp to 0-100%
    if (humidity_pct < 0.0f) humidity_pct = 0.0f;
    if (humidity_pct > 100.0f) humidity_pct = 100.0f;

    out->value = humidity_pct;
    out->valid = true;

    return ESP_OK;
}

esp_err_t bme680_read_pressure(sensor_reading_t* out)
{
    if (!bme680_initialized || out == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    // Read pressure registers (simplified - production needs full compensation)
    uint8_t data[3];
    esp_err_t ret = i2c_bus_read(bme680_addr, BME680_REG_PRESSURE_MSB, data, 3);

    if (ret != ESP_OK) {
        out->valid = false;
        out->value = NAN;
        return ESP_FAIL;
    }

    // Simplified pressure calculation (production needs calibration coefficients)
    int32_t adc_press = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4);
    float pressure_hpa = (float)adc_press / 256.0f;  // Simplified conversion

    // Apply calibration if valid
    if (pressure_cal.valid) {
        pressure_hpa = pressure_hpa * pressure_cal.scale + pressure_cal.offset;
    }

    out->value = pressure_hpa;
    out->valid = true;

    return ESP_OK;
}

esp_err_t bme680_read_gas(sensor_reading_t* out)
{
    if (!bme680_initialized || out == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    // Read gas resistance registers (simplified - production needs heater control)
    uint8_t data[2];
    esp_err_t ret = i2c_bus_read(bme680_addr, BME680_REG_GAS_R_MSB, data, 2);

    if (ret != ESP_OK) {
        out->valid = false;
        out->value = NAN;
        return ESP_FAIL;
    }

    // Raw gas resistance ADC value (NOT calibrated to specific gas ppm)
    int32_t gas_adc = (data[0] << 2) | (data[1] >> 6);

    // Return raw ADC value, matching MQ-2 semantics
    // This is NOT ppm, NOT calibrated to specific gas concentration
    out->value = (float)gas_adc;
    out->valid = true;

    return ESP_OK;
}

esp_err_t bme680_deinit(void)
{
    bme680_initialized = false;
    ESP_LOGI(TAG, "BME680 deinitialized");
    return ESP_OK;
}
