# Track 4: Edge Intelligence Integration Implementation Plan

**Date**: 2026-09-16  
**Status**: TASK 4 IN PROGRESS  
**Dependencies**: TASK 1 ✅, TASK 2 ✅, TASK 3 ✅

---

## Implementation Approach

### Changes to `main/main.c`

#### 1. Add History Buffers (Static Storage)

```c
// History buffers for temporal/duration tracking
#define HISTORY_SIZE 10  // Last 10 samples for rate-of-change

static struct {
    float temp_history[HISTORY_SIZE];
    uint32_t temp_timestamps_ms[HISTORY_SIZE];
    uint8_t temp_index;
    uint8_t temp_count;
    
    float humid_history[HISTORY_SIZE];
    uint32_t humid_timestamps_ms[HISTORY_SIZE];
    uint8_t humid_index;
    uint8_t humid_count;
    
    // Duration tracking
    float time_above_fire_threshold_s;
    uint32_t duration_start_ms;
    bool duration_active;
} g_intelligence_history = {0};

// Sample accumulation for baseline computation
#define BASELINE_HISTORY_SIZE 50  // Accumulate samples before computing baseline
static struct {
    float temp_samples[BASELINE_HISTORY_SIZE];
    uint16_t temp_count;
    
    float humid_samples[BASELINE_HISTORY_SIZE];
    uint16_t humid_count;
} g_baseline_history = {0};
```

#### 2. Baseline Stats Population Function

```c
/**
 * Accumulate samples and compute baseline stats when ready
 */
static void update_baseline_stats(float temp_c, float humidity_pct)
{
    baseline_config_t cfg = baseline_default_config();
    
    // Accumulate temperature samples
    if (!isnan(temp_c) && g_baseline_history.temp_count < BASELINE_HISTORY_SIZE) {
        g_baseline_history.temp_samples[g_baseline_history.temp_count++] = temp_c;
    }
    
    // Accumulate humidity samples
    if (!isnan(humidity_pct) && g_baseline_history.humid_count < BASELINE_HISTORY_SIZE) {
        g_baseline_history.humid_samples[g_baseline_history.humid_count++] = humidity_pct;
    }
    
    // Compute baseline stats when we have enough samples and baseline is LEARNING or READY
    if (baseline_current_state >= BASELINE_LEARNING) {
        // Temperature baseline
        if (g_baseline_history.temp_count >= cfg.min_samples_learning && baseline_stats[0].valid == false) {
            baseline_stats[0] = compute_robust_baseline(
                g_baseline_history.temp_samples,
                g_baseline_history.temp_count,
                cfg.epsilon
            );
            if (baseline_stats[0].valid) {
                ESP_LOGI(TAG, "Temperature baseline computed: median=%.2f, scale=%.2f",
                         baseline_stats[0].median, baseline_stats[0].scale);
            }
        }
        
        // Humidity baseline
        if (g_baseline_history.humid_count >= cfg.min_samples_learning && baseline_stats[1].valid == false) {
            baseline_stats[1] = compute_robust_baseline(
                g_baseline_history.humid_samples,
                g_baseline_history.humid_count,
                cfg.epsilon
            );
            if (baseline_stats[1].valid) {
                ESP_LOGI(TAG, "Humidity baseline computed: median=%.2f, scale=%.2f",
                         baseline_stats[1].median, baseline_stats[1].scale);
            }
        }
    }
}
```

#### 3. Temporal Rate-of-Change Function

```c
/**
 * Compute rate of change from history
 * Returns: rate in units/second, or NAN if insufficient history
 */
static float compute_rate_of_change(
    const float* history,
    const uint32_t* timestamps_ms,
    uint8_t count,
    uint8_t index
)
{
    if (count < 2) {
        return NAN;  // Need at least 2 samples
    }
    
    // Get most recent sample
    uint8_t latest_idx = (index > 0) ? (index - 1) : (count - 1);
    float latest_value = history[latest_idx];
    uint32_t latest_time_ms = timestamps_ms[latest_idx];
    
    // Get oldest sample
    uint8_t oldest_idx = (count < HISTORY_SIZE) ? 0 : index;
    float oldest_value = history[oldest_idx];
    uint32_t oldest_time_ms = timestamps_ms[oldest_idx];
    
    // Compute rate
    float delta_value = latest_value - oldest_value;
    float delta_time_s = (latest_time_ms - oldest_time_ms) / 1000.0f;
    
    if (delta_time_s < 0.1f) {
        return NAN;  // Too short interval
    }
    
    return delta_value / delta_time_s;  // units/second
}
```

#### 4. Duration Tracking Function

