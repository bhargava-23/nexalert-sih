# Main Application Component
# NexAlert ESP32-S3 firmware - Complete intelligence pipeline integration

idf_component_register(
    SRCS "main.c" "calibration_store.c"
    INCLUDE_DIRS "."
    REQUIRES nvs_flash sensors telemetry network intelligence config resilience
)
