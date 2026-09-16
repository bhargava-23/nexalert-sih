# Track 3A File State Reconciliation

**Date**: 2026-09-16  
**Purpose**: Clean reconciliation of current file state vs intended Track 3A architecture

---

## Current File State Assessment

### 1. main/main.c

**Sensor Driver Includes (Lines 32-35):**
```c
#include "i2c_bus.h"
#include "bme680.h"
#include "mpu6050.h"
#include "mq2.h"
```
✅ **STATUS**: CORRECT - BME680/MPU6050/MQ-2 includes present
✅ **STATUS**: CORRECT - No DHT22 include

**Sensor Initialization (Lines 223-283):**
- ✅ I2C bus initialization (line 224)
- ✅ BME680 initialization with calibration (lines 232-260)
- ✅ MPU6050 initialization (lines 262-271)
- ✅ MQ-2 initialization (lines 273-283)
- ✅ No DHT22 initialization

**Sensor Acquisition (Lines 292-356):**
- ✅ BME680: temperature, humidity, pressure, gas readings
- ✅ MPU6050: acceleration readings
- ✅ MQ-2: gas ADC readings
- ✅ No DHT22 acquisition calls

**DHT22 References:**
- Line 249: Comment "replaces DHT22" - ✅ ACCEPTABLE (comment only)
- Line 276: Comment "was DHT22 pin" - ✅ ACCEPTABLE (comment only)

**CONCLUSION**: main.c is CLEAN - no duplicate sensor paths, no production DHT22 code

---

### 2. components/sensors/include/sensor_api.h

**Sensor Types Enum (Lines 23-31):**
```c
typedef enum {
    SENSOR_TYPE_DHT22 = 0,      // Temperature + Humidity (legacy)
    SENSOR_TYPE_BMP280,          // Pressure
    SENSOR_TYPE_PMS5003,         // PM2.5 / PM10
    SENSOR_TYPE_BME680,          // Track 3A: Temperature + Humidity + Pressure + Gas
    SENSOR_TYPE_MPU6050,         // Track 3A: Accelerometer (vibration)
    SENSOR_TYPE_MQ2,             // Track 3A: Gas sensor (raw ADC)
    SENSOR_TYPE_MAX
} sensor_type_t;
```

**ISSUES IDENTIFIED:**
- ❌ DHT22 marked as "legacy" but still present in enum
- ❌ No duplicate enum values (GOOD)
- ⚠️ DHT22 retained for backward compatibility but NOT used in production path

**CONCLUSION**: sensor_api.h is ACCEPTABLE - DHT22 enum kept for legacy/compatibility, not duplicate

---

### 3. components/sensors/CMakeLists.txt

**Current State:**
```cmake
idf_component_register(
    SRCS "dht22.c" "i2c_bus.c" "bme680.c" "mpu6050.c" "mq2.c"
    INCLUDE_DIRS "include"
    REQUIRES driver esp_timer esp_rom esp_adc
)
```

**ISSUES IDENTIFIED:**
- ❌ **CRITICAL**: DHT22.c still in SRCS list
- ❌ **CRITICAL**: DHT22 driver will be compiled and linked even though not used

**ACTION REQUIRED**: Remove "dht22.c" from SRCS

---

### 4. components/config/node_config.c

**MQTT Configuration (Lines 36-46):**
```c
.mqtt = {
    .broker_host = "10.42.0.1",  // Track 3A: Raspberry Pi field broker
    .broker_port = 1883,
    .topic = "Nexalert/telemetry/node1",  // Track 3A: Matches recovered Arduino topic
    .tls_enabled = false,
    .username = "",
    .password = "",
    .keepalive_s = 60,
    .timeout_ms = 5000,
},
```

✅ **STATUS**: CORRECT - Matches Track 3A requirements:
- ✅ broker_host = "10.42.0.1"
- ✅ broker_port = 1883
- ✅ topic = "Nexalert/telemetry/node1"

**Node Identity (Lines 23-28):**
```c
.identity = {
    .node_id = "NODE-001",
    .latitude = 12.9716,
    .longitude = 77.5946,
    .altitude = 920.0f,
},
```

✅ **STATUS**: CORRECT - node_id = "NODE-001"

**CONCLUSION**: node_config.c MQTT and identity settings are CORRECT

---

### 5. components/config/include/node_config.h

**WiFi Configuration Added (Line 46):**
```c
} wifi_config_t;
```

