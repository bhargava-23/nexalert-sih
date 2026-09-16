/**
 * @file bme680.h
 * @brief BME680 environmental sensor driver (I2C)
 *
 * Bosch BME680 combined temperature, humidity, pressure and gas sensor.
 * I2C interface at 0x77 (primary) or 0x76 (secondary).
 *
 * Matches recovered Arduino deployment behavior:
 * - Address 0x77 with fallback to 0x76
 * - Returns temperature (°C), humidity (%), pressure (hPa), gas resistance (raw ADC)
 */

#ifndef NEXALERT_BME680_H
#define NEXALERT_BME680_H

#include "sensor_api.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * BME680 I2C addresses
 */
#define BME680_I2C_ADDR_PRIMARY   0x77
#define BME680_I2C_ADDR_SECONDARY 0x76

/**
 * BME680-specific configuration
 */
typedef struct {
    uint8_t i2c_addr;            // I2C address (0x77 or 0x76)
    calibration_t temp_cal;      // Temperature calibration
    calibration_t humid_cal;     // Humidity calibration
    calibration_t pressure_cal;  // Pressure calibration
} bme680_config_t;

/**
 * Initialize BME680 sensor
 *
 * Attempts initialization at configured address.
 * If primary address (0x77) fails, automatically retries at secondary (0x76).
 *
 * @param config Configuration with I2C address and calibrations
 * @return ESP_OK on success, ESP_ERR_NOT_FOUND if sensor not found at either address
 */
esp_err_t bme680_init(const bme680_config_t* config);

/**
 * Read temperature from BME680
 *
 * @param out Temperature reading (°C, calibrated)
 * @return ESP_OK on success, ESP_FAIL if sensor communication fails
 */
esp_err_t bme680_read_temperature(sensor_reading_t* out);

/**
 * Read humidity from BME680
 *
 * @param out Humidity reading (%, calibrated)
 * @return ESP_OK on success, ESP_FAIL if sensor communication fails
 */
esp_err_t bme680_read_humidity(sensor_reading_t* out);

/**
 * Read pressure from BME680
 *
 * @param out Pressure reading (hPa, calibrated)
 * @return ESP_OK on success, ESP_FAIL if sensor communication fails
 */
esp_err_t bme680_read_pressure(sensor_reading_t* out);

/**
 * Read gas resistance from BME680
 *
 * Returns RAW ADC value, NOT calibrated to specific gas concentration.
 * This matches the recovered Arduino deployment semantics where MQ-2 ADC
 * is reported in the "gas_ppm" field but is not actually calibrated to ppm.
 *
 * @param out Gas resistance reading (raw ADC value, NOT ppm)
 * @return ESP_OK on success, ESP_FAIL if sensor communication fails
 */
esp_err_t bme680_read_gas(sensor_reading_t* out);

/**
 * Deinitialize BME680
 *
 * @return ESP_OK on success
 */
esp_err_t bme680_deinit(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_BME680_H
