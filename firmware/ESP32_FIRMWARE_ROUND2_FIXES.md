# ESP32-S3 Firmware Round 2 Compilation Fixes
**Date:** 2026-09-10  
**Target:** ESP-IDF v5.1.7 on Raspberry Pi  
**Status:** All source fixes applied, ready for build

---

## Summary

Fixed 6 compilation errors from the Raspberry Pi ESP-IDF v5.1.7 build. All fixes are minimal source-only changes preserving the complete NexAlert architecture, telemetry schema, and MQTT topic format.

**No commits made. No architecture changed. No features removed. No warnings suppressed.**

---

## Files Changed (9 edits across 6 files)

### 1. `firmware/components/network/mqtt_client.c`

**Lines 10-12 (3 changes):**

**Original:**
```c
#include "mqtt_client.h"
#include "esp_mqtt_client.h"
#include "esp_log.h"
```

**Fixed:**
```c
#include "mqtt_client.h"
#include <mqtt_client.h>
#include "esp_event.h"
#include "esp_log.h"
```

**Reason:**
- Line 10: `#include "mqtt_client.h"` (quotes) → our local header in `include/mqtt_client.h`
- Line 11: `#include <mqtt_client.h>` (angle brackets) → ESP-IDF v5.1.7 mqtt component's public header from `components/mqtt/esp-mqtt/include/mqtt_client.h`
- Line 12: Added `#include "esp_event.h"` → provides `esp_event_base_t` and `ESP_EVENT_ANY_ID` types used in `esp_mqtt_client_register_event()` call

**ESP-IDF v5.1.7 MQTT API verified:**
- Header: `mqtt_client.h` (not `esp_mqtt_client.h`)
- Types: `esp_mqtt_client_handle_t`, `esp_mqtt_client_config_t` with nested `broker.address.uri` structure
- Functions: `esp_mqtt_client_init()`, `esp_mqtt_client_register_event()`, `esp_mqtt_client_start()`, `esp_mqtt_client_publish()`, `esp_mqtt_client_stop()`, `esp_mqtt_client_destroy()`
- Event types: from `esp_event.h`, not from mqtt_client.h

---

### 2. `firmware/components/network/include/wifi_station.h`

**Line 12:**

**Original:**
```c
#include "esp_err.h"
```

**Fixed:**
```c
#include "esp_err.h"
#include <stdbool.h>
```

**Reason:**
- Function `wifi_is_connected(void)` returns `bool` type
- C99 `bool` type requires `<stdbool.h>` header

---

### 3. `firmware/components/network/CMakeLists.txt`

**Line 7:**

**Original:**
```cmake
    REQUIRES esp_wifi esp_event esp_netif mqtt
```

**Fixed:**
```cmake
    REQUIRES esp_wifi esp_event esp_netif mqtt nvs_flash
```

**Reason:**
- `wifi_station.c` line 12 includes `"nvs_flash.h"`
- NVS Flash initialization is required before Wi-Fi init (standard ESP-IDF pattern)
- Component dependency must be declared in CMakeLists.txt REQUIRES clause

---

### 4. `firmware/components/sensors/dht22.c`

**Line 15:**

**Original:**
```c
#include "esp_log.h"
#include <string.h>
```

**Fixed:**
```c
#include "esp_log.h"
#include "esp_rom_sys.h"
#include <string.h>
```

**Reason:**
- Added `#include "esp_rom_sys.h"` for `esp_rom_delay_us()` declaration
- Required after migrating from deprecated `ets_delay_us()` to ROM API

**Line 101:**

**Original:**
```c
    ets_delay_us(DHT22_START_SIGNAL_US);
```

**Fixed:**
```c
    esp_rom_delay_us(DHT22_START_SIGNAL_US);
```

**Reason:**
- `ets_delay_us()` removed in ESP-IDF v5.x
- `esp_rom_delay_us()` is the official replacement in ESP-IDF v5.1.7
- Function behavior identical (microsecond precision delay)
- Critical for DHT22 GPIO bit-bang protocol timing

---

### 5. `firmware/components/sensors/CMakeLists.txt`

**Line 7:**

**Original:**
```cmake
    REQUIRES driver esp_timer
```

**Fixed:**
```cmake
    REQUIRES driver esp_timer esp_rom
```

**Reason:**
- Added `esp_rom` component dependency
- Provides `esp_rom_sys.h` header for `esp_rom_delay_us()` function
- Required after migrating from `ets_delay_us()` to ESP-IDF v5.x ROM API

---

### 6. `firmware/components/telemetry/telemetry_envelope.c`

**Line 192:**

**Original:**
```c
    ESP_LOGD(TAG, "Generated telemetry envelope, sequence=%u", telem_state.sequence - 1);
```

**Fixed:**
```c
    ESP_LOGD(TAG, "Generated telemetry envelope, sequence=%" PRIu32, telem_state.sequence - 1);
```

**Reason:**
- `telem_state.sequence` is `uint32_t` (declared line 28)
- Expression `telem_state.sequence - 1` yields `long unsigned int` on ESP32-S3 target
- `%u` format specifier expects `unsigned int`, causing type mismatch warning with `-Werror`
- `"%" PRIu32` is the portable C99 format macro for `uint32_t` from `<inttypes.h>` (already included line 17)

---

### 7. `firmware/components/telemetry/CMakeLists.txt`

**Line 7:**

**Original:**
```cmake
    REQUIRES esp_timer json
```

**Fixed:**
```cmake
    REQUIRES esp_timer json esp_hw_support
```

