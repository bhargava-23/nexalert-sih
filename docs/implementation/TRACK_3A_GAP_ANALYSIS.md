# Track 3A: Gap Analysis - Recovered Arduino vs Repository ESP-IDF

**Date**: 2026-09-16  
**Status**: IN PROGRESS

---

## Executive Summary

This document compares the **recovered Arduino sketch** (proven hardware deployment) against the **repository ESP-IDF firmware** to identify gaps and guide Track 3A implementation.

**Recovered Arduino Sketch**: `C:\Users\bhargav\OneDrive\Documents\SIH_4.0.ino`  
**Repository ESP-IDF Firmware**: `firmware/main/main.c`

---

## 1. Recovered Arduino Sketch - Behavioral Reference

### Hardware Configuration (Arduino)

```cpp
#define NODE_ID "NODE-001"
#define I2C_SDA 8   
#define I2C_SCL 9   
#define MQ2_PIN 4   // ESP32-S3 ADC1 pin
#define TELEMETRY_INTERVAL_MS 5000
#define VIBRATION_SAMPLE_INTERVAL_MS 20
```

### Network Configuration (Arduino)

```cpp
const char* ssid = "NexAlert_Field_Net"
const char* pi_ip_address = "10.42.0.1"
const char* mqtt_server = "10.42.0.1"
const int mqtt_port = 1883
const char* mqtt_topic = "Nexalert/telemetry/node1"
const char* ntp_server = "10.42.0.1"
```

### Sensor Drivers (Arduino)

**BME680**:
- Library: `Adafruit_BME680`
- I2C Address: 0x77 with fallback to 0x76
- Initialization: `bme.begin(0x77)` with retry at `0x76`
- Measurements: temperature_c, humidity_rh, pressure_hpa, gas_resistance (raw ADC)

**MPU6050**:
- Library: `Adafruit_MPU6050`
- I2C Address: 0x68 (default)
- Initialization: `mpu.begin()`
- Measurements: accel.acceleration.x/y/z (vibration)

**MQ-2**:
- Library: Direct `analogRead()`
- Pin: GPIO4 (ESP32-S3 ADC1)
- Measurement: Raw ADC value (0-4095)
- **NOT calibrated to ppm** - raw ADC only

**PM2.5 / PM10**:
- **NOT PRESENT** in recovered sketch
- Fields: `null` in JSON
- Availability: `false`

### Hardware JSON Payload (Arduino)

```json
{
  "node_id": "NODE-001",
  "timestamp_ms": <epoch_ms>,
  "sequence": <counter>,
  "sensors": {
    "temperature_c": <float_or_null>,
    "humidity_rh": <float_or_null>,
    "pm25_ugm3": null,
    "pm10_ugm3": null,
    "gas_ppm": <raw_adc_not_ppm>,
    "pressure_hpa": <float_or_null>,
    "water_level_m": null,
    "rainfall_mm_h": null,
    "soil_moisture_vwc_pct": null,
    "vibration_mps2": <float_or_null>
  },
  "availability": {
    "temperature": <bool>,
    "humidity": <bool>,
    "pm25": false,
    "pm10": false,
    "gas": <bool>,
    "pressure": <bool>,
    "water_level": false,
    "rainfall": false,
    "soil_moisture": false,
    "vibration": <bool>
  },
  "power": {
    "battery_pct": 86.0,
    "solar_state": "ACTIVE"
  }
}
```

### Key Observations (Arduino)

1. **Sensor sampling**: BME680 every 5 seconds, MPU6050 every 20ms
2. **Missing sensors**: PM2.5, PM10, water level, rainfall, soil moisture all null/unavailable
3. **MQ-2 semantics**: Raw ADC value in `gas_ppm` field (misleading name, not calibrated ppm)
4. **Power fields**: Hardcoded/demo values (battery_pct=86.0, solar_state="ACTIVE")
5. **Error handling**: Sensors have availability flags, values are null when unavailable
6. **MQTT**: PubSubClient library, publish to "Nexalert/telemetry/node1"
7. **Sequence**: Incrementing counter starting from 0
8. **Timestamp**: NTP sync from 10.42.0.1, fallback to relative uptime

---

## 2. Repository ESP-IDF Firmware - Current State

### Hardware Configuration (ESP-IDF)

**Entry Point**: `firmware/main/main.c`

**NOT FOUND**:
- No BME680 driver in repository
- No MPU6050 driver in repository
- No MQ-2 driver in repository
- No PM2.5/PM10 drivers in repository

