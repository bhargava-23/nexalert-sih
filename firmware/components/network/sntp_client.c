/**
 * @file sntp_client.c
 * @brief SNTP/NTP client for NexAlert ESP32 nodes
 *
 * Track 3A: Synchronizes wall-clock time from field NTP server (10.42.0.1).
 */

#include "sntp_client.h"
#include "esp_sntp.h"
#include "esp_log.h"
#include "esp_timer.h"
#include <time.h>
#include <sys/time.h>

static const char *TAG = "sntp_client";

static bool sntp_initialized = false;
static bool sntp_synced = false;

/**
 * SNTP sync notification callback
 */
static void sntp_sync_notification_cb(struct timeval *tv)
{
    sntp_synced = true;
    time_t now = tv->tv_sec;
    struct tm timeinfo;
    localtime_r(&now, &timeinfo);

    ESP_LOGI(TAG, "SNTP synchronized: %04d-%02d-%02d %02d:%02d:%02d UTC",
             timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
             timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
}

esp_err_t sntp_client_init(const sntp_config_t* config)
{
    if (config == NULL || config->ntp_server == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (sntp_initialized) {
        ESP_LOGW(TAG, "SNTP already initialized");
        return ESP_OK;
    }

    // Set timezone to UTC (NexAlert uses UTC timestamps)
    setenv("TZ", "UTC", 1);
    tzset();

    // Initialize SNTP
    esp_sntp_setoperatingmode(SNTP_OPMODE_POLL);
    esp_sntp_setservername(0, config->ntp_server);
    esp_sntp_set_sync_mode(SNTP_SYNC_MODE_SMOOTH);
    esp_sntp_set_time_sync_notification_cb(sntp_sync_notification_cb);

    esp_sntp_init();
    sntp_initialized = true;

    ESP_LOGI(TAG, "SNTP client initialized with server: %s", config->ntp_server);
    return ESP_OK;
}

esp_err_t sntp_wait_for_sync(uint32_t timeout_ms)
{
    if (!sntp_initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    uint32_t start = esp_timer_get_time() / 1000;  // Convert to ms
    uint32_t elapsed = 0;

    while (!sntp_synced && elapsed < timeout_ms) {
        vTaskDelay(pdMS_TO_TICKS(100));
        elapsed = (esp_timer_get_time() / 1000) - start;
    }

    if (sntp_synced) {
        return ESP_OK;
    } else {
        ESP_LOGW(TAG, "SNTP sync timeout after %lu ms", elapsed);
        return ESP_ERR_TIMEOUT;
    }
}

bool sntp_is_synced(void)
{
    return sntp_synced;
}

int64_t sntp_get_timestamp_ms(bool* is_wallclock)
{
    if (sntp_synced) {
        // Wall-clock time available
        struct timeval tv;
        gettimeofday(&tv, NULL);

        // === TEMPORARY DEBUG LOGGING - REMOVE AFTER VERIFICATION ===
        struct tm utc_comp, local_comp;
        gmtime_r(&tv.tv_sec, &utc_comp);
        localtime_r(&tv.tv_sec, &local_comp);

        char *tz_env = getenv("TZ");
        int64_t timestamp_ms = (int64_t)tv.tv_sec * 1000LL + (int64_t)tv.tv_usec / 1000LL;

        ESP_LOGI(TAG, "=== TIMESTAMP DEBUG ===");
        ESP_LOGI(TAG, "  timestamp_ms: %lld", timestamp_ms);
        ESP_LOGI(TAG, "  epoch_sec: %ld", tv.tv_sec);
        ESP_LOGI(TAG, "  TZ env: %s", tz_env ? tz_env : "(not set)");
        ESP_LOGI(TAG, "  gmtime_r (always UTC): %04d-%02d-%02d %02d:%02d:%02d",
                 utc_comp.tm_year + 1900, utc_comp.tm_mon + 1, utc_comp.tm_mday,
                 utc_comp.tm_hour, utc_comp.tm_min, utc_comp.tm_sec);
        ESP_LOGI(TAG, "  localtime_r (uses TZ): %04d-%02d-%02d %02d:%02d:%02d",
                 local_comp.tm_year + 1900, local_comp.tm_mon + 1, local_comp.tm_mday,
                 local_comp.tm_hour, local_comp.tm_min, local_comp.tm_sec);
        ESP_LOGI(TAG, "=======================");
        // === END DEBUG ===

        if (is_wallclock != NULL) {
            *is_wallclock = true;
        }

        // Convert to milliseconds
        return (int64_t)tv.tv_sec * 1000LL + (int64_t)tv.tv_usec / 1000LL;
    } else {
        // Fallback to uptime-based timestamp
        if (is_wallclock != NULL) {
            *is_wallclock = false;
        }

        // Return uptime in milliseconds
        return esp_timer_get_time() / 1000LL;
    }
}

esp_err_t sntp_client_deinit(void)
{
    if (!sntp_initialized) {
        return ESP_OK;
    }

    esp_sntp_stop();
    sntp_initialized = false;
    sntp_synced = false;

    ESP_LOGI(TAG, "SNTP client deinitialized");
    return ESP_OK;
}
