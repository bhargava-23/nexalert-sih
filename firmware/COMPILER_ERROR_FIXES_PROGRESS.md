# ESP32-S3 Firmware: Raspberry Pi Compiler Error Fixes

**Date:** 2026-09-10  
**Build:** Raspberry Pi ESP-IDF v5.1.7  
**Status:** IN PROGRESS

---

## Type Ownership Conflicts (CRITICAL)

### 1. mqtt_config_t - FIXED ✅
**Problem:** TWO conflicting definitions
- nexalert_mqtt.h: 3-field network module version (pointers)
- node_config.h: 8-field config module version (arrays)

**Solution:**
- Renamed nexalert_mqtt.h version to `mqtt_init_params_t`
- node_config.h keeps `mqtt_config_t` (authoritative)
- Updated mqtt_client.c to use `mqtt_init_params_t`

### 2. buffer_config_t - TO CHECK
**Location:** node_config.h:57-60
**Check:** Search for duplicate definitions

### 3. heartbeat_config_t - TO CHECK
**Location:** node_config.h:65-68
**Check:** Search for duplicate definitions

### 4. sensor_reading_t - TO CHECK
**Location:** sensor_api.h:37-41
**Fields:** value, valid, timestamp_ms
**Check:** Verify main.c usage matches these fields

### 5. compute_temporal() - TO CHECK
**Location:** severity.h:159-165
**Signature:** `float compute_temporal(float current, float previous, float time_delta_seconds, float max_rate_per_second, float max_age_seconds)`
**Check:** Search for duplicate declarations

---

## Baseline API Mismatches

### Current baseline.h API:
- `baseline_state_t` is ENUM (values: BASELINE_INITIALIZING, BASELINE_LEARNING, BASELINE_READY, BASELINE_FROZEN, BASELINE_RECOVERING)
- NOT struct, NOT `BASELINE_STATE_*` prefix
- Functions: `update_baseline_state()`, `baseline_default_config()`, `compute_baseline_z_score()`

### main.c fixes needed:
- Change `BASELINE_STATE_*` → `BASELINE_*` (wrong prefix)
- Use enum values correctly
- Verify z-score computation API usage

---

## Severity API Mismatches

### Current severity.h API:
- `severity_weights_t` fields: `w_I`, `w_T`, `w_D` (NOT intensity/temporal/duration)

### main.c fixes needed:
- Change field names from `.intensity`/`.temporal`/`.duration` → `.w_I`/`.w_T`/`.w_D`

---

## Hazard State API

### Current hazard_state.h:
- `should_freeze_baseline()` function EXISTS in header

### main.c fixes needed:
- Remove duplicate static implementation
- Use function from hazard_state.h

---

## MQTT Fixes

### Header name: ✅ FIXED
- Renamed: Nexalert_mqtt.h → nexalert_mqtt.h

### MQTT topic: ✅ CORRECT
- Canonical: `Nexalert/telemetry/node1` (case-sensitive)
- Verified in mqtt_client.c:74

### MQTT event logging warning:
**File:** mqtt_client.c:58
**Issue:** `ESP_LOGD(TAG, "MQTT event: %d", event_id)` where event_id is int32_t
**Fix:** Use proper PRI macro: `ESP_LOGD(TAG, "MQTT event: %" PRId32, event_id)`
**Include:** Add `#include <inttypes.h>` at top of mqtt_client.c

---

## Next Steps

1. Search for remaining duplicate type definitions
2. Fix main.c baseline API usage
3. Fix main.c severity API usage
4. Remove duplicate should_freeze_baseline() from main.c
5. Fix MQTT event logging format
6. Global search for stale header references
7. Validation searches
8. Provide final report

---

**NO COMMITS YET**  
**VALIDATION ON RASPBERRY PI REQUIRED**
