# NexAlert ESP32-S3 Firmware

**Edge node firmware for NexAlert environmental monitoring system**

## Overview

This is the ESP32-S3 firmware for NexAlert field nodes, implementing:
- Sensor sampling
- Lightweight edge intelligence
- Local emergency AP/captive portal
- Telemetry envelope generation
- HMAC authentication
- Store-and-forward resilience

## Prerequisites

**CRITICAL: ESP-IDF 5.1.x REQUIRED**

This firmware requires ESP-IDF 5.1.x installed on your development machine.

### Installation

1. Install ESP-IDF 5.1.x from https://docs.espressif.com/projects/esp-idf/en/v5.1/esp32s3/get-started/
2. Set up environment: `. $IDF_PATH/export.sh`
3. Verify: `idf.py --version` (should report v5.1.x)

## Build

```bash
# Set up ESP-IDF environment
. $IDF_PATH/export.sh

# Configure
cd firmware
idf.py set-target esp32s3

# Build
idf.py build

# Flash (requires hardware)
idf.py flash

# Monitor (requires hardware)
idf.py monitor
```

## Project Structure

```
firmware/
├── CMakeLists.txt          # Top-level project
├── sdkconfig.defaults      # ESP32-S3 defaults
├── partitions.csv          # Partition table
├── main/
│   ├── main.c              # Entry point
│   ├── CMakeLists.txt
│   └── Kconfig.projbuild
└── components/
    ├── sensors/            # Sensor drivers
    ├── diagnostics/        # Health computation
    ├── intelligence/       # Edge intelligence
    ├── telemetry/          # Envelope generation
    ├── security/           # HMAC generation
    ├── network/            # Wi-Fi/TCP
    ├── storage/            # Persistent queue
    ├── system/             # Boot, watchdog
    └── local_ap/           # Emergency AP
```

## Phase 3 Status

**Structure only** - No implementations yet. Component implementations will be added in Phase 4+.

## Version

0.1.0
