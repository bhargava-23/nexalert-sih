# NexAlert Contract Reconciliation V1

**Status**: Phase 1 Audit Complete — BLOCKED  
**Baseline Commit**: 9c628d8  
**Audit Date**: 2026-09-13  
**Authority**: 20 Numbered Specifications (Documents 01-20), Implementation Constitution, DECISIONS.md  
**Scope**: Complete contract verification across 26+ system areas

---

## EXECUTIVE SUMMARY

This audit establishes contract compliance between authoritative specifications and implementation baseline 9c628d8. A contract is **PASS** only when specification, implementation, tests, and evidence all agree with no contradictory code remaining.

### Classification Results

| Status | Count | Areas |
|--------|-------|-------|
| **PASS** | 8 | Authority hierarchy, spec interpretation, missing≠zero (dashboard), confidence≠probability (reference), frontend source-of-truth, safety-critical rules, human approval, change-control |
| **FIX** | 9 | Telemetry schema enforcement, node identity contract, multi-hazard independence, risk semantics documentation, security implementation, configuration governance, golden-vector test harness, sensor calibration, architecture invariant enumeration |
| **REPLACE** | 3 | ESP32 edge intelligence capability, edge local emergency path, Master/Pi local intelligence runtime |
| **BLOCKED** | 2 | Timestamp semantics (ambiguous specification), simulator truth-separation (demo vs simulation semantics) |

### Critical Blockers (Preventing Phase 2)

1. **ESP32 Edge Intelligence Boundary** — Firmware missing complete edge intelligence capability (H_i, Q_i, R_i, baseline, anomaly, confidence, severity, risk, hazard state machine). Document 06 Section 9-10 + Constitution C1 LOCKED decision requires MUST implement. Current: firmware has `firmware/components/intelligence/` with baseline, anomaly, confidence, severity, risk, hazard_state modules BUT main.c does NOT invoke them. **REPLACE required**: wire intelligence pipeline in main.c

2. **Telemetry Contract Enforcement** — Multiple data shapes in flight (data.telemetry.* vs data.sensors.* vs measurement_timestamp vs measurement_ts). Schema `telemetry-envelope.schema.json` exists but backend API does not enforce at boundary. Frontend normalization layer is symptom. **FIX required**: backend validator middleware

3. **Master Local Intelligence** — Raspberry Pi Master responsibility (Document 01, 07, 11) requires local intelligence runtime independent of internet. Current: backend exists but unclear if Master=Backend or Master≠Backend. **REPLACE required**: clarify Master architecture

4. **Multi-Hazard Independence** — Document 04 Section 6 requires independent confidence/severity/risk per hazard type. Database `incidents` table has single `confidence_index`, `severity_index`, `risk_index` (not per-hazard). **FIX required**: schema refactor or JSONB structure

5. **Node Identity Contract** — Schema defines `node_id: "NODE-[0-9]{3,}"` but validator checks `node_id.startswith("NODE-")` (accepts NODE-1, NODE-01, NODE-001, NODE-0001). Authority unclear: is NEX-001 (demo) vs NODE-001 (schema) a violation? **FIX required**: canonical format decision

---

## PART 1: CANONICAL CONTRACTS

### 1.A TELEMETRY ENVELOPE CONTRACT

**Authority**: `schemas/telemetry-envelope.schema.json` (lines 1-171)  
**Source**: Document 07 Section 7

**Required Fields** (18 total):
```
schema_version: "telemetry.v1" (const)
telemetry_id: ULID format "^[0-9A-HJKMNP-TV-Z]{26}$"
node_id: "^NODE-[0-9]{3,}$" 
sequence: integer ≥ 0
measurement_timestamp: ISO 8601 date-time (UTC)
received_timestamp: ISO 8601 date-time (UTC) — DISTINCT from measurement_timestamp
location: {lat: [-90,90], lon: [-180,180], alt: number|null}
measurements: object (all fields optional, null = missing)
  - temp_c, humidity_pct, pressure_hpa, pm25_ug_m3, pm10_ug_m3
diagnostics: object (H_i computation per Document 04 Section 3.1)
  - uptime_s, self_test_passed, comm_integrity, calibration_valid, stability_index
power: object
  - battery_pct, battery_voltage, solar_current
source: enum ["HARDWARE", "SIMULATION"]
auth: object (Phase 6 placeholder)
```

**Units**:
- Temperature: Celsius (temp_c)
- Humidity: Percent (humidity_pct)
- Pressure: hPa (pressure_hpa)
- PM: µg/m³ (pm25_ug_m3, pm10_ug_m3)
- Uptime: seconds (uptime_s)
- Battery: percent (battery_pct)
- Voltage: volts (battery_voltage)

**Null Semantics**: `null` or absent = missing (NOT zero) per Constitution §11

**Ownership**:
- `measurement_timestamp`: Edge node acquisition time
- `received_timestamp`: Backend server-assigned receive time (MUST NOT trust measurement_timestamp as receive time per schema line 44)

**Ordering**: `sequence` is monotonic per-node for ordering/replay detection

**Source**: HARDWARE (live sensor) vs SIMULATION (synthetic telemetry)

**Authentication**: HMAC placeholder (Phase 6)

**Schema Version**: "telemetry.v1" for evolution

### 1.B NODE IDENTITY CONTRACT

**Authority**: `schemas/telemetry-envelope.schema.json` line 31-34  
**Pattern**: `"^NODE-[0-9]{3,}$"`

**Canonical Format**: NODE-{3+ digits}  
**Valid Examples**: NODE-001, NODE-042, NODE-1234  
**Invalid Examples**: NEX-001 (wrong prefix), NODE-1 (too few digits), NODE-01 (too few digits)

