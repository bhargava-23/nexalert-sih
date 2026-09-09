/**
 * @file node_config.h
 * @brief Centralized embedded configuration for NexAlert edge node
 *
 * CRITICAL: Do NOT scatter configuration values through main.c and modules.
 * All configurable parameters centralized here with explicit structures.
 *
 * PROTOTYPE/DEMO configuration clearly labeled as UNVALIDATED.
 */

#ifndef NEXALERT_NODE_CONFIG_H
#define NEXALERT_NODE_CONFIG_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Node identity and location
 */
typedef struct {
    char node_id[32];            // Node identifier (e.g., "node1")
    float latitude;              // WGS84 latitude
    float longitude;             // WGS84 longitude
    float altitude;              // Altitude in meters (or NAN)
} node_identity_t;

/**
 * Sampling configuration
 */
typedef struct {
    uint32_t interval_ms;        // Sampling interval (milliseconds)
    uint32_t warmup_ms;          // Sensor warmup delay (milliseconds)
} sampling_config_t;

/**
 * MQTT broker configuration
 */
typedef struct {
    char broker_host[128];       // Broker hostname/IP
    uint16_t broker_port;        // Broker port (default 1883)
    char topic[128];             // Telemetry topic (LOCKED: "Nexalert/telemetry/node1")
    bool tls_enabled;            // TLS/SSL enabled
    char username[64];           // MQTT username (empty = no auth)
    char password[64];           // MQTT password (empty = no auth)
    uint16_t keepalive_s;        // Keepalive interval (seconds)
    uint16_t timeout_ms;         // Connection timeout (milliseconds)
} mqtt_config_t;

/**
 * Buffer configuration
 */
typedef struct {
    uint16_t capacity;           // Maximum buffered messages
    bool enabled;                // Buffering enabled
} buffer_config_t;

/**
 * Heartbeat configuration
 */
typedef struct {
    uint32_t interval_ms;        // Heartbeat interval (milliseconds)
    bool enabled;                // Heartbeat enabled
} heartbeat_config_t;

/**
 * Calibration configuration
 */
typedef struct {
    float K_temp;                // Temperature calibration factor
    float K_humidity;            // Humidity calibration factor
    float K_pressure;            // Pressure calibration factor
} calibration_config_t;

/**
 * Intelligence thresholds (PROTOTYPE - UNVALIDATED)
 */
typedef struct {
    // Baseline configuration
    uint16_t baseline_window;    // Baseline window size (samples)
    float baseline_alpha;        // EMA smoothing factor

    // Anomaly configuration
    float anomaly_lambda;        // Exponential decay lambda
    float anomaly_z_cap;         // Z-score cap

    // Confidence weights
    float confidence_w_cov;      // Coverage weight
    float confidence_w_agree;    // Agreement weight
    float confidence_w_temp;     // Temporal weight
    float confidence_w_base;     // Baseline weight

    // Severity weights
    float severity_w_intensity;  // Intensity weight
    float severity_w_temporal;   // Temporal weight
    float severity_w_duration;   // Duration weight

    // Risk weights
    float risk_w_evidence;       // Evidence weight
    float risk_w_severity;       // Severity weight
    float risk_w_temporal;       // Temporal weight

    // State machine thresholds
    float watch_risk_enter;      // NORMAL → WATCH risk threshold
    float watch_anomaly_enter;   // NORMAL → WATCH anomaly threshold
    float suspected_evidence_enter; // WATCH → SUSPECTED evidence threshold
    float confirmed_evidence_enter; // SUSPECTED → CONFIRMED evidence threshold
    float confirmed_confidence_min; // CONFIRMED confidence minimum
    float critical_severity_enter;  // CONFIRMED → CRITICAL severity threshold
    float critical_risk_enter;      // CONFIRMED → CRITICAL risk threshold

    // Persistence counters
    uint8_t watch_persistence;   // WATCH enter persistence (samples)
    uint8_t suspected_persistence; // SUSPECTED enter persistence
    uint8_t confirmed_persistence; // CONFIRMED enter persistence
    uint8_t critical_persistence;  // CRITICAL enter persistence
    uint8_t resolved_persistence;  // RESOLVED enter persistence

    // Hysteresis values
    float watch_risk_exit;       // WATCH → NORMAL risk threshold
    float suspected_evidence_exit; // SUSPECTED → WATCH evidence threshold
    float confirmed_evidence_exit; // CONFIRMED → SUSPECTED evidence threshold
    float critical_severity_exit;  // CRITICAL → CONFIRMED severity threshold
    float critical_risk_exit;      // CRITICAL → CONFIRMED risk threshold
} intelligence_config_t;

/**
 * Logging configuration
 */
typedef struct {
    uint8_t log_level;           // ESP_LOG_* level (NONE=0, ERROR=1, WARN=2, INFO=3, DEBUG=4, VERBOSE=5)
} logging_config_t;

/**
 * Complete node configuration
 */
typedef struct {
    node_identity_t identity;
    sampling_config_t sampling;
    mqtt_config_t mqtt;
    buffer_config_t buffer;
    heartbeat_config_t heartbeat;
    calibration_config_t calibration;
    intelligence_config_t intelligence;
    logging_config_t logging;
} node_config_complete_t;

/**
 * Get default development configuration
 *
 * PROTOTYPE/DEMO configuration:
 * - Node ID: "node1"
 * - Location: Dummy coordinates
 * - MQTT: Localhost broker, topic "Nexalert/telemetry/node1"
 * - All intelligence thresholds UNVALIDATED
 *
 * @return Default configuration structure
 */
node_config_complete_t node_config_default(void);

/**
 * Validate configuration parameters
 *
 * Checks:
 * - Node ID not empty
 * - Sampling interval > 0
 * - MQTT broker not empty
 * - MQTT topic matches canonical format
 * - Buffer capacity reasonable
 * - Intelligence thresholds in valid ranges
 * - Weights sum checks where applicable
 *
 * @param config Configuration to validate
 * @return ESP_OK if valid, ESP_ERR_INVALID_ARG otherwise
 */
esp_err_t node_config_validate(const node_config_complete_t* config);

/**
 * Load configuration from NVS
 *
 * Falls back to default configuration if NVS empty or invalid.
 *
 * @param out_config Output configuration
 * @return ESP_OK on success, ESP_ERR_NOT_FOUND if using defaults
 */
esp_err_t node_config_load(node_config_complete_t* out_config);

/**
 * Save configuration to NVS
 *
 * Validates before saving. Configuration persists across reboots.
 *
 * @param config Configuration to save
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if validation fails
 */
esp_err_t node_config_save(const node_config_complete_t* config);

/**
 * Reset configuration to defaults and clear NVS
 *
 * @return ESP_OK on success
 */
esp_err_t node_config_reset(void);

#ifdef __cplusplus
}
#endif

#endif // NEXALERT_NODE_CONFIG_H
