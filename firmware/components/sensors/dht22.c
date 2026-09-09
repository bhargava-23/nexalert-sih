/**
 * @file dht22.c
 * @brief DHT22 temperature and humidity sensor driver implementation
 *
 * GPIO bit-bang protocol for DHT22/AM2302 sensor.
 * Implements calibration and preserves missing != zero invariant.
 */

#include "dht22.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_timer.h"
#include "esp_log.h"
#include <string.h>

static const char *TAG = "dht22";

// DHT22 timing constants (microseconds)
#define DHT22_START_SIGNAL_US   1000
#define DHT22_RESPONSE_WAIT_US  40
#define DHT22_BIT_THRESHOLD_US  40

// Module state
static struct {
    bool initialized;
    int gpio_pin;
    calibration_t temp_cal;
    calibration_t humid_cal;
} dht22_state = {0};

esp_err_t dht22_init(const dht22_config_t* config)
{
    if (config == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Configure GPIO
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << config->gpio_pin),
        .mode = GPIO_MODE_INPUT_OUTPUT_OD,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    esp_err_t ret = gpio_config(&io_conf);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "GPIO config failed: %d", ret);
        return ret;
    }

    // Store configuration
    dht22_state.gpio_pin = config->gpio_pin;
    dht22_state.temp_cal = config->temp_cal;
    dht22_state.humid_cal = config->humid_cal;
    dht22_state.initialized = true;

    ESP_LOGI(TAG, "Initialized on GPIO %d", config->gpio_pin);
    if (config->temp_cal.valid) {
        ESP_LOGI(TAG, "Temperature calibration: offset=%.2f, scale=%.4f",
                 config->temp_cal.offset, config->temp_cal.scale);
    }
    if (config->humid_cal.valid) {
        ESP_LOGI(TAG, "Humidity calibration: offset=%.2f, scale=%.4f",
                 config->humid_cal.offset, config->humid_cal.scale);
    }

    return ESP_OK;
}

/**
 * Wait for GPIO level with timeout
 * @return true if level reached, false if timeout
 */
static bool wait_for_level(int pin, int level, uint32_t timeout_us)
{
    uint32_t start = esp_timer_get_time();
    while (gpio_get_level(pin) != level) {
        if ((esp_timer_get_time() - start) > timeout_us) {
            return false;
        }
    }
    return true;
}

/**
 * Read 40 bits from DHT22
 * @return ESP_OK on success, ESP_ERR_TIMEOUT on failure
 */
static esp_err_t dht22_read_raw(uint8_t data[5])
{
    if (!dht22_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    int pin = dht22_state.gpio_pin;

    // Send start signal
    gpio_set_level(pin, 0);
    ets_delay_us(DHT22_START_SIGNAL_US);
    gpio_set_level(pin, 1);

    // Wait for response
    if (!wait_for_level(pin, 0, 40)) {
        ESP_LOGW(TAG, "No response from sensor");
        return ESP_ERR_TIMEOUT;
    }
    if (!wait_for_level(pin, 1, 80)) {
        return ESP_ERR_TIMEOUT;
    }
    if (!wait_for_level(pin, 0, 80)) {
        return ESP_ERR_TIMEOUT;
    }

    // Read 40 bits
    memset(data, 0, 5);
    for (int i = 0; i < 40; i++) {
        // Wait for bit start
        if (!wait_for_level(pin, 1, 50)) {
            return ESP_ERR_TIMEOUT;
        }

        // Measure high pulse duration
        uint32_t start = esp_timer_get_time();
        if (!wait_for_level(pin, 0, 70)) {
            return ESP_ERR_TIMEOUT;
        }
        uint32_t duration = esp_timer_get_time() - start;

        // Bit value based on duration
        if (duration > DHT22_BIT_THRESHOLD_US) {
            data[i / 8] |= (1 << (7 - (i % 8)));
        }
    }

    // Verify checksum
    uint8_t checksum = data[0] + data[1] + data[2] + data[3];
    if (checksum != data[4]) {
        ESP_LOGW(TAG, "Checksum mismatch: calc=%02x, recv=%02x", checksum, data[4]);
        return ESP_ERR_INVALID_CRC;
    }

    return ESP_OK;
}

/**
 * Apply calibration to raw value
 * CRITICAL: Preserves missing != zero invariant
 */
static void apply_calibration(float raw_value, const calibration_t* cal, sensor_reading_t* out)
{
    out->timestamp_ms = esp_timer_get_time() / 1000;

    if (!cal->valid) {
        // No calibration: use raw value
        out->value = raw_value;
        out->valid = true;
    } else {
        // Apply calibration: value_calibrated = (raw * scale) + offset
        out->value = (raw_value * cal->scale) + cal->offset;
        out->valid = true;
    }
}

esp_err_t dht22_read_temperature(sensor_reading_t* out)
{
    if (!dht22_state.initialized || out == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    uint8_t data[5];
    esp_err_t ret = dht22_read_raw(data);
    if (ret != ESP_OK) {
        // Sensor read failed: return missing (valid=false)
        // CRITICAL: Preserves missing != zero invariant
        out->valid = false;
        out->timestamp_ms = esp_timer_get_time() / 1000;
        return ret;
    }

    // Parse temperature (16-bit signed, tenths of degree)
    int16_t temp_raw = ((data[2] & 0x7F) << 8) | data[3];
    if (data[2] & 0x80) {
        temp_raw = -temp_raw;
    }
    float temp_c = temp_raw / 10.0f;

    // Apply calibration
    apply_calibration(temp_c, &dht22_state.temp_cal, out);

    return ESP_OK;
}

esp_err_t dht22_read_humidity(sensor_reading_t* out)
{
    if (!dht22_state.initialized || out == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    uint8_t data[5];
    esp_err_t ret = dht22_read_raw(data);
    if (ret != ESP_OK) {
        // Sensor read failed: return missing (valid=false)
        // CRITICAL: Preserves missing != zero invariant
        out->valid = false;
        out->timestamp_ms = esp_timer_get_time() / 1000;
        return ret;
    }

    // Parse humidity (16-bit unsigned, tenths of percent)
    uint16_t humid_raw = (data[0] << 8) | data[1];
    float humid_pct = humid_raw / 10.0f;

    // Apply calibration
    apply_calibration(humid_pct, &dht22_state.humid_cal, out);

    return ESP_OK;
}

esp_err_t dht22_deinit(void)
{
    if (!dht22_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    gpio_reset_pin(dht22_state.gpio_pin);
    memset(&dht22_state, 0, sizeof(dht22_state));

    ESP_LOGI(TAG, "Deinitialized");
    return ESP_OK;
}
