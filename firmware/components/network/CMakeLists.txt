# Network Component
# Wi-Fi station mode and MQTT client for telemetry publishing

idf_component_register(
    SRCS "wifi_station.c" "mqtt_client.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_wifi esp_event esp_netif mqtt nvs_flash
)
