# Track 3A: CRITICAL TELEMETRY CONTRACT MISMATCH

**Date**: 2026-09-16  
**Status**: BLOCKING ISSUE DETECTED

---

## CRITICAL FINDING

The current firmware telemetry envelope **DOES NOT MATCH** the locked hardware JSON contract specified in Track 3A requirements.

---

## Contract Mismatch Analysis

### LOCKED HARDWARE JSON CONTRACT (Required):

```json
{
  "node_id": "NODE-001",
  "timestamp_ms": 1750000000000,
  "sequence": 1842,
  "sensors": {
    "temperature_c": 31.4,
    "humidity_rh": 58.2,
    "pm25_ugm3": 14.7,
    "pm10_ugm3": 22.1,
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
    "pm25": true,
    "pm10": true,
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

### CURRENT FIRMWARE TELEMETRY ENVELOPE (Actual):

**File**: `components/telemetry/telemetry_envelope.c`

**Generated Structure**:
```json
{
  "schema_version": "telemetry.v1",
  "telemetry_id": "<ULID>",
  "node_id": "NODE-001",
  "sequence": 1842,
  "measurement_timestamp": "2026-09-16T09:38:05Z",
  "received_timestamp": "2026-09-16T09:38:05Z",
  "location": {
    "lat": 12.9716,
    "lon": 77.5946,
    "alt": 920.0
  },
  "measurements": {
    "temp_c": 31.4,
    "humidity_pct": 58.2,
    "pressure_hpa": 1009.8,
    "pm25_ug_m3": 14.7,
    "pm10_ug_m3": 22.1
  },
  "diagnostics": {
    "uptime_s": 3600,
    "self_test_passed": true,
    "comm_integrity": 0.95,
    "calibration_valid": true,
    "stability_index": 0.88
  },
  "power": {
    "battery_pct": 86.0,
    "battery_voltage": 12.6,
    "solar_current": 0.5
  },
  "source": "HARDWARE"
}
```

---

## Critical Mismatches

### STRUCTURE MISMATCHES:

| Issue | Current | Required | Impact |
|-------|---------|----------|--------|
| **Root structure** | Complex envelope with metadata | Simple hardware JSON | ❌ INCOMPATIBLE |
| **Sensor container** | "measurements" | "sensors" | ❌ WRONG NAME |
| **Timestamp format** | ISO8601 string | Unix timestamp_ms | ❌ INCOMPATIBLE |
| **availability object** | NOT PRESENT | REQUIRED | ❌ MISSING |
| **location object** | Present | NOT in contract | ❌ EXTRA |
| **diagnostics object** | Present | NOT in contract | ❌ EXTRA |
| **schema_version** | Present | NOT in contract | ❌ EXTRA |
| **telemetry_id** | Present | NOT in contract | ❌ EXTRA |
| **source** | Present | NOT in contract | ❌ EXTRA |

### MISSING SENSOR FIELDS:

| Field | Required | Current | Status |
|-------|----------|---------|--------|
| gas_ppm | YES (MQ-2) | NOT PRESENT | ❌ MISSING |
| vibration_mps2 | YES (MPU6050) | NOT PRESENT | ❌ MISSING |
| water_level_m | YES (null) | NOT PRESENT | ❌ MISSING |
| rainfall_mm_h | YES (null) | NOT PRESENT | ❌ MISSING |
| soil_moisture_vwc_pct | YES (null) | NOT PRESENT | ❌ MISSING |

### FIELD NAME MISMATCHES:

| Contract Field | Current Field | Status |
|----------------|---------------|--------|
| temperature_c | temp_c | ⚠️ MISMATCH |
| humidity_rh | humidity_pct | ⚠️ MISMATCH |
| pm25_ugm3 | pm25_ug_m3 | ⚠️ MISMATCH |
| pm10_ugm3 | pm10_ug_m3 | ⚠️ MISMATCH |

### POWER STRUCTURE MISMATCH:

**Contract requires:**
```json
"power": {
  "battery_pct": 86.0,
  "solar_state": "ACTIVE"
}
```

**Current provides:**
```json
"power": {
  "battery_pct": 86.0,
  "battery_voltage": 12.6,
  "solar_current": 0.5
}
```

❌ **Missing**: `solar_state` field
❌ **Extra**: `battery_voltage`, `solar_current` fields

---

## Root Cause Analysis

### 1. Architectural Mismatch

The current telemetry envelope (`telemetry_envelope.c`) was designed for a **backend intelligence pipeline** that expects:
- Rich metadata (schema_version, telemetry_id, timestamps, location)
- Intelligence diagnostics
- Complex nested structure

The Track 3A locked contract requires **simple hardware JSON** that:
- Publishes ONLY hardware sensor readings
- Uses flat sensor + availability structure
- Has NO intelligence metadata
- Has NO diagnostics
- Has NO location in payload (location is in config, not telemetry)

### 2. Recovered Arduino Contract

The locked hardware JSON contract matches the **recovered Arduino deployment** behavior:
- Simple flat structure
- sensors + availability + power
- timestamp_ms (Unix milliseconds)
- sequence (monotonic)
- node_id

The current ESP-IDF firmware does **NOT** match the recovered Arduino deployment.

---

## Decision Required

**CRITICAL QUESTION**: Which contract is authoritative for Track 3A?

### Option A: Backend Intelligence Pipeline Contract (Current)
- Complex envelope with diagnostics
- ISO8601 timestamps
- Rich metadata
- location/diagnostics/source fields
- measurements (not sensors)
- NO availability object

### Option B: Recovered Arduino Hardware Contract (Track 3A Requirement)
- Simple hardware JSON
- Unix timestamp_ms
- Minimal metadata
- sensors + availability + power
- NO location/diagnostics/source fields

**Track 3A instructions explicitly state**: Use the recovered Arduino hardware contract (Option B).

**But the existing ESP-IDF firmware uses**: Backend intelligence pipeline contract (Option A).

---

## Impact Assessment

### If We Change to Match Track 3A Contract:

**BREAKS**:
- ❌ Existing backend ingestion (expects current envelope)
- ❌ Existing MQTT consumers (expect current structure)
- ❌ Existing telemetry_envelope.c API
- ❌ Existing tests for telemetry envelope
- ❌ Any downstream systems expecting diagnostics

**FIXES**:
- ✅ Matches recovered Arduino deployment
- ✅ Matches Track 3A locked contract
- ✅ Simpler hardware JSON
- ✅ Clear separation: hardware sensors vs intelligence

### If We Keep Current Contract:

**PRESERVES**:
- ✅ Existing backend integration
- ✅ Existing ESP-IDF firmware behavior
- ✅ Existing tests

**BREAKS**:
- ❌ Track 3A requirements
- ❌ Recovered Arduino contract compatibility
- ❌ Hardware/intelligence separation
- ❌ Track 3A acceptance criteria

---

## Recommendation

**STOP Track 3A firmware integration until contract authority is clarified.**

### Questions for User:

1. **Which contract is authoritative?**
   - Recovered Arduino hardware JSON (Track 3A requirement)?
   - Existing ESP-IDF backend pipeline JSON (current firmware)?

2. **If Arduino contract is authoritative (as Track 3A instructions state):**
   - Rewrite `telemetry_envelope.c` to match Arduino contract?
   - Create NEW `hardware_json.c` separate from `telemetry_envelope.c`?
   - Update backend to accept both formats?

3. **What about existing backend integration?**
   - Backend must be updated to accept new format?
   - Maintain backward compatibility with both formats?
   - Migration path for existing deployments?

---

## Blocked Tasks

**Cannot proceed with**:
- TASK 2: Sensor mapping reconciliation
- TASK 3: Serialization safety verification
- TASK 4: SNTP/NTP implementation
- TASK 5: Configuration consistency
- TASK 6: Documentation updates

**Reason**: Unknown which JSON contract to implement.

---

## Files Requiring Changes (If Arduino Contract Selected)

1. **components/telemetry/include/telemetry_envelope.h**
   - Redefine measurements_t to match sensors structure
   - Add availability_t struct
   - Remove diagnostics_t (not in hardware JSON)
   - Change power_t to match contract (solar_state, not voltage/current)

2. **components/telemetry/telemetry_envelope.c**
   - Rewrite JSON generation to match Arduino contract
   - Change "measurements" → "sensors"
   - Add "availability" object generation
   - Change timestamp to Unix milliseconds
   - Remove schema_version, telemetry_id, location, diagnostics, source

3. **main/main.c**
   - Update telemetry generation calls
   - Add all missing sensor fields (gas_ppm, vibration_mps2, water_level_m, etc.)
   - Generate availability flags
   - Change power state reporting

---

## Next Steps

**WAITING FOR USER DECISION**:

Which contract should Track 3A implement?

- **Option A**: Keep current backend intelligence pipeline JSON
- **Option B**: Implement recovered Arduino hardware JSON (as Track 3A instructions state)

**Track 3A integration is BLOCKED until this is resolved.**

---

**END OF CONTRACT MISMATCH REPORT**
