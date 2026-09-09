/**
 * @file telemetry_envelope.h
 * @brief Canonical NexAlert telemetry envelope generation
 *
 * Implements telemetry-envelope.schema.json (LOCKED authoritative contract).
 * Preserves missing != zero invariant per IMPLEMENTATION_CONSTITUTION.md Section 3.
 */

#ifndef NEXALERT_TELEMETRY_ENVELOPE_H
#define NEXALERT_TELEMETRY_ENVELOPE_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Telemetry envelope configuration
 */
typedef struct {
    const char* node_id;         // "NODE-XXX" format
    float latitude;              // WGS84 latitude
    float longitude;             // WGS84 longitude
    float altitude;              // Altitude in meters (or NAN for missing)
} telemetry_config_t;

/**
 * Sensor measurements
 * CRITICAL: Use NAN for missing values, NOT 0.0
 * Preserves missing != zero invariant.
 */
typedef struct {
    float temp_c;                // Temperature °C (NAN = missing)
    float humidity_pct;          // Humidity % (NAN = missing)
    float pressure_hpa;          // Pressure hPa (NAN = missing)
    float pm25_ug_m3;            // PM2.5 µg/m³ (NAN = missing)
    float pm10_ug_m3;            // PM10 µg/m³ (NAN = missing)
} measurements_t;

/**
 * Diagnostic dimensions for H_i computation
 * Per Document 04, Section 3.1
 */
typedef struct {
    uint32_t uptime_s;           // Uptime in seconds (0 = missing)
    bool self_test_passed;       // Self-test result
    float comm_integrity;        // Communication integrity [0,1] (NAN = missing)
    bool calibration_valid;      // Calibration validity
    float stability_index;       // Long-term stability [0,1] (NAN = missing)
} diagnostics_t;

/**
 * Power state
 */
typedef struct {
    float battery_pct;           // Battery % (NAN = missing)
    float battery_voltage;       // Battery voltage (NAN = missing)
    float solar_current;         // Solar current amps (NAN = missing)
} power_t;

/**
 * Initialize telemetry envelope module
 *
 * @param config Configuration with node ID and location
 * @return ESP_OK on success
 */
esp_err_t telemetry_envelope_init(const telemetry_config_t* config);

/**
 * Generate telemetry envelope JSON
 *
 * Conforms to schemas/telemetry-envelope.schema.json (LOCKED contract).
 * Returns dynamically allocated JSON string (caller must free).
 *
 * CRITICAL: Missing numeric values serialized as JSON null, NOT 0.0.
 *
 * @param measurements Sensor measurements (NAN = missing)
 * @param diagnostics Diagnostic dimensions
 * @param power Power state
 * @param out_json Output JSON string (caller must free with free())
 * @return ESP_OK on success, ESP_ERR_NO_MEM if allocation fails
 */
esp_err_t telemetry_envelope_generate(
    const measurements_t* measurements,
    const diagnostics_t* diagnostics,
    const power_t* power,
    char** out_json
);

/**
 * Get current sequence number (monotonic per-node)
 *
 * @return Current sequence number
 */
uint32_t telemetry_envelope_get_sequence(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_TELEMETRY_ENVELOPE_H
