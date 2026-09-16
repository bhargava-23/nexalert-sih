# Sensors Component
# BME680, MPU6050, MQ-2 sensor drivers and unified sensor API
# Track 3A: Matches recovered Arduino deployment hardware configuration

idf_component_register(
    SRCS "i2c_bus.c" "bme680.c" "mpu6050.c" "mq2.c"
    INCLUDE_DIRS "include"
    REQUIRES driver esp_timer esp_rom esp_adc
)
