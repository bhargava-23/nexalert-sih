# Track 4: Edge Intelligence Data Flow Definition

**Date**: 2026-09-16  
**Status**: TASK 2 COMPLETE — Data Flow Mapped  
**Previous**: TASK 1 COMPLETE — Audit Complete

---

## Overview

This document defines the complete edge intelligence data flow for Track 4, mapping how sensor readings flow through the intelligence pipeline from raw hardware inputs to local hazard state determination.

**Architecture Principle**: The intelligence pipeline runs IN PARALLEL with hardware JSON generation. Intelligence results feed LOCAL state/action but DO NOT modify the MQTT hardware payload.

---

## Complete Data Flow Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 0: Raw Hardware Sensors                                   │
├─────────────────────────────────────────────────────────────────┤
│ BME680 (I2C 0x77): temp_c, humidity_pct, pressure_hpa, gas_ohm │
│ MPU6050 (I2C 0x68): accel_x/y/z → vibration_mps2               │
│ MQ-2 (ADC GPIO4): raw_adc [0-4095]                             │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 0.5: Sensor Reading Acquisition                          │
├─────────────────────────────────────────────────────────────────┤
│ File: main/main.c sampling loop                                 │
│ Output: Per-sensor float values or NAN (missing)                │
│                                                                  │
│ BME680:                                                          │
│   - temperature_c: °C                                            │
│   - humidity_pct: % RH [0-100]                                  │
│   - pressure_hpa: hPa                                            │
│   - gas_resistance_ohm: Ω                                        │
│                                                                  │
│ MPU6050:                                                         │
│   - vibration_mps2: m/s² (magnitude)                            │
│                                                                  │
│ MQ-2:                                                            │
│   - mq2_raw_adc: [0-4095] RAW ADC                               │
│   - NOT CONVERTED TO PPM (no calibration)                       │
│                                                                  │
│ Missing → NAN (preserves missing != zero)                       │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
                    ┌────┴────┐
                    │         │
         ┌──────────┴─┐   ┌───┴────────────┐
         │            │   │                │
         ↓            ↓   ↓                ↓
┌────────────────┐   Hardware JSON    Intelligence
│ PARALLEL PATHS │   Generation       Pipeline
└────────────────┘   (Track 3A)       (Track 4)
                     ↓                 ↓
              ┌──────────────┐   ┌─────────────────┐
              │ hardware_json│   │ LAYER 1:        │
              │ .c serializer│   │ Health, Quality,│
              └──────┬───────┘   │ Reliability     │
                     ↓           └─────────────────┘
              ┌──────────────┐
              │ MQTT Publish │
              │ Nexalert/    │
              │ telemetry/   │
              │ node1        │
              └──────────────┘
                     ↓
              Track 3C Normalization
              (backend, not edge)
```

---

## LAYER 1: Health, Quality, Reliability

### 1.1 Health Computation (H_i)

**Module**: `components/intelligence/health.c`  
**API**: `health_result_t compute_health(const health_diagnostic_t* diagnostics, uint8_t num_diagnostics, bool hard_failure)`

**Formula**: `H_i = Σ(w_j × D_j)` if F_i=0, else H_i=0

**Input Derivation** (from sensor validity):

```c
// Per-sensor health diagnostics derived from validity
health_diagnostic_t diagnostics[] = {
    {
        .key = "sensor_valid",
        .value = sensor_reading.valid ? 1.0f : 0.0f,  // Binary: valid=1, invalid=0
        .weight = 0.6f
    },
    {
        .key = "value_in_range",
        .value = (value >= sensor_min && value <= sensor_max) ? 1.0f : 0.0f,
        .weight = 0.4f
    }
};

bool hard_failure = false;  // Set true if sensor I2C communication fails completely
health_result_t h_result = compute_health(diagnostics, 2, hard_failure);
float H_i = h_result.complete ? h_result.h_i : NAN;
```

**Decision**: Health is derived from sensor validity flags and range checks, NOT hardcoded to 1.0.

**Output**: `H_i ∈ [0, 1]` or NAN (missing)

---

### 1.2 Quality Computation (Q_i)

**Module**: `components/intelligence/quality.c`  
**API**: `quality_result_t compute_quality(float q_integrity, float q_stability)`

**Formula**: `Q_i = q_integrity × q_stability`

**Input Derivation** (from sensor characteristics):

```c
// q_integrity: Based on sample validity over time window
// Example: 9 valid readings out of 10 recent samples → q_integrity = 0.9
float q_integrity = (float)valid_count / (float)total_samples;