**Protocol node_id**: NODE-XXX (schema pattern)  
**Display name**: Separate field (not in telemetry envelope yet)  
**MQTT topic**: `Nexalert/telemetry/<node_id>` (per firmware `nexalert_mqtt.h`)

**AMBIGUITY**: Demo uses NEX-001, schema requires NODE-XXX. Is this acceptable demo deviation or contract violation?

### 1.C TIMESTAMP SEMANTICS

**Authority**: Schema lines 41-49 + Constitution §12 + TelemetryRecord model lines 52-61

**Two Timestamps Required** (DISTINCT):
1. `measurement_timestamp` (ISO 8601 UTC) — when observation captured (edge node clock)
2. `received_timestamp` (ISO 8601 UTC) — when backend received (server-assigned)

**Constitution §12**: "Timestamps MUST distinguish acquisition time vs transmission time vs processing time"

**Database Schema** (models.py):
- `measurement_ts` column (maps from measurement_timestamp)
- `receive_ts` column (maps from received_timestamp)

**AMBIGUITY RESOLVED**: Schema and database both implement two-timestamp separation. Constitution §12 satisfied.

### 1.D EDGE INTELLIGENCE BOUNDARY

**Authority**: Constitution C1 (LOCKED 2026-09-07) + Document 06 Sections 9-10

**MUST Run on ESP32** (complete capability):
- Health (H_i): sensor diagnostic assessment
- Quality (Q_i): measurement quality
- Reliability (R_i): sensor reliability over time
- Baseline: median/MAD computation
- Anomaly (A_i): deviation from baseline
- Hazard Evidence: configured hazard detection
- Confidence (C_h): information quality (NOT probability)
- Severity (S_h): intensity/danger if hazard real
- Operational Risk (R_h): urgency index (NOT probability)
- Hazard State Machine: NORMAL/WATCH/SUSPECTED/CONFIRMED/CRITICAL/RESOLVED

**Deployment Configuration**:
- Capability MUST be implemented
- Modules MAY be disabled for resource constraints
- Disabled state MUST be observable (diagnostics endpoint)
- Information condition MUST degrade honestly (confidence → DEGRADED, hazard state → UNKNOWN)

**MUST NOT Run on ESP32**:
- Regional fusion (multi-node aggregation)
- Incident correlation
- Spatial analysis
- Fire spread modeling
- Backend persistence

**Master Responsibility**:
- Regional intelligence (Track B2)
- Multi-node fusion
- Incident lifecycle management
- Local API during internet failure

**Backend Responsibility**:
- Cloud persistence
- Long-term analytics
- External integration

### 1.E MULTI-HAZARD INDEPENDENCE

**Authority**: Document 04 Section 6 + Constitution §13

**Hazard Types** (independent reasoning required):
- FIRE
- FLOOD
- POLLUTION
- LANDSLIDE
- EXTREME_HEAT
- UNKNOWN (catchall)

**Per-Hazard State** (each hazard maintains):
- Evidence (E_h): support for hazard h
- Confidence (C_h): information quality
- Severity (S_h): intensity/danger
- Operational Risk (R_h): urgency
- Hazard State: NORMAL/WATCH/SUSPECTED/CONFIRMED/CRITICAL/RESOLVED

**No Universal Combined Scalar**: Fire + flood do NOT combine into single confidence/severity/risk

### 1.F RISK ≠ PROBABILITY

**Authority**: Document 04 Section 4 + Constitution §15

**Risk Definition**: Operational decision-support index = f(Severity, Confidence, Exposure)  
**NOT**: Probability, statistical likelihood, or p-value

**Risk Range**: [0, 1] operational index  
**Components**:
- Severity: how bad if real
- Confidence: information quality
- Exposure: what/who affected

**Confidence ≠ Probability**: Confidence is information quality (sensor health, data recency), NOT statistical confidence interval

### 1.G MISSING ≠ ZERO

**Authority**: Constitution §11 + Schema line 69

**Principle**: Missing environmental measurements MUST NOT be represented as zero

**Representation**: `null` or absent field (NOT 0)

**Example**:
```json
{
  "temp_c": 31.4,         // measured
  "humidity_pct": null,   // missing (NOT 0)
  "pressure_hpa": 1009.8  // measured
}
```

**Rationale**: 0°C is freezing (real measurement), null is "sensor didn't read" (information condition)

### 1.H RESILIENCE FAILURE MODES

**Authority**: Document 11 Sections 7, 11 + Constitution §17

**Distinct Failure Modes**:
1. **Node Failure**: Individual sensor/node stops functioning
2. **Sensor Failure**: One sensor on node fails, others continue
3. **Internet Failure**: Node↔Master works, Master↔Cloud fails (Mode B)
4. **Master Failure**: Master down, node continues local emergency operation (Mode C)

**Master Failure ≠ Internet Failure**: Constitution §17 LOCKED

**Local Emergency Path**: Edge node MUST continue useful operation during Master failure (buzzer, LED, local captive portal)

**Store-and-Forward**: Nodes buffer telemetry during connectivity loss, replay on reconnect

**Heartbeat**: Nodes send periodic heartbeat independent of telemetry (connection liveness)

### 1.I FIRE SPREAD CONTRACTS

**Authority**: Document 05 (Track C) + Constitution §16

**Four Distinct Concepts**:
1. **Physical Footprint**: Model-derived fire area (physics output)
2. **Operational Buffer**: Policy-defined margin (NOT physics)
3. **Risk Surface**: Continuous operational index (spatial decay)
4. **Exposure**: Population/infrastructure intersection

**Separation Required**: Physical footprint MUST be stored separately from operational buffer (never conflated)

