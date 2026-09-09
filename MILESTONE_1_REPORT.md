# Track A: Hardware Vertical Slice - Milestone 1 Implementation Report

**Status:** SOFTWARE COMPLETE - Hardware Testing Required

## Overview

Milestone 1 implements the first real end-to-end hardware path:
```
ESP32-S3 → Sensor Reading → Calibration → Canonical Telemetry JSON → MQTT → Raspberry Pi → Schema Validation → Persistence
```

## Files Created/Modified

### ESP32 Firmware (C/ESP-IDF)

**Component: Sensors**
- `firmware/components/sensors/include/sensor_api.h` - Unified sensor interface
- `firmware/components/sensors/include/dht22.h` - DHT22 driver interface  
- `firmware/components/sensors/dht22.c` - DHT22 implementation with calibration
- `firmware/components/sensors/CMakeLists.txt` - Build configuration

**Component: Telemetry**
- `firmware/components/telemetry/include/telemetry_envelope.h` - Envelope generation interface
- `firmware/components/telemetry/telemetry_envelope.c` - JSON serialization per canonical schema
- `firmware/components/telemetry/CMakeLists.txt` - Build configuration

**Component: Network**
- `firmware/components/network/include/wifi_station.h` - Wi-Fi station interface
- `firmware/components/network/wifi_station.c` - Wi-Fi connection management
- `firmware/components/network/include/mqtt_client.h` - MQTT publisher interface
- `firmware/components/network/mqtt_client.c` - MQTT QoS 1 publishing
- `firmware/components/network/CMakeLists.txt` - Build configuration

**Main Application**
- `firmware/main/calibration_store.h` - NVS calibration storage interface
- `firmware/main/calibration_store.c` - Calibration persistence
- `firmware/main/main.c` - Node application (UPDATED)
- `firmware/main/CMakeLists.txt` - Build configuration (UPDATED)

### Raspberry Pi Receiver (Python)

**MQTT Subscriber**
- `scripts/pi_mqtt_subscriber.py` - MQTT subscriber with schema validation
- `scripts/requirements.txt` - Python dependencies
- `scripts/setup_pi.sh` - Pi setup automation

**Total:** 17 files created/modified

## Architecture Compliance

### ✅ Preserves Locked Architecture
- No modifications to Phase 5 intelligence pipeline
- No modifications to canonical schema (schemas/telemetry-envelope.schema.json)
- No duplicate telemetry formats created
- Missing != zero invariant preserved (NAN for missing measurements)

### ✅ Canonical Telemetry Contract
- Uses existing schemas/telemetry-envelope.schema.json
- Generates compliant JSON with cJSON library
- ULID for telemetry_id
- ISO 8601 timestamps
- Source: "HARDWARE" (distinguishes from simulation)
- Nullable measurements serialized as JSON null

### ✅ Calibration Flow (Decision C2)
```
Raw Sensor → Calibration Coefficients (NVS) → Calibrated Value → Diagnostics → Telemetry
```
- Calibration stored in NVS, NOT hardcoded
- Per-sensor calibration (temperature, humidity separate)
- Versioned calibration artifacts
- Valid flags preserve missing != zero

### ✅ MQTT Transport
- Topic: `nexalert/nodes/{node_id}/telemetry`
- QoS: 1 (at least once delivery)
- Local Mosquitto broker on Raspberry Pi
- Auto-reconnect on disconnect

## Key Implementation Details

### ESP32 Sensor Pipeline

1. **Initialization** (app_main):
   - Calibration store (NVS)
   - Telemetry envelope generator
   - Wi-Fi station mode
   - MQTT client connection

2. **Sampling Task** (60-second period):
   - Load calibration from NVS
   - Initialize DHT22 with calibration
   - Read temperature and humidity
   - Apply calibration (value_calibrated = raw * scale + offset)
   - Build telemetry envelope (measurements, diagnostics, power)
   - Generate JSON with ULID and timestamp
   - Publish to MQTT with QoS 1

3. **Missing Value Handling**:
   - Sensor errors → valid=false in sensor_reading_t
   - valid=false → NAN in measurements_t
   - NAN → JSON null via add_nullable_number()
   - Missing != zero invariant preserved throughout

### Raspberry Pi Receiver

1. **Subscription**:
   - Connect to localhost:1883
   - Subscribe to `nexalert/nodes/+/telemetry` (all nodes)
   - Parse JSON payload

