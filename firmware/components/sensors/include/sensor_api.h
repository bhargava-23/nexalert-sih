/**
 * @file sensor_api.h
 * @brief Unified sensor interface for NexAlert field nodes
 *
 * Provides common API for all sensor types with calibration support.
 * Preserves missing != zero invariant per IMPLEMENTATION_CONSTITUTION.md Section 3.
 */

#ifndef NEXALERT_SENSOR_API_H
#define NEXALERT_SENSOR_API_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Sensor types supported by NexAlert nodes
 */
typedef enum {
    SENSOR_TYPE_DHT22 = 0,      // Temperature + Humidity
    SENSOR_TYPE_BMP280,          // Pressure
    SENSOR_TYPE_PMS5003,         // PM2.5 / PM10
    SENSOR_TYPE_MAX
} sensor_type_t;

/**
 * Sensor reading result
 *
 * CRITICAL: valid flag distinguishes measurement vs missing.
 * When valid=false, value field is UNDEFINED and must NOT be interpreted as zero.
 * This preserves missing != zero invariant.
 */
typedef struct {
    float value;                 // Measurement value (ONLY valid when valid=true)
    bool valid;                  // true = measurement present, false = missing
    uint32_t timestamp_ms;       // Measurement timestamp (ESP timer tick)
} sensor_reading_t;

/**
 * Calibration coefficients for sensor correction
 *
 * Per Decision C2: Calibration is versioned provisioning artifact,
 * NOT hardcoded in drivers.
 */
typedef struct {
    float offset;                // Additive offset
    float scale;                 // Multiplicative scale factor
    uint32_t version;            // Calibration version
    bool valid;                  // Calibration present flag
} calibration_t;

/**
 * Initialize sensor with calibration
 *
 * @param type Sensor type to initialize
 * @param cal Calibration coefficients (may be NULL for uncalibrated)
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t sensor_init(sensor_type_t type, const calibration_t* cal);

/**
 * Read sensor measurement
 *
 * Applies calibration if configured. Returns calibrated value.
 * Sets out->valid=false for missing/failed measurements (missing != zero).
 *
 * @param type Sensor type to read
 * @param out Output reading (valid flag indicates presence)
 * @return ESP_OK on success, ESP_ERR_INVALID_STATE if not initialized
 */
esp_err_t sensor_read(sensor_type_t type, sensor_reading_t* out);

/**
 * Deinitialize sensor
 *
 * @param type Sensor type to deinitialize
 * @return ESP_OK on success
 */
esp_err_t sensor_deinit(sensor_type_t type);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_SENSOR_API_H
