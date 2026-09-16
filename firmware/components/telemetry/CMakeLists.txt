# Telemetry Component
# - Canonical telemetry envelope generation per schemas/telemetry-envelope.schema.json (Track 3C backend)
# - Hardware JSON payload generation for ESP32 → MQTT transport (Track 3A)

idf_component_register(
    SRCS "telemetry_envelope.c" "hardware_json.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_timer json esp_hw_support
)