// q_stability: Based on signal variance/jitter
// Example: Low variance → high stability
float variance = compute_variance(recent_samples, sample_count);
float q_stability = expf(-variance / stability_threshold);  // Decreases with variance

quality_result_t q_result = compute_quality(q_integrity, q_stability);
float Q_i = q_result.valid ? q_result.q_i : NAN;
```

**Decision**: Quality computed from actual sample integrity and stability, NOT hardcoded to 1.0.

**Output**: `Q_i ∈ [0, 1]` or NAN (missing)

---

### 1.3 Reliability Computation (R_i)

**Module**: `components/intelligence/reliability.c`  
**API**: `reliability_result_t compute_reliability(float h_i, float q_i, float k_i)`

**Formula**: `R_i = H_i × Q_i × K_i`

**Input**:
- `h_i`: From compute_health()
- `q_i`: From compute_quality()
- `k_i`: Calibration validity (Track 4: use 1.0 for uncalibrated sensors, reserve for future)

```c
float K_i = 1.0f;  // No calibration subsystem yet (Phase 6+)

reliability_result_t r_result = compute_reliability(H_i, Q_i, K_i);
float R_i = r_result.valid ? r_result.r_i : NAN;
```

**Output**: `R_i ∈ [0, 1]` or NAN (missing)

---

## LAYER 2: Baseline

**Module**: `components/intelligence/baseline.c`  
**API**:
- `baseline_stats_t compute_robust_baseline(const float* samples, uint16_t count, float epsilon)`
- `baseline_result_t compute_baseline_z_score(float value, const baseline_stats_t* stats)`
- `baseline_state_result_t update_baseline_state(...)`

**Formula**:
```
median = median(samples)
MAD = median(|samples - median|)
scale = 1.4826 × MAD + ε
z_i = (value - median) / scale
```

**Input Sensors** (Track 4 reconciliation):

| Sensor | Use in Baseline | Notes |
|--------|----------------|-------|
| BME680 temperature | ✅ YES | Continuous numeric, stable baseline |
| BME680 humidity | ✅ YES | Continuous numeric, stable baseline |
| BME680 pressure | ✅ YES | Continuous numeric, stable baseline |
| BME680 gas resistance | ✅ YES | Continuous numeric, may drift |
| MPU6050 vibration | ✅ YES | Continuous numeric, magnitude |
| MQ-2 raw ADC | ✅ YES (with care) | RAW ADC only, detect CHANGES not absolute levels |

**MQ-2 Handling**:
- ✅ Use MQ-2 raw ADC in baseline to detect CHANGES from normal
- ❌ DO NOT interpret z-score as "gas concentration exceeded threshold"
- ❌ DO NOT convert raw ADC to ppm (no calibration available)
- ✅ Treat as "gas sensor anomaly detected" (change from baseline)

**State Machine**: INITIALIZING → LEARNING → READY ⇄ FROZEN → RECOVERING

**Current Gap**: `compute_robust_baseline()` exists but NOT YET CALLED in main.c — baseline_stats[] arrays are unpopulated, so z-scores are currently invalid.

**Output**: `z_i` (standardized deviation, signed float) or NAN (missing)

---

## LAYER 3: Anomaly

**Module**: `components/intelligence/anomaly.c`  
**API**:
- `individual_anomaly_result_t compute_individual_anomaly(float z_score, float lambda_param, float z_cap)`
- `node_anomaly_result_t compute_node_aggregate_anomaly(const sensor_anomaly_t* sensors, uint8_t count, float epsilon)`
- `hazard_anomaly_result_t compute_hazard_specific_anomaly(const sensor_anomaly_t* sensors, uint8_t count, float epsilon)`

**Formulas**:
```
A_i = 1 - exp(-min(|z_i|, z_cap) / λ)
A_node = Σ(R_i × A_i) / Σ(R_i)
A_h = Σ(w_ih × R_i × A_i) / Σ(w_ih × R_i)
```

**Input**: z-scores from baseline, R_i from reliability, hazard weights w_ih

**Configuration** (PROTOTYPE):
- λ (lambda_param): 2.0
- z_cap: 5.0

**Sensor Weights for Fire Hazard** (w_ih):

| Sensor | Fire Weight | Rationale |
|--------|-------------|-----------|
| BME680 temperature | 0.5 | Primary fire indicator |
| BME680 gas resistance | 0.3 | Smoke/combustion byproducts |
| BME680 humidity | 0.1 | Supporting (decreases in fire) |
| MPU6050 vibration | 0.1 | Supporting (structural response) |
| BME680 pressure | 0.0 | Not relevant for fire |
| MQ-2 raw ADC | 0.0 | Cannot use without calibration in hazard-specific |

**MQ-2 in Anomaly**:
- ✅ Include in A_node (node aggregate, generic anomaly detection)
- ❌ Exclude from A_h(fire) (cannot interpret raw ADC as fire-specific evidence)
- Weight for A_node: use R_i naturally (no hazard-specific weight)

**Status**: ✅ FULLY WIRED in main.c

**Output**: `A_i, A_node, A_h ∈ [0, 1]` or NAN (missing)

---

## LAYER 4: Evidence

**Module**: `components/intelligence/evidence.c`  
**API**: `evidence_result_t compute_evidence(const sensor_reading_t* readings, uint8_t reading_count, const evidence_config_t* config, float epsilon)`

**Formula**: E_h = threshold-based rule matching with core evidence floor

**Existing Threshold Configuration** (from Python reference):

```python
# PROTOTYPE FIRE EVIDENCE (UNVALIDATED)
fire_evidence_config = {
    "core_evidence": [
        {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 0.5},
        {"sensor": "smoke", "threshold_min": 0.3, "threshold_max": 1.0, "weight": 0.3}
    ],
    "supporting_evidence": [
        {"sensor": "humidity", "threshold_min": 0.0, "threshold_max": 0.3, "weight": 0.1}
    ],
    "core_floor": {
        "min_core_coverage": 0.5,
        "cap_without_core": 0.3
    }
}
```

**Track 4 Sensor Mapping**:

| Evidence Rule | Track 4 Sensor | Available? | Notes |
|---------------|----------------|------------|-------|
| temperature [60-150°C] | BME680 temperature | ✅ YES | Direct mapping |
| smoke [0.3-1.0] | ❌ NOT AVAILABLE | NO | No smoke sensor on node |
| humidity [0-0.3] | BME680 humidity [0-100%] → [0-1.0] | ✅ YES | Normalize to [0,1] |

**MQ-2 Decision**:
- ❌ DO NOT add MQ-2 raw ADC to evidence thresholds
- ❌ DO NOT invent "gas_adc > X means fire" rule
- Rationale: Raw ADC has no known mapping to ppm or fire threshold

**Evidence Configuration Gap**:
- ⚠️ Core evidence "smoke" sensor NOT AVAILABLE on this hardware
- ⚠️ Core floor will cap E_h at 0.3 (cap_without_core) due to insufficient core coverage
- Decision: DOCUMENT AS BLOCKER — fire evidence limited without smoke sensor

**Status**: ✅ API exists, ❌ NOT YET CALLED in main.c

**Output**: `E_h ∈ [0, 1]` or NAN (missing), capped by core floor

---

## LAYER 5: Confidence

**Module**: `components/intelligence/confidence.c`  
**API**: `confidence_result_t compute_confidence(float c_cov, float c_agree, float c_temp, float c_base, const confidence_weights_t* weights, float epsilon)`

**Formula**: `C_h = w_c × C_cov + w_a × C_agree + w_t × C_temp + w_b × C_base`

**Component Computation**:

### C_cov (Coverage Confidence)
```c
// Fraction of relevant sensors available
uint8_t available = 0;
uint8_t total = 5;  // temp, humidity, pressure, gas, vibration

