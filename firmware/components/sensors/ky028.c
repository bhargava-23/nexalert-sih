/**
 * @file ky028.c
 * @brief KY-028 thermistor temperature sensor driver (ADC)
 *
 * KY-028 digital temperature module with NTC thermistor implementation for ESP32-S3.
 * Replaces BME680 temperature source while preserving existing telemetry contract.
 *
 * HARDWARE WIRING:
 * - VCC -> 3.3V
 * - GND -> GND
 * - AO -> GPIO10 (ADC1_CHANNEL_9)
 * - DO -> Not connected
 *
 * NTC THERMISTOR CONVERSION:
 * The KY-028 module typically contains a 10kΩ NTC thermistor in a voltage divider
 * with a 10kΩ series resistor. Temperature is derived using Steinhart-Hart equation.
 *
 * CALIBRATION APPROACH:
 * Default conversion uses typical NTC parameters. For production accuracy, calibrate
 * against known reference temperatures and adjust the calibration_t offset/scale.
 */

#include "ky028.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_log.h"
#include <math.h>

static const char *TAG = "ky028";

// External ADC1 handle shared with MQ-2
extern adc_oneshot_unit_handle_t adc1_handle;

// ADC configuration
static bool ky028_initialized = false;
static adc_channel_t ky028_channel;
static calibration_t ky028_calibration = {0};

// NTC Thermistor parameters (typical for KY-028 module)
// NOTE: These are APPROXIMATE defaults. Real hardware may vary.
// Calibrate against known reference temperatures for production accuracy.
#define NTC_R0            10000.0f   // NTC resistance at T0 (10kΩ at 25°C)
#define NTC_T0            298.15f    // Reference temperature (25°C in Kelvin)
#define NTC_BETA          3950.0f    // Beta coefficient (typical for common NTC)
#define SERIES_RESISTOR   10000.0f   // Series resistor in voltage divider (10kΩ)
#define V_REF             3.3f       // ADC reference voltage (3.3V)
#define ADC_MAX           4095.0f    // 12-bit ADC maximum value

// Sampling configuration
#define KY028_SAMPLES     8          // Number of ADC samples to average

// External ADC1 handle shared with MQ-2
extern adc_oneshot_unit_handle_t adc1_handle;

