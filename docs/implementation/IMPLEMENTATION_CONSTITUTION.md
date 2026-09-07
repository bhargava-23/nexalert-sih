# NexAlert Implementation Constitution

**Version**: 1.0  
**Status**: ACTIVE  
**Last Updated**: 2026-09-07  
**Authority**: This document governs all NexAlert implementation. It overrides convenience, overrides existing code patterns, and cannot be silently waived.

---

## Table of Contents

1. [Authority Hierarchy](#1-authority-hierarchy)
2. [Specification Interpretation Rules](#2-specification-interpretation-rules)
3. [Non-Negotiable Architecture Invariants](#3-non-negotiable-architecture-invariants)
4. [ESP32 Edge Node Ownership](#4-esp32-edge-node-ownership)
5. [Master (Raspberry Pi) Ownership](#5-master-raspberry-pi-ownership)
6. [Backend/Cloud Ownership](#6-backendcloud-ownership)
7. [Reference Python vs Production Implementations](#7-reference-python-vs-production-implementations)
8. [Golden-Vector/Parity Requirements](#8-golden-vectorparity-requirements)
9. [Sensor-Driver Boundaries](#9-sensor-driver-boundaries)
10. [Telemetry Contract Rules](#10-telemetry-contract-rules)
11. [Missing ≠ Zero](#11-missing--zero)
12. [Timestamp Semantics](#12-timestamp-semantics)
13. [Multi-Hazard Independence](#13-multi-hazard-independence)
14. [Confidence ≠ Probability](#14-confidence--probability)
15. [Risk ≠ Probability](#15-risk--probability)
16. [Physical Footprint ≠ Operational Buffer](#16-physical-footprint--operational-buffer)
17. [Master Failure ≠ Internet Failure](#17-master-failure--internet-failure)
18. [Simulator Truth-Separation Rules](#18-simulator-truth-separation-rules)
19. [Security Invariants](#19-security-invariants)
20. [Human Approval Requirement](#20-human-approval-requirement)
21. [Configuration Governance](#21-configuration-governance)
22. [Frontend Source-of-Truth Rule](#22-frontend-source-of-truth-rule)
23. [Safety-Critical Change Rules](#23-safety-critical-change-rules)
24. [AI/Vibe-Coding Rules](#24-aivibe-coding-rules)
25. [Testing Requirements](#25-testing-requirements)
26. [Change-Control / Architecture-Deviation Rules](#26-change-control--architecture-deviation-rules)

---

## 1. Authority Hierarchy

**The 20 numbered specifications are the engineering source of truth.**

When implementation choices conflict, use this precedence order (per Document 18):

1. **Master Architecture & Invariants** (Document 01)
2. **Technical Requirements Document (TRD)** (Document 02)
3. **Math/Geospatial Specifications** (Documents 04, 05)
4. **Hardware Specification** (Document 06)
5. **Backend/API Specification** (Document 07)
6. **UI Documents** (Documents 12, 13, 14)
7. **Simulation Documents** (Documents 08, 09, 15)
8. **Security Specification** (Document 16)
9. **Validation Specification** (Document 17)
10. **Execution Document** (Document 18)

### Core Rules

- **This constitution governs implementation interpretation of specifications**
- **Specification changes require explicit human approval**
- **Existing code MUST NOT override specifications**
- **Convenience is NOT justification for architecture deviation**
- **When locked architecture conflicts with discovered reality**: Surface the conflict, propose resolution, wait for approval

---

## 2. Specification Interpretation Rules

### Language Precision

- **MUST**: Non-negotiable requirement. Cannot be waived for convenience.
- **MUST NOT**: Prohibited. Cannot be justified by implementation ease.
- **MAY**: Implementation choice. Document the choice made.
- **SHOULD**: Strong recommendation with documented exception path when not followed.

### Ambiguity Handling

- **Surface ambiguity explicitly**. Do NOT silently resolve with "reasonable" assumption.
- **Ask**: When specification leaves something unresolved, ask human decision-maker.
- **Document**: Record resolution in `DECISIONS.md` with rationale.

### Legacy References

- **Older material is historical context only** when it conflicts with numbered specifications 01-20.
- **Do NOT revive legacy architecture** mentioned in older material that contradicts current specifications.

### Specification Updates

- Require explicit human approval
- Versioned specification update with change log
- Impact analysis across affected subsystems
- Migration path for existing code

---

## 3. Non-Negotiable Architecture Invariants

**Reference**: Document 01 defines 37 locked architecture invariants.

### Critical Invariants (Subset)

1. **Missing ≠ zero**: Semantic distinction preserved throughout all 20 layers
2. **measurement_timestamp ≠ receive_timestamp**: Always separate fields
3. **node_state ≠ regional_incident_state**: Local vs distributed fusion
4. **sensor_health ≠ battery_health**: Separate dimensions
5. **signal_quality ≠ hazard_confidence**: Telemetry trust vs decision confidence
6. **confidence ≠ severity**: Evidence quality vs operational seriousness
7. **operational_risk ≠ probability**: Decision index vs statistical forecast
8. **physical_footprint ≠ operational_buffer**: Distinct geometric layers
9. **multi-hazard independence**: Each hazard maintains independent reasoning vector
10. **Master_failure ≠ internet_failure**: Distinct failure modes with distinct handling

### All 37 Invariants

Full list available in Document 01, Section 7. Every invariant is non-negotiable and MUST be preserved in implementation.

---

## 4. ESP32 Edge Node Ownership

**Reference**: Documents 03, 06, 18, plus C1 resolution (2026-09-07)

### MUST Run (Mandatory Capability)

The ESP32 firmware **MUST implement** complete lightweight edge-intelligence capability:

- **Sensor sampling**: All configured sensor classes (temperature, humidity, PM, gas, water_level, rainfall, soil_moisture, vibration)
- **Diagnostics**: H_i computation (sensor health)
- **Signal quality**: Q_i computation (integrity × stability)
- **Reliability**: R_i = H_i × Q_i × K_i (evidence reliability)
- **Baseline**: Robust median/MAD with states (INITIALIZING/LEARNING/READY/FROZEN/RECOVERING)
- **Anomaly**: A_i = 1 - exp(-min(|z_i|, z_cap) / λ)
- **Hazard evidence**: Configured lightweight rules per hazard
- **Confidence**: C_h (coverage-based computation)
- **Severity/Risk**: S_h, R_h (edge indices)
- **Local hazard state**: State machine (NORMAL/WATCH/SUSPECTED/CONFIRMED/CRITICAL/RESOLVED)
- **Canonical telemetry envelope**: With HMAC-SHA256 signing
- **Store-and-forward**: Bounded queue (Q0 CRITICAL / Q1 HIGH / Q2 NORMAL / Q3 BULK)
- **Local Wi-Fi AP**: Distinctive NexAlert SSID
- **Captive portal**: Local emergency page serving
- **Cached emergency state**: Latest signed canonical emergency information

### Deployment Configuration

- **Capability MUST be implemented** in firmware
- **Deployment configuration MAY disable** explicitly designated optional modules for resource constraints
- **Disabled state MUST be observable** (diagnostics, configuration query)
- **Effective configuration MUST be versioned** (node reports active config version)
- **Information Condition MUST degrade honestly** when modules disabled (e.g., DEGRADED, UNKNOWN)

### MUST NOT Run (Prohibited)

- **Fire spread propagation** (arrival-time engine, ROS computation)
- **Geospatial raster operations** (DEM gradients, slope/aspect)
- **Population exposure calculations** (spatial joins, demographic overlays)
- **Multi-node fusion** (cross-node evidence correlation)
- **Full GIS operations** (PostGIS queries, geometry repair)
- **Master-only intelligence layers** (full evidence engine, incident correlation)

### Rationale

- **Local autonomy**: Master failure must not eliminate all intelligence
- **Resilience requirement**: Local emergency path survives Master/internet loss
- **Resource constraints**: Lightweight subset for ESP32-S3 hardware

---

## 5. Master (Raspberry Pi) Ownership

**Reference**: Documents 03, 07, 18, plus C3 resolution (2026-09-07)

### MUST Run (Authoritative Intelligence)

- **Full intelligence stack** (all equations from Document 04):
  * H_i with complete diagnostic weighting
  * Q_i with full integrity/stability/freshness logic
  * R_i = H_i × Q_i × K_i
  * Baseline: median/MAD with states INITIALIZING/LEARNING/READY/FROZEN/RECOVERING
  * Anomaly: A_i with z-capping, A_node aggregate, A_h hazard-specific
  * Evidence: configuration-driven engine with core/supporting/temporal/context/availability classes
  * Confidence: C_h = weighted combination (coverage/agreement/temporal/baseline)
  * Severity: S_h = w_I × I_h + w_T × T_h + w_D × D_h
  * Operational Risk: R_h = w_E × E_h + w_S × S_h + w_T × T_h
  * Hazard state machine: full hysteresis/persistence/escalation/unknown fallback
  * Information Condition: GOOD/DEGRADED/UNKNOWN

- **Fire spread geospatial chain** (Document 05):
  * DEM gradient computation (∂z/∂x, ∂z/∂y)
  * Wind FROM→TO conversion: θ_TO = (θ_FROM + 180°) mod 360°
  * Directional ROS: ROS(c,d) = R_base(c) × F_dir(c,d; V_eff, θ_eff)
  * 8-neighbor arrival-time propagation
  * Current/warning/projection zones from arrival-time thresholds
  * Physical footprint vs operational buffer (separate layers)
  * Risk surface: R_haz,c = w_U × U_c + w_I × I_c + w_E × E_c

- **Distributed fusion**:
  * Multi-node evidence correlation
  * Incident correlation (spatial 50m, temporal 30s defaults)
  * Conflict resolution (preserve local valid truth under disagreement)

- **Local emergency operations**:
  * Cached canonical emergency state
  * Local Wi-Fi AP/captive portal gateway
  * Offline citizen emergency page serving
  * Authority diagnostics/status

### Rationale

- **Resilience**: Master MUST function during internet loss
- **Authority**: Master is source of truth for geospatial reasoning and hazard state
- **C3 Resolution**: Master-local fire spread computation mandatory for V1

---

## 6. Backend/Cloud Ownership

**Reference**: Documents 03, 07, 18, plus C3 resolution (2026-09-07)

### MUST Run

- **Canonical telemetry persistence**: PostgreSQL/PostGIS with UNIQUE(node_id, sequence)
- **HMAC/signature verification**: Node authentication, replay protection
- **Alert lifecycle management**: DRAFT → PENDING_APPROVAL → APPROVED → ISSUED → DELIVERING → DELIVERED → ACKNOWLEDGED
- **Human approval workflow**: Authority role-based access control (RBAC)
- **Audit trail**: Immutable append-only audit_events table
- **Response recommendation engine**: Ranked actions with human approval gate
- **SOS handling**: Categorical tiers (IMMEDIATE/HIGH/STANDARD/VERIFY), never auto-rejected
- **Authority/citizen identity management**: User accounts, sessions, credentials
- **Simulation orchestration**: Scenario engine, virtual node fleet, ground truth store

### MAY Run (Optional Extensions)

- **Heavy geospatial computation**: Large-area fire spread offload (per C3 resolution)
- **Historical analytics**: Long-term baseline learning, trend analysis
- **External integration adapters**: Cell broadcast, push notifications, third-party APIs

### Rationale

- **Canonical persistence**: PostgreSQL is source of truth for historical telemetry
- **C3 Resolution**: Backend MAY offload fire spread; V1 does not depend on it
- **Scalability**: Backend handles heavy computation and external integrations

---

## 7. Reference Python vs Production Implementations

**Reference**: Documents 04, 06, 17, 18

### Python Reference Math

- **Python reference implementation is canonical** for golden vector generation
- **All mathematical formulas** (H_i, Q_i, R_i, baseline, A_i, C_h, S_h, R_h) have Python reference
- **Reference math is source of truth** for numerical correctness
- **Located in**: `packages/nexalert-math/` or `tests/golden-vectors/reference/`

### C/C++ Embedded Implementation

- **C/C++ embedded implementation MUST match Python** within documented tolerances
- **Parity validation REQUIRED** before firmware merge
- **Firmware merge BLOCKED** if golden vector parity regresses without reviewed spec change
- **Tolerances documented** per formula in validation specification (Document 17)

### Backend Production Python

- **Backend production Python SHOULD reuse reference math** where practical
- **When diverging**: Document reason, maintain parity tests
- **No duplication without parity**: If rewriting math, golden vectors MUST pass

---

## 8. Golden-Vector/Parity Requirements

**Reference**: Document 17, Sections 4-8

### 11 Golden Vector Sets

| **Vector** | **Purpose** | **Validation** |
|---|---|---|
| **GV-H01** | Health (H_i) | All nominal, one hard failure, weighted degradation |
| **GV-Q01** | Quality (Q_i) | Fresh/stable, stale, high jitter, missing samples |
| **GV-R01** | Reliability (R_i) | H, Q, K combinations |
| **GV-B01** | Baseline | INITIALIZING→LEARNING→READY, contamination, recovery |
| **GV-A01** | Anomaly (A_i) | z=0, ±1, ±z_cap, extreme |
| **GV-C01** | Confidence (C_h) | Coverage/agree/temp/base edge combinations |
| **GV-S01** | Severity/Risk | Boundary and weighted extremes |
| **GV-HZ01** | Hysteresis | Trigger, persistence, clear, escalation |
| **GV-GEO01** | Gradient | Flat, plane, edge conditions |
| **GV-FIRE01** | ROS/arrival | No wind, wind-aligned, crosswind, uphill/downhill, barrier |
| **GV-GEO02** | Geometry | Single blob, holes, disjoint zones |

### Numerical Tolerances

- **Scalar reference math**: Absolute/relative tolerance (chosen per quantity, documented units)
- **State machine**: Exact match (state, reason code, event transition)
- **Geometry**: Topological + area/shape tolerance
- **Arrival raster**: Cellwise/time tolerance

### Parity Rules

- **No unexplained drift**: Golden vector results stable across runs with same inputs/config/version
- **Firmware merge gate**: All relevant golden vectors MUST pass before merge to main branch
- **Regression blocking**: Parity regression without reviewed spec change blocks CI/CD pipeline

---

## 9. Sensor-Driver Boundaries

**Reference**: Documents 06, 17, plus C2 resolution (2026-09-07)

### Sensor Driver Responsibilities

- **Produces raw measurement**: Numeric value in specified units
- **Produces diagnostics**: Sensor-specific health indicators (e.g., CRC valid, warm-up complete)
- **Reports missing data**: null/absent status, NEVER fabricated zero

### Sensor Driver Prohibitions

- **MUST NOT directly conclude hazard state** (e.g., "fire detected")
- **MUST NOT directly trigger alerts**
- **MUST NOT make incident-level decisions**

### Calibration Rules (C2 Resolution)

- **Per-node calibration constants MUST NOT be hard-coded** in sensor drivers
- **Calibration is versioned provisioning artifact** associated with node_id
- **Calibration includes**: Offset, gain, response curve, gas species mapping
- **Calibration source**: Secure provisioning store, NOT embedded in firmware source
- **Calibration lifecycle**: Field-replaceable, audit trail, recalibration-capable

### Missing Sensor Reading

- **null/absent/stale status**: Explicit representation
- **NEVER fabricated zero**: Missing ≠ 0.0
- **Quality/reliability degrade**: Q_i, R_i reflect unavailable data

---

## 10. Telemetry Contract Rules

**Reference**: Documents 06, 07, 08

### Canonical Schema

Required fields (always present):

```json
{
  "telemetry_id": "UUID",
  "node_id": "string",
  "sequence": "integer (node-scoped monotonic)",
  "measurement_timestamp": "ISO8601 (device clock)",
  "receive_timestamp": "ISO8601 (server clock)",
  "location": {"latitude": float, "longitude": float, "altitude_m": float},
  "measurements": {},
  "diagnostics": {},
  "power": {},
  "source": "LIVE_HARDWARE | SIMULATION",
  "schema_version": "string",
  "auth": {"hmac": "base64", "algorithm": "HMAC-SHA256"}
}
```

### Schema Evolution

- **Schema changes require version bump**: Increment `schema_version`
- **Migration path REQUIRED**: Old nodes continue working or explicit deprecation notice
- **Backward compatibility**: New fields optional; old fields retained or explicitly deprecated
- **Breaking changes**: Require coordinated firmware + backend deployment

### Database Constraints

- **UNIQUE(node_id, sequence)**: Enforced at database level
- **Replay protection**: Backend rejects duplicate (node_id, sequence) within replay window
- **Idempotency**: Resubmission of same telemetry_id acknowledged, not reprocessed

---

## 11. Missing ≠ Zero

**Reference**: Document 01 (Invariant 1), Documents 04, 06, 08

### Core Principle

**Semantic distinction preserved throughout all 20 layers:**

- **null**: Sensor not present, not configured, or failed
- **absent**: Expected measurement not received (communication loss, sensor timeout)
- **stale**: Measurement timestamp older than freshness threshold
- **invalid**: Measurement failed validation (out-of-range, CRC error)
- **zero**: Sensor actually measured numeric value 0.0

### Implementation Rules

- **No silent imputation**: Do NOT fill missing with mean, last-value, or zero
- **Quality/reliability degrade**: Q_i, R_i reflect missing data
- **Confidence degrades honestly**: C_h accounts for coverage gaps
- **Information Condition**: DEGRADED or UNKNOWN when critical data missing

### Examples

- **Temperature sensor disconnected**: `measurements.temperature = null`, NOT `0.0`
- **PM2.5 stale (>30s old)**: `measurements.pm25 = <last_value>`, but `Q_i` reflects staleness
- **Water level sensor reports actual zero depth**: `measurements.water_level_m = 0.0` (valid measurement)

---

## 12. Timestamp Semantics

**Reference**: Documents 06, 07, 11, 16

### Two Distinct Timestamps

- **measurement_timestamp**: When sensor observed phenomenon (device clock)
  * Source: ESP32 device clock
  * Semantics: Physical event time
  * Use: Temporal ordering of observations, stale detection

- **receive_timestamp**: When telemetry arrived at ingestion (server clock)
  * Source: Backend/Master server clock
  * Semantics: Ingestion time
  * Use: Network latency analysis, replay protection, audit trail

### Rules

- **ALWAYS separate fields**: Never conflate, never derive one from the other
- **Replay protection uses both**: Sequence + measurement_timestamp + receive_timestamp
- **Stale detection**: `current_time - measurement_timestamp > stale_threshold`
- **Clock skew tolerance**: `comm.max_clock_skew_s = 60` (configurable)

### Clock Synchronization

- **ESP32 clock**: NTP sync when available, monotonic fallback when offline
- **device_monotonic_ms**: Monotonic millisecond counter (device uptime), separate field
- **Clock anomaly detection**: Backward timestamps flagged, measurement time vs monotonic checked

---

## 13. Multi-Hazard Independence

**Reference**: Documents 01 (Invariant 17-19), 04, 09, 10, 13, 14

### Core Principle

**Independent reasoning vectors per hazard:**

- **Fire**: Full geospatial, arrival-time propagation
- **Flood**: Water level trends, rainfall correlation
- **Pollution**: PM/gas concentration persistence
- **Landslide**: Vibration/moisture triggers
- **Extreme Heat**: Temperature/humidity duration
- **Unknown**: Observable anomaly without classified hazard

### Each Hazard Maintains Independent

- **Evidence groups**: Core/supporting/temporal/context/availability
- **Confidence**: C_h_fire, C_h_flood, C_h_pollution (separate)
- **Severity**: S_h (hazard-specific)
- **Operational Risk**: R_h (hazard-specific)
- **State machine**: NORMAL/WATCH/SUSPECTED/CONFIRMED/CRITICAL/RESOLVED (per hazard)
- **Information Condition**: GOOD/DEGRADED/UNKNOWN (per hazard)

### Prohibited

- **NO universal combined risk scalar**: Do NOT create `Risk_combined = sum(Risk_h)`
- **NO merged hazard state**: Each hazard has separate incident card
- **NO collapsed multi-hazard UI**: Display separate hazard cards, separate risk surfaces

### Safe-Location Ranking

- **Evaluates ALL active hazards**: Route exposure for fire AND flood AND pollution
- **Does NOT collapse them**: Multi-criteria decision, NOT single combined risk
- **Explicit tradeoffs**: Show destination conflicts (e.g., "Safe from fire, flood-exposed")

---

## 14. Confidence ≠ Probability

**Reference**: Documents 01 (Invariant 6), 04, 10, 13, 14

### Core Principle

**C_h (confidence) is operational evidence-quality index, NOT calibrated probability.**

### Formula

```
C_h = w_cov × C_cov + w_agree × C_agree + w_temp × C_temp + w_base × C_base
```

Where:
- **C_cov**: Coverage (core evidence present)
- **C_agree**: Agreement (sensors corroborate)
- **C_temp**: Temporal (persistence, trend)
- **C_base**: Baseline (established reference)

### Configuration

- `hazard.coverage_weight = 0.30`
- `hazard.agreement_weight = 0.30`
- `hazard.temporal_weight = 0.20`
- `hazard.baseline_weight = 0.20`
- `hazard.confidence_assess_floor = 0.30` (below → N/A, not 0%)

### UI Rules

- **MUST NOT present C_h as "X% probability of fire"**
- **MUST present as**: "Evidence quality: HIGH/MODERATE/LOW" or "Confidence: 0.85 (operational index)"
- **Below evidence floor**: Display as "N/A" or "UNKNOWN", not "0% confidence"

---

## 15. Risk ≠ Probability

**Reference**: Documents 01 (Invariant 7), 04, 10, 13, 14

### Core Principle

**R_h (operational risk) is decision urgency index, NOT statistical probability.**

### Formula

```
R_h = w_E × E_h + w_S × S_h + w_T × T_h
```

Where:
- **E_h**: Evidence strength
- **S_h**: Severity (impact/trajectory/duration)
- **T_h**: Temporal urgency

### UI Rules

- **MUST NOT present R_h as "X% probability"**
- **MUST present as**: "Operational risk: HIGH/MODERATE/LOW" or explicit operational urgency language
- **Risk informs**: Priority, resource allocation, escalation speed
- **NOT probabilistic forecast**: No calibration claims, no "odds of occurrence"

---

## 16. Physical Footprint ≠ Operational Buffer

**Reference**: Documents 01 (Invariant 8), 05, 10, 13

### Core Principle

**Physical hazard footprint and operational policy buffer are distinct geometric layers.**

### Physical Footprint

- **Derived from arrival-time field** (fire) or evidence (other hazards)
- **Source of truth**: Arrival-time raster T_a(c) for fire
- **Current affected area**: A_current(t) = {c | T_a(c) ≤ t}
- **Authoritative**: Never decorative, never invented

### Operational Buffer

- **Policy margin around physical footprint**
- **Configurable**: `fire.operational_buffer_m = 100` (default, POLICY parameter)
- **Separate GeoJSON layer**: Distinct from physical footprint
- **Labeled explicitly**: "Operational buffer (policy)" in UI

### UI Rules

- **Physical footprint**: "Current fire area" (from arrival-time field)
- **Operational buffer**: "Operational safety buffer (100m policy margin)" (separate layer, separate styling)
- **NEVER conflate**: Operational buffer is NOT physical fire boundary

---

## 17. Master Failure ≠ Internet Failure

**Reference**: Documents 01 (Invariant 36), 06, 11, 17

### Core Principle

**Master failure and internet failure are DISTINCT failure modes with DISTINCT handling.**

### Failure Modes

| **Mode** | **Master** | **Internet** | **Behavior** |
|---|---|---|---|
| **A: Fully Connected** | UP | UP | Full authority/cloud/citizen channels operational |
| **B: Internet Lost** | UP | DOWN | Local authority/fusion CONTINUE; cloud delivery PAUSES |
| **C: Master Lost** | DOWN | ANY | Node-local emergency path CONTINUES; no fusion/incident correlation |
| **D: Master+Internet** | DOWN | DOWN | Field nodes operate independently; local emergency USABLE |
| **E: Node Isolated** | ANY | ANY | Single node unreachable; Master marks STALE; incident reasoning continues |

### Tests MUST Validate Independently

- **Test Mode B**: Disable internet → show degraded state, local services continue
- **Test Mode C**: Kill Master → show node-local emergency + honest degraded state
- **NO conflation**: "offline" is ambiguous; specify Master vs internet in diagnostics/UI

### Information Condition

- **Mode B (Internet lost)**: Information Condition may remain GOOD (local sensors/Master operational)
- **Mode C (Master lost)**: Information Condition → DEGRADED (no fusion, node-local only)

---

## 18. Simulator Truth-Separation Rules

**Reference**: Documents 01 (Invariant 35), 08, 09, 15, 17

### Core Principle

**Simulation produces telemetry/events ONLY. Same ingestion/reasoning path as hardware.**

### Simulation Data Flow

```
Scenario Definition
  ↓
Virtual Environment (terrain, weather, fuel)
  ↓
Virtual Node Telemetry (canonical schema with source=SIMULATION)
  ↓
Authentication/Envelope Validation (SAME PATH as LIVE)
  ↓
Ingestion → Health/Quality → Reliability → Baseline/Anomaly → Evidence → Confidence/Severity/Risk → Hazard State → Incident → Alert → UI
```

### Ground Truth (PRIVATE to Evaluator)

**Ground truth NEVER enters inference path:**

- **Hazard labels** (true ignition, true hazard type): Evaluator only
- **True perimeter**: Evaluator only
- **True onset/end time**: Evaluator only
- **Simulator source intensity**: Evaluator only
- **Expected state transitions**: Evaluator only

### Visible to Reasoning

- **Telemetry observation**: YES (canonical schema)
- **Sensor diagnostics**: YES
- **Receive timestamp/sequence**: YES
- **Scenario ID**: OPTIONAL / CONTROLLED (metadata only, never as label)

### Frontend LIVE/SIMULATION Toggle

- **Changes data source ONLY**: Different backend endpoint or database view
- **Does NOT change algorithm**: Same fire spread engine, same risk computation
- **Same UI components**: Same geometry rendering, same state machine display

### Test FI-13

**Simulator ground truth injection MUST be rejected by decision engine:**
- Attempt to inject true hazard label → reasoning ignores it, infers from telemetry only
- Test validates truth separation is enforced

---

## 19. Security Invariants

**Reference**: Documents 02 (NFR-030 through NFR-036), 03, 06, 16, 19

### Node Telemetry Authentication

- **HMAC-SHA256 REQUIRED** before ingestion
- **Per-node HMAC secrets** via secure provisioning (NEVER in source control)
- **Canonical message**: schema_version | node_id | telemetry_id | sequence | measurement_timestamp | payload_hash
- **Replay protection**: Sequence + timestamp within `comm.replay_window_s = 120`

### Emergency Event Integrity

- **Ed25519 signatures** for canonical emergency events
- **Signed event model**: event_id | incident_id | hazard_type | state | severity | issued_at | expires_at | nonce | issuer_id | payload
- **Verification REQUIRED**: UI shows signature/trust status
- **Citizen UI**: Displays issuer and verification state

### Secrets Management

**Secrets NEVER in:**
- **Source control** (.git repository)
- **Frontend bundles** (JavaScript/TypeScript compiled output)
- **Public configuration** (unencrypted config files)
- **Embedded firmware** without secure storage (ESP32 NVS/efuse where supported)

**Secrets injection:**
- **Environment variables** (deployment-specific)
- **Secret manager** (AWS Secrets Manager, HashiCorp Vault, etc.)
- **Secure provisioning** (per-node HMAC secrets)

### SIMULATION Credentials Isolated

- **SIMULATION credentials cannot authenticate to LIVE** ingestion endpoints
- **Ground-truth endpoints require evaluator/admin role** (not citizen-facing)
- **Simulation alerts visibly labeled** (cannot present as live emergency)
- **Notification adapters default to sink/console** in SIMULATION mode

### Audit Trail Immutability

- **Append-only audit_events table**
- **Restricted DB permissions**: Application can INSERT, auditor/admin can SELECT, DELETE prohibited
- **Retention**: `security.audit_retention_days = 365`

---

## 20. Human Approval Requirement

**Reference**: Documents 02 (FR-042), 10, 16, 19

### Core Principle

**NexAlert recommends → authorized humans approve operational actions.**

### Configuration

- **alert.require_human_approval = true** (configuration-enforced)
- **flag.authority_auto_dispatch = false** (MUST REMAIN OFF)

### Response Recommendation Engine

- **Provides ranked recommended actions** based on incident state, severity, operational risk
- **Does NOT execute actions**: No autonomous dispatch
- **Human approval gate**: Authority operator reviews and explicitly approves

### Alert Lifecycle

```
DRAFT → PENDING_APPROVAL → (human approval) → APPROVED → ISSUED → DELIVERING → DELIVERED → ACKNOWLEDGED
```

### Prohibited

- **NO autonomous emergency dispatch**
- **NO automatic alert issuance** without human approval
- **NO circumventing approval workflow** through "emergency override" or other mechanism

### SOS Handling

- **Never auto-rejected**: SOS remains available regardless of hazard classification
- **Categorical tiers**: IMMEDIATE / HIGH / STANDARD / VERIFY (human review assigns tier)
- **Human intervention REQUIRED**: Even IMMEDIATE SOS reviewed by operator (rapid, but not autonomous)

---

## 21. Configuration Governance

**Reference**: Document 19

### Single Controlled Registry

**Configuration classes:**

| **Class** | **Change Policy** |
|---|---|
| **CONST** | Mathematical constant or fixed protocol value → Code review; rare change |
| **TUNABLE** | Operational model parameter → Config change + tests |
| **POLICY** | Authority/operator policy → Named owner + audit |
| **LIMIT** | Hard safety/resource ceiling → Must pass load/failure tests |
| **ENUM** | Controlled state/mode value → Code+contract change if altered |
| **FLAG** | Feature gate → Default OFF for experimental |
| **SECRET** | Credential/key material → Never stored in source/config repo |
| **PROFILE** | Environment bundle → Versioned snapshot |

### Runtime Precedence

1. Built-in safe default
2. Versioned application configuration file/profile
3. Environment-specific override
4. Secret manager / provisioning store (for secrets)
5. Runtime operator controls (only for explicitly whitelisted POLICY keys)

### Critical Flags (LOCKED)

- **fire_engine_v1 = true**: Mandatory for fire simulation
- **authority_auto_dispatch = false**: MUST REMAIN OFF (human approval required)
- **synthetic_live_merge = false**: MUST stay OFF in SIH/live unless specifically approved

### Configuration Changes

**Validation gates:**
- Schema validation (valid type, enum/range, unit)
- Cross-key consistency (e.g., warning_horizon < projection_horizon)
- Safety ceilings (no value exceeds documented hard limit)
- Secrets hygiene (no secrets in plain config)
- Feature compatibility (flag combinations valid)

---

## 22. Frontend Source-of-Truth Rule

**Reference**: Documents 01 (Invariant 26), 03, 12, 13, 14

### Core Principle

**Frontend renders authoritative backend state. Frontend NEVER invents hazard geometry, confidence scores, fire spread, incident state, or alert content.**

### Frontend MUST NOT

- **Invent hazard geometry**: No decorative radius/animation replacing authoritative fire spread
- **Recompute fire spread**: No independent arrival-time propagation in TypeScript
- **Invent confidence scores**: No client-side C_h computation
- **Generate incident state**: No client-side state machine transitions
- **Create alert content**: No fabricated hazard descriptions

### Frontend MAY

- **Display/simplify geometry**: Render authoritative geometry with appropriate styling
- **Cache for offline**: Store backend-provided emergency state for offline access
- **Compute UI-only conveniences**: Distance, bearing for display (NOT authoritative routing)
- **Interpolate animations**: Smooth transitions between authoritative states (clearly non-authoritative)

### Decorative Animations PROHIBITED

- **Where they could be mistaken for authoritative state**
- **Example prohibition**: Expanding circle animation representing "fire spreading" when no backend arrival-time update
- **Permitted**: Loading spinners, fade transitions, hover effects (clearly UI-only)

### LIVE/SIMULATION Mode

- **Changes data source ONLY**: Different backend endpoint or API filter
- **Does NOT change computation**: Same rendering logic, same state display

---

## 23. Safety-Critical Change Rules

**Reference**: Documents 16, 17, 18

### Safety-Critical Code Includes

- **HMAC verification**: Node authentication logic
- **Replay protection**: Sequence/timestamp checks
- **Signature verification**: Ed25519 event signing/verification
- **Baseline freeze logic**: Contamination prevention during CONFIRMED/CRITICAL
- **Hazard state machine**: Transition logic, hysteresis, persistence
- **Incident correlation**: Spatial/temporal thresholds, deterministic rules
- **Alert issuance**: Lifecycle state transitions, human approval gate
- **SOS handling**: Priority tiers, never-reject rule
- **Offline emergency path**: Local AP, cached state, captive portal

### Change Requirements

Changes to safety-critical code REQUIRE:

1. **Explicit test coverage**:
   - Unit tests for modified functions
   - Integration tests for affected paths
   - Relevant golden vectors (if mathematical)
   - Security tests (if authentication/authorization)

2. **Review by technical lead or designated safety reviewer**:
   - Architecture compliance verified
   - Non-negotiable invariants preserved
   - Test coverage adequate

3. **Documentation**:
   - What changed and why
   - Which invariants/requirements affected
   - Test evidence provided

4. **Validation**:
   - Relevant acceptance gates still pass
   - No regression in related test suites

### Prohibited

- **No silent refactoring** of safety-critical paths without test coverage
- **No "cleanup" changes** bundled with feature work (separate PR)
- **No circumventing review** through emergency merge or "hotfix" without post-review

---

## 24. AI/Vibe-Coding Rules

**Reference**: Documents 01, 18

### Four-Role Loop

**Architect** (design/plan) → **Builder** (implement) → **Red Team** (adversarial review) → **Verifier** (test/validate)

### AI Assistant MUST NOT

- **Silently redesign locked architecture**: Propose changes explicitly, wait for approval
- **Invent thresholds not in configuration registry**: Use documented config parameters
- **Duplicate mathematical definitions without parity tests**: Reuse reference math or validate parity
- **Create decorative simulation behavior replacing production computation**: Use same engine for LIVE/SIMULATION
- **Resolve specification ambiguities without surfacing them**: Ask, document, wait for decision
- **Skip tests and claim "done"**: Test-before-done rule mandatory

### AI Assistant MUST

- **Propose architectural changes before implementing**: Surface conflicts, explain rationale, wait for approval
- **Reference specification sources**: Cite Document X, Section Y when implementing requirements
- **Run relevant tests before claiming task complete**: Unit tests, integration tests, golden vectors
- **Surface ambiguities explicitly**: "Specification does not define X; options are A/B; recommend A because..."
- **Preserve non-negotiable invariants**: Check invariants before merge, block on violation

### When AI Encounters Locked Architecture Conflict

1. **Stop implementation**
2. **Surface the conflict**: "Specification X requires Y, but implementation constraint Z prevents it"
3. **Propose resolution options**: A (modify spec), B (modify constraint), C (alternative approach)
4. **Wait for human decision**
5. **Document resolution** in `DECISIONS.md`

---

## 25. Testing Requirements

**Reference**: Document 17

### Test-Before-Done

**No task is "complete" until relevant tests pass.**

### Verification Levels

| **Level** | **Name** | **Evidence** |
|---|---|---|
| **L0** | Static/schema | Schema validation, lint, static checks |
| **L1** | Unit | Unit tests, boundary tests, golden vectors |
| **L2** | Component | Subsystem end-to-end (node, telemetry, intelligence, GIS, alert) |
| **L3** | Integration | Cross-subsystem contracts (Edge→Master→Backend→UI traces) |
| **L4** | System | Scenario runs, fault injection, replay, multi-node |
| **L5** | Field/operational | Controlled trials, calibration, environmental trials, operator acceptance |

### 10 Acceptance Gates (All PASS/BLOCK)

| **Gate** | **Evidence** |
|---|---|
| **Gate A** | Build integrity (static checks, unit tests, schema validation, firmware build) |
| **Gate B** | Mathematical parity (golden vectors + Python↔embedded parity) |
| **Gate C** | Hardware readiness (sensor calibration, edge concurrency, power-cycle, local path) |
| **Gate D** | End-to-end path (canonical telemetry→incident→alert→UI trace) |
| **Gate E** | Resilience (internet loss, Master loss, reconnect, offline citizen path) |
| **Gate F** | Security (HMAC, replay, signed event, RBAC) |
| **Gate G** | Geo/fire (directional, barrier, dynamic recompute, geometry/risk) |
| **Gate H** | Scenario coverage (normal + rapid + slow + contradiction + multi-hazard) |
| **Gate I** | Soak/performance (representative soak + latency + resource stability) |
| **Gate J** | Demo readiness (operator walkthrough, citizen walkthrough, fault injection) |

### Security Tests

**Mandatory**: SEC-01 through SEC-14 (Document 16, Section 12)

### Fault Injection

**Required**: FI-01 through FI-14 (Document 17, Section 14)

### Performance Targets

- **Telemetry ingestion latency**: p95 ≤ 500ms (local network, normal load)
- **Critical alert decision latency**: p95 ≤ 2s (after required evidence available)
- **8+ hour soak**: No crash, leak, state corruption, queue divergence
- **24 hour extended soak**: Preferred pre-demo validation

---

## 26. Change-Control / Architecture-Deviation Rules

**Reference**: Documents 01, 18

### Specification Changes

**Require:**
- Explicit human approval
- Versioned specification update with change log
- Impact analysis across affected subsystems
- Migration path for existing code

### Architecture Deviations

**MUST be proposed with:**
- **Rationale**: Why deviation necessary
- **Alternatives considered**: What other approaches were evaluated
- **Risks documented**: What could go wrong
- **Mitigation**: How risks will be managed
- **Approval**: Explicit human approval required

### Configuration Changes

- **Schema validation**: Type, enum/range, unit checks pass
- **Version bump if breaking**: Increment config version
- **Migration path**: How existing deployments transition

### "Convenience" is NOT Justification

- **Convenience does NOT override locked architecture**
- **Implementation ease does NOT justify architectural deviation**
- **Developer preference does NOT supersede specification requirements**

### When Locked Architecture Conflicts with Reality

1. **Surface the conflict**: Describe locked requirement vs discovered constraint
2. **Propose resolution**: Options with tradeoffs
3. **Wait for approval**: Do NOT proceed without explicit human decision
4. **Document resolution**: Record in `DECISIONS.md` with rationale

---

## Summary

This constitution establishes **25 non-negotiable rules** governing NexAlert implementation. Every engineer (human and AI) working on NexAlert MUST:

1. **Preserve the 37 architecture invariants** from Document 01
2. **Follow subsystem ownership boundaries** (ESP32 vs Master vs Backend vs Frontend)
3. **Maintain parity** between Python reference math and C/C++ embedded implementations
4. **Preserve security invariants** (HMAC authentication, replay protection, secrets hygiene)
5. **Require human approval** for safety-critical actions (alert issuance, architectural changes)
6. **Surface ambiguities explicitly** rather than resolving silently
7. **Test before claiming done** (no task complete until tests pass)

**Violations of this constitution block merges, block releases, and require explicit human approval to resolve.**

---

**END OF IMPLEMENTATION CONSTITUTION**