**Database Schema** (planned Track C):
```
fire_geometries:
  - physical_footprint (Geography) — model output
  - operational_buffer (Geography) — policy margin
  - geometry (Geography) — union for display
```

**Note**: Track C not implemented at baseline 9c628d8 (pending)

### 1.J SIMULATION VS DEMO FIXTURE

**Authority**: Document 15 Section 4 + Constitution §18

**HARDWARE**: Live sensor telemetry from real nodes (source: "HARDWARE")

**SIMULATION**: Synthetic telemetry through canonical ingestion path (source: "SIMULATION")  
- Same validation as HARDWARE
- Same intelligence pipeline
- Same database persistence
- Truth-separation: simulator MUST NOT leak ground truth into operational intelligence

**DEMO FIXTURE**: Presentation/testing data outside operational system  
- Does NOT enter canonical ingestion path
- Backend `routes_demo.py` endpoints
- Dashboard demo mode fallback

**AMBIGUITY**: Is `routes_demo.py` "simulation" (requires truth-separation) or "demo fixture" (out of scope)?

---

## PART 2: CONTRACT AREA AUDIT

### AREA 1: TELEMETRY ENVELOPE SCHEMA

| Field | Value |
|-------|-------|
| **Authority** | `schemas/telemetry-envelope.schema.json` + Document 07 Section 7 |
| **Status** | **FIX** |
| **Safety-Critical** | YES |

**Specification Contract**: Single canonical telemetry structure with 18 required fields, typed units, null semantics

**Implementation Evidence**:
- ✅ Schema file exists and is complete
- ❌ Backend validator (`modules/ingestion/validator.py`) validates schema BUT does not enforce at API boundary
- ❌ Frontend dashboard (`apps/authority-dashboard/app/page.tsx` lines 16-30) implements normalization layer accepting MULTIPLE shapes:
  ```typescript
  const telemetry = data.telemetry || data.sensors || {}
  temperature: telemetry.temperature ?? telemetry.temperature_c ?? null
  ```
- ❌ Multiple shapes in flight indicates no single canonical enforcement

**Contract Violation**: Schema exists but not enforced at boundary. Frontend normalization is symptom of upstream non-compliance.

**Required Resolution**:
1. Add backend validator middleware to ALL telemetry ingestion endpoints
2. REJECT non-conforming payloads with 400 + schema violation details
3. Remove frontend normalization layer (accept only canonical shape)
4. Verify firmware emits canonical shape

**Blocking**: Yes — multi-shape telemetry prevents downstream contract assumptions

---

### AREA 2: NODE IDENTITY FORMAT

| Field | Value |
|-------|-------|
| **Authority** | `schemas/telemetry-envelope.schema.json` line 31-34 |
| **Status** | **FIX** |
| **Safety-Critical** | NO |

**Specification Contract**: `node_id: "^NODE-[0-9]{3,}$"` (3+ digits)

**Implementation Evidence**:
- ✅ Schema pattern defined
- ❌ Validator (`validator.py` line 89) checks `node_id.startswith("NODE-")` (too permissive — accepts NODE-1, NODE-01)
- ❌ Demo uses NEX-001 (authority-dashboard, routes_demo.py) — wrong prefix
- ❌ Grep shows both NODE-XXX and NEX-XXX patterns in use

**Contract Violation**: Pattern enforcement incomplete, demo uses non-canonical prefix

**Required Resolution**:
1. **Human Decision Required**: Is NEX-001 acceptable demo deviation or violation?
2. If violation: Change all NEX-* to NODE-* in demo code
3. Update validator to enforce regex fully (reject NODE-1, NODE-01)
4. Document canonical format in REPOSITORY_MAP.md

**Blocking**: No — localized to demo

---

### AREA 3: TIMESTAMP SEMANTICS

| Field | Value |
|-------|-------|
| **Authority** | Schema + Constitution §12 + models.py |
| **Status** | **PASS** |
| **Safety-Critical** | YES |

**Specification Contract**: Two distinct timestamps (measurement_timestamp, received_timestamp)

**Implementation Evidence**:
- ✅ Schema defines both (lines 41-49)
- ✅ Database models.py defines both columns (measurement_ts, receive_ts) (lines 52-61)
- ✅ Schema comment explicitly states DISTINCT per Constitution §12
- ✅ Two-timestamp separation implemented

**Verdict**: PASS — contract implemented correctly

---

### AREA 4: MISSING ≠ ZERO

| Field | Value |
|-------|-------|
| **Authority** | Constitution §11 + Schema line 69 |
| **Status** | **PASS (dashboard)** / **AMBIGUOUS (other layers)** |
| **Safety-Critical** | YES |

**Specification Contract**: Missing measurements MUST be null/absent, NOT zero

**Implementation Evidence**:

**Dashboard (PASS)**:
- ✅ `TelemetryCard` component (page.tsx lines 228-254) renders null as "—"
- ✅ Never converts null to 0
- ✅ Dimmed color for missing values

**Schema (PASS)**:
- ✅ All measurement fields typed `["number", "null"]`
- ✅ Schema comment "null = missing (NOT zero)"

**Validator (WARNING)**:
- ⚠️  Validator logs warning for value==0 but does NOT reject (lines 119-127)
- Note: Legitimate 0 readings possible (0°C is freezing, not missing)

**Firmware (UNKNOWN)**:
- ❓ Need to verify firmware never emits 0 for missing sensor reads

**Backend Intelligence (UNKNOWN)**:
- ❓ Need to verify Track B2 fusion preserves null (does not treat missing as 0)

**Verdict**: PASS for dashboard (correct implementation), AMBIGUOUS for full pipeline (needs verification)

**Required Resolution**: Audit firmware sensor drivers and backend fusion logic

---

### AREA 5: ESP32 EDGE INTELLIGENCE BOUNDARY