**ISSUES IDENTIFIED:**
- ⚠️ wifi_config_t struct was added
- ❌ **MISSING**: WiFi config not integrated into node_config_complete_t
- ❌ **MISSING**: WiFi SSID "NexAlert_Field_Net" not set in defaults

**ACTION REQUIRED**: 
1. Add wifi_config_t to node_config_complete_t struct
2. Set default SSID to "NexAlert_Field_Net"

---

## Critical Issues Summary

### BLOCKING ISSUES (Must Fix):

1. **CMakeLists.txt**: DHT22.c still in build
   - **Impact**: Compiles unused DHT22 driver
   - **Fix**: Remove "dht22.c" from SRCS list

2. **node_config.h**: WiFi config incomplete
   - **Impact**: No WiFi SSID configuration in firmware
   - **Fix**: Add wifi field to node_config_complete_t, set "NexAlert_Field_Net" default

### NON-BLOCKING ISSUES:

3. **sensor_api.h**: DHT22 enum still present
   - **Impact**: Minor - enum exists but not used in production path
   - **Fix**: Can remain for backward compatibility (marked "legacy")

---

## Missing Track 3A Components

### Not Yet Implemented:

1. **NTP/SNTP Client**
   - **Requirement**: NTP sync from 10.42.0.1
   - **Status**: NOT STARTED

2. **Telemetry Envelope Updates**
   - **Requirement**: Include pressure, vibration, MQ-2 gas in hardware JSON
   - **Status**: NEEDS VERIFICATION - check current telemetry structure

3. **WiFi SSID Integration**
   - **Requirement**: Use "NexAlert_Field_Net" in production
   - **Status**: PARTIALLY IMPLEMENTED - struct exists, not integrated

---

## LOCKED Configuration Values - Current Status

| Setting | Required Value | Current Value | Status |
|---------|---------------|---------------|--------|
| NODE_ID | NODE-001 | NODE-001 | ✅ CORRECT |
| WiFi SSID | NexAlert_Field_Net | NOT SET | ❌ MISSING |
| MQTT broker | 10.42.0.1 | 10.42.0.1 | ✅ CORRECT |
| MQTT port | 1883 | 1883 | ✅ CORRECT |
| MQTT topic | Nexalert/telemetry/node1 | Nexalert/telemetry/node1 | ✅ CORRECT |
| NTP server | 10.42.0.1 | NOT IMPLEMENTED | ❌ MISSING |

---

## Required Cleanup Actions

### IMMEDIATE (Must Fix Before Build):

1. **Remove DHT22 from build**:
   ```cmake
   # components/sensors/CMakeLists.txt
   # REMOVE: "dht22.c" from SRCS
   SRCS "i2c_bus.c" "bme680.c" "mpu6050.c" "mq2.c"
   ```

2. **Complete WiFi configuration integration**:
   - Add wifi field to node_config_complete_t
   - Set default SSID to "NexAlert_Field_Net"
   - Set default password (empty or from recovered Arduino)

### DEFERRED (Required for Track 3A Completion):

3. **Implement NTP/SNTP client**
   - Use ESP-IDF SNTP component
   - Configure NTP server as 10.42.0.1
   - Add fallback to relative uptime if NTP fails

4. **Verify telemetry envelope structure**
   - Check current hardware JSON fields
   - Ensure pressure, vibration, gas fields exist
   - Verify PM2.5/PM10 remain as null/unavailable
   - Ensure NO "intelligence" object added

5. **Verify sensor value serialization**
   - NAN values must serialize as null in JSON
   - Availability flags must be false for missing sensors
   - MQ-2 raw ADC must NOT be converted to ppm

---

## Files Currently Clean (No Duplicates)

✅ main/main.c - Single sensor path (BME680/MPU6050/MQ-2), no DHT22 production code
✅ sensor_api.h - No duplicate enum values
✅ node_config.c - MQTT/node_id settings correct
✅ All sensor drivers (bme680.c, mpu6050.c, mq2.c, i2c_bus.c) - No duplicates

---

## Next Steps (After Cleanup)

1. Apply immediate cleanup fixes (CMakeLists.txt, WiFi config)
2. Verify telemetry envelope structure
3. Implement NTP/SNTP client
4. Attempt firmware build (requires ESP-IDF installation)
5. Document ESP-IDF version requirements
6. Fix any compilation errors
7. Update Track 3A completion documentation

---

**END OF RECONCILIATION REPORT**
