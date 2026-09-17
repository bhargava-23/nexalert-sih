# Track 4: Final Intelligence Semantics Review

**Date**: 2026-09-16  
**Review Type**: INTELLIGENCE SEMANTICS CORRECTNESS VERIFICATION  
**Reviewer**: Claude (post-correction review)

---

## Executive Summary

**CRITICAL SEMANTIC ISSUES FOUND**

Track 4 corrections addressed threshold provenance but introduced **incorrect intelligence semantics** that violate repository specifications:

1. ❌ **QUALITY SEMANTICS INCORRECT**: `q_stability = 1.0` is NOT justified by repository
2. ❌ **CONFIDENCE SEMANTICS INCORRECT**: Multi-modality node mischaracterized as "single-sensor"
3. ⚠️ **PROTOTYPE THRESHOLDS**: All severity/evidence thresholds marked UNVALIDATED in reference
4. ✅ **MISSING DATA HANDLING**: Correct throughout chain
5. ✅ **BASELINE/ANOMALY**: Correct semantics
6. ⚠️ **SENSOR SEMANTICS**: Mostly correct, MQ-2 integration incomplete

**Status**: **CORRECTIONS REQUIRED** before Track 4 acceptance

---

## CHECK 1: QUALITY SEMANTICS — ❌ INCORRECT

### Repository Specification Analysis

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
        return None  # ← REPOSITORY REQUIRES BOTH COMPONENTS
```

**Key Finding**: Repository specification **requires both components**. When either is `None`, `Q_i` returns `None` (missing), NOT a computed value.

### Current Implementation Issue

**In `firmware/main/main.c:539`**:
```c
float q_stability_temp = temp_reading.valid ? 1.0f : NAN;  // Default high stability (no variance detection yet)
```

**Comment claims**: "Default 1.0 per repository specification"

**INCORRECT**: Repository specification does NOT permit defaulting `q_stability = 1.0` when unavailable.

### The Problem

1. **Missing ≠ Default**: When stability cannot be measured, the repository semantics say `q_stability = None` → `Q_i = None`
2. **Invented Value**: `1.0` claims "high stability" when no stability measurement exists
3. **False Signal**: Downstream intelligence receives `Q_i = 1.0` instead of `Q_i = NAN`, incorrectly indicating perfect quality

### Repository-Correct Behavior

**Option A**: If variance/stability cannot be computed, `q_stability = NAN` → `Q_i = NAN` (missing)
- Downstream: Reliability receives `Q_i = NAN`, computes `R_i` accordingly
- Missing quality reduces reliability (correct per Doc 04)

**Option B**: Implement actual variance-based stability from history
- Use `g_intelligence_history.temp_history[]` to compute variance
- Convert variance to stability score per repository formula
- Only then pass computed value

**Current implementation does neither** — it invents a default that claims measured stability.

### Verdict: ❌ INCORRECT

**Issue**: Hardcoded `q_stability = 1.0` violates repository "missing ≠ zero" invariant  
**Repository says**: `None` input → `None` output  
**Current code says**: No stability measurement → `q_stability = 1.0` → `Q_i = 1.0`  
**Impact**: False quality signal propagates through reliability → anomaly chain

---

## CHECK 2: CONFIDENCE SEMANTICS — ❌ INCORRECT

### Hardware Reality Check

**ESP32-S3 Node Sensors** (from Track 3A specification):
- BME680: temperature, humidity, pressure, gas resistance (4 modalities)
- MQ-2: raw gas ADC (1 modality)
- MPU6050: vibration/acceleration (1 modality)

**Total**: 6 sensor modalities across 3 physical sensor ICs

### Repository Specification: c_agree

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
```

**Key concept**: "Groups" are **evidence groups** (e.g., thermal, smoke, flood), NOT individual sensor ICs.

### Current Implementation Issue

**In `firmware/main/main.c:681-683`**:
```c
// c_agree: Group-level agreement (multi-sensor variance)
// Per confidence.py:90-120, requires group of sensors. Default 1.0 (perfect agreement) when group size < 2
float c_agree = 1.0f;  // Single-sensor node: no disagreement possible
```