if (!isnan(temperature_c)) available++;
if (!isnan(humidity_pct)) available++;
if (!isnan(pressure_hpa)) available++;
if (!isnan(gas_resistance_ohm)) available++;
if (!isnan(vibration_mps2)) available++;

float c_cov = (float)available / (float)total;
```

### C_agree (Agreement Confidence)
```c
// Variance among similar sensors (if multiple exist)
// Track 4: Single BME680, single MPU6050 → use placeholder
float c_agree = 1.0f;  // High agreement (no redundant sensors to disagree)
```

### C_temp (Temporal Confidence)
```c
// Data freshness
// Track 4: All readings from current loop iteration → fresh
float c_temp = 1.0f;  // All data fresh (< 1 second old)
```

### C_base (Baseline Confidence)
```c
// Baseline readiness
float c_base;
if (baseline_current_state == BASELINE_READY) {
    c_base = 1.0f;
} else if (baseline_current_state == BASELINE_LEARNING) {
    c_base = 0.5f;
} else {
    c_base = 0.0f;  // INITIALIZING, FROZEN, RECOVERING
}
```

**Weights** (PROTOTYPE):
- w_c (coverage): 0.3
- w_a (agreement): 0.3
- w_t (temporal): 0.2
- w_b (baseline): 0.2

**Status**: ⚠️ PARTIALLY WIRED — c_cov and c_base correct, c_agree/c_temp placeholders

**Output**: `C_h ∈ [0, 1]` or NAN (missing)

---

## LAYER 6: Severity

**Module**: `components/intelligence/severity.c`  
**API**:
- `float compute_fire_intensity(float temperature, float smoke, const fire_intensity_config_t* config)`
- `float compute_temporal(float current_rate, float max_rate)`
- `float compute_duration(float above_threshold_seconds, float max_duration_seconds)`
- `severity_result_t compute_severity(float i_h, float t_h, float d_h, const severity_weights_t* weights, float epsilon)`

**Formula**: `S_h = w_I × I_h + w_T × T_h + w_D × D_h`

### I_h (Intensity Component)

**Fire Intensity Thresholds** (from severity.c, PROTOTYPE):
```c
fire_intensity_config_t {
    .temp_low = 40.0f,   // °C
    .temp_high = 100.0f, // °C
    .smoke_low = 0.2f,   // normalized [0,1]
    .smoke_high = 0.8f   // normalized [0,1]
}
```

**Track 4 Mapping**:
- ✅ temperature: BME680 temperature_c
- ❌ smoke: NOT AVAILABLE (no smoke sensor)

**Computation**:
```c
// Temperature intensity (linear interpolation)
float i_temp;
if (temperature_c <= 40.0f) {
    i_temp = 0.0f;
} else if (temperature_c >= 100.0f) {
    i_temp = 1.0f;
} else {
    i_temp = (temperature_c - 40.0f) / (100.0f - 40.0f);
}

