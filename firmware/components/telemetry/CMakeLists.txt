# Telemetry Component
# Canonical telemetry envelope generation per schemas/telemetry-envelope.schema.json

idf_component_register(
    SRCS "telemetry_envelope.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_timer json esp_hw_support
)
