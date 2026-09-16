# Network Component
# Wi-Fi station mode, MQTT client, and SNTP/NTP client

idf_component_register(
    SRCS "wifi_station.c" "mqtt_client.c" "sntp_client.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_wifi esp_event esp_netif mqtt nvs_flash lwip
)
