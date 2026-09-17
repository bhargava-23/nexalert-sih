# Track 4: Implementation Truth Verification

**Date**: 2026-09-16  
**Status**: VERIFICATION IN PROGRESS

---

## Critical Finding: C_temp Timestamp Architecture

### SNTP/NTP Infrastructure Exists

**From main.c lines 40, 980-991**:
```c
#include "sntp_client.h"        // Track 3A: SNTP/NTP for time synchronization

// In app_main():
sntp_config_t sntp_cfg = {
    .ntp_server = "10.42.0.1",  // Track 3A: Locked NTP server (Raspberry Pi)
};
ESP_ERROR_CHECK(sntp_client_init(&sntp_cfg));

// Wait for sync
esp_err_t sntp_ret = sntp_wait_for_sync(10000);
if (sntp_ret == ESP_OK) {
    ESP_LOGI(TAG, "SNTP synchronized");
} else {
    ESP_LOGW(TAG, "SNTP sync timeout, using uptime-based timestamps");
}
```

### Current Timestamp Sources

**Available in code**:
1. `esp_timer_get_time()` — Monotonic microseconds since boot (used extensively)
2. SNTP sync — Wall-clock time synchronization attempted
3. No `time()`, `gettimeofday()`, or `clock_gettime()` calls found in current code

### Problem Identified

**Current c_temp implementation (line 694)**:
```c
float telemetry_age_seconds = 0.0f;  // Measurements just acquired in this loop
```

**Issue**: Assumes age is zero, but measurements could be from:
- Previous loop iteration (if loop rate varies)
- Sensor acquisition time vs intelligence processing time
- Actual wall-clock timestamps if SNTP synced

**Repository requirement** (confidence.py:183-229):
- Actual age: `t_now - t_measurement`
- When age unknown/unavailable: return 0.0 (missing temporal information)

### Architecture Assessment

**Current architecture uses**:
- Monotonic time (`esp_timer_get_time()`) for history timestamps
- No per-sensor measurement timestamp storage
- All sensors read sequentially in same loop
- Intelligence computed immediately after sensor reads

**Measurement age reality**:
- Sensor read → immediate intelligence computation
- Age ≈ 0-50ms (processing time within loop)
- All sensors from same loop iteration

**Decision Options**:

**A) Use actual loop time as measurement time**:
```c
uint32_t measurement_time_ms = loop_time_ms;  // From line 895
uint32_t current_time_ms = (uint32_t)(esp_timer_get_time() / 1000);
float telemetry_age_seconds = (float)(current_time_ms - measurement_time_ms) / 1000.0f;
```
Result: age ≈ 0-0.05s (processing delay)

**B) Document zero-age assumption**:
If measurements truly acquired in current loop with negligible delay, document that age=0 is architectural truth, not assumption

**Recommended**: **Option A** — Compute actual processing age

---

## MQ-2 Integration Analysis

### Current MQ-2 Status

**Data acquired** (main.c lines 430-440, 485-492):
```c
// MQ-2 initialized
mq2_config_t mq2_cfg = {
    .gpio_pin = 4,
    .adc_channel = ADC1_CHANNEL_3,
};
ret = mq2_init(&mq2_cfg);

// MQ-2 read in sampling loop
sensor_reading_t mq2_reading;
ret = mq2_read_raw(&mq2_reading);
if (ret == ESP_OK && mq2_reading.valid) {
    ESP_LOGI(TAG, "MQ-2: %u ADC (raw)", (uint32_t)mq2_reading.value);
}
```

**Integration check**:
- ❌ NOT in history buffers (only temp, humidity have history)
- ❌ NOT in baseline accumulation
- ❌ NOT in z-score computation
- ❌ NOT in anomaly aggregation
- ❌ NOT in evidence rules

**Verdict**: MQ-2 data acquired but **NOT integrated** into intelligence

### Integration Feasibility

**Baseline API** (baseline.h):
```c
baseline_stats_t compute_robust_baseline(
    const float* samples,
    uint16_t sample_count,
    float epsilon
);
```
✅ Generic API — accepts any float samples (no ppm requirement)

**Anomaly API** (anomaly.h):
```c
anomaly_result_t compute_individual_anomaly(
    float z_score,
    float r_i,
    float lambda_param,
    float z_cap
);
```
✅ Generic API — accepts any z-score (no ppm requirement)

**Required for integration**:
1. Add gas history to `g_intelligence_history` struct
2. Add gas samples to `g_baseline_history` struct
3. Add gas to baseline stats array: `baseline_stats[2]` (index 2)
4. Accumulate MQ-2 in `update_baseline_stats()`
5. Compute gas z-score
6. Add gas to anomaly aggregation

**Complexity**: ~50 lines of code additions

**Decision**: Integration IS feasible with current architecture

---

## Quality Stability — Final Verification

**Repository specification**:
- Describes: "High jitter decreases q_stability"
- Provides: NO formula for jitter → stability conversion
- Reference: NO implementation of stability calculation

**Current implementation**:
```c
float q_stability_temp = NAN;  // Stability not measured → missing per repository specification
```

**Verdict**: ✅ CORRECT — Repository provides no computation method

---

## Agreement — Evidence Group Verification

**Repository semantics** (confidence.py:90-180):
```python
def compute_agreement(
    group_evidence: Dict[str, float],
    group_weights: Dict[str, float],
    ...
) -> float:
    if len(valid_groups) == 1:
        return 1.0  # Single source = no disagreement
```

**Current fire evidence**:
- Thermal group: temperature + humidity (correlated)
- Smoke group: unavailable

**Active groups**: 1 (thermal only)

**Current implementation**:
```c
float c_agree = 1.0f;
```

**Verdict**: ✅ VALUE CORRECT, comments need final verification

---

**ANALYSIS CONTINUES...**