**FOUND**:
- DHT22 driver only: `firmware/components/sensors/dht22.c`
- GPIO4 configured for DHT22 (conflicts with Arduino's MQ-2 on GPIO4)

### Network Configuration (ESP-IDF)

**WiFi**: `firmware/components/network/wifi_station.h`
- SSID: Not hardcoded (loaded from config)
- IP: Not specified

**MQTT**: `firmware/components/network/nexalert_mqtt.h`
- Broker: Not hardcoded (loaded from config)
- Topic: Not hardcoded
- Library: ESP-IDF native MQTT client

**NTP**: Not found in repository

### Intelligence Modules (ESP-IDF)

**PRESENT** in `firmware/components/intelligence/`:
- health.c / health.h
- quality.c / quality.h
- reliability.c / reliability.h
- baseline.c / baseline.h
- anomaly.c / anomaly.h
- evidence.c / evidence.h
- confidence.c / confidence.h
- severity.c / severity.h
- risk.c / risk.h
- hazard_state.c / hazard_state.h

**CURRENT USAGE** in `firmware/main/main.c`:
- Intelligence pipeline IMPLEMENTED for DHT22 only
- Pipeline: Sensor → Health → Quality → Reliability → Baseline → Anomaly → Evidence → Confidence → Severity → Risk → Hazard State
- Output: Comprehensive telemetry envelope with intelligence results

### Telemetry Generation (ESP-IDF)

**FOUND**: `firmware/components/telemetry/telemetry_envelope.h`
- Generates comprehensive telemetry envelope
- Includes intelligence results
- **DIFFERENT STRUCTURE** than Arduino hardware JSON

**ESP-IDF Telemetry Structure** (from `main.c`):
- Includes intelligence pipeline results (H_i, Q_i, R_i, baseline, anomaly, evidence, confidence, severity, risk, hazard_state)
- Includes calibration info
- Includes buffer stats
- **NOT COMPATIBLE** with Arduino hardware JSON contract

---

## 3. Gap Analysis

### Gap 1: Sensor Drivers

| Sensor | Arduino | ESP-IDF | Gap |
|--------|---------|---------|-----|
| BME680 | ✅ Adafruit lib | ❌ NOT FOUND | **CRITICAL** - Need BME680 driver |
| MPU6050 | ✅ Adafruit lib | ❌ NOT FOUND | **CRITICAL** - Need MPU6050 driver |
| MQ-2 | ✅ analogRead | ❌ NOT FOUND | **CRITICAL** - Need MQ-2 ADC driver |
| PM2.5 | ❌ null | ❌ null | **OK** - Planned future |
| PM10 | ❌ null | ❌ null | **OK** - Planned future |
| DHT22 | ❌ NOT USED | ✅ PRESENT | **CONFLICT** - Arduino uses BME680, not DHT22 |

**Conclusion**: Repository has **ZERO** of the Arduino's actual sensors. Need to add BME680, MPU6050, and MQ-2 drivers.

### Gap 2: GPIO Configuration

| Pin | Arduino | ESP-IDF | Gap |
|-----|---------|---------|-----|
| GPIO4 | MQ-2 ADC | DHT22 data | **CONFLICT** |
| GPIO8 | I2C SDA | Not configured | **MISSING** |
| GPIO9 | I2C SCL | Not configured | **MISSING** |

**Conclusion**: Need to configure I2C on GPIO8/9 and move MQ-2 to GPIO4 (remove DHT22).

### Gap 3: Network Configuration

| Config | Arduino | ESP-IDF | Gap |
|--------|---------|---------|-----|
| SSID | "NexAlert_Field_Net" | Config-based | **COMPATIBLE** - Can configure |
| Broker | 10.42.0.1:1883 | Config-based | **COMPATIBLE** - Can configure |
| MQTT Topic | "Nexalert/telemetry/node1" | Config-based | **COMPATIBLE** - Can configure |
| NTP | 10.42.0.1 | NOT FOUND | **MISSING** - Need NTP client |

**Conclusion**: Network config is flexible. Need to add NTP client.

### Gap 4: Telemetry Payload Structure

**Arduino Hardware JSON**:
```json
{
  "node_id": "NODE-001",
  "timestamp_ms": 0,
  "sequence": 0,
  "sensors": {...},
  "availability": {...},
  "power": {...}
}
```

**ESP-IDF Intelligence Envelope**:
```json
{
  "node_id": "NODE-001",
  "sequence": 0,
  "timestamp_epoch_s": 0,
  "sensors": {...},
  "intelligence": {
    "H_i": {...},
    "Q_i": {...},
    "R_i": {...},
    "baseline": {...},
    "anomaly": {...},
    ...
  },
  "calibration": {...},
  "buffer": {...}
}
```

**Conclusion**: **INCOMPATIBLE** structures. Need to choose one or support both.

### Gap 5: Intelligence Integration

**Arduino**: **NO intelligence modules** - raw sensor data only

**ESP-IDF**: **FULL intelligence pipeline** implemented

**Track 3A Requirement**: "Reuse the existing intelligence modules under firmware/components/intelligence/"

**Conclusion**: Need to integrate ESP-IDF intelligence into hardware JSON payload.

### Gap 6: MQTT Transport

**Arduino**: PubSubClient library (Arduino ecosystem)

**ESP-IDF**: ESP-IDF native MQTT client

**Conclusion**: **COMPATIBLE** - Both can publish to same broker/topic.

### Gap 7: Missing Data Semantics

**Arduino**: `null` values for missing sensors, availability flags

**ESP-IDF**: `NAN` values for missing sensors

**Conclusion**: **COMPATIBLE** - Both preserve missing != zero.

---

## 4. Implementation Strategy

### Phase 1: Add Missing Sensor Drivers

**Priority: CRITICAL**

1. **BME680 Driver** (`firmware/components/sensors/bme680.c`)
   - I2C interface (GPIO8 SDA, GPIO9 SCL)
   - Address: 0x77 with fallback to 0x76
   - Read: temperature, humidity, pressure, gas resistance

2. **MPU6050 Driver** (`firmware/components/sensors/mpu6050.c`)
   - I2C interface (GPIO8 SDA, GPIO9 SCL)
   - Address: 0x68
   - Read: acceleration x/y/z

3. **MQ-2 Driver** (`firmware/components/sensors/mq2.c`)
   - ADC1 interface (GPIO4)
   - Read: Raw ADC value (NOT ppm)

4. **I2C Initialization** (`firmware/components/sensors/i2c_bus.c`)
   - Configure I2C on GPIO8/9
   - Shared by BME680 and MPU6050

### Phase 2: Remove DHT22 Conflict

**Priority: HIGH**

- Remove DHT22 initialization from `main.c`
- Remove GPIO4 DHT22 config (conflicts with MQ-2)

### Phase 3: Add NTP Client

**Priority: MEDIUM**

- Add NTP sync from 10.42.0.1
- Fallback to relative uptime if NTP fails

### Phase 4: Telemetry Payload Decision

**Priority: CRITICAL**

**Option A: Hardware JSON Only (Simplest)**
- Produce Arduino-compatible hardware JSON
- Keep intelligence results internal
- Backend ingestion layer adds intelligence later (Track 3C)

**Option B: Extended Hardware JSON (Recommended)**
- Add `intelligence` section to hardware JSON
- Preserve Arduino compatibility for raw sensors
- Backend can consume intelligence if present

**Option C: Dual Payloads**
- Publish hardware JSON to `Nexalert/telemetry/node1`
- Publish intelligence envelope to separate topic
- Most complex, not recommended

**RECOMMENDATION**: **Option B** - Extended hardware JSON with optional intelligence section.

### Phase 5: Integrate Intelligence Pipeline

**Priority: HIGH**

1. Wire BME680/MPU6050/MQ-2 into intelligence pipeline
2. Compute H_i, Q_i, R_i, baseline, anomaly, evidence, confidence, severity, risk, hazard_state
3. Add intelligence results to telemetry payload (if Option B chosen)

### Phase 6: Preserve Arduino External Behavior

**Priority: CRITICAL**

1. NODE-001 preserved
2. MQTT topic `Nexalert/telemetry/node1` preserved
3. 5-second sampling interval preserved
4. Null values for unavailable sensors preserved
5. MQ-2 documented as raw ADC, not ppm
6. Battery/solar hardcoded demo values preserved

---

## 5. Acceptance Criteria Mapping

| Criterion | Status | Notes |
|-----------|--------|-------|
| A. Recovered Arduino sketch documented | ✅ YES | This document |
| B. Repository production firmware path identified | ✅ YES | `firmware/main/main.c` (ESP-IDF) |
| C. Proven sensor/MQTT config preserved | ⏸️ PENDING | Need to port to ESP-IDF |
| D. Existing edge intelligence connected | ⏸️ PENDING | Intelligence modules exist but need sensor data |
| E. Hardware payload contract-compatible | ⏸️ PENDING | Need telemetry decision (Option B) |
| F. Missing sensors null + availability=false | ✅ YES | PM2.5/PM10 remain null |
| G. MQ-2 raw ADC not presented as ppm | ✅ YES | Will document clearly |
| H. Firmware build succeeds | ⏸️ PENDING | Need to implement |
| I. Relevant firmware tests pass | ⏸️ PENDING | Need to run |
| J. Hardware-dependent issues reported | ⏸️ PENDING | Will document |
| K. Completion report with evidence | ⏸️ PENDING | After implementation |

---

## 6. Next Steps

1. **Immediate**: Implement BME680, MPU6050, MQ-2 drivers
2. **Immediate**: Add I2C bus initialization
3. **Immediate**: Remove DHT22 conflict
4. **Immediate**: Decide telemetry payload structure (Option B recommended)
5. **Immediate**: Integrate intelligence pipeline
6. **Immediate**: Build and test firmware
7. **Final**: Write Track 3A completion report with exact evidence

---

## 7. Blocking Issues

**NONE** - All gaps can be addressed with code changes. No physical hardware required for build verification.

**Hardware-Dependent Verification**:
- BME680 I2C communication (cannot verify without hardware)
- MPU6050 I2C communication (cannot verify without hardware)
- MQ-2 ADC reading (cannot verify without hardware)
- Actual sensor values (cannot verify without hardware)

**Build Verification**: CAN be done without hardware using ESP-IDF build system.

---

**TRACK 3A STATUS**: **IN PROGRESS** - Gap analysis complete, implementation pending.
