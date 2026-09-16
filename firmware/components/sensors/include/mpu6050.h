/**
 * @file mpu6050.h
 * @brief MPU6050 accelerometer/gyroscope sensor driver (I2C)
 *
 * InvenSense MPU6050 6-axis motion tracking device.
 * I2C interface at 0x68 (default).
 *
 * Matches recovered Arduino deployment behavior:
 * - Address 0x68
 * - Returns acceleration x/y/z for vibration detection
 * - Local sampling at 20ms intervals
 */

#ifndef NEXALERT_MPU6050_H
#define NEXALERT_MPU6050_H

#include "sensor_api.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * MPU6050 I2C address
 */
#define MPU6050_I2C_ADDR 0x68

/**
 * MPU6050-specific configuration
 */
typedef struct {
    uint8_t i2c_addr;            // I2C address (default 0x68)
    uint16_t sample_rate_hz;     // Accelerometer sample rate (default 50 Hz for 20ms intervals)
} mpu6050_config_t;

/**
 * Acceleration reading (3-axis)
 */
typedef struct {
    float x;  // m/s²
    float y;  // m/s²
    float z;  // m/s²
    bool valid;
} mpu6050_accel_t;

/**
 * Initialize MPU6050 sensor
 *
 * @param config Configuration with I2C address and sample rate
 * @return ESP_OK on success, ESP_ERR_NOT_FOUND if sensor not found
 */
esp_err_t mpu6050_init(const mpu6050_config_t* config);

/**
 * Read acceleration from MPU6050
 *
 * Returns 3-axis acceleration for vibration detection.
 * Matches recovered Arduino deployment: accel.acceleration.x/y/z
 *
 * @param out Acceleration reading (m/s²)
 * @return ESP_OK on success, ESP_FAIL if sensor communication fails
 */
esp_err_t mpu6050_read_accel(mpu6050_accel_t* out);

/**
 * Deinitialize MPU6050
 *
 * @return ESP_OK on success
 */
esp_err_t mpu6050_deinit(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_MPU6050_H