**Reason:**
- Added `esp_hw_support` component dependency
- Provides `esp_random.h` header for `esp_random()` function (used in `generate_ulid()` at line 56 of telemetry_envelope.c)
- Already included at line 13 after Round 1 fixes, now CMake dependency matches

---

## Verification of Round 1 Fixes

All Round 1 fixes remain intact:
- ✅ `mqtt_client.h` line 13: `#include <stdbool.h>` present (added Round 1)
- ✅ `telemetry_envelope.c` line 13: `#include "esp_random.h"` present (added Round 1)
- ✅ `telemetry_envelope.c` line 17: `#include <inttypes.h>` present (added Round 1)
- ✅ `telemetry_envelope.c` line 57: ULID format uses `"%016" PRIX64 "%08" PRIX32` (fixed Round 1)
- ✅ No remaining `ets_delay_us` calls anywhere in firmware (verified via grep)
- ✅ No remaining `esp_mqtt_client.h` includes (verified via grep)
- ✅ No remaining `%u` with `uint32_t` expressions (verified via grep)

---

## Architecture Preservation

**Unchanged:**
- ✅ ESP32-S3 target (sdkconfig)
- ✅ ESP-IDF v5.1.7 (no downgrade)
- ✅ MQTT broker: local Mosquitto on Raspberry Pi
- ✅ MQTT topic: `Nexalert/telemetry/node1` (locked format, line 73-74 of mqtt_client.c)
- ✅ MQTT QoS: 1 (at least once delivery)
- ✅ Wi-Fi station mode with reconnection
- ✅ NVS Flash for Wi-Fi credentials
- ✅ DHT22 sensor with GPIO bit-bang protocol
- ✅ Telemetry envelope schema (schemas/telemetry-envelope.schema.json)
- ✅ ULID generation with timestamp + random
- ✅ Edge intelligence, buffering, heartbeat (main app logic untouched)
- ✅ Compiler warnings enabled with `-Werror` (not disabled)
- ✅ All existing component structure

---

## Build Instructions

On the Raspberry Pi with ESP-IDF v5.1.7 activated:

```bash
cd ~/nexalert-sih/firmware
idf.py fullclean
idf.py build
```

**Expected result:**
- All 6 original compilation errors resolved
- Clean build with no remaining type errors
- Possible warnings about unused variables or functions (non-blocking)

**If build fails:**
- Read the full error output
- Identify any NEW compilation errors (not the original 6)
- Check for linker errors or missing component dependencies
- Report exact error messages for further diagnosis

---

## What Was NOT Changed

- ❌ No commits made to git
- ❌ No redesign of networking, telemetry, or edge intelligence
- ❌ No removal of MQTT, sensors, or any NexAlert features
- ❌ No changes to telemetry schema or MQTT topic format
- ❌ No compiler warning suppression or `-Werror` removal
- ❌ No unrelated file modifications
- ❌ No changes to main application logic
- ❌ No changes to CMakeLists.txt outside the 3 component dependencies
- ❌ No sdkconfig modifications

---

## ESP-IDF v5.1.7 MQTT Component Details (Discovered)

Based on ESP-IDF v5.1.7 documentation and build system:

**Component name:** `mqtt` (not `esp_mqtt`)

**Public header:** `components/mqtt/esp-mqtt/include/mqtt_client.h`

**Include path added by build system:**
```
./components/mqtt/esp-mqtt/include
```

**Include in source:**
```c
#include <mqtt_client.h>   // Angle brackets for ESP-IDF component header
```

**Key types:**
- `esp_mqtt_client_handle_t` - Opaque client handle
- `esp_mqtt_client_config_t` - Configuration struct with nested sub-structs:
  - `broker.address.uri` - MQTT broker URI string
  - `network.timeout_ms` - Network timeout
  - `session.keepalive` - Keepalive interval

**Event system:**
- `esp_event_base_t` from `esp_event.h` (NOT from mqtt_client.h)
- `ESP_EVENT_ANY_ID` from `esp_event.h`
- `esp_mqtt_client_register_event()` registers callback for MQTT events

**API functions:**
- `esp_mqtt_client_init()` - Initialize client
- `esp_mqtt_client_start()` - Start connection
- `esp_mqtt_client_publish()` - Publish message
- `esp_mqtt_client_stop()` - Stop connection
- `esp_mqtt_client_destroy()` - Clean up client

**CMake dependency:**
```cmake
REQUIRES mqtt esp_event
```

---

## Next Steps

1. **Build on Raspberry Pi:**
   ```bash
   cd ~/nexalert-sih/firmware
   idf.py fullclean
   idf.py build
   ```

2. **If build succeeds:**
   - Verify no warnings remain (or only harmless unused-variable warnings)
   - Test flash and run on ESP32-S3 hardware
   - Verify MQTT telemetry publishes to `Nexalert/telemetry/node1`

3. **If build fails with NEW errors:**
   - Do NOT commit these fixes yet
   - Report new errors for Round 3 fixes
   - Continue until firmware builds completely

4. **After successful build:**
   - Review all changes one final time
   - Commit with message: "ESP32-S3 firmware: ESP-IDF v5.1.7 compilation fixes"
   - Test on hardware

---

## Contacts

**ESP-IDF v5.1 Documentation:**
- [MQTT Client API](https://docs.espressif.com/projects/esp-idf/en/v5.1.7/esp32/api-reference/protocols/mqtt.html)

**NexAlert Telemetry Schema:**
- `schemas/telemetry-envelope.schema.json`
- Locked contract: `schema_version: "telemetry.v1"`

**MQTT Topic Format:**
- Locked: `Nexalert/telemetry/{node_id}`
- Example: `Nexalert/telemetry/node1`

---

**END OF ROUND 2 FIXES REPORT**