// I_h(fire) = max(i_temp) since smoke unavailable
float I_h = i_temp;
```

### T_h (Temporal Component)

**Configuration** (PROTOTYPE):
- max_temp_rate: 5.0°C/s

**Computation**:
```c
// Rate of change (requires history)
float current_temp_rate = (current_temp - prev_temp) / delta_t;
float T_h = compute_temporal(current_temp_rate, 5.0f);  // Returns [0,1]
```

**Current Gap**: Temperature history NOT YET TRACKED in main.c

### D_h (Duration Component)

**Configuration** (PROTOTYPE):
- fire_temp_threshold: 50.0°C
- max_duration: 60.0s

**Computation**:
```c
// Time above threshold (requires tracking)
static float time_above_threshold = 0.0f;
if (temperature_c >= 50.0f) {
    time_above_threshold += delta_t;
} else {
    time_above_threshold = 0.0f;  // Reset when below
}

float D_h = compute_duration(time_above_threshold, 60.0f);  // Returns [0,1]
```

**Current Gap**: Duration tracking NOT YET IMPLEMENTED in main.c

**Weights** (PROTOTYPE):
- w_I (intensity): 0.5
- w_T (temporal): 0.3
- w_D (duration): 0.2

**Status**: ⚠️ PARTIALLY WIRED — I_h incomplete (no smoke), T_h/D_h missing tracking

**Output**: `S_h ∈ [0, 1]` or NAN (missing)

---

## LAYER 7: Risk

**Module**: `components/intelligence/risk.c`  
**API**: `risk_result_t compute_risk(float e_h, float s_h, float t_h, const risk_weights_t* weights, float epsilon)`

**Formula**: `R_h = w_E × E_h + w_S × S_h + w_T × T_h`

**Input**:
- `e_h`: From compute_evidence()
- `s_h`: From compute_severity()
- `t_h`: Temporal/threat component (reused from severity temporal)

**Weights** (PROTOTYPE):
- w_E (evidence): 0.4
- w_S (severity): 0.4
- w_T (temporal): 0.2

**Status**: ⚠️ CALLED but E_h currently hardcoded NAN (evidence not wired)

**Output**: `R_h ∈ [0, 1]` or NAN (missing)

---

## LAYER 8: Hazard State Machine

**Module**: `components/intelligence/hazard_state.c`  
**API**: `hazard_transition_t evaluate_hazard_transition(const intelligence_inputs_t* inputs, ...)`

**States**: NORMAL → WATCH → SUSPECTED → CONFIRMED → CRITICAL → RESOLVED

**Input Structure**:
```c
intelligence_inputs_t {
    float e_h;              // Evidence [0,1]
    float c_h;              // Confidence [0,1]
    float s_h;              // Severity [0,1]
    float r_h;              // Risk [0,1]
    float a_h;              // Anomaly [0,1]
    float core_coverage;    // Core evidence coverage [0,1]
}
```

**Transition Logic** (DETERMINISTIC):
- NORMAL → WATCH: R_h >= 0.3
- WATCH → SUSPECTED: A_h >= 0.5 AND C_h >= 0.3
- SUSPECTED → CONFIRMED: E_h >= 0.5 AND C_h >= 0.5
- CONFIRMED → CRITICAL: S_h >= 0.7 OR R_h >= 0.8
- Any → RESOLVED: R_h < 0.2 for persistence duration

**CRITICAL INVARIANT**: UNKNOWN information condition prevents NEW CONFIRMED declarations when C_h < 0.5 or core_coverage < 0.5

**Status**: ✅ FULLY WIRED with state transitions

**Output**: `hazard_state_t` enum, `information_condition_t`, persistence counter

---

## Sensor Input Reconciliation (TASK 3)

### Available Sensors → Intelligence Modules

| Sensor | Baseline | Anomaly | Evidence | Severity | Confidence | Notes |
|--------|----------|---------|----------|----------|------------|-------|
| **BME680 temp** | ✅ | ✅ | ✅ [60-150°C] | ✅ I_h [40-100°C] | ✅ c_cov | Ready |
| **BME680 humidity** | ✅ | ✅ | ✅ [0-30%] | ❌ | ✅ c_cov | Ready |
| **BME680 pressure** | ✅ | ✅ | ❌ | ❌ | ✅ c_cov | Baseline/anomaly only |
| **BME680 gas** | ✅ | ✅ | ❌ | ❌ | ✅ c_cov | Baseline/anomaly only |
| **MPU6050 vibration** | ✅ | ✅ | ❌ | ❌ | ✅ c_cov | Baseline/anomaly only |
| **MQ-2 raw ADC** | ✅ (changes) | ✅ (A_node) | ❌ | ❌ | ❌ | NO ppm interpretation |

### MQ-2 Raw ADC Handling Rules

1. ✅ **ALLOWED**:
   - Use in baseline to establish "normal" ADC range
   - Detect CHANGES from baseline (z-score computation)
   - Include in node aggregate anomaly (A_node) with reliability weighting
   - Label as "gas sensor anomaly detected" when A_i high

2. ❌ **PROHIBITED**:
   - Convert raw ADC to ppm (no calibration available)
   - Use in evidence thresholds (cannot claim "gas concentration exceeded X ppm")
   - Use in hazard-specific anomaly A_h(fire) (cannot interpret as fire-related)
   - Treat high ADC as "fire detected" or "hazardous gas present"
   - Invent conversion factors or thresholds

3. ✅ **SAFE INTERPRETATION**:
   - "MQ-2 sensor reading deviated from baseline by X standard deviations"
   - "Gas sensor anomaly detected (change from normal)"
   - Include in overall node health/anomaly assessment

4. ❌ **UNSAFE INTERPRETATION**:
   - "Gas concentration is Y ppm"
   - "Smoke detected"
   - "Combustible gas threshold exceeded"

---

## Data Flow Summary Table

| Layer | Module | Input | Output | Status | Gap |
|-------|--------|-------|--------|--------|-----|
| 0 | Sensor drivers | I2C/ADC | float values or NAN | ✅ Complete | - |
| 1a | health.c | sensor validity | H_i [0,1] | ❌ Not called | Need to wire |
| 1b | quality.c | integrity, stability | Q_i [0,1] | ❌ Not called | Need to wire |
| 1c | reliability.c | H_i, Q_i, K_i | R_i [0,1] | ⚠️ Hardcoded 1.0 | Need H_i, Q_i |
| 2 | baseline.c | sensor samples | z_i | ⚠️ Stats empty | Need compute_robust_baseline |
| 3 | anomaly.c | z_i, R_i | A_i, A_node, A_h | ✅ Fully wired | - |
| 4 | evidence.c | sensor values, rules | E_h [0,1] | ❌ Not called | Need to wire + smoke gap |
| 5 | confidence.c | cov, agree, temp, base | C_h [0,1] | ⚠️ Partial | Need c_agree, c_temp |
| 6 | severity.c | I_h, T_h, D_h | S_h [0,1] | ⚠️ Partial | Need T_h, D_h tracking |
| 7 | risk.c | E_h, S_h, T_h | R_h [0,1] | ⚠️ E_h missing | Need evidence |
| 8 | hazard_state.c | E_h, C_h, S_h, R_h, A_h | state enum | ✅ Fully wired | - |

---

## Critical Gaps Identified

### 1. Health/Quality Not Wired (TASK 4)
- **Impact**: R_i currently hardcoded to 1.0, loses sensor validity information
- **Fix**: Implement health/quality derivation from sensor validity flags
- **Priority**: HIGH (foundation for reliability)

### 2. Baseline Stats Unpopulated (TASK 4)
- **Impact**: z-scores invalid, anomaly computation meaningless
- **Fix**: Call `compute_robust_baseline()` to populate baseline_stats[]
- **Priority**: CRITICAL (blocks all downstream intelligence)

### 3. Evidence Not Wired (TASK 4)
- **Impact**: E_h = NAN, risk computation incomplete, hazard state cannot reach CONFIRMED
- **Fix**: Wire evidence computation with existing thresholds
- **Priority**: HIGH (required for CONFIRMED state)

### 4. Smoke Sensor Unavailable (HARDWARE LIMITATION)
- **Impact**: Core fire evidence incomplete, E_h capped at 0.3 by core floor
- **Fix**: CANNOT FIX (hardware constraint)
- **Mitigation**: Document as known limitation, rely on temperature + anomaly
- **Priority**: DOCUMENT AS BLOCKER

### 5. Temporal/Duration Tracking Missing (TASK 4)
- **Impact**: T_h, D_h components incomplete, severity reduced
- **Fix**: Add history buffers for rate-of-change and duration tracking
- **Priority**: MEDIUM (severity still partially functional)

### 6. MQ-2 Raw ADC Limited Use (DESIGN DECISION)
- **Impact**: Cannot use MQ-2 for absolute gas concentration claims
- **Fix**: Use ONLY for baseline/anomaly change detection
- **Mitigation**: Clearly label as "sensor anomaly" not "gas detected"
- **Priority**: DOCUMENT AS DECISION

---

## Hardware JSON Independence

**CRITICAL**: Intelligence results DO NOT modify hardware JSON payload.

```
┌─────────────────────────────────┐
│ Sensor Readings                 │
└────────┬───────────────┬────────┘
         │               │
         ↓               ↓