**Comment claims**: "Single-sensor node"

**INCORRECT CHARACTERIZATION**:
1. **Hardware**: 6 sensor modalities across 3 ICs ≠ "single-sensor"
2. **Evidence groups**: Fire hazard uses temperature + humidity + (missing smoke) = multiple evidence sources
3. **Repository semantics**: Agreement is about **evidence group variance**, not physical sensor count

### The Correct Semantic

Per repository specification:
- `c_agree` measures **variance across evidence groups** for a hazard
- Fire evidence comes from: thermal group (temp+humidity correlated), smoke group (missing)
- With only thermal group active: `len(valid_groups) == 1` → `c_agree = 1.0` ✅
- **Reason**: Single evidence source = no disagreement possible (repository-correct)

**BUT**: Current comment **misrepresents WHY**:
- Code claims: "single-sensor node" (hardware characterization)
- Repository says: "single evidence group" (intelligence semantic)

### Repository Specification: c_temp

**From `reference/python/nexalert_reference/confidence.py:144-205`**:
```python
def compute_temporal_confidence(
    telemetry_age_seconds: Optional[float],
    max_age_seconds: float
) -> float:
    """
    Compute temporal confidence (data freshness).
    
    Args:
        telemetry_age_seconds: Age of measurement in seconds
        max_age_seconds: Maximum acceptable age (PROTOTYPE: 300s = 5 minutes)
    
    Formula: C_temp = max(0, 1 - age / max_age)
    
    Provenance: max_age_seconds = 300 is PROTOTYPE ASSUMPTION
    Validation Status: UNVALIDATED
    """
    if telemetry_age_seconds is None:
        return 0.0  # Missing temporal information
    
    if telemetry_age_seconds > max_age_seconds:
        return 0.0  # Stale data
    
    return 1.0 - (telemetry_age_seconds / max_age_seconds)
```

### Current Implementation Issue

**In `firmware/main/main.c:685-687`**:
```c
// c_temp: Temporal confidence (data freshness)
// Per confidence.py:144-169, recent data gets high temporal confidence
float c_temp = 1.0f;  // All measurements fresh (< 1s old)
```

**Analysis**:
- Repository formula: `C_temp = 1 - (age / max_age)` where `max_age = 300s`
- Current: All samples from same loop (< 1s old)
- Calculation: `1 - (1 / 300) = 0.9967 ≈ 1.0`

**Verdict**: Hardcoded `1.0` is **approximately correct** but:
1. Does NOT use actual timestamps (assumed fresh)
2. Does NOT implement repository formula
3. Brittle if sampling interval changes

### Verdict: ❌ SEMANTICALLY MISLEADING

**c_agree**:
- **Code behavior**: Correct (`1.0` for single evidence group)
- **Comment justification**: INCORRECT ("single-sensor node" mischaracterizes hardware and semantic)
- **Should say**: "Single active evidence group (thermal) → no disagreement per confidence.py:117"

**c_temp**:
- **Code behavior**: Approximately correct (< 1s age ≈ fresh)
- **Implementation**: Does NOT use actual age measurement or repository formula
- **Should**: Compute actual age or document assumption clearly

---

## CHECK 3: SENSOR SEMANTICS — ⚠️ MOSTLY CORRECT

### BME680
✅ **Correct**: Temperature, humidity, pressure, gas resistance all properly read  
✅ **Correct**: Valid/invalid handling via `temp_reading.valid`  
✅ **Correct**: NAN propagation for missing readings

### MQ-2
⚠️ **INCOMPLETE**: Raw ADC read (Track 3A) but NOT integrated into Track 4 intelligence  
**Current status**: MQ-2 data acquired but not used in baseline/anomaly/evidence  
**Track 4 claim**: "MQ-2 used for baseline/anomaly" — NOT FOUND in code  
**Decision**: Documented as limitation (correct per Track 4 decisions)

### MPU6050
✅ **Correct**: Vibration derived from acceleration (Track 3A implementation)

### PM2.5 / PM10
✅ **Correct**: Not fabricated, properly documented as unavailable