```c
/**
 * Update duration tracking for threshold exceedance
 */
static void update_duration_tracking(
    float current_value,
    float threshold,
    uint32_t current_time_ms
)
{
    if (isnan(current_value)) {
        // Missing value: reset duration
        g_intelligence_history.duration_active = false;
        g_intelligence_history.time_above_fire_threshold_s = 0.0f;
        return;
    }
    
    if (current_value >= threshold) {
        // Above threshold
        if (!g_intelligence_history.duration_active) {
            // Just crossed threshold: start duration
            g_intelligence_history.duration_active = true;
            g_intelligence_history.duration_start_ms = current_time_ms;
            g_intelligence_history.time_above_fire_threshold_s = 0.0f;
        } else {
            // Still above: update duration
            uint32_t elapsed_ms = current_time_ms - g_intelligence_history.duration_start_ms;
            g_intelligence_history.time_above_fire_threshold_s = elapsed_ms / 1000.0f;
        }
    } else {
        // Below threshold: reset
        g_intelligence_history.duration_active = false;
        g_intelligence_history.time_above_fire_threshold_s = 0.0f;
    }
}
```

#### 5. Health/Quality Derivation from Sensor Validity

Replace hardcoded `H_i = 1.0f, Q_i = 1.0f` with:

```c
// GATE 1: Health (H_i) - derived from sensor validity
health_diagnostic_t health_diagnostics[] = {
    {
        .key = "sensor_valid",
        .value = bme_result.valid ? 1.0f : 0.0f,
        .weight = 0.6f
    },
    {
        .key = "value_in_range",
        .value = (!isnan(temp_c) && temp_c >= -40.0f && temp_c <= 85.0f) ? 1.0f : 0.0f,
        .weight = 0.4f
    }
};

health_result_t h_temp_result = compute_health(health_diagnostics, 2, false);
float H_temp = h_temp_result.complete ? h_temp_result.h_i : NAN;

// GATE 2: Quality (Q_i) - derived from sample integrity
// q_integrity: use sensor validity as proxy
float q_integrity_temp = bme_result.valid ? 1.0f : 0.0f;

// q_stability: compute from recent variance if history available
float q_stability_temp = 1.0f;  // Default high stability
if (g_intelligence_history.temp_count >= 3) {
    // Compute variance of recent samples
    float mean = 0.0f;
    for (uint8_t i = 0; i < g_intelligence_history.temp_count; i++) {
        mean += g_intelligence_history.temp_history[i];
    }
    mean /= g_intelligence_history.temp_count;
    
    float variance = 0.0f;
    for (uint8_t i = 0; i < g_intelligence_history.temp_count; i++) {
        float diff = g_intelligence_history.temp_history[i] - mean;
        variance += diff * diff;
    }
    variance /= g_intelligence_history.temp_count;
    
    // Stability decreases with variance (exponential decay)
    q_stability_temp = expf(-variance / 10.0f);  // 10.0 = stability threshold
}

quality_result_t q_temp_result = compute_quality(q_integrity_temp, q_stability_temp);
float Q_temp = q_temp_result.valid ? q_temp_result.q_i : NAN;
```

#### 6. Complete Temporal/Duration Components in Severity

Replace placeholders with:

```c
// Temporal component (rate of change)
float temp_rate = compute_rate_of_change(
    g_intelligence_history.temp_history,
    g_intelligence_history.temp_timestamps_ms,
    g_intelligence_history.temp_count,
    g_intelligence_history.temp_index
);

float t_h = NAN;
if (!isnan(temp_rate)) {
    float max_temp_rate = 5.0f;  // °C/s (PROTOTYPE)
    t_h = compute_temporal(temp_rate, max_temp_rate);
}

// Duration component
float fire_threshold = 50.0f;  // °C (PROTOTYPE)
uint32_t current_time_ms = esp_timer_get_time() / 1000;
update_duration_tracking(temp_c, fire_threshold, current_time_ms);

float d_h = NAN;
if (g_intelligence_history.duration_active) {
    float max_duration = 60.0f;  // seconds (PROTOTYPE)
    d_h = compute_duration(g_intelligence_history.time_above_fire_threshold_s, max_duration);
}
```

#### 7. Update History Buffers After Each Sample

Add at the end of sampling loop:

```c
// Update history buffers
uint32_t current_time_ms = esp_timer_get_time() / 1000;

// Temperature history (circular buffer)
if (!isnan(temp_c)) {
    g_intelligence_history.temp_history[g_intelligence_history.temp_index] = temp_c;
    g_intelligence_history.temp_timestamps_ms[g_intelligence_history.temp_index] = current_time_ms;
    g_intelligence_history.temp_index = (g_intelligence_history.temp_index + 1) % HISTORY_SIZE;
    if (g_intelligence_history.temp_count < HISTORY_SIZE) {
        g_intelligence_history.temp_count++;
    }
}

// Humidity history (circular buffer)
if (!isnan(humidity_pct)) {
    g_intelligence_history.humid_history[g_intelligence_history.humid_index] = humidity_pct;
    g_intelligence_history.humid_timestamps_ms[g_intelligence_history.humid_index] = current_time_ms;
    g_intelligence_history.humid_index = (g_intelligence_history.humid_index + 1) % HISTORY_SIZE;
    if (g_intelligence_history.humid_count < HISTORY_SIZE) {
        g_intelligence_history.humid_count++;
    }
}

// Update baseline stats accumulation
update_baseline_stats(temp_c, humidity_pct);
```