┌────────────────┐  ┌──────────────────┐
│ Hardware JSON  │  │ Intelligence     │
│ (Track 3A)     │  │ Pipeline         │
│                │  │ (Track 4)        │
│ - temperature_c│  │ - H_i, Q_i, R_i  │
│ - humidity_rh  │  │ - B_i, A_i       │
│ - pressure_hpa │  │ - E_h, C_h, S_h  │
│ - gas_ppm      │  │ - R_h            │
│ - vibration... │  │ - hazard_state   │
│ - availability │  │                  │
│ - power        │  │ Local actions:   │
│                │  │ - LED indicator  │
│ NO intelligence│  │ - Local alarm    │
│ fields         │  │ - Priority       │
└────────┬───────┘  └──────────────────┘
         ↓
┌────────────────────────────────┐
│ MQTT Publish                   │
│ Nexalert/telemetry/node1       │
│ (Hardware JSON ONLY)           │
└────────────────────────────────┘
```

**Intelligence results MAY be used for**:
- Setting MQTT message priority (QoS based on hazard_state)
- Local LED indicators (red = CRITICAL, yellow = WATCH, green = NORMAL)
- Local buzzer/alarm activation
- Buffering strategy (retain more messages when hazard active)

**Intelligence results MUST NOT**:
- Add fields to hardware JSON
- Create separate MQTT intelligence topic
- Modify sensor values in hardware JSON
- Override availability flags

---

## Next Steps (TASK 4)

1. **Wire Health/Quality computation** from sensor validity
2. **Call compute_robust_baseline()** to populate baseline stats
3. **Wire Evidence computation** with existing fire thresholds
4. **Add Temporal/Duration tracking** for T_h, D_h components
5. **Complete Confidence** c_agree, c_temp computation
6. **Test end-to-end** pipeline with all 10 modules integrated
7. **Document smoke sensor limitation** as hardware constraint

---

**TRACK 4 TASK 2 COMPLETE**  
**TRACK 4 TASK 3 COMPLETE** (sensor reconciliation documented)  
**Ready for TASK 4**: Integration implementation

---

**END OF DATA FLOW DEFINITION**
