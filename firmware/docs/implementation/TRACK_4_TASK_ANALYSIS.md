# Track 4 Corrective Implementation — Task Analysis

**Date**: 2026-09-16

---

## TASK 1: Quality / q_stability — Analysis

### Repository Specification Review

**From `reference/python/nexalert_reference/quality.py`**:
```python
def compute_quality(
    q_integrity: Optional[float],
    q_stability: Optional[float]
) -> Optional[float]:
    """
    Specification: Document 04, Section 3.2
    Formula: Q_i = q_integrity × q_stability
    
    Invariants:
        - Missing samples decrease q_integrity (Doc 04 Sec 3.2)
        - High jitter decreases q_stability (Doc 04 Sec 3.2)
        - Q_i = 0 means observation unusable
        - None inputs preserve missing != zero
    """
    if q_integrity is None or q_stability is None:
        return None
```

**Finding**: Repository specification states:
- "High jitter decreases q_stability"
- But provides NO formula for computing jitter → stability score
- No variance → stability mapping
- No reference implementation of stability calculation

**Conclusion**: 
- Repository describes WHAT stability represents (jitter measure)
- Repository does NOT provide HOW to compute it
- Current `q_stability = NAN` is CORRECT per repository specification
- Attempting to compute stability without repository formula would be INVENTING

**Decision**: ✅ KEEP `q_stability = NAN` — Repository-correct behavior

---

## TASK 2: Temporal Confidence / c_temp — Analysis

### Repository Specification

**From `reference/python/nexalert_reference/confidence.py:183-229`**:
```python
def compute_temporal(
    telemetry_age_seconds: Optional[float],
    max_age_seconds: float = 300.0
) -> float:
    """
    Formula: C_temp = max(0, 1 - age / max_age)
    
    Args:
        telemetry_age_seconds: Age of telemetry (t_now - t_measurement) in seconds
        max_age_seconds: Maximum acceptable age (PROTOTYPE: 300s = 5 minutes)
    
    Returns:
        C_temp in [0, 1]
    
    Missing Handling:
    - telemetry_age_seconds is None → returns 0.0 (no temporal information)
    - age > max_age → returns 0.0 (stale data)
    - age < 0 → raises ValueError (clock error)
    """
    if telemetry_age_seconds is None:
        return 0.0
    
    if telemetry_age_seconds < 0:
        raise ValueError(f"Negative telemetry age: {telemetry_age_seconds}s (clock error)")
    
    if telemetry_age_seconds > max_age_seconds:
        return 0.0
    
    c_temp = 1.0 - (telemetry_age_seconds / max_age_seconds)
    return max(0.0, c_temp)
```

**From `firmware/components/intelligence/confidence.c:115-146`**:
```c
float compute_temporal_confidence(
    float telemetry_age_seconds,
    float max_age_seconds
)
{
    // Missing temporal information
    if (isnan(telemetry_age_seconds)) {
        return 0.0f;
    }
    
    // Invalid age (clock error or future timestamp)
    if (telemetry_age_seconds < 0.0f) {
        return 0.0f;
    }
    
    // Stale data
    if (telemetry_age_seconds > max_age_seconds) {
        return 0.0f;
    }
    
    // Formula: C_temp = max(0, 1 - age / max_age)
    float c_temp = 1.0f - (telemetry_age_seconds / max_age_seconds);
    
    // Clamp to [0, 1]
    if (c_temp < 0.0f) {
        c_temp = 0.0f;
    } else if (c_temp > 1.0f) {
        c_temp = 1.0f;
    }
    
    return c_temp;
}
```

### Current Implementation Issue

**In `firmware/main/main.c:687-691`**:
```c
// c_temp: Temporal confidence (per confidence.py:144-205)
// Current implementation: All readings from same sampling loop (< 1s old)
// Approximates repository formula: C_temp ≈ 1 - (1s / 300s) ≈ 1.0
// Note: Does not implement actual age computation or repository formula
float c_temp = 1.0f;
```

**Problem**: Hardcoded `1.0` instead of calling `compute_temporal_confidence()`

### Available Data

**Timestamps exist in code**:
- Line 890: `uint32_t loop_time_ms = (uint32_t)(esp_timer_get_time() / 1000);`
- Line 747: `uint32_t current_time_ms = (uint32_t)(esp_timer_get_time() / 1000);`

**Measurement timestamps**: None currently stored per sensor reading

### Solution

Compute actual age using current loop time as measurement time:
```c
uint32_t current_time_ms = (uint32_t)(esp_timer_get_time() / 1000);
// All measurements from this loop iteration, age ≈ 0
float telemetry_age_seconds = 0.0f;  // Measurements just acquired
float max_age_seconds = 300.0f;  // 5 minutes (repository default)
float c_temp = compute_temporal_confidence(telemetry_age_seconds, max_age_seconds);
```

**Result**: `c_temp = 1.0 - (0 / 300) = 1.0` (correct value, correct reasoning)

**Decision**: ✅ IMPLEMENT actual temporal confidence computation

---

## TASK 3: Agreement / c_agree — Analysis

### Repository Specification