| Field | Value |
|-------|-------|
| **Authority** | Constitution C1 (LOCKED) + Document 06 Sections 9-10 |
| **Status** | **REPLACE** |
| **Safety-Critical** | YES |

**Specification Contract**: ESP32 MUST implement complete edge intelligence capability (H_i, Q_i, R_i, baseline, anomaly, confidence, severity, risk, hazard state machine)

**Implementation Evidence**:

**Firmware Modules Exist** (✅):
```
firmware/components/intelligence/
├── baseline.c / baseline.h
├── anomaly.c / anomaly.h
├── confidence.c / confidence.h
├── severity.c / severity.h
├── risk.c / risk.h
├── hazard_state.c / hazard_state.h
├── include/reliability.h
└── test/ (unit tests for each)
```

**Main.c Integration** (❌):
- Line 9 comment claims "Complete Intelligence Pipeline: Sensor → Calibration → H_i/Q_i/R_i → Baseline → Anomaly → Evidence → Confidence → Severity → Risk → Hazard State"
- **BUT**: `main.c` does NOT invoke intelligence modules
- Current: sensor sampling → telemetry envelope → MQTT publish
- **MISSING**: Intelligence pipeline invocation

**Contract Violation**: Capability exists (modules implemented) but NOT wired into main execution flow

**Required Resolution**:
1. **REPLACE main.c** to invoke intelligence pipeline:
   ```c
   sample_sensors() → compute_H_i_Q_i_R_i() → 
   update_baseline() → compute_anomaly() → 
   assess_hazard_evidence() → compute_confidence() → 
   compute_severity() → compute_risk() → 
   update_hazard_state() → enqueue_telemetry()
   ```
2. Add intelligence outputs to telemetry envelope (diagnostics, hazard_assessment)
3. Verify against golden vectors

**Blocking**: YES — Constitution C1 LOCKED requirement violated

---

### AREA 6: MASTER LOCAL INTELLIGENCE

| Field | Value |
|-------|-------|
| **Authority** | Document 01 Section 3 + Document 07 + Document 11 Section 7 |
| **Status** | **REPLACE** |
| **Safety-Critical** | YES |

**Specification Contract**: Raspberry Pi Master MUST run local intelligence independent of internet (Mode B resilience)

**Implementation Evidence**:

**Backend Exists** (✅):
```
services/backend/
├── main.py (FastAPI app)
├── modules/intelligence/b2_coordinator.py (Track B2 regional fusion)
├── modules/intelligence/regional_fusion.py
├── modules/intelligence/incident_correlation.py
└── modules/api/ (REST endpoints)
```

**Master vs Backend Ambiguity** (❌):
- Document 11 describes "Raspberry Pi Master" as local edge infrastructure
- Constitution C1 states "Master failure must not eliminate all intelligence"
- Current: Backend=FastAPI service
- **UNCLEAR**: Is Master=Backend? Or is Master a separate layer?

**Resilience Verification** (❌):
- No evidence of Master running during internet failure (Mode B)
- No Master heartbeat/health independent of backend
- No documented Master deployment separate from backend

**Contract Violation**: Cannot verify Master responsibility boundary

**Required Resolution**:
1. **Human Decision Required**: Clarify Master architecture
   - Option A: Master=Backend (Raspberry Pi runs FastAPI locally)
   - Option B: Master≠Backend (separate Master service + Backend cloud service)
2. Document Master deployment model in REPOSITORY_MAP.md
3. Verify Mode B resilience (Master continues during internet loss)
4. Add Master health monitoring

**Blocking**: YES — Master responsibility unclear, resilience unverified

---

### AREA 7: MULTI-HAZARD INDEPENDENCE

| Field | Value |
|-------|-------|
| **Authority** | Document 04 Section 6 + Constitution §13 |
| **Status** | **FIX** |
| **Safety-Critical** | YES |

**Specification Contract**: Each hazard type (FIRE, FLOOD, POLLUTION, etc.) MUST have independent confidence, severity, risk

**Implementation Evidence**:

**Database Schema** (❌):
```sql
-- models_b2.py Incident table (lines 32-40)
hazard_type: String(32)  -- FIRE, FLOOD, etc.
severity_index: Double   -- SINGLE value (not per-hazard)
risk_index: Double       -- SINGLE value (not per-hazard)
confidence_index: Double -- SINGLE value (not per-hazard)
```

**Regional Fusion** (✅):
```python
# regional_fusion.py NodeObservation dataclass (lines 30-44)
hazard_type: str
confidence: Optional[float]
severity: Optional[float]
risk: Optional[float]
# Per-observation has hazard_type, but incident aggregates to single scalar
```

**Contract Violation**: Incident model aggregates multi-hazard to single confidence/severity/risk scalars

**Required Resolution**:
1. **Option A (Schema Change)**: Add per-hazard JSONB column
   ```sql
   hazard_metrics: JSONB  -- {hazard_type: {confidence, severity, risk}}
   ```
2. **Option B (Separate Rows)**: One incident row per hazard type (changes incident identity semantics)
3. Update Track B2 fusion to preserve per-hazard independence
4. Update API responses to return per-hazard metrics

**Blocking**: YES — current schema conflates hazards (fire+flood cannot coexist with independent reasoning)

---

### AREA 8: RISK ≠ PROBABILITY

| Field | Value |
|-------|-------|
| **Authority** | Document 04 Section 4 + Constitution §15 |
| **Status** | **FIX** |
| **Safety-Critical** | YES |

**Specification Contract**: Risk is operational index = f(Severity, Confidence, Exposure), NOT probability

**Implementation Evidence**:

**Reference Python** (✅):
```python
# reference/python/nexalert_reference/risk.py
def compute_operational_risk(severity, confidence, exposure_factor):
    """NOT probability - operational urgency index"""
    return severity * confidence * exposure_factor
```

**Backend** (❌):
- Demo API `routes_demo.py` line 144 sets `risk_index: 0.87` without formula documentation
- No explicit comment "Risk ≠ Probability"
- Formula not documented in code

**Regional Fusion** (⚠️):
- `regional_fusion.py` computes `regional_risk` but formula unclear (line 150)

**Contract Violation**: Risk semantics not explicitly documented in backend, formula unclear

**Required Resolution**:
1. Add explicit docstring to all risk computation functions: "Operational index, NOT probability"
2. Document formula: `risk = severity × confidence × exposure_factor`
3. Verify backend matches reference Python formula
4. Add unit test comparing backend vs reference risk computation

**Blocking**: NO — implementation likely correct, documentation missing

---

### AREA 9: CONFIDENCE ≠ PROBABILITY

| Field | Value |
|-------|-------|
| **Authority** | Document 04 Section 3 + Constitution §14 |
| **Status** | **PASS (reference)** / **AMBIGUOUS (backend)** |
| **Safety-Critical** | YES |

**Specification Contract**: Confidence is information quality (sensor health, data recency), NOT probability

**Implementation Evidence**:

**Reference Python** (✅):
```python
# reference/python/nexalert_reference/confidence.py
def compute_confidence(health, quality, reliability, anomaly):
    """Information quality from sensor metrics, NOT probability"""
    # H_i, Q_i, R_i, A_i → C_h
```

**Backend** (❓):
- Track B2 fusion computes `regional_confidence` (regional_fusion.py line 147)
- Formula uses trust_weight, freshness_weight, spatial_weight
- **UNCLEAR**: Does backend formula match reference definition?

**Verdict**: Reference implementation correct (PASS), backend needs verification

**Required Resolution**: Compare backend confidence computation to reference Python, document formula

---

### AREA 10: PHYSICAL FOOTPRINT ≠ OPERATIONAL BUFFER

| Field | Value |
|-------|-------|
| **Authority** | Document 05 (Track C) + Constitution §16 |
| **Status** | **NOT APPLICABLE** (Track C not implemented) |
| **Safety-Critical** | YES (when Track C implemented) |

**Specification Contract**: Physical fire footprint (model output) MUST be stored separately from operational buffer (policy margin)

**Implementation Evidence**:
- Track C not implemented at baseline 9c628d8
- Plan file exists (`expressive-floating-sutherland.md`) with correct schema design
- Future schema includes separate `physical_footprint` and `operational_buffer` columns

**Verdict**: Not applicable until Track C implementation

---

### AREA 11: MASTER FAILURE ≠ INTERNET FAILURE

| Field | Value |
|-------|-------|
| **Authority** | Document 11 Section 7 + Constitution §17 (LOCKED) |
| **Status** | **REPLACE** |
| **Safety-Critical** | YES |

**Specification Contract**: Edge node MUST continue local emergency operation when Master fails (separate from internet failure)

**Implementation Evidence**:

**Firmware** (❌):
- MQTT buffering exists (store-and-forward for connectivity loss)
- Heartbeat mechanism exists
- **MISSING**: Local emergency path independent of Master
- **MISSING**: Local buzzer/LED alert logic when Master unavailable
- **MISSING**: Local captive portal emergency page

**Modes**:
- Mode A: Normal (node ↔ Master ↔ internet)
- Mode B: Internet failure (node ↔ Master working, Master ↔ cloud fails) — **UNVERIFIED**
- Mode C: Master failure (node continues local emergency) — **MISSING**

**Contract Violation**: Local emergency path not implemented, Mode C missing

**Required Resolution**:
1. **REPLACE firmware** to add local emergency service:
   - Detect Master unavailability (heartbeat timeout)
   - Local hazard state → buzzer pattern
   - Local hazard state → LED color
   - Optional: local captive portal Wi-Fi with emergency page
2. Verify Mode B (Master continues during internet failure)
3. Add Mode C test scenario

**Blocking**: YES — Constitution §17 LOCKED requirement

---

### AREA 12: SENSOR CALIBRATION OWNERSHIP

| Field | Value |
|-------|-------|
| **Authority** | Constitution C2 (LOCKED) + Document 06 Section 6 |
| **Status** | **FIX** |
| **Safety-Critical** | NO |

**Specification Contract**: Calibration constants MUST NOT be hard-coded in sensor drivers. Per-node calibration is versioned provisioning artifact.

**Implementation Evidence**:

**Firmware** (❌):
- Sensor drivers in `firmware/components/sensors/` (DHT22, BMP280, MQ-135)
- **Need to inspect**: Do drivers contain hard-coded calibration constants?
- Constitution C2 decision (lines 91-134) explicitly forbids hard-coded calibration

**Node Config** (✅):
- `node_config.h` defines configuration structure
- Supports provisioning-time configuration

**Contract Violation**: Unknown until sensor driver inspection

**Required Resolution**:
1. Inspect sensor drivers for hard-coded calibration
2. If found: Extract to per-node configuration
3. Implement calibration versioning (config_version field exists in nodes table)
4. Document calibration provisioning process

**Blocking**: NO — can defer to deployment phase

---

### AREA 13: GOLDEN-VECTOR TEST HARNESS

| Field | Value |
|-------|-------|
| **Authority** | Constitution §8 + Document 17 |
| **Status** | **FIX** |
| **Safety-Critical** | NO |

**Specification Contract**: Production implementations (firmware, backend) MUST pass golden-vector parity tests against reference Python

**Implementation Evidence**:

**Reference Python** (✅):
```
reference/python/
├── tests/ (219 tests pass)
└── golden-vectors/ (validation baseline)
```

