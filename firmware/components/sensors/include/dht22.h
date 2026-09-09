/**
 * @file dht22.h
 * @brief DHT22 temperature and humidity sensor driver
 *
 * GPIO bit-bang protocol for DHT22/AM2302 sensor.
 * Provides calibrated temperature (°C) and humidity (%).
 */

#ifndef NEXALERT_DHT22_H
#define NEXALERT_DHT22_H

#include "sensor_api.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * DHT22-specific configuration
 */
typedef struct {
    int gpio_pin;                // GPIO pin for data line
    calibration_t temp_cal;      // Temperature calibration
    calibration_t humid_cal;     // Humidity calibration
} dht22_config_t;

/**
 * Initialize DHT22 sensor
 *
 * @param config Configuration with GPIO pin and calibration
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t dht22_init(const dht22_config_t* config);

/**
 * Read temperature from DHT22
 *
 * @param out Temperature reading (°C, calibrated)
 * @return ESP_OK on success, ESP_ERR_TIMEOUT if sensor non-responsive
 */
esp_err_t dht22_read_temperature(sensor_reading_t* out);

/**
 * Read humidity from DHT22
 *
 * @param out Humidity reading (%, calibrated)
 * @return ESP_OK on success, ESP_ERR_TIMEOUT if sensor non-responsive
 */
esp_err_t dht22_read_humidity(sensor_reading_t* out);

/**
 * Deinitialize DHT22
 *
 * @return ESP_OK on success
 */
esp_err_t dht22_deinit(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_DHT22_H
