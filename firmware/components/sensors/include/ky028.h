/**
 * @file ky028.h
 * @brief KY-028 thermistor temperature sensor driver (ADC)
 *
 * KY-028 digital temperature sensor module with NTC thermistor.
 * ADC interface (ESP32-S3 ADC1).
 *
 * Hardware Configuration:
 * - VCC -> 3.3V
 * - GND -> GND
 * - AO (Analog Output) -> ESP32-S3 GPIO10 (ADC1_CHANNEL_9)
 * - DO (Digital Output) -> Not connected
 *
 * IMPORTANT: This module reads the analog output (AO) which provides
 * a voltage proportional to temperature via an NTC thermistor divider.
 * Temperature conversion requires calibration against known reference points.
 */

#ifndef NEXALERT_KY028_H
#define NEXALERT_KY028_H

#include "sensor_api.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * KY-028 configuration
 */
typedef struct {
    int adc_channel;         // ADC1 channel (GPIO10 = ADC1_CHANNEL_9 on ESP32-S3)
    int gpio_pin;            // GPIO pin (10)
    calibration_t temp_cal;  // Temperature calibration (offset/scale)
} ky028_config_t;

/**
 * Initialize KY-028 sensor
 *
 * Configures ADC1 for thermistor temperature reading.
 *
 * @param config Configuration with ADC channel, GPIO pin, and calibration
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t ky028_init(const ky028_config_t* config);

/**
 * Read temperature from KY-028
 *
 * Reads ADC value, applies NTC thermistor conversion, and applies calibration.
 * Takes multiple samples and averages to reduce noise.
 *
 * Temperature conversion uses Steinhart-Hart approximation for NTC thermistor.
 * Default calibration assumes:
 * - 10kΩ NTC thermistor at 25°C (common KY-028 configuration)
 * - 10kΩ series resistor
 * - 3.3V reference voltage
 * - Beta coefficient B = 3950K (typical for common NTC thermistors)
 *
 * Calibration via sensor_api calibration_t adjusts the computed temperature.
 *
 * @param out Temperature reading (°C, calibrated)
 * @return ESP_OK on success, ESP_FAIL if ADC read fails
 */
esp_err_t ky028_read_temperature(sensor_reading_t* out);

/**
 * Deinitialize KY-028
 *
 * Note: Does NOT delete ADC unit handle if shared with other sensors (e.g., MQ-2).
 *
 * @return ESP_OK on success
 */
esp_err_t ky028_deinit(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_KY028_H