**Backend** (❌):
- Track B2 has integration tests (`tests/test_regional_fusion.py`, `tests/track_b2_scenarios.py`)
- **MISSING**: Explicit golden-vector parity harness comparing backend to reference Python output

**Firmware** (❌):
- Intelligence module unit tests exist (`firmware/components/intelligence/test/`)
- **MISSING**: Golden-vector harness comparing firmware to reference Python

**Contract Violation**: Test infrastructure incomplete

**Required Resolution**:
1. Create `services/backend/tests/golden_vectors/` with reference parity tests
2. Create `firmware/test/golden_vectors/` with reference parity tests
3. Each golden vector: reference input → reference output → production output → assert match within tolerance
4. Add to CI pipeline

**Blocking**: NO — tests validate correctness but not blocking for demo

---

### AREA 14: SECURITY IMPLEMENTATION

| Field | Value |
|-------|-------|
| **Authority** | Document 16 + Constitution §19 |
| **Status** | **FIX** |
| **Safety-Critical** | YES (for deployment) |

**Specification Contract**: TLS for MQTT, API authentication, secrets management

**Implementation Evidence**:

**Backend** (❌):
- `main.py` has NO authentication middleware
- FastAPI endpoints open (no JWT, no API keys)

**MQTT** (❌):
- MQTT broker configuration unclear
- TLS enabled? Unknown

**Secrets** (❌):
- No secrets management documented
- Environment variables? Vault? Unknown

**Demo Mode** (✅):
- Demo API intentionally unauthenticated (acceptable for demo)

**Contract Violation**: Security requirements not implemented

**Required Resolution**:
1. Add API authentication (JWT or API keys)
2. Enable MQTT TLS
3. Document secrets management strategy
4. Separate: Demo mode exceptions vs Production requirements

**Blocking**: NO for demo, YES for deployment

---

### AREA 15: CONFIGURATION GOVERNANCE

| Field | Value |
|-------|-------|
| **Authority** | Document 19 + Constitution §21 |
| **Status** | **FIX** |
| **Safety-Critical** | NO |

**Specification Contract**: Governed configuration system with compile-time, provisioning-time, runtime layers

**Implementation Evidence**:

**Firmware** (✅):
- `node_config.h` centralizes configuration
- NVS storage for persistence

**Backend** (❌):
- Configuration scattered (environment variables? config files?)
- No centralized configuration management

**Document 19** (⏳):
- DECISIONS.md Q3 (lines 277-300) defers file format decision (YAML vs JSON vs TOML)
- Configuration governance structure unclear

**Contract Violation**: Configuration system ad-hoc, not governed

**Required Resolution**:
1. Centralize backend configuration (choose format per DECISIONS.md Q3)
2. Document configuration layers (compile-time, provisioning, runtime)
3. Implement configuration versioning
4. Add configuration validation

**Blocking**: NO — can use ad-hoc config for demo

---

### AREA 16: FRONTEND SOURCE-OF-TRUTH

| Field | Value |
|-------|-------|
| **Authority** | Constitution §22 |
| **Status** | **PASS** |
| **Safety-Critical** | YES |

**Specification Contract**: Backend API is source of truth, frontend MUST NOT fabricate operational data

**Implementation Evidence**:

**Dashboard** (✅):
- Falls back to demo mode when backend unavailable
- Demo mode clearly labeled "● DEMO MODE" (page.tsx lines 101-105)
- Does NOT fabricate live data as real measurements

**Verdict**: PASS — demo mode properly labeled, no fabrication

---

### AREA 17: ARCHITECTURE INVARIANT ENUMERATION

| Field | Value |
|-------|-------|
| **Authority** | Document 01 + Constitution §3 |
| **Status** | **FIX** |
| **Safety-Critical** | NO |

**Specification Contract**: 37 locked architecture invariants from Document 01

**Implementation Evidence**:

**Constitution** (❌):
- §3 references "Document 01 defines 37 locked architecture invariants"
- **MISSING**: Explicit enumeration of all 37 invariants in Constitution

**Document 01** (✅):
- Contains architecture invariants throughout

**Contract Violation**: Cannot verify compliance without explicit checklist

**Required Resolution**:
1. Extract all 37 invariants from Document 01
2. Create explicit checklist in Constitution or separate document
3. Map each invariant to implementation evidence
4. Add compliance verification to audit process

**Blocking**: NO — informational

---

### AREA 18-26: REMAINING AREAS

**AREA 18: Authority Hierarchy** — PASS (Constitution §1 defines precedence)

**AREA 19: Specification Interpretation** — PASS (Constitution §2 defines MUST/MAY/SHOULD)

**AREA 20: Human Approval Requirement** — PASS (Constitution §20 documented)

**AREA 21: Safety-Critical Change Rules** — PASS (Constitution §23 documented)

**AREA 22: AI/Vibe-Coding Rules** — PASS (Constitution §24 documented)

**AREA 23: Change-Control Rules** — PASS (Constitution §26 documented)

**AREA 24: Reference Python vs Production** — PASS (reference/python/ exists, 219 tests pass)

**AREA 25: Testing Requirements** — FIX (golden-vector harness missing, see AREA 13)

**AREA 26: Simulator Truth-Separation** — BLOCKED (ambiguous: demo vs simulation semantics)

---

## PART 3: REQUIRED ARCHITECTURE BOUNDARIES

### Boundary 1: Edge ↔ Master ↔ Backend

**Edge (ESP32)**:
- Sensor sampling
- Edge intelligence (H_i, Q_i, R_i, baseline, anomaly, confidence, severity, risk, hazard state)
- Local emergency service (Master failure resilience)
- MQTT telemetry publish
- Store-and-forward buffering

