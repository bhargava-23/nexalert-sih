#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

static const char *TAG = "nexalert-main";

void app_main(void)
{
    ESP_LOGI(TAG, "NexAlert Node Firmware");
    ESP_LOGI(TAG, "Version: 0.1.0");
    ESP_LOGI(TAG, "Phase 3: Structure only - no implementation yet");

    // Phase 3: Empty main function
    // Component initialization and main loop will be added in Phase 4+
}
