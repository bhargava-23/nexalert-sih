# Track 3A: Hardware JSON Architecture Decision

**Date**: 2026-09-16  
**Status**: IMPLEMENTED

---

## Architecture Decision: Hardware JSON vs Canonical Telemetry

### Authoritative Decision

Track 3A publishes the **recovered Arduino hardware JSON** on MQTT.

The existing **canonical telemetry.v1 envelope** is NOT being discarded. It belongs to the software-side canonical ingestion/normalization layer (Track 3C).

### Architecture Flow

```
ESP32 (Track 3A)
  ↓
Hardware JSON (simple sensor readings)
  ↓
MQTT topic: Nexalert/telemetry/node1
  ↓
Track 3C Hardware-to-Canonical Normalization (future)
  ↓
Canonical telemetry.v1 Envelope (backend)
  ↓
Master/Backend Services
```

### Two Contracts, Two Purposes

1. **Hardware JSON** = ESP32/MQTT Transport Contract
   - **Purpose**: Raw sensor readings from hardware
   - **Location**: ESP32 firmware → MQTT
   - **Structure**: Simple flat sensor + availability + power
   - **File**: `firmware/components/telemetry/hardware_json.c`

2. **Canonical Telemetry.v1** = Backend Software Contract
   - **Purpose**: Normalized backend intelligence pipeline
   - **Location**: Track 3C ingestion → Backend
   - **Structure**: Rich envelope with diagnostics, location, metadata
   - **File**: `firmware/components/telemetry/telemetry_envelope.c` (PRESERVED)

---

## Hardware JSON Implementation

### Files Created

1. **`components/telemetry/include/hardware_json.h`**
   - Hardware JSON serializer header
   - Defines hardware_sensor_readings_t struct
   - Defines hardware_power_t struct
   - API: hardware_json_init(), hardware_json_generate(), hardware_json_get_sequence()

2. **`components/telemetry/hardware_json.c`**
   - Hardware JSON serializer implementation
   - Generates EXACT locked hardware JSON structure
   - NAN → JSON null serialization
   - Availability flags derived from NAN check
   - timestamp_ms (Unix milliseconds)
   - sequence (monotonic per-node)

### Files Modified

1. **`components/telemetry/CMakeLists.txt`**
   - Added hardware_json.c to SRCS

2. **`main/main.c`**
   - Changed include from telemetry_envelope.h to hardware_json.h
   - Updated telemetry generation to use hardware_json_generate()
   - Maps Track 3A sensors to hardware JSON structure:
     - BME680 → temperature_c, humidity_rh, pressure_hpa
     - MPU6050 → vibration_mps2
     - MQ-2 → gas_ppm (raw ADC)
     - PM2.5/PM10 → null + unavailable
   - Updated initialization to call hardware_json_init()
   - Updated WiFi config to use g_config.wifi.ssid (NexAlert_Field_Net)

### Files Preserved (NOT Modified)

1. **`components/telemetry/telemetry_envelope.c`** - PRESERVED for Track 3C backend canonical ingestion
2. **`components/telemetry/include/telemetry_envelope.h`** - PRESERVED for Track 3C

---

## Hardware JSON Contract (Locked)

### Structure

```json
{
  "node_id": "NODE-001",
  "timestamp_ms": 1750000000000,
  "sequence": 1842,
  "sensors": {
    "temperature_c": 31.4,
    "humidity_rh": 58.2,
    "pm25_ugm3": null,
    "pm10_ugm3": null,
    "gas_ppm": 3.2,
    "pressure_hpa": 1009.8,
    "water_level_m": null,
    "rainfall_mm_h": null,
    "soil_moisture_vwc_pct": null,
    "vibration_mps2": null
  },
  "availability": {
    "temperature": true,
    "humidity": true,
    "pm25": false,
    "pm10": false,
    "gas": true,
    "pressure": true,
    "water_level": false,
    "rainfall": false,
    "soil_moisture": false,
    "vibration": false
  },
  "power": {
    "battery_pct": 86.0,
    "solar_state": "ACTIVE"
  }
}
```

### Critical Rules

1. **Missing numeric values (NAN) MUST serialize as JSON null**
2. **Never emit NaN, infinity, or substitute zero**
3. **Availability flags derived from NAN check**
4. **PM2.5/PM10 remain null + unavailable until physical sensors connected**
5. **gas_ppm field name preserved (hardware contract) but value is RAW ADC (0-4095), NOT calibrated ppm**
6. **NO intelligence, diagnostics, location, or metadata fields**

### Sensor Mapping

| Physical Sensor | Hardware JSON Field | Notes |
|----------------|---------------------|-------|
| BME680 temperature | temperature_c | Calibrated °C |
| BME680 humidity | humidity_rh | Calibrated % RH |
| BME680 pressure | pressure_hpa | Calibrated hPa |
| MQ-2 gas | gas_ppm | RAW ADC (0-4095), NOT ppm |
| MPU6050 acceleration | vibration_mps2 | Magnitude m/s² |
| PM2.5 sensor | pm25_ugm3 | null (not connected) |
| PM10 sensor | pm10_ugm3 | null (not connected) |
| Water level | water_level_m | null (not connected) |
| Rainfall | rainfall_mm_h | null (not connected) |
| Soil moisture | soil_moisture_vwc_pct | null (not connected) |

---

## Configuration Values (Locked)

All locked configuration values are preserved:

| Setting | Value | Location |
|---------|-------|----------|
| NODE_ID | NODE-001 | g_config.identity.node_id |
| WiFi SSID | NexAlert_Field_Net | g_config.wifi.ssid |
| MQTT broker | 10.42.0.1 | g_config.mqtt.broker_host |
| MQTT port | 1883 | g_config.mqtt.broker_port |
| MQTT topic | Nexalert/telemetry/node1 | g_config.mqtt.topic |
| NTP server | 10.42.0.1 | (NOT YET IMPLEMENTED) |

---

## Next Steps (NOT YET STARTED)

1. **SNTP/NTP Implementation** - NOT YET STARTED
   - Use ESP-IDF SNTP component
   - Configure NTP server as 10.42.0.1
   - Fallback to uptime-based timestamp if NTP fails

2. **Hardware JSON Tests** - NOT YET STARTED
   - Test exact field names
   - Test exact structure
   - Test null handling
   - Test availability flags
   - Test sequence monotonicity
   - Test timestamp_ms format
   - Test PM2.5/PM10 unavailable state
   - Test no intelligence object
   - Test no extra root fields

3. **ESP-IDF Installation** - BLOCKED
   - Determine ESP-IDF version requirements
   - Install ESP-IDF toolchain
   - Attempt firmware build
   - Fix compilation errors

---

## Remaining Blockers

1. **ESP-IDF toolchain not installed** - Cannot build firmware
2. **Physical hardware not available** - Cannot verify runtime behavior
3. **NTP/SNTP not implemented** - timestamp_ms currently uses uptime, not wall-clock time
4. **Hardware JSON tests not written** - Need focused tests for contract compliance

---

**END OF ARCHITECTURE DECISION DOCUMENTATION**