---

## Testing Strategy

### Unit Test Coverage

1. **Baseline Stats Population**
   - Test: Accumulate 50 samples, verify `compute_robust_baseline()` called
   - Test: Verify baseline_stats[0].valid transitions to true
   - Test: Verify z-scores become valid after baseline computed

2. **Rate-of-Change Computation**
   - Test: 2 samples 1 second apart with Δ5°C → 5°C/s
   - Test: Insufficient history → NAN
   - Test: Circular buffer wrap-around correctness

3. **Duration Tracking**
   - Test: Value crosses threshold → duration starts
   - Test: Value stays above → duration accumulates
   - Test: Value drops below → duration resets
   - Test: Missing value → duration resets

4. **Health/Quality Derivation**
   - Test: Valid sensor reading → H_i = 1.0, Q_i = 1.0
   - Test: Invalid sensor reading → H_i < 1.0
   - Test: High variance → Q_i < 1.0

### Integration Test

**End-to-End Pipeline Test**:

1. Initialize system
2. Feed 50 temperature samples (20°C baseline)
3. Verify baseline_stats[0].valid = true
4. Feed sample at 60°C (above fire threshold)
5. Verify:
   - z-score > 0 (anomaly detected)
   - A_i > 0 (individual anomaly)
   - E_h > 0 (evidence present, temperature in [60-150])
   - I_h > 0 (intensity from fire threshold)
   - hazard_state transitions: NORMAL → WATCH → SUSPECTED
6. Feed 5 more samples at 80°C (sustained)
7. Verify:
   - T_h > 0 (rate of change)
   - D_h > 0 (duration above threshold)
   - S_h > 0 (severity from I/T/D)
   - R_h > 0 (risk from E/S/T)
   - hazard_state transitions: SUSPECTED → CONFIRMED
8. Feed samples at 95°C (critical)
9. Verify:
   - hazard_state transitions: CONFIRMED → CRITICAL
10. Feed samples back to 25°C (resolved)
11. Verify:
    - hazard_state transitions: CRITICAL → RESOLVED → NORMAL

---

## Gaps Remaining After Task 4

### 1. MQ-2 Raw ADC Integration (DOCUMENTED)

**Status**: MQ-2 handled per decisions:
- ✅ Used in baseline for change detection
- ✅ Used in A_node (node aggregate anomaly)
- ❌ NOT used in evidence thresholds
- ❌ NOT used in A_h (fire-specific anomaly)
- ❌ NO ppm conversion

**Documentation**: Included in data flow doc

### 2. Smoke Sensor Unavailable (HARDWARE LIMITATION)

**Status**: Fire evidence incomplete
- Core evidence requires temperature + smoke
- Only temperature available
- Core floor caps E_h at 0.3 (cap_without_core)
- Cannot reach full CONFIRMED state without smoke sensor

**Impact**: 
- Hazard state can reach SUSPECTED (based on anomaly + confidence)
- Cannot reach CONFIRMED (requires E_h >= 0.5, capped at 0.3)
- System relies on anomaly/severity for fire detection

**Mitigation**: DOCUMENT AS KNOWN LIMITATION

### 3. Multi-Sensor Variance (c_agree) Not Implemented

**Status**: Single BME680, no redundant sensors
- c_agree placeholder = 1.0 (high agreement, no disagreement possible)
- Not a bug, just hardware constraint

### 4. Measurement Age Tracking (c_temp) Simplified

**Status**: All readings from current loop iteration
- c_temp = 1.0 (all fresh, < 1 second old)
- Could add timestamp checking if sampling intervals become irregular

---

## Implementation Checklist

- [ ] Add history buffer structs to main.c
- [ ] Implement `update_baseline_stats()` function
- [ ] Implement `compute_rate_of_change()` function
- [ ] Implement `update_duration_tracking()` function
- [ ] Replace hardcoded H_i/Q_i with derived values
- [ ] Wire temporal T_h computation
- [ ] Wire duration D_h computation
- [ ] Add history buffer updates at end of sampling loop
- [ ] Test baseline stats population (50 samples)
- [ ] Test rate-of-change computation (multiple samples)
- [ ] Test duration tracking (threshold crossing)
- [ ] Test end-to-end pipeline (NORMAL → WATCH → SUSPECTED)
- [ ] Document remaining gaps (smoke sensor, MQ-2 limits)
- [ ] Create Track 4 completion report

---

**TRACK 4 TASK 4 IMPLEMENTATION PLAN COMPLETE**  
**Ready to execute changes to main.c**
