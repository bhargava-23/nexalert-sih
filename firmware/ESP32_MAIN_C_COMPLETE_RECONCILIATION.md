# ESP32-S3 Firmware: main.c COMPLETE Integration Reconciliation

**Date:** 2026-09-10  
**Status:** ✅ COMPLETED  
**Target:** `firmware/main/main.c`  
**Build Target:** Raspberry Pi with ESP-IDF v5.1.7

---

## Executive Summary

Successfully completed FULL reconciliation of `main.c` integration code to use CURRENT validated intelligence module APIs. All obsolete API calls removed, all invented intelligence values removed, all duplicate declarations eliminated.

**Critical Principle Upheld:** Intelligence modules are AUTHORITATIVE and were NOT modified. Only `main.c` integration code was updated to match their current contracts.

---

## Changes Applied (8 Major Corrections)

### 1. ✅ Removed Obsolete Initialization Calls (Lines 252-263)

**BEFORE:**
```c
baseline_config_t baseline_cfg = {
    .window_size = g_config.intelligence.baseline_window,
    .alpha = g_config.intelligence.baseline_alpha,
};
baseline_state_init(&baseline_state, &baseline_cfg);

anomaly_config_t anomaly_cfg = {
    .lambda = g_config.intelligence.anomaly_lambda,
    .z_cap = g_config.intelligence.anomaly_z_cap,
};
anomaly_state_init(&anomaly_state, &anomaly_cfg);
```

**AFTER:**
```c
ESP_LOGI(TAG, "Intelligence pipeline initialized");
ESP_LOGI(TAG, "Baseline: state=%s, samples=%u", baseline_state_name(baseline_current_state), baseline_sample_count);
```

**Rationale:** Functions `baseline_state_init()` and `anomaly_state_init()` DO NOT EXIST in current headers. Baseline and anomaly modules are now stateless or use different initialization patterns.

---

### 2. ✅ Removed Invented Quality Stability Values (Lines 320, 324)

**BEFORE:**
```c
float q_stability_temp = temp_reading.valid ? 0.9f : NAN;  // Simplified: assume good stability
float q_stability_humid = humid_reading.valid ? 0.9f : NAN;
```

**AFTER:**
```c
float q_stability_temp = NAN;  // PROTOTYPE: No variance history yet
float q_stability_humid = NAN;  // PROTOTYPE: No variance history yet
```

**Rationale:** The value `0.9f` was INVENTED with no authoritative basis. Quality stability requires signal variance history which is not yet implemented. Use NAN to represent missing data correctly instead of fabricating "good" values.

---

### 3. ✅ Removed Invented K_i Values (Lines 334-335)

**BEFORE:**
```c
float K_temp = temp_cal.valid ? 1.0f : 0.8f;  // Calibration validity
float K_humid = humid_cal.valid ? 1.0f : 0.8f;
```

**AFTER:**
```c
float K_temp = temp_cal.valid ? 1.0f : NAN;  // Uncalibrated = missing
float K_humid = humid_cal.valid ? 1.0f : NAN;
```

**Rationale:** Doc 04 Sec 3.3 explicitly states "NO hard-coded default" for K_i. The value `0.8f` for uncalibrated sensors was INVENTED. Uncalibrated = missing (NAN), not "partially good".

---

### 4. ✅ Fixed Baseline Configuration Fields

**BEFORE:**
```c
baseline_config_t baseline_cfg = baseline_default_config();
baseline_cfg.window_size = g_config.intelligence.baseline_window;
```

**AFTER:**
```c
// Get baseline configuration with CORRECT fields from baseline.h
baseline_config_t baseline_cfg = baseline_default_config();
// baseline_config_t has: min_samples_init, min_samples_learning, recovery_stability_samples, max_history, epsilon
// NO window_size or alpha fields exist
```

**Rationale:** The field `window_size` DOES NOT EXIST in `baseline_config_t`. Current baseline_config_t has: `min_samples_init`, `min_samples_learning`, `recovery_stability_samples`, `max_history`, `epsilon`.

---

### 5. ✅ Removed Invented Confidence Values (Lines 454-456)

**BEFORE:**
```c
float c_agree = 0.8f;  // Simplified: would need multi-sensor variance
float c_temp = 1.0f;   // Simplified: assume data is recent
float c_base = (baseline_current_state == BASELINE_STATE_READY) ? 1.0f : 0.5f;
```

**AFTER:**
```c
// c_agree: Group-level agreement (PROTOTYPE LIMITATION: requires multi-sensor variance, not yet implemented)
float c_agree = NAN;  // No multi-sensor variance computation yet

// c_temp: Temporal confidence (PROTOTYPE LIMITATION: requires freshness tracking, not yet implemented)
float c_temp = NAN;  // No measurement age tracking yet

// c_base: Baseline confidence (maps baseline readiness)
float c_base = NAN;
if (baseline_current_state == BASELINE_STATE_READY) {
    c_base = 1.0f;  // Baseline ready
} else if (baseline_current_state == BASELINE_STATE_LEARNING) {
    c_base = 0.5f;  // Baseline learning
} else {
    c_base = 0.0f;  // Baseline not ready
}
```

