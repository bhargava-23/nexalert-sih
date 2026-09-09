/**
 * @file calibration_store.h
 * @brief NVS-based calibration storage for sensor calibration coefficients
 *
 * Per Decision C2: Calibration is versioned provisioning artifact,
 * NOT hardcoded in drivers.
 */

#ifndef NEXALERT_CALIBRATION_STORE_H
#define NEXALERT_CALIBRATION_STORE_H

#include "sensor_api.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Initialize calibration storage
 *
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t calibration_store_init(void);

/**
 * Load calibration for sensor type
 *
 * @param type Sensor type
 * @param sensor_id Sensor identifier (e.g., "temp", "humid", "pressure")
 * @param cal Output calibration (valid flag set if found)
 * @return ESP_OK on success, ESP_ERR_NOT_FOUND if no calibration
 */
esp_err_t calibration_load(sensor_type_t type, const char* sensor_id, calibration_t* cal);

/**
 * Save calibration for sensor type
 *
 * @param type Sensor type
 * @param sensor_id Sensor identifier
 * @param cal Calibration to save
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t calibration_save(sensor_type_t type, const char* sensor_id, const calibration_t* cal);

/**
 * Clear all calibrations
 *
 * @return ESP_OK on success
 */
esp_err_t calibration_clear_all(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_CALIBRATION_STORE_H
