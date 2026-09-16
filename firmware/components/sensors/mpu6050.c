/**
 * @file mpu6050.c
 * @brief MPU6050 accelerometer/gyroscope driver (I2C)
 *
 * InvenSense MPU6050 implementation for ESP32-S3.
 * Matches recovered Arduino deployment behavior.
 *
 * NOTE: This is a minimal driver for Track 3A. A production implementation
 * would use proper sensor configuration, self-test, and advanced features.
 *
 * Track 3A focuses on interface compatibility and build verification.
 * Physical sensor operation requires the actual hardware.
 */

#include "mpu6050.h"
#include "i2c_bus.h"
#include "esp_log.h"
#include <math.h>

static const char *TAG = "mpu6050";

// MPU6050 register addresses
#define MPU6050_REG_WHO_AM_I        0x75
#define MPU6050_REG_PWR_MGMT_1      0x6B
#define MPU6050_REG_ACCEL_XOUT_H    0x3B
#define MPU6050_REG_ACCEL_CONFIG    0x1C

#define MPU6050_WHO_AM_I_VALUE      0x68
#define MPU6050_ACCEL_SCALE_2G      16384.0f  // LSB/g for ±2g range

static bool mpu6050_initialized = false;

esp_err_t mpu6050_init(const mpu6050_config_t* config)
{
    if (config == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Read WHO_AM_I register
    uint8_t who_am_i;
    esp_err_t ret = i2c_bus_read(config->i2c_addr, MPU6050_REG_WHO_AM_I, &who_am_i, 1);

    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "MPU6050 not found at 0x%02X", config->i2c_addr);
        return ESP_ERR_NOT_FOUND;
    }

    if (who_am_i != MPU6050_WHO_AM_I_VALUE) {
        ESP_LOGE(TAG, "MPU6050 WHO_AM_I mismatch: expected 0x%02X, got 0x%02X",
                 MPU6050_WHO_AM_I_VALUE, who_am_i);
        return ESP_ERR_NOT_FOUND;
    }

    // Wake up MPU6050 (clear sleep bit)
    uint8_t pwr_mgmt = 0x00;
    ret = i2c_bus_write(config->i2c_addr, MPU6050_REG_PWR_MGMT_1, &pwr_mgmt, 1);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to wake MPU6050");
        return ret;
    }

    // Configure accelerometer to ±2g range (matches recovered Arduino behavior)
    uint8_t accel_config = 0x00;  // ±2g range
    ret = i2c_bus_write(config->i2c_addr, MPU6050_REG_ACCEL_CONFIG, &accel_config, 1);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to configure MPU6050 accelerometer");
        return ret;
    }

    mpu6050_initialized = true;
    ESP_LOGI(TAG, "MPU6050 initialized at 0x%02X", config->i2c_addr);

    return ESP_OK;
}

esp_err_t mpu6050_read_accel(mpu6050_accel_t* out)
{
    if (!mpu6050_initialized || out == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    // Read 6 bytes: ACCEL_XOUT_H, ACCEL_XOUT_L, ACCEL_YOUT_H, ACCEL_YOUT_L, ACCEL_ZOUT_H, ACCEL_ZOUT_L
    uint8_t data[6];
    esp_err_t ret = i2c_bus_read(MPU6050_I2C_ADDR, MPU6050_REG_ACCEL_XOUT_H, data, 6);

    if (ret != ESP_OK) {
        out->valid = false;
        out->x = NAN;
        out->y = NAN;
        out->z = NAN;
        return ESP_FAIL;
    }

    // Convert to signed 16-bit values
    int16_t raw_x = (int16_t)((data[0] << 8) | data[1]);
    int16_t raw_y = (int16_t)((data[2] << 8) | data[3]);
    int16_t raw_z = (int16_t)((data[4] << 8) | data[5]);

    // Convert to m/s² (1g = 9.81 m/s²)
    // For ±2g range: sensitivity = 16384 LSB/g
    out->x = (float)raw_x / MPU6050_ACCEL_SCALE_2G * 9.81f;
    out->y = (float)raw_y / MPU6050_ACCEL_SCALE_2G * 9.81f;
    out->z = (float)raw_z / MPU6050_ACCEL_SCALE_2G * 9.81f;
    out->valid = true;

    return ESP_OK;
}

esp_err_t mpu6050_deinit(void)
{
    if (!mpu6050_initialized) {
        return ESP_OK;
    }

    // Put MPU6050 to sleep
    uint8_t pwr_mgmt = 0x40;  // Sleep bit
    i2c_bus_write(MPU6050_I2C_ADDR, MPU6050_REG_PWR_MGMT_1, &pwr_mgmt, 1);

    mpu6050_initialized = false;
    ESP_LOGI(TAG, "MPU6050 deinitialized");

    return ESP_OK;
}
