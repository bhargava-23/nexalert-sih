#!/bin/bash
# ESP-IDF v5.1.7 MQTT Component Inspection Script
# Run this on the Raspberry Pi where ESP-IDF is installed

echo "========================================="
echo "ESP-IDF MQTT Component Inspection"
echo "========================================="
echo ""

echo "1. Listing MQTT include directory:"
ls -la ~/esp/esp-idf/components/mqtt/esp-mqtt/include
echo ""

echo "2. Finding all header files:"
find ~/esp/esp-idf/components/mqtt/esp-mqtt/include -maxdepth 1 -type f -print
echo ""

echo "3. Searching for esp_mqtt_client_handle_t typedef:"
grep -Rni "typedef.*esp_mqtt_client_handle_t" ~/esp/esp-idf/components/mqtt/esp-mqtt/include
echo ""

echo "4. Searching for esp_mqtt_client_config_t struct:"
grep -Rni "typedef.*esp_mqtt_client_config_t" ~/esp/esp-idf/components/mqtt/esp-mqtt/include
echo ""

echo "5. Searching for esp_mqtt_client_init function:"
grep -Rni "esp_mqtt_client_init" ~/esp/esp-idf/components/mqtt/esp-mqtt/include
echo ""

echo "6. Searching for esp_event_base_t in MQTT headers:"
grep -Rni "esp_event_base_t" ~/esp/esp-idf/components/mqtt/esp-mqtt/include
echo ""

echo "7. Searching for ESP_EVENT_ANY_ID in MQTT headers:"
grep -Rni "ESP_EVENT_ANY_ID" ~/esp/esp-idf/components/mqtt/esp-mqtt/include
echo ""

echo "8. Checking if mqtt_client.h exists:"
if [ -f ~/esp/esp-idf/components/mqtt/esp-mqtt/include/mqtt_client.h ]; then
    echo "FILE EXISTS: mqtt_client.h"
    echo ""
    echo "9. First 100 lines of mqtt_client.h:"
    head -100 ~/esp/esp-idf/components/mqtt/esp-mqtt/include/mqtt_client.h
    echo ""
    echo "10. All #include directives in mqtt_client.h:"
    grep "^#include" ~/esp/esp-idf/components/mqtt/esp-mqtt/include/mqtt_client.h
    echo ""
    echo "11. All typedef lines in mqtt_client.h:"
    grep "typedef" ~/esp/esp-idf/components/mqtt/esp-mqtt/include/mqtt_client.h | head -20
else
    echo "FILE NOT FOUND: mqtt_client.h"
fi
echo ""

echo "12. Checking esp-mqtt directory structure:"
ls -R ~/esp/esp-idf/components/mqtt/esp-mqtt/ | head -50
echo ""

echo "========================================="
echo "Current firmware mqtt_client.c includes:"
echo "========================================="
head -20 ~/nexalert-sih/firmware/components/network/mqtt_client.c
echo ""

echo "========================================="
echo "Current network CMakeLists.txt:"
echo "========================================="
cat ~/nexalert-sih/firmware/components/network/CMakeLists.txt
echo ""

echo "========================================="
echo "INSPECTION COMPLETE"
echo "========================================="
