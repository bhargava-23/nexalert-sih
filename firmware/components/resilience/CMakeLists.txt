# Resilience Component
# Edge resilience: buffering, reconnect/replay, heartbeat
# CRITICAL INVARIANT: Network failure != Edge intelligence failure

idf_component_register(
    SRCS "telemetry_buffer.c" "node_heartbeat.c"
    INCLUDE_DIRS "include"
    REQUIRES freertos
)