2. **Validation**:
   - Load schemas/telemetry-envelope.schema.json
   - Validate against canonical contract
   - Schema enforces missing != zero via ["number", "null"] types

3. **Persistence** (Milestone 1):
   - Simple file persistence: `telemetry_{node_id}_{telemetry_id}_{timestamp}.json`
   - Production: TimescaleDB/PostgreSQL integration (later)

## Configuration Required (Before Hardware Testing)

### ESP32 (firmware/main/main.c)
```c
#define WIFI_SSID "YOUR_WIFI_SSID"        // Replace with actual SSID
#define WIFI_PASS "YOUR_WIFI_PASSWORD"    // Replace with actual password
#define MQTT_BROKER "192.168.1.100"       // Replace with Pi IP address
```

### Raspberry Pi
```bash
# Run setup script
cd /c/projects/nexalert-sih/scripts
chmod +x setup_pi.sh
./setup_pi.sh

# Start subscriber
python3 pi_mqtt_subscriber.py
```

## Build Instructions

### ESP32 Firmware (Requires ESP-IDF 5.1.x)

```bash
# Set IDF_PATH environment variable
export IDF_PATH=/path/to/esp-idf

# Navigate to firmware directory
cd /c/projects/nexalert-sih/firmware

# Configure project
idf.py menuconfig
# → Set Wi-Fi SSID/password in component config → NexAlert Node
# → Set MQTT broker IP

# Build firmware
idf.py build

# Flash to ESP32-S3 (with device connected)
idf.py -p /dev/ttyUSB0 flash monitor
```

### Raspberry Pi Setup

```bash
# On Raspberry Pi
cd /path/to/nexalert-sih/scripts

# Run setup script (installs Mosquitto + Python deps)
chmod +x setup_pi.sh
./setup_pi.sh

# Start MQTT subscriber
python3 pi_mqtt_subscriber.py
```

## Verification Plan (Hardware-Dependent)

### Step 1: ESP32 Build Verification
```bash
cd firmware
idf.py build
# Expected: Build succeeds, firmware.bin generated
```

### Step 2: Pi Setup Verification
```bash
cd scripts
./setup_pi.sh
# Expected: Mosquitto running, Python deps installed
```

### Step 3: MQTT End-to-End Test
```bash
# Terminal 1 (Pi): Start subscriber
python3 pi_mqtt_subscriber.py

# Terminal 2 (Pi): Publish test message
mosquitto_pub -h localhost -t "nexalert/nodes/TEST-001/telemetry" -m '{
  "telemetry_id": "01HZTEST0000000000000000",
  "node_id": "TEST-001",
  "timestamp": "2026-09-09T10:00:00.000Z",
  "sequence": 0,
  "source": "HARDWARE",
  "measurements": {"temp_c": 25.5, "humidity_pct": 60.0},
  "diagnostics": {"uptime_s": 100, "self_test_passed": true},
  "power": {},
  "location": {"latitude": 28.6139, "longitude": 77.2090}
}'

# Expected: Subscriber receives, validates schema, persists JSON file
```

### Step 4: ESP32 → Pi Integration Test
1. Flash ESP32 with built firmware
2. Connect DHT22 sensor to GPIO4
3. Power on ESP32
4. Verify Wi-Fi connection in serial monitor
5. Verify MQTT connection established
6. Observe telemetry published every 60 seconds
7. Verify Pi subscriber receives and validates messages
8. Verify JSON files persisted with correct schema

### Step 5: Calibration Test
```bash
# On ESP32 (via serial monitor or provisioning tool)
# Set calibration coefficients in NVS
nvs_set calibration 0_temp blob <calibration_t bytes>

# Expected: Calibrated values differ from raw DHT22 readings
```

## Known Limitations (Milestone 1)

### Hardware-Dependent Items
- ❌ **Cannot verify ESP32 build** without ESP-IDF toolchain
- ❌ **Cannot verify firmware execution** without ESP32-S3 hardware
- ❌ **Cannot verify DHT22 readings** without physical sensor
- ❌ **Cannot verify MQTT transport** without Pi broker + ESP32 connection
- ❌ **Cannot verify end-to-end flow** without complete hardware setup

### Software Limitations
- File-based persistence only (no database integration yet)
- Single node support (no multi-node coordination)
- No calibration provisioning workflow (manual NVS setting required)
- No OTA firmware updates
- No power management optimization
- No diagnostic alerts

