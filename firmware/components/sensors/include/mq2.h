/**
 * @file mq2.h
 * @brief MQ-2 gas sensor driver (ADC)
 *
 * MQ-2 combustible gas sensor.
 * ADC interface (ESP32-S3 ADC1).
 *
 * Matches recovered Arduino deployment behavior:
 * - GPIO4 ADC pin
 * - Returns RAW ADC value (0-4095)
 * - NOT calibrated to ppm or specific gas concentration
 *
 * IMPORTANT: The recovered Arduino deployment published this raw ADC value
 * in a field named "gas_ppm", which is MISLEADING. The value is NOT calibrated
 * to ppm. This driver preserves the raw ADC semantics and documents the
 * mismatch clearly.
 */

#ifndef NEXALERT_MQ2_H
#define NEXALERT_MQ2_H

#include "sensor_api.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * MQ-2 configuration
 */
typedef struct {
    int adc_channel;  // ADC1 channel (GPIO4 = ADC1_CHANNEL_3 on ESP32-S3)
    int gpio_pin;     // GPIO pin (4)
} mq2_config_t;

/**
 * Initialize MQ-2 sensor
 *
 * Configures ADC1 for gas sensor reading.
 *
 * @param config Configuration with ADC channel and GPIO pin
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t mq2_init(const mq2_config_t* config);

/**
 * Read gas sensor from MQ-2
 *
 * Returns RAW ADC value (0-4095), NOT calibrated to ppm.
 *
 * The recovered Arduino deployment published this value in a field named
 * "gas_ppm", but it is NOT actually calibrated to ppm or any specific gas
 * concentration. It is a raw ADC reading only.
 *
 * Track 3A preserves this raw ADC semantic and documents the field name
 * mismatch in the hardware JSON payload.
 *
 * @param out Gas sensor reading (raw ADC value 0-4095, NOT ppm)
 * @return ESP_OK on success, ESP_FAIL if ADC read fails
 */
esp_err_t mq2_read_gas(sensor_reading_t* out);

/**
 * Deinitialize MQ-2
 *
 * @return ESP_OK on success
 */
esp_err_t mq2_deinit(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_MQ2_H
