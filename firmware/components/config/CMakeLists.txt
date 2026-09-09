# Configuration Component
# Centralized embedded configuration for NexAlert edge node

idf_component_register(
    SRCS "node_config.c"
    INCLUDE_DIRS "include"
    REQUIRES nvs_flash
)
