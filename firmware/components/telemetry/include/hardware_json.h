/**
 * @file hardware_json.h
 * @brief Hardware JSON payload serializer for ESP32 → MQTT transport
 *
 * Track 3A: Implements the EXACT hardware JSON contract from recovered Arduino deployment.
 * This is the ESP32/MQTT transport boundary, NOT the canonical backend telemetry.v1 envelope.
 *
 * Architecture:
 * ESP32 → Hardware JSON → MQTT (Nexalert/telemetry/node1)
 *       → Track 3C normalization
 *       → Canonical telemetry.v1 envelope
 *       → Backend
 *
 * LOCKED CONTRACT: Do NOT add intelligence, diagnostics, location, or metadata fields.
 * LOCKED TOPIC: Nexalert/telemetry/node1
 * LOCKED BROKER: 10.42.0.1:1883
 */

#ifndef NEXALERT_HARDWARE_JSON_H
#define NEXALERT_HARDWARE_JSON_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Hardware sensor readings (Track 3A)
 *
 * CRITICAL: Use NAN for missing values, NOT 0.0
 * NAN serializes as JSON null in the hardware payload.
 */
typedef struct {
    // BME680 sensors
    float temperature_c;         // Temperature °C (NAN = missing)
    float humidity_rh;           // Humidity % RH (NAN = missing)
    float pressure_hpa;          // Pressure hPa (NAN = missing)

    // MQ-2 gas sensor (RAW ADC, NOT calibrated ppm)
    float gas_ppm;               // Gas sensor ADC value (NAN = missing)
                                 // NOTE: Field name is "gas_ppm" per hardware contract,
                                 // but value is RAW ADC (0-4095), NOT calibrated ppm.
                                 // This matches recovered Arduino deployment semantics.

    // MPU6050 accelerometer
    float vibration_mps2;        // Vibration magnitude m/s² (NAN = missing)

    // PM sensors (not yet connected)
    float pm25_ugm3;             // PM2.5 µg/m³ (NAN = missing, must be null until sensor connected)
    float pm10_ugm3;             // PM10 µg/m³ (NAN = missing, must be null until sensor connected)

    // Environmental sensors (not connected)
    float water_level_m;         // Water level meters (NAN = missing, must be null)
    float rainfall_mm_h;         // Rainfall mm/h (NAN = missing, must be null)
    float soil_moisture_vwc_pct; // Soil moisture % VWC (NAN = missing, must be null)
} hardware_sensor_readings_t;

/**
 * Hardware power state
 */
typedef struct {
    float battery_pct;           // Battery % (NAN = missing)
    const char* solar_state;     // Solar state: "ACTIVE", "INACTIVE", "CHARGING" (NULL = missing)
} hardware_power_t;

/**
 * Initialize hardware JSON module
 *
 * @param node_id Node identifier (e.g., "NODE-001")
 * @return ESP_OK on success
 */
esp_err_t hardware_json_init(const char* node_id);

/**
 * Generate hardware JSON payload
 *
 * Generates the EXACT locked hardware JSON structure for ESP32 → MQTT transport.
 *
 * LOCKED STRUCTURE:
 * {
 *   "node_id": "NODE-001",
 *   "timestamp_ms": 1750000000000,
 *   "sequence": 1842,
 *   "sensors": {
 *     "temperature_c": 31.4,
 *     "humidity_rh": 58.2,
 *     "pm25_ugm3": null,
 *     "pm10_ugm3": null,
 *     "gas_ppm": 3.2,
 *     "pressure_hpa": 1009.8,
 *     "water_level_m": null,
 *     "rainfall_mm_h": null,
 *     "soil_moisture_vwc_pct": null,
 *     "vibration_mps2": null
 *   },
 *   "availability": {
 *     "temperature": true,
 *     "humidity": true,
 *     "pm25": false,
 *     "pm10": false,
 *     "gas": true,
 *     "pressure": true,
 *     "water_level": false,
 *     "rainfall": false,
 *     "soil_moisture": false,
 *     "vibration": false
 *   },
 *   "power": {
 *     "battery_pct": 86.0,
 *     "solar_state": "ACTIVE"
 *   }
 * }
 *
 * CRITICAL RULES:
 * - Missing numeric values (NAN) MUST serialize as JSON null
 * - Never emit NaN, infinity, or substitute zero
 * - Availability flags derived from NAN check
 * - PM2.5/PM10 remain null + unavailable until physical sensors connected
 * - gas_ppm field name preserved (hardware contract) but value is RAW ADC
 * - NO intelligence, diagnostics, location, or metadata fields
 *
 * @param sensors Sensor readings (NAN = missing)
 * @param power Power state
 * @param out_json Output JSON string (caller must free with free())
 * @return ESP_OK on success, ESP_ERR_NO_MEM if allocation fails
 */
esp_err_t hardware_json_generate(
    const hardware_sensor_readings_t* sensors,
    const hardware_power_t* power,
    char** out_json
);

/**
 * Get current sequence number (monotonic per-node)
 *
 * @return Current sequence number
 */
uint32_t hardware_json_get_sequence(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_HARDWARE_JSON_H