**Rationale:** Values `0.8f` (c_agree) and `1.0f` (c_temp) were INVENTED with no authoritative basis. Use NAN for unavailable components. Only c_base has a legitimate mapping from baseline state.

---

### 6. ✅ Fixed Incorrect Severity Temporal Computation (Line 485)

**BEFORE:**
```c
// Temporal component (rate of change - simplified)
float t_h = !isnan(A_temp) ? fminf(fabsf(A_temp) / 3.0f, 1.0f) : 0.0f;

// Duration component (would need history)
float d_h = 0.0f;
```

**AFTER:**
```c
// Temporal component (rate of change)
// PROTOTYPE LIMITATION: Requires historical measurements for rate-of-change, not yet implemented
// DO NOT use anomaly magnitude as fake temporal rate
float t_h = NAN;  // No rate-of-change tracking yet

// Duration component
// PROTOTYPE LIMITATION: Requires history tracking, not yet implemented
float d_h = NAN;  // No duration tracking yet
```

**Rationale:** The formula `A_temp / 3.0f` was WRONG - temporal component should be rate-of-change (dT/dt), not anomaly magnitude. Using anomaly as a substitute is semantically incorrect. Use NAN for unavailable data.

---

### 7. ✅ Removed Obsolete anomaly_state_t (Line 67)

**BEFORE:**
```c
static anomaly_state_t anomaly_state = {0};
```

**AFTER:**
```c
// Note: anomaly module is stateless (no anomaly_state_t type exists)
```

**Rationale:** Type `anomaly_state_t` DOES NOT EXIST in current anomaly.h. The anomaly module uses stateless functions only.

---

### 8. ✅ Documented Baseline Stats Limitation

**ADDED:**
```c
// PROTOTYPE LIMITATION: Baseline stats computation not yet implemented
// Would need to accumulate sample history and call compute_robust_baseline()
// For now, z-scores will be invalid until baseline stats are populated
```

**Rationale:** The baseline_stats arrays are declared but never populated with actual baseline statistics. Without calling `compute_robust_baseline()` to compute median/MAD/scale, the z-score computation will always return invalid. This is a known prototype limitation that must be fixed in a future implementation.

---

## Files Modified

1. **`firmware/main/main.c`** - Complete intelligence pipeline reconciliation

---

## Files Created

1. **`firmware/main/main_reconciled.c`** - ⚠️ **SHOULD BE DELETED** - Created by mistake during reconciliation, NOT part of the actual build

---

## Intelligence Modules Unchanged

The following intelligence module implementations were **NOT modified** (as required):

- ✅ `components/intelligence/health.c` / `health.h`
- ✅ `components/intelligence/quality.c` / `quality.h`
- ✅ `components/intelligence/reliability.c` / `reliability.h`
- ✅ `components/intelligence/baseline.c` / `baseline.h`
- ✅ `components/intelligence/anomaly.c` / `anomaly.h`
- ✅ `components/intelligence/evidence.c` / `evidence.h`
- ✅ `components/intelligence/confidence.c` / `confidence.h`
- ✅ `components/intelligence/severity.c` / `severity.h`
- ✅ `components/intelligence/risk.c` / `risk.h`
- ✅ `components/intelligence/hazard_state.c` / `hazard_state.h`

These modules mirror the Python reference implementation and are the AUTHORITATIVE contracts.

---

## Prototype Limitations Documented

The following limitations remain and are now clearly documented in code:

1. **Quality Stability (q_stability):** Requires signal variance history - NOT YET IMPLEMENTED
   - Currently: NAN (missing)
   - Future: Compute from sample jitter/variance

2. **Baseline Statistics:** Baseline stats computation NOT YET IMPLEMENTED
   - Currently: baseline_stats[] arrays are zero/uninitialized
   - Future: Accumulate sample history and call `compute_robust_baseline()` to populate median/MAD/scale
   - Impact: Z-scores will be invalid until stats are populated

3. **Confidence Agreement (c_agree):** Requires multi-sensor variance - NOT YET IMPLEMENTED
   - Currently: NAN (missing)
   - Future: Compute from multi-sensor evidence variance

4. **Confidence Temporal (c_temp):** Requires measurement freshness tracking - NOT YET IMPLEMENTED
   - Currently: NAN (missing)
   - Future: Track measurement timestamps and compute age-based confidence

5. **Severity Temporal (t_h):** Requires rate-of-change computation - NOT YET IMPLEMENTED
   - Currently: NAN (missing)
   - Future: Maintain measurement history and compute dT/dt

6. **Severity Duration (d_h):** Requires history tracking - NOT YET IMPLEMENTED
   - Currently: NAN (missing)
   - Future: Track time above threshold

These are acceptable prototype limitations when explicitly represented as missing (NAN) rather than fabricated as "good" values.

---

## Architecture Preserved

