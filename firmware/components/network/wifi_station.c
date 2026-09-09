/**
 * @file wifi_station.c
 * @brief Wi-Fi station mode implementation
 *
 * Connects ESP32 to local Wi-Fi network to reach Raspberry Pi MQTT broker.
 */

#include "wifi_station.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include <string.h>

static const char *TAG = "wifi";

// Event bits for connection status
#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT      BIT1

// Module state
static struct {
    bool initialized;
    bool connected;
    EventGroupHandle_t event_group;
    esp_netif_t* netif;
    char ip_address[16];
} wifi_state = {0};

/**
 * Wi-Fi event handler
 */
static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                               int32_t event_id, void* event_data)
{
    if (event_base == WIFI_EVENT) {
        if (event_id == WIFI_EVENT_STA_START) {
            ESP_LOGI(TAG, "Wi-Fi started, connecting...");
            esp_wifi_connect();
        } else if (event_id == WIFI_EVENT_STA_DISCONNECTED) {
            ESP_LOGW(TAG, "Wi-Fi disconnected, reconnecting...");
            wifi_state.connected = false;
            memset(wifi_state.ip_address, 0, sizeof(wifi_state.ip_address));
            xEventGroupClearBits(wifi_state.event_group, WIFI_CONNECTED_BIT);
            esp_wifi_connect();
        }
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        snprintf(wifi_state.ip_address, sizeof(wifi_state.ip_address),
                 IPSTR, IP2STR(&event->ip_info.ip));
        ESP_LOGI(TAG, "Got IP address: %s", wifi_state.ip_address);
        wifi_state.connected = true;
        xEventGroupSetBits(wifi_state.event_group, WIFI_CONNECTED_BIT);
    }
}

esp_err_t wifi_station_init(const nexalert_wifi_config_t* config)
{
    if (config == NULL || config->ssid == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Create event group
    wifi_state.event_group = xEventGroupCreate();
    if (wifi_state.event_group == NULL) {
        return ESP_ERR_NO_MEM;
    }

    // Initialize network interface
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    wifi_state.netif = esp_netif_create_default_wifi_sta();

    // Initialize Wi-Fi with default config
    wifi_init_config_t wifi_init_cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&wifi_init_cfg));

    // Register event handlers
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID,
                                               &wifi_event_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP,
                                               &wifi_event_handler, NULL));

    // Configure Wi-Fi
    wifi_config_t wifi_cfg = {0};
    strncpy((char*)wifi_cfg.sta.ssid, config->ssid, sizeof(wifi_cfg.sta.ssid) - 1);
    if (config->password != NULL) {
        strncpy((char*)wifi_cfg.sta.password, config->password, sizeof(wifi_cfg.sta.password) - 1);
    }
    wifi_cfg.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
    wifi_cfg.sta.pmf_cfg.capable = true;
    wifi_cfg.sta.pmf_cfg.required = false;

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_cfg));
    ESP_ERROR_CHECK(esp_wifi_start());

    wifi_state.initialized = true;
    ESP_LOGI(TAG, "Wi-Fi station initialized, connecting to SSID: %s", config->ssid);

    // Wait for connection (with timeout)
    EventBits_t bits = xEventGroupWaitBits(wifi_state.event_group,
                                           WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
                                           pdFALSE, pdFALSE,
                                           pdMS_TO_TICKS(10000));

    if (bits & WIFI_CONNECTED_BIT) {
        ESP_LOGI(TAG, "Connected to Wi-Fi");
        return ESP_OK;
    } else {
        ESP_LOGW(TAG, "Wi-Fi connection timeout (will retry in background)");
        return ESP_OK; // Still return OK, background reconnect will handle it
    }
}

bool wifi_is_connected(void)
{
    return wifi_state.connected;
}

esp_err_t wifi_get_ip(char* ip_str, size_t len)
{
    if (!wifi_state.connected || len < 16) {
        return ESP_ERR_INVALID_STATE;
    }

    strncpy(ip_str, wifi_state.ip_address, len - 1);
    ip_str[len - 1] = '\0';
    return ESP_OK;
}

esp_err_t wifi_station_deinit(void)
{
    if (!wifi_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    esp_wifi_stop();
    esp_wifi_deinit();
    esp_event_handler_unregister(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler);
    esp_event_handler_unregister(IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler);
    vEventGroupDelete(wifi_state.event_group);

    memset(&wifi_state, 0, sizeof(wifi_state));
    ESP_LOGI(TAG, "Wi-Fi station deinitialized");

    return ESP_OK;
}