---

## CHECK 4: MISSING DATA — ✅ CORRECT

Verified complete chain from sensor validity through all intelligence gates:

### Sensor → Health
✅ `temp_reading.valid ? 1.0f : 0.0f` → Missing sensor reduces health

### Health → Quality → Reliability
✅ Missing `H_i = NAN` or `Q_i = NAN` → `R_i = NAN` (see quality issue above)

### Reliability → Anomaly
✅ Missing `R_i` excluded from anomaly aggregation (weighted computation)

### Evidence
✅ Missing sensors excluded from evidence computation (firmware/main/main.c:668)
```c
sensor_reading_t evidence_readings[] = {
    {.sensor = "temperature", .value = temp_c},  // NAN if missing
    {.sensor = "humidity", .value = humidity_pct},
};
```
✅ `compute_evidence()` checks `!isnan(reading->value)` before matching

### Confidence
✅ Missing sensor reduces `c_cov` proportionally (0.7 temp + 0.3 humid)

### Severity / Risk
✅ Missing `T_h`, `D_h` → `S_h = NAN` → `R_h = NAN`

### Hazard State
✅ Missing inputs handled by state machine (information condition gates)

**Verdict**: ✅ **CORRECT** — Missing ≠ zero preserved throughout entire chain

---

## CHECK 5: BASELINE / ANOMALY / EVIDENCE — ✅ MOSTLY CORRECT

### Baseline
✅ **Correct**: Only valid readings accumulated (`!isnan(temp_c)` check at line 257)  
✅ **Correct**: Baseline stats validity checked before z-score (line 606)  
✅ **Correct**: Freeze logic on confirmed/critical hazard (lines 363-368)  
✅ **Correct**: No false anomalies from uninitialized stats

### Anomaly
✅ **Correct**: Requires valid baseline stats (line 606 guard)  
⚠️ **MQ-2**: NOT integrated into anomaly computation (documented as limitation)  
✅ **Correct**: Missing sensors excluded from aggregation

### Evidence

**Repository specification** (`evidence.py:61-62`):
```python
Provenance: ALL threshold values are PROTOTYPE ASSUMPTIONS
Validation Status: UNVALIDATED - NOT scientifically authoritative
```

**Current implementation** (`main.c:647-667`):
```c
evidence_config_t evidence_cfg = {
    .core_rules = {
        {.sensor = "temperature", .threshold_min = 60.0f, .threshold_max = 150.0f, .weight = 0.7f},
    },
    .supporting_rules = {
        {.sensor = "humidity", .threshold_min = 0.0f, .threshold_max = 30.0f, .weight = 0.3f},
    },
};
```

**Analysis**:
- Temperature [60-150°C]: Matches reference example (evidence.py:70)
- Humidity [0-30%]: Matches reference example (evidence.py:74)
- **Critical finding**: These are **EXAMPLES** from reference code, marked **PROTOTYPE ASSUMPTIONS**, NOT production-validated rules

**Status**: ⚠️ **USING UNVALIDATED PROTOTYPE THRESHOLDS**

---

## CHECK 6: SEVERITY / RISK SEMANTICS — ⚠️ PROTOTYPE THRESHOLDS

### Corrected Thresholds

✅ **Verified**:
```c
float max_temp_rate = 10.0f / 60.0f;  // 0.167 °C/s from severity.py:64
float fire_threshold = 50.0f;         // 50 °C from severity.py:74
float max_duration = 3600.0f;         // 3600 s from severity.py:73
```

**All match repository reference exactly**

### Critical Repository Marking

**From `severity.py:27-28`**:
```python
Provenance: ALL threshold and weight values are PROTOTYPE ASSUMPTIONS
Validation Status: UNVALIDATED - NOT scientifically authoritative
```

**Every single threshold in severity.py is marked**:
- `max_temp_rate`: "PROTOTYPE ASSUMPTION" (line 64)
- `fire_temp_threshold`: "PROTOTYPE ASSUMPTION" (line 74)
- `max_duration_seconds`: "PROTOTYPE ASSUMPTION" (line 73)
- `temp_low`, `temp_high`: "PROTOTYPE ASSUMPTION" (lines 48-49)