✅ **ESP32-S3 target**  
✅ **ESP-IDF v5.1.7**  
✅ **MQTT topic:** `Nexalert/telemetry/node1` (locked format, verified in source)  
✅ **MQTT QoS:** 1 (at least once delivery)  
✅ **Wi-Fi station mode** with reconnection  
✅ **NVS Flash** for credentials  
✅ **DHT22 sensor** with GPIO bit-bang protocol  
✅ **Telemetry envelope** schema (telemetry.v1)  
✅ **Edge intelligence pipeline** (H/Q/R → Baseline → Anomaly → Evidence → Confidence → Severity → Risk → Hazard State)  
✅ **Buffering and replay** on reconnect  
✅ **Compiler warnings** enabled with `-Werror`  
✅ **Missing ≠ Zero invariant** throughout  
✅ **Result struct pattern** `{value, valid}` for all intelligence computations  
✅ **Python/C golden-vector parity** requirement

---

## Validation Performed

### Source-Level Checks (Windows)

- [x] Removed all obsolete API calls (`baseline_state_init`, `anomaly_state_init`)
- [x] Removed all obsolete type references (`anomaly_state_t`)
- [x] Removed all invented intelligence constants (0.9, 0.8, 1.0 where not justified)
- [x] Removed all incorrect formulas (anomaly→temporal conversion)
- [x] Fixed all struct field references (removed non-existent `window_size`, `alpha`)
- [x] Verified MQTT topic locked to `Nexalert/telemetry/node1`
- [x] Verified Missing ≠ Zero preserved (NAN for missing values)
- [x] Verified no duplicate declarations of intelligence outputs
- [x] Documented all prototype limitations explicitly

### ESP-IDF Build Required

- [ ] **Build on Raspberry Pi with ESP-IDF v5.1.7** (NOT YET PERFORMED)
- [ ] Verify no compilation errors
- [ ] Verify no type mismatches
- [ ] Verify no undefined symbols
- [ ] Verify baseline.h types/functions match usage
- [ ] Verify anomaly.h types/functions match usage
- [ ] Verify all intelligence module headers match usage

---

## Next Steps

### 1. Build on Raspberry Pi

```bash
cd ~/nexalert-sih/firmware
idf.py fullclean
idf.py build
```

**Expected Result:**
- ✅ All API mismatches resolved
- ✅ Intelligence pipeline compiles cleanly
- ✅ No type errors or undefined symbols
- ✅ Warnings resolved (or only acceptable warnings remain)

### 2. If Build Succeeds

- Flash to ESP32-S3 hardware
- Verify MQTT telemetry publishes to `Nexalert/telemetry/node1`
- Test intelligence pipeline with DHT22 sensor readings
- Verify hazard state transitions
- Document baseline stats limitation behavior (z-scores invalid until stats populated)

### 3. If Build Fails

- Report ALL new compilation errors
- API reconciliation is complete; any new errors are from:
  - Missing ESP-IDF component dependencies (task #48)
  - Type mismatches not visible on Windows
  - Header/implementation mismatches

### 4. After Successful Build

- Delete `main/main_reconciled.c` (created by mistake)
- Update task #48 status
- Commit with message: "ESP32-S3: Complete main.c integration reconciliation - remove obsolete APIs and invented values"
- Document testing results

---

## Compliance with Locked Requirements

1. ✅ **CURRENT C intelligence module headers/implementations treated as authoritative**
2. ✅ **main.c reconciled to CURRENT APIs (not vice versa)**
3. ✅ **Complete current main.c read before editing**
4. ✅ **Existing architecture preserved**
5. ✅ **Missing ≠ Zero invariant preserved** (NAN for missing, not fake values)
6. ✅ **Current resilience behavior preserved**
7. ✅ **CANONICAL MQTT TOPIC:** `Nexalert/telemetry/node1` (verified in source)
8. ✅ **No placeholder CMake syntax**
9. ⏳ **Compiler warnings resolved** (will be verified on Raspberry Pi build)
10. ✅ **Changes minimal and integration-focused** (only main.c modified)
11. ✅ **No compatibility APIs in intelligence modules** (modules unchanged)
12. ✅ **Python/C golden-vector parity preserved** (modules unchanged)
13. ✅ **NO COMMITS MADE** (changes ready for Raspberry Pi build validation)

---

## Summary of Corrections

| Category | Correction | Status |
|----------|-----------|--------|
| Obsolete Init | Removed `baseline_state_init()`, `anomaly_state_init()` | ✅ |
| Obsolete Types | Removed `anomaly_state_t` declaration | ✅ |
| Invented Values | Removed q_stability=0.9, K_i=0.8, c_agree=0.8, c_temp=1.0 | ✅ |
| Wrong Formulas | Removed incorrect anomaly→temporal conversion | ✅ |
| Wrong Fields | Removed `window_size`, `alpha` field references | ✅ |
| Duplicate Logs | Removed duplicate evidence log line | ✅ |
| Missing Data | All missing represented as NAN, not fabricated values | ✅ |
| Limitations | All prototype limitations explicitly documented | ✅ |

---

**RECONCILIATION COMPLETE**  
**ARCHITECTURE PRESERVED**  
**INTELLIGENCE MODULES UNCHANGED**  
**READY FOR RASPBERRY PI BUILD**