esp_err_t ky028_init(const ky028_config_t* config)
{
    if (config == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Use the existing ADC1 handle shared with MQ-2
    // The ADC unit is already initialized by MQ-2, we only configure our channel
    if (adc1_handle == NULL) {
        ESP_LOGE(TAG, "ADC1 handle is NULL - MQ-2 should initialize ADC1 first");
        return ESP_ERR_INVALID_STATE;
    }

    ESP_LOGI(TAG, "Using shared ADC1 unit handle (initialized by MQ-2)");

    // Configure ADC channel for KY-028
    ky028_channel = config->adc_channel;
    adc_oneshot_chan_cfg_t chan_config = {
        .bitwidth = ADC_BITWIDTH_12,   // 0-4095
        .atten = ADC_ATTEN_DB_12,      // 12 dB attenuation, 0-3.3V range
    };

    esp_err_t ret = adc_oneshot_config_channel(adc1_handle, ky028_channel, &chan_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADC channel config failed: %s", esp_err_to_name(ret));
        // Don't delete ADC unit here - it may be shared with MQ-2
        return ret;
    }

    // Store calibration
    ky028_calibration = config->temp_cal;

    ky028_initialized = true;
    ESP_LOGI(TAG, "KY-028 initialized on GPIO%d (ADC1 channel %d)",
             config->gpio_pin, config->adc_channel);
    ESP_LOGI(TAG, "NTC parameters: R0=%.0fΩ, Beta=%.0fK, Rseries=%.0fΩ",
             NTC_R0, NTC_BETA, SERIES_RESISTOR);
    if (ky028_calibration.valid) {
        ESP_LOGI(TAG, "Temperature calibration: offset=%.2f, scale=%.3f",
                 ky028_calibration.offset, ky028_calibration.scale);
    } else {
        ESP_LOGI(TAG, "Temperature calibration: NONE (using default conversion)");
    }

    return ESP_OK;
}

esp_err_t ky028_read_temperature(sensor_reading_t* out)
{
    if (!ky028_initialized || out == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    // Take multiple ADC samples and average to reduce noise
    int32_t adc_sum = 0;
    int valid_samples = 0;

    for (int i = 0; i < KY028_SAMPLES; i++) {
        int adc_raw;
        esp_err_t ret = adc_oneshot_read(adc1_handle, ky028_channel, &adc_raw);

        if (ret == ESP_OK && adc_raw >= 0 && adc_raw <= ADC_MAX) {
            adc_sum += adc_raw;
            valid_samples++;
        }
    }

    if (valid_samples == 0) {
        ESP_LOGD(TAG, "ADC read failed: no valid samples");
        out->valid = false;
        out->value = NAN;
        return ESP_FAIL;
    }

    // Compute average ADC value
    float adc_avg = (float)adc_sum / (float)valid_samples;

    // Sanity check: ADC should not be at extreme limits
    // (indicates open circuit or short circuit)
    if (adc_avg < 50.0f || adc_avg > (ADC_MAX - 50.0f)) {
        ESP_LOGW(TAG, "ADC value out of expected range: %.0f (possible sensor fault)", adc_avg);
        out->valid = false;
        out->value = NAN;
        return ESP_FAIL;
    }

    // Convert ADC to voltage
    float v_out = (adc_avg / ADC_MAX) * V_REF;

    // Calculate NTC resistance from voltage divider
    // V_out = V_ref * (R_ntc / (R_series + R_ntc))
    // R_ntc = R_series * V_out / (V_ref - V_out)
    float r_ntc = SERIES_RESISTOR * v_out / (V_REF - v_out);

    // Sanity check: NTC resistance should be in reasonable range (1kΩ - 100kΩ)
    if (r_ntc < 1000.0f || r_ntc > 100000.0f) {
        ESP_LOGW(TAG, "NTC resistance out of range: %.0f Ω (ADC=%.0f)", r_ntc, adc_avg);
        out->valid = false;
        out->value = NAN;
        return ESP_FAIL;
    }

    // Steinhart-Hart equation (simplified Beta parameter equation)
    // 1/T = 1/T0 + (1/B) * ln(R/R0)
    // T = 1 / (1/T0 + (1/B) * ln(R/R0))
    float ln_ratio = logf(r_ntc / NTC_R0);
    float temp_kelvin = 1.0f / ((1.0f / NTC_T0) + (ln_ratio / NTC_BETA));
    float temp_celsius = temp_kelvin - 273.15f;

    // Store raw temperature before calibration
    float temp_raw = temp_celsius;

    // DIAGNOSTIC OUTPUT - Print all measurements
    ESP_LOGI(TAG, "  ┌─ ADC raw avg: %.1f (from %d samples)", adc_avg, valid_samples);
    ESP_LOGI(TAG, "  ├─ Voltage: %.3f V", v_out);
    ESP_LOGI(TAG, "  ├─ NTC Resistance: %.0f Ω", r_ntc);
    ESP_LOGI(TAG, "  ├─ Raw temperature (before cal): %.2f °C", temp_raw);

    // Apply calibration if configured
    if (ky028_calibration.valid) {
        temp_celsius = (temp_celsius * ky028_calibration.scale) + ky028_calibration.offset;
        ESP_LOGI(TAG, "  ├─ Calibration: offset=%.2f, scale=%.3f",
                 ky028_calibration.offset, ky028_calibration.scale);
        ESP_LOGI(TAG, "  └─ Final temp (after cal): %.2f °C", temp_celsius);
    } else {
        ESP_LOGI(TAG, "  ├─ Calibration: NONE");
        ESP_LOGI(TAG, "  └─ Final temp: %.2f °C (same as raw)", temp_celsius);
    }

    // Sanity check: temperature should be in plausible range (-40°C to +85°C)
    // TEMPORARILY WIDENED for diagnostic - allow unusual temperatures through
    if (temp_celsius < -40.0f || temp_celsius > 125.0f) {
        ESP_LOGW(TAG, "  ⚠ Temperature unusual: %.1f °C (R_ntc=%.0f Ω) - allowing through for diagnostic",
                 temp_celsius, r_ntc);
        // Don't reject during diagnostic phase
    }

    out->value = temp_celsius;
    out->valid = true;

    return ESP_OK;
}

esp_err_t ky028_deinit(void)
{
    if (!ky028_initialized) {
        return ESP_OK;
    }

    // NOTE: We do NOT delete the ADC1 unit handle here because it may be
    // shared with other sensors (e.g., MQ-2). Each sensor using ADC1 only
    // configures its own channel. The ADC unit is cleaned up when the system
    // deinitializes all sensors.

    ky028_initialized = false;
    ESP_LOGI(TAG, "KY-028 deinitialized (ADC1 unit left active for shared use)");

    return ESP_OK;
}