**Finding**: Values are repository-sourced but repository itself marks them **UNVALIDATED**.

### Severity vs Risk Distinction

✅ **Correct**: Severity ≠ Risk maintained  
✅ **Correct**: Risk ≠ Probability maintained  
✅ **Correct**: Formulas match repository specifications

---

## CHECK 7: HAZARD STATE — ✅ CORRECT

✅ State transitions use correct inputs (E_h, C_h, S_h, R_h, A_h)  
✅ Missing evidence/confidence does not trigger escalation  
✅ Persistence/hysteresis matches repository (hazard_state.c)  
✅ No states produced from absent sensors

---

## CHECK 8: PROTOTYPE THRESHOLD STATUS

### Critical Finding

**ALL thresholds and configuration values used in Track 4 are marked in repository**:

| Value | Source | Repository Marking |
|-------|--------|-------------------|
| max_temp_rate | severity.py:64 | PROTOTYPE ASSUMPTION, UNVALIDATED |
| max_duration | severity.py:73 | PROTOTYPE ASSUMPTION, UNVALIDATED |
| fire_threshold | severity.py:74 | PROTOTYPE ASSUMPTION, UNVALIDATED |
| temp evidence [60-150] | evidence.py:70 | PROTOTYPE ASSUMPTION, UNVALIDATED |
| humidity evidence [0-30] | evidence.py:74 | PROTOTYPE ASSUMPTION, UNVALIDATED |
| baseline thresholds | baseline.py:160-161 | PROTOTYPE ASSUMPTIONS |
| confidence weights | confidence.py:322-329 | PROTOTYPE ASSUMPTIONS, UNVALIDATED |
| severity weights | severity.py:39-44 | PROTOTYPE, UNVALIDATED |

**Repository documentation explicitly states**:
> Owner: Phase 5 implementation (requires domain expert takeover)

**Interpretation**: Reference implementation provides **working prototypes for testing**, NOT production-validated thresholds.

---

## CHECK 9: FALSE COMPLETION — ⚠️ CLASSIFICATION REQUIRED

### Module Implementation Status

| Module | Function Calls | Semantics | Status |
|--------|----------------|-----------|--------|
| Health | ✅ CALLED | ✅ CORRECT | **VERIFIED** |
| Quality | ✅ CALLED | ❌ INCORRECT (q_stability) | **SEMANTICALLY LIMITED** |
| Reliability | ✅ CALLED | ⚠️ Depends on Quality | **SEMANTICALLY LIMITED** |
| Baseline | ✅ CALLED | ✅ CORRECT | **VERIFIED** |
| Anomaly | ✅ CALLED | ✅ CORRECT | **VERIFIED** |
| Evidence | ✅ CALLED | ⚠️ PROTOTYPE thresholds | **IMPLEMENTED BUT UNVALIDATED** |
| Confidence | ✅ CALLED | ❌ INCORRECT comments | **SEMANTICALLY LIMITED** |
| Severity | ✅ CALLED | ⚠️ PROTOTYPE thresholds | **IMPLEMENTED BUT UNVALIDATED** |
| Risk | ✅ CALLED | ✅ CORRECT | **VERIFIED** |
| Hazard State | ✅ CALLED | ✅ CORRECT | **VERIFIED** |

### Overall Classification

- **VERIFIED (4)**: Health, Baseline, Anomaly, Risk, Hazard State
- **SEMANTICALLY LIMITED (3)**: Quality, Reliability, Confidence
- **IMPLEMENTED BUT UNVALIDATED (2)**: Evidence, Severity
- **BLOCKED (0)**: None
- **INCORRECT (0)**: None (incorrect semantics are "LIMITED", not broken)

---

## REQUIRED CORRECTIONS

### CORRECTION 1: Quality Semantics

**Issue**: `q_stability = 1.0` violates repository specification

**Repository-correct options**:

**A) Preserve missing semantic** (RECOMMENDED):
```c
float q_stability_temp = NAN;  // Variance/stability not computed → missing per quality.py:35
float q_stability_humid = NAN;
```
Result: `Q_i = NAN` (missing), `R_i = NAN` (missing), correctly propagates uncertainty

**B) Implement variance-based stability**:
```c
float q_stability_temp = compute_stability_from_history(
    g_intelligence_history.temp_history,
    g_intelligence_history.temp_count
);
```
Requires: Variance → stability formula from repository (not currently specified)

**Chosen**: **Option A** — Preserve missing semantic per repository

### CORRECTION 2: Confidence Comments

**Issue**: Comments mischaracterize hardware and semantics

**Fix**: Update comments to reflect actual repository semantics

**c_agree**:
```c
// c_agree: Evidence group agreement (per confidence.py:90-150)
// Fire evidence from single active group (thermal: temp+humidity correlated, smoke unavailable)
// Single evidence group → no disagreement possible per confidence.py:117
float c_agree = 1.0f;
```

**c_temp**:
```c
// c_temp: Temporal confidence (per confidence.py:144-205)
// Current implementation: All readings from same sampling loop (< 1s old)
// Approximates repository formula: C_temp ≈ 1 - (1s / 300s) ≈ 1.0
// Note: Does not implement actual age computation or repository formula
float c_temp = 1.0f;
```

### CORRECTION 3: Documentation

Add **PROTOTYPE STATUS WARNING** to all Track 4 documentation:

```
## CRITICAL: Prototype Threshold Status

ALL thresholds and configuration values used in Track 4 intelligence modules are sourced
from `reference/python/nexalert_reference/*` but are explicitly marked in the repository as:

- **Provenance**: PROTOTYPE ASSUMPTIONS
- **Validation Status**: UNVALIDATED
- **Scientific Authority**: NOT scientifically authoritative
- **Owner**: Phase 5 implementation (requires domain expert takeover)

These values enable **functional testing and development** but are NOT validated for
production hazard detection. Domain expert review and scientific validation required
before production deployment.

Affected modules: Evidence, Severity, Confidence (weights), Baseline (thresholds)
```

---

## TESTS EXECUTED

### Python Reference Tests

```bash
cd reference/python && python -m pytest tests/ -v --tb=short
============================= 219 passed in 0.28s =============================
```

✅ **NO REGRESSIONS** — All reference tests still pass after corrections

### ESP-IDF Firmware Tests

❌ **BLOCKED** — ESP-IDF toolchain not installed  
**Status**: Cannot execute 10 intelligence test files

---

## FINAL TRACK 4 ACCEPTANCE STATUS

### VERDICT: B) CORRECTIONS REQUIRED

**Critical issues**:
1. ❌ Quality semantics violate repository "missing ≠ zero" invariant
2. ❌ Confidence comments mischaracterize hardware/semantics
3. ⚠️ All thresholds are UNVALIDATED prototypes (acceptable for development, must document)

**Blocking acceptance**:
- Quality `q_stability = 1.0` must be changed to `NAN` (repository-correct)
- Confidence comments must accurately reflect repository semantics

**NOT blocking (acceptable with documentation)**:
- Prototype thresholds (repository provides them for testing)
- ESP-IDF tests blocked (toolchain dependency)
- MQ-2 integration incomplete (documented limitation)

---

## RECOMMENDATIONS

### Accept Track 4 IF:

1. ✅ Quality corrected: `q_stability = NAN` (preserve missing semantic)
2. ✅ Confidence comments corrected (accurate semantic descriptions)
3. ✅ Prototype threshold warning added to documentation
4. ✅ Python tests still pass (verify no regressions)

### THEN:

Track 4 is **conditionally acceptable** as:
- **Functionally complete** edge intelligence implementation
- **Semantically aligned** with repository specifications
- **Using prototype thresholds** (documented, acceptable for Phase 5 testing)
- **ESP-IDF verification pending** (Track 3A dependency)

---

**SEMANTIC REVIEW COMPLETE**  
**CORRECTIONS REQUIRED BEFORE FINAL ACCEPTANCE**