### Deferred to Later Milestones
- H_i/Q_i/R_i computation on ESP32 (Milestone 2)
- Phase 5 intelligence pipeline integration (Milestone 3)
- Regional fusion and Master communication (Phase 6)
- Database persistence on Pi (Phase 8)
- Calibration workflow tooling (Phase 10)

## Success Criteria (Software Complete)

### ✅ Completed
- [x] ESP32 firmware components created
- [x] Sensor API with unified interface
- [x] DHT22 driver with calibration support
- [x] Calibration NVS storage
- [x] Canonical telemetry envelope generation
- [x] ULID generation
- [x] ISO 8601 timestamp formatting
- [x] JSON serialization with cJSON
- [x] Missing != zero preserved (NAN → null)
- [x] Wi-Fi station mode
- [x] MQTT QoS 1 publisher
- [x] Raspberry Pi MQTT subscriber
- [x] JSON schema validation
- [x] File-based persistence
- [x] CMakeLists.txt for all components
- [x] Pi setup automation script

### ⏳ Pending Hardware Testing
- [ ] ESP32 firmware build succeeds
- [ ] ESP32 connects to Wi-Fi
- [ ] ESP32 connects to MQTT broker
- [ ] DHT22 sensor readings acquired
- [ ] Calibration applied correctly
- [ ] Telemetry JSON published to MQTT
- [ ] Pi subscriber receives messages
- [ ] Schema validation passes
- [ ] Telemetry persisted to files
- [ ] End-to-end latency < 5 seconds

## Next Steps

### Immediate (For Hardware Team)
1. Install ESP-IDF 5.1.x toolchain
2. Update Wi-Fi/MQTT configuration in firmware/main/main.c
3. Build ESP32 firmware: `idf.py build`
4. Setup Raspberry Pi: `scripts/setup_pi.sh`
5. Flash ESP32 and test end-to-end flow

### Milestone 2 (After M1 Hardware Verification)
1. Implement H_i/Q_i/R_i computation on ESP32
2. Add diagnostic metrics (comm_integrity, stability_index)
3. Integrate with Phase 5 reference implementations
4. Add calibration provisioning tools
5. Implement OTA firmware updates

### Milestone 3 (Pi Intelligence Integration)
1. Python implementation of Phase 5 pipeline
2. Baseline computation (B_i)
3. Anomaly detection (A_i, A_node, A_h)
4. Evidence aggregation (E_h)
5. Local persistence to TimescaleDB

## File Locations

```
firmware/
├── components/
│   ├── sensors/
│   │   ├── include/
│   │   │   ├── sensor_api.h
│   │   │   └── dht22.h
│   │   ├── dht22.c
│   │   └── CMakeLists.txt
│   ├── telemetry/
│   │   ├── include/
│   │   │   └── telemetry_envelope.h
│   │   ├── telemetry_envelope.c
│   │   └── CMakeLists.txt
│   └── network/
│       ├── include/
│       │   ├── wifi_station.h
│       │   └── mqtt_client.h
│       ├── wifi_station.c
│       ├── mqtt_client.c
│       └── CMakeLists.txt
└── main/
    ├── calibration_store.h
    ├── calibration_store.c
    ├── main.c
    └── CMakeLists.txt

scripts/
├── pi_mqtt_subscriber.py
├── requirements.txt
└── setup_pi.sh

schemas/
└── telemetry-envelope.schema.json (LOCKED, not modified)
```

## Architectural Invariants Preserved

1. **No Phase 5 Modifications**: ✅ All Phase 5 modules untouched
2. **Canonical Schema**: ✅ schemas/telemetry-envelope.schema.json used as-is
3. **Missing != Zero**: ✅ NAN values preserved throughout pipeline
4. **Calibration Not Hardcoded**: ✅ Decision C2 followed (NVS storage)
5. **No Duplicate Telemetry**: ✅ Single authoritative schema
6. **No New Math**: ✅ Phase 5 reference implementations remain golden

---

**Implementation Status:** SOFTWARE COMPLETE  
**Hardware Status:** AWAITING PHYSICAL TESTING  
**Blocking Items:** ESP-IDF toolchain, ESP32-S3 hardware, Raspberry Pi, DHT22 sensor  
**Ready For:** Hardware team calibration workflow development  

**Track A Milestone 1:** 🟡 Software delivery complete, hardware verification pending
