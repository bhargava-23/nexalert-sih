# Sensors Component
# DHT22 temperature/humidity sensor driver and unified sensor API

idf_component_register(
    SRCS "dht22.c"
    INCLUDE_DIRS "include"
    REQUIRES driver
)
