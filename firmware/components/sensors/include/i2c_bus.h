/**
 * @file i2c_bus.h
 * @brief Shared I2C bus initialization and management
 *
 * Initializes I2C bus on GPIO8 (SDA) and GPIO9 (SCL) for ESP32-S3.
 * Shared by BME680 and MPU6050 sensors.
 *
 * Matches recovered Arduino deployment configuration:
 * - I2C SDA: GPIO8
 * - I2C SCL: GPIO9
 * - Devices: BME680 (0x77/0x76), MPU6050 (0x68)
 */

#ifndef NEXALERT_I2C_BUS_H
#define NEXALERT_I2C_BUS_H

#include "esp_err.h"
#include "driver/i2c.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * I2C bus configuration (matches recovered Arduino deployment)
 */
#define I2C_MASTER_SCL_IO           9    // GPIO9
#define I2C_MASTER_SDA_IO           8    // GPIO8
#define I2C_MASTER_NUM              I2C_NUM_0
#define I2C_MASTER_FREQ_HZ          100000  // 100kHz standard mode
#define I2C_MASTER_TX_BUF_DISABLE   0
#define I2C_MASTER_RX_BUF_DISABLE   0
#define I2C_MASTER_TIMEOUT_MS       1000

/**
 * Initialize I2C bus
 *
 * Configures I2C master on GPIO8 (SDA) and GPIO9 (SCL).
 * Must be called before initializing BME680 or MPU6050.
 *
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t i2c_bus_init(void);

/**
 * Deinitialize I2C bus
 *
 * @return ESP_OK on success
 */
esp_err_t i2c_bus_deinit(void);

/**
 * Read from I2C device
 *
 * @param dev_addr I2C device address (7-bit)
 * @param reg_addr Register address to read from
 * @param data Buffer to store read data
 * @param len Number of bytes to read
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t i2c_bus_read(uint8_t dev_addr, uint8_t reg_addr, uint8_t *data, size_t len);

/**
 * Write to I2C device
 *
 * @param dev_addr I2C device address (7-bit)
 * @param reg_addr Register address to write to
 * @param data Data to write
 * @param len Number of bytes to write
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t i2c_bus_write(uint8_t dev_addr, uint8_t reg_addr, const uint8_t *data, size_t len);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_I2C_BUS_H