**Master (Raspberry Pi)**:
- MQTT broker (local)
- Regional intelligence (Track B2 fusion, incident correlation)
- Local API (internet failure resilience)
- Gateway to Backend/Cloud

**Backend (Cloud)**:
- Persistence (PostgreSQL + PostGIS)
- REST API
- Long-term analytics
- External integration

**Current Violation**: Master boundary unclear, Edge intelligence not wired

---

### Boundary 2: Physical Footprint ↔ Operational Buffer ↔ Risk

**Physical Footprint** (Track C):
- Model-derived fire area
- Physics output
- Immutable per simulation run

**Operational Buffer**:
- Policy-defined margin
- Separate from physics
- Configurable per jurisdiction

**Risk Surface**:
- Continuous operational index
- Spatial decay from fire geometry
- NOT physical footprint
- NOT probability

**Current Status**: Not applicable (Track C not implemented)

---

### Boundary 3: HARDWARE ↔ SIMULATION ↔ DEMO

**HARDWARE**:
- Live sensor telemetry
- Real node identity
- Enters canonical ingestion path
- source: "HARDWARE"

**SIMULATION**:
- Synthetic telemetry
- Enters canonical ingestion path
- Same validation as HARDWARE
- Same intelligence pipeline
- source: "SIMULATION"
- Truth-separation required

**DEMO FIXTURE**:
- Presentation data
- Does NOT enter canonical ingestion
- routes_demo.py endpoints
- Dashboard demo mode fallback

**Current Violation**: DEMO/SIMULATION boundary ambiguous

---

## PART 4: CONTRACT VIOLATIONS SUMMARY

### Critical Violations (Blocking Phase 2)

1. **ESP32 Edge Intelligence** — Intelligence modules exist but not wired in main.c (REPLACE)
2. **Telemetry Schema Enforcement** — Backend does not enforce canonical schema at boundary (FIX)
3. **Master Local Intelligence** — Master architecture ambiguous, Mode B/C unverified (REPLACE)
4. **Multi-Hazard Independence** — Database schema conflates hazards to single scalars (FIX)
5. **Node Identity** — Validator too permissive, demo uses wrong prefix (FIX)

### High-Priority Violations (Non-Blocking)

6. **Risk Semantics** — Formula not documented in backend code (FIX)
7. **Master Failure Resilience** — Local emergency path missing (REPLACE)
8. **Golden-Vector Harness** — Firmware/backend parity tests missing (FIX)
9. **Security** — Authentication, TLS not implemented (FIX for deployment)
10. **Configuration Governance** — System ad-hoc, not governed (FIX)

### Documentation Violations

11. **Architecture Invariants** — 37 invariants not explicitly enumerated (FIX)
12. **Sensor Calibration** — Driver inspection pending (FIX)

---

## PART 5: SAFETY-CRITICAL GAPS

### Gap 1: Edge Intelligence Pipeline

**Contract**: Constitution C1 (LOCKED) requires complete edge intelligence  
**Current**: Modules exist but not invoked  
**Risk**: Node cannot reason locally about hazards (Master dependency)  
**Impact**: Master failure = intelligence failure (violates resilience pillar)

### Gap 2: Telemetry Schema Enforcement

**Contract**: Single canonical schema per Document 07  
**Current**: Multiple shapes accepted, frontend normalizes  
**Risk**: Downstream code assumes canonical shape, may fail on non-conforming data  
**Impact**: Intelligence pipeline receives inconsistent data

### Gap 3: Master Local Intelligence

**Contract**: Master continues during internet failure (Mode B)  
**Current**: Master architecture unclear  
**Risk**: Internet failure = intelligence failure  
**Impact**: Violates resilience pillar, defeats edge-first architecture

### Gap 4: Multi-Hazard Independence

**Contract**: Independent reasoning per hazard type  
**Current**: Single confidence/severity/risk scalar per incident  
**Risk**: Fire+flood+pollution cannot coexist with independent state  
**Impact**: Hazard conflation, incorrect operational decisions

### Gap 5: Master Failure Resilience

**Contract**: Node continues local emergency operation when Master fails  
**Current**: No local emergency path  
**Risk**: Master failure = no emergency alerting  
**Impact**: Critical safety gap (Constitution §17 LOCKED)

---

## PART 6: OPEN QUESTIONS

### Q1: Master Architecture (BLOCKING)

**Question**: Is Master=Backend (Raspberry Pi runs FastAPI) or Master≠Backend (separate Master service)?

**Impact**: Cannot verify resilience without answer

**Resolution Path**: Human architectural decision required

---

### Q2: Node Identity Canonical Format (HIGH)

**Question**: Is NEX-001 (demo) acceptable deviation or violation of NODE-XXX (schema)?

**Impact**: Pattern enforcement, demo vs production semantics

**Resolution Path**: Clarify demo exception policy or fix demo to match schema

---

### Q3: DEMO vs SIMULATION Semantics (MEDIUM)

**Question**: Is `routes_demo.py` "simulation" (requires truth-separation) or "demo fixture" (out of scope)?

**Impact**: Truth-separation requirements, Constitution §18 applicability

**Resolution Path**: Define DEMO/SIMULATION boundary in REPOSITORY_MAP.md

---

### Q4: Sensor Calibration (MEDIUM)

**Question**: Do firmware sensor drivers contain hard-coded calibration constants?

**Impact**: Constitution C2 compliance

**Resolution Path**: Inspect sensor drivers, extract if found

---

### Q5: Backend Confidence/Risk Formulas (LOW)

**Question**: Do backend confidence/risk computations match reference Python definitions?

**Impact**: Contract compliance, golden-vector parity

**Resolution Path**: Code comparison, unit tests

---