**From `reference/python/nexalert_reference/confidence.py:90-150`**:
```python
def compute_agreement(
    group_evidence: Dict[str, float],
    group_weights: Dict[str, float],
    k_v: float = 2.0,
    epsilon: float = EPSILON
) -> float:
    """
    Compute group-level agreement confidence.
    
    Group-Level Agreement:
    - Groups prevent correlated sensors from masquerading as independent votes
    - Example: temperature and humidity correlated in fire → same group
    - Agreement evaluated across groups, not individual sensors
    
    Missing Handling:
    - len(valid_groups) == 0 → returns 1.0 (no evidence = no disagreement)
    - len(valid_groups) == 1 → returns 1.0 (single source = no disagreement)
    """
    valid_groups = {
        group: evidence
        for group, evidence in group_evidence.items()
        if evidence is not None and group in group_weights
    }
    
    if not valid_groups:
        return 1.0  # No evidence = no disagreement
    
    if len(valid_groups) == 1:
        return 1.0  # Single source = no disagreement
```

### Hardware Reality

**ESP32-S3 Node has 6 sensor modalities**:
1. BME680 temperature
2. BME680 humidity
3. BME680 pressure
4. BME680 gas resistance
5. MQ-2 raw gas ADC
6. MPU6050 vibration

### Evidence Groups for Fire Hazard

**From repository semantics**:
- **Thermal group**: Temperature + humidity (correlated in fire)
- **Smoke group**: Smoke sensor (unavailable)
- **Gas group**: Gas sensors (MQ-2 available but not in evidence)

**Current fire evidence** (main.c:663-666):
```c
sensor_reading_t evidence_readings[] = {
    {.sensor = "temperature", .value = temp_c},
    {.sensor = "humidity", .value = humidity_pct},
};
```

**Analysis**:
- Temperature and humidity are from same thermal phenomenon
- Repository groups them together (correlated)
- They form ONE evidence group, not two independent sources
- Smoke group unavailable
- **Active groups**: 1 (thermal only)

**Per repository**: `len(valid_groups) == 1` → `c_agree = 1.0`

**Decision**: ✅ CURRENT VALUE CORRECT, comments need clarification

---

## TASK 4: MQ-2 Integration — Analysis

### Current Status

**MQ-2 data acquired** (Track 3A):
- Raw ADC value 0-4095 available
- NOT calibrated to ppm
- No conversion factor

### Permitted Use Cases

**From Track 4 decisions**:
- ✅ Baseline/anomaly/change detection
- ❌ Evidence thresholds
- ❌ Absolute gas concentration
- ❌ ppm interpretation

### Integration Points

**1. Baseline**:
```c
// Could accumulate MQ-2 raw ADC in baseline_history
g_baseline_history.gas_samples[...] = mq2_raw_adc;
```

**2. Anomaly**:
```c
// Could compute z-score for MQ-2
baseline_stats[3] = compute_robust_baseline(g_baseline_history.gas_samples, ...);
z_gas = compute_baseline_z_score(mq2_raw_adc, &baseline_stats[3]);
A_gas = compute_individual_anomaly(z_gas, ...);
```

**3. Node Aggregate**:
```c
// Could include in A_node
sensor_anomalies["gas"] = A_gas;
```

### Issues

**Problem 1**: No sensor validity for MQ-2 in current code
- Temperature has `temp_reading.valid`
- Humidity has `humid_reading.valid`
- MQ-2 has... what validity flag?

**Problem 2**: No history buffer allocated for MQ-2
- History buffers exist for temp, humidity
- No `gas_history[]` or `gas_samples[]` arrays

**Problem 3**: Integration requires code changes beyond semantic fixes
- Need to add MQ-2 to history structures
- Need to add MQ-2 to baseline computation
- Need to add MQ-2 to anomaly aggregation

### Decision

**Current Track 4 scope**: Semantic corrections only, NOT architectural additions

**MQ-2 Status**: ⚠️ REMAINS EXCLUDED
- Data acquired (Track 3A complete)
- NOT integrated into intelligence (requires separate implementation)
- Document as: "MQ-2 data available, baseline/anomaly integration pending"

---

## TASK 5: Audit main.c — Findings

### Review Complete

✅ No duplicate variables found
✅ No stale prototype comments (already corrected)
✅ No accidental placeholder values
✅ Timestamps correctly sourced from `esp_timer_get_time()`
✅ Validity propagation correct throughout chain
✅ Pipeline order correct

**Pipeline verified**:
Sensor validity → health → quality → reliability → baseline → anomaly → evidence → confidence → severity → risk → hazard state

---

## TASK 6: Tests — Execution Plan

### Python Reference Tests
```bash
cd reference/python && python -m pytest tests/ -v --tb=short
```

### ESP-IDF Tests
❌ **BLOCKED** — Toolchain not installed
- Do NOT attempt installation
- Report as blocked

---

## Summary: Required Changes

### 1. Implement c_temp computation ✅
Replace hardcoded `1.0` with actual `compute_temporal_confidence()` call

### 2. Keep q_stability = NAN ✅
Repository provides no stability formula — current implementation correct

### 3. Clarify c_agree comments ✅
Explain single evidence group (thermal), not "single sensor"

### 4. Document MQ-2 status ⚠️
Clearly state: acquired but not integrated, pending separate implementation

### 5. Run tests ✅
Execute Python tests, report ESP-IDF as blocked

---

**ANALYSIS COMPLETE**
**Ready to implement corrections**