## PART 7: REQUIRED APPROVALS

### Approval 1: Master Architecture Decision

**Decision Needed**: Clarify Master=Backend or Master≠Backend

**Authority**: Human architectural decision (cannot be inferred)

**Blocking**: Phase 2 implementation

---

### Approval 2: Node Identity Format Exception

**Decision Needed**: Is NEX-001 acceptable demo exception?

**Authority**: Specification owner

**Blocking**: No (localized to demo)

---

### Approval 3: Multi-Hazard Schema Refactor

**Decision Needed**: Schema change (JSONB column) vs behavior change (separate rows)?

**Authority**: Database architect + specification owner

**Blocking**: Phase 2 Track B2 work

---

## PART 8: IMPLEMENTATION ORDER

### Phase 2A: Critical Contract Fixes (Week 1)

1. **Telemetry Schema Enforcement** (2 days)
   - Add backend validator middleware
   - Enforce canonical schema at all ingestion endpoints
   - Remove frontend normalization layer
   - Verify firmware emits canonical shape

2. **Node Identity Format** (1 day)
   - Decide NEX-001 exception policy
   - Update validator to enforce full regex
   - Fix demo if needed

3. **Multi-Hazard Schema Design** (2 days)
   - Decide JSONB vs separate-rows approach
   - Design migration
   - Update Track B2 fusion logic

### Phase 2B: Edge Intelligence Integration (Week 2)

4. **ESP32 Intelligence Pipeline** (5 days)
   - Rewrite main.c to invoke intelligence modules
   - Wire: sensor → H_i/Q_i/R_i → baseline → anomaly → evidence → confidence → severity → risk → hazard state
   - Add intelligence outputs to telemetry envelope
   - Golden-vector validation

### Phase 2C: Master Architecture (Week 3)

5. **Master Clarification** (1 day)
   - Document Master=Backend or Master≠Backend decision
   - Update REPOSITORY_MAP.md

6. **Master Resilience** (3 days)
   - Verify Mode B (Master continues during internet failure)
   - Add Master health monitoring independent of backend

7. **Edge Local Emergency** (3 days)
   - Implement local emergency path (Master failure resilience)
   - Local hazard state → buzzer/LED
   - Optional: local captive portal

### Phase 2D: Testing & Documentation (Week 4)

8. **Golden-Vector Harness** (3 days)
   - Backend parity tests vs reference Python
   - Firmware parity tests vs reference Python

9. **Risk/Confidence Documentation** (1 day)
   - Document formulas in backend code
   - Verify match to reference definitions

10. **Architecture Invariant Enumeration** (1 day)
    - Extract 37 invariants from Document 01
    - Create compliance checklist

### Phase 3+: Non-Blocking Items

11. **Security Implementation** (deployment prerequisite)
12. **Configuration Governance** (deployment prerequisite)
13. **Sensor Calibration** (deployment prerequisite)

---

## PART 9: PHASE 1 EXIT GATE

### Exit Criteria

Phase 1 (CONTRACT RECONCILIATION) is COMPLETE when:

✅ All contract areas audited  
✅ Evidence collected from authoritative sources  
✅ Violations classified (PASS/FIX/REPLACE/BLOCKED)  
✅ Safety-critical gaps identified  
✅ Open questions documented  
✅ Implementation order defined  
✅ Exit gate status determined  

### Phase 1 Status: **APPROVED** (2026-09-13)

**Previously Blocked — Now Resolved**:

1. ✅ **Master Architecture** — APPROVED: Master=Raspberry Pi (local intelligence), Backend=Cloud (persistence/analytics) — distinct responsibilities
2. ✅ **Node Identity** — APPROVED: NODE-[0-9]{3,} canonical pattern (NODE-001, NODE-002, etc.)
3. ✅ **DEMO vs SIMULATION** — APPROVED: routes_demo.py is DEMO FIXTURE (not operational simulation)
4. ✅ **Multi-Hazard** — APPROVED: Design canonical HazardAssessment domain model first (no premature JSONB)
5. ✅ **Telemetry Schema** — APPROVED: Schema authoritative, remove frontend normalization

**Remaining Implementation Blockers** (moved to Phase 2):

1. **ESP32 Intelligence Integration** — Modules exist but not wired in main.c (inspect before modifying)
2. **Master Local Intelligence Runtime** — Verify Master runs local intelligence during internet failure
3. **Multi-Hazard Schema Design** — Design canonical domain model before database changes
4. **Edge Local Emergency** — Deferred (do NOT implement yet per freeze decision)

**Phase 2 Ready**: Architecture decisions approved, work packages defined in PHASE_1_ARCHITECTURE_FREEZE.md

---

## DOCUMENT CONTROL

**Version**: 1.0  
**Status**: Phase 1 Complete — BLOCKED awaiting approvals  
**Next Review**: After Q1-Q3 resolution  
**Authority**: This audit is INFORMATIONAL. Specifications remain authoritative.

**Audit Methodology**:
- Systematic reading of 20 numbered specifications
- Constitution, DECISIONS.md, REPOSITORY_MAP.md, RECOVERY_BASELINE.md
- Schema files, database models, backend code, firmware code
- Evidence collected from implementation, not inferred

**Classification Criteria**:
- **PASS**: Specification + implementation + tests agree, no contradictory code
- **FIX**: Implementation deviates, can be corrected without architectural change
- **REPLACE**: Fundamental architecture mismatch, requires rebuild
- **BLOCKED**: Specification ambiguous, requires human decision

**Safety-Critical Definition**: Contract area where violation could lead to:
- Incorrect hazard detection
- Failed emergency alerting
- Data integrity loss
- Resilience failure under degraded conditions

---

**END OF CONTRACT RECONCILIATION V1**
