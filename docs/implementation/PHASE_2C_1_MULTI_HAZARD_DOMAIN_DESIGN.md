# PHASE 2C-1 MULTI-HAZARD DOMAIN DESIGN

**Date**: 2026-09-13  
**Mode**: AUTO / MAXIMUM EFFORT  
**Status**: ✅ **DESIGN COMPLETE**  
**Classification**: **A — READY FOR PHASE 2C IMPLEMENTATION**

---

## EXECUTIVE SUMMARY

This document defines the canonical multi-hazard domain model for NexAlert based on systematic analysis of the current Track B1/B2 architecture, Track C fire spread implementation, and authoritative architectural decisions.

**Key Finding**: The current architecture contains a **critical architectural contradiction** — the `Incident` model stores scalar `severity_index`, `confidence_index`, and `risk_index` at the incident level, violating the locked architectural decision that "each hazard assessment owns Evidence, Confidence, Severity, Operational Risk, and Hazard State."

**Canonical Domain Model**:
- One `Incident` MAY contain multiple independent `HazardAssessment` entities
- Each `HazardAssessment` owns its own evidence, confidence, severity, risk, and state
- `Incident` serves as correlation/grouping container, NOT as universal hazard scalar holder
- Multi-hazard incidents (FIRE + FLOOD simultaneously) are representable

**Recommended Persistence Strategy**: **Hybrid Relational + JSONB**
- Core hazard assessment fields remain relational (queryable, indexed, type-safe)
- Hazard-specific evidence stored in JSONB (fire geometry, flood depth, etc.)
- Preserves PostgreSQL query performance while supporting hazard extensibility

**Migration Strategy**: Adapt existing Track B2 `Incident` model to remove universal scalars, add proper `HazardAssessment` relationship

---

## 1. AUTHORITATIVE DECISIONS

### 1.1 Locked Architectural Decision (Phase 2C-1 Instructions)

**MUST**: The canonical domain model treats each hazard independently.

Each hazard assessment owns:
- Evidence
- Confidence
- Severity
- Operational Risk
- Hazard State

**Conceptual Model**:
```
Incident
├── HazardAssessment(FIRE)
│   ├── Evidence
│   ├── Confidence
│   ├── Severity
│   ├── Operational Risk
│   └── Hazard State
│
├── HazardAssessment(FLOOD)
│   ├── Evidence
│   ├── Confidence
│   ├── Severity
│   ├── Operational Risk
│   └── Hazard State
│
└── HazardAssessment(OTHER)
    ├── Evidence
    ├── Confidence
    ├── Severity
    ├── Operational Risk
    └── Hazard State
```

**MUST NOT**:
- Collapse into one universal severity scalar
- Collapse into one universal confidence scalar
- Collapse into one universal risk scalar
- Collapse into one universal hazard state
- Equate confidence with probability
- Equate operational risk with probability

---

### 1.2 Implementation Constitution (Section 13)

**Reference**: `docs/implementation/IMPLEMENTATION_CONSTITUTION.md`, Section 13

**Multi-Hazard Independence**:
> "Each hazard assessment (fire, flood, structural, gas) is independent. Evidence accumulation, confidence computation, and severity/risk estimation for one hazard do NOT directly depend on another hazard's state."

**Key Invariants**:
- Fire evidence does NOT require flood absence
- Flood confidence does NOT depend on fire state
- Hazard vectors remain independent until explicit correlation rules apply
- Multi-hazard correlation is a SEPARATE layer above individual assessments

---

### 1.3 Confidence ≠ Probability (Section 14)

**Reference**: `docs/implementation/IMPLEMENTATION_CONSTITUTION.md`, Section 14

> "Confidence is: How much the system trusts its own assessment given the available information. Confidence is NOT: The probability that the hazard exists."

**Confidence Definition**:
- Reflects data quality, sensor reliability, information freshness
- High confidence with low evidence = "We confidently see nothing unusual"
- Low confidence with high evidence = "Sensors degraded, results uncertain"

---

### 1.4 Risk ≠ Probability (Section 15)

**Reference**: `docs/implementation/IMPLEMENTATION_CONSTITUTION.md`, Section 15

> "Operational Risk is an operational decision/prioritization index. It is NOT a calibrated probability."

**Operational Risk Definition**:
- Combines hazard severity, exposure, timing, uncertainty
- Used for response prioritization, resource allocation
- NOT a statistical probability estimate

---

## 2. CURRENT ARCHITECTURE INVENTORY

### 2.1 Database Models

**Track B1 (Edge Intelligence)**:
- `HazardAssessment` (models.py:118-142)
  - Per-telemetry, per-hazard-type assessment
  - Fields: `evidence`, `confidence`, `severity`, `risk`, `state`, `information_condition`
  - Linked to single `telemetry_id`
  - **Status**: ✅ Correctly represents independent hazard assessments

**Track B2 (Regional Intelligence)**:
- `Incident` (models_b2.py:17-82)
  - Regional incident correlation container
  - Fields: `hazard_type`, `state`, `severity_index`, `confidence_index`, `risk_index`
  - **Status**: ❌ **ARCHITECTURAL CONTRADICTION** — stores universal scalars at incident level
  
- `RegionalHazardAssessment` (models_b2.py:131-181)
  - Fused multi-node assessment
  - Fields: `hazard_type`, `regional_evidence`, `regional_confidence`, `regional_severity`, `regional_risk`
  - Linked to `incident_id`
  - **Status**: ✅ Correctly represents hazard-specific regional fusion

- `IncidentObservation` (models_b2.py:85-129)
  - Links telemetry/hazard assessments to incidents
  - **Status**: ✅ Correct correlation tracking structure

---

### 2.2 Current API Contracts

**Track B2 API** (`routes_b2.py:23-41`):
```python
class IncidentResponse(BaseModel):
    incident_id: str
    hazard_type: str
    state: str
    information_condition: Optional[str]
    severity_index: Optional[float]      # ❌ Universal scalar
    risk_index: Optional[float]          # ❌ Universal scalar
    confidence_index: Optional[float]    # ❌ Universal scalar
    # ...
```

**Status**: ❌ Exposes universal scalars, contradicts canonical model

---

### 2.3 Intelligence Modules

**Regional Fusion** (`regional_fusion.py`):
- Correctly fuses per-hazard observations independently
- Returns `RegionalFusionResult` with hazard-specific metrics
- **Status**: ✅ Compatible with canonical model

**Incident Correlation** (`incident_correlation.py`):
- Uses `IncidentCandidate` with `severity_index`, `risk_index`
- Correlates observations spatially/temporally
- **Status**: ⚠️ Uses legacy scalar fields, needs adaptation

**B2 Coordinator** (`b2_coordinator.py`):
- Triggers fusion per hazard type
- Creates/updates incidents
- **Status**: ⚠️ Compatible logic, uses legacy persistence

---

## 3. ARCHITECTURAL CONTRADICTIONS

### 3.1 Critical Contradiction Matrix

| Component | Current Implementation | Canonical Model | Classification |
|-----------|----------------------|-----------------|----------------|
| **Incident.severity_index** | Single scalar at incident level | Per-hazard assessment | ❌ **C: ARCHITECTURAL CONTRADICTION** |
| **Incident.confidence_index** | Single scalar at incident level | Per-hazard assessment | ❌ **C: ARCHITECTURAL CONTRADICTION** |
| **Incident.risk_index** | Single scalar at incident level | Per-hazard assessment | ❌ **C: ARCHITECTURAL CONTRADICTION** |
| **Incident.hazard_type** | Single hazard type per incident | MAY contain multiple hazards | ❌ **C: ARCHITECTURAL CONTRADICTION** |
| **RegionalHazardAssessment** | Hazard-specific, linked to incident | Independent per hazard | ✅ **A: COMPATIBLE** |
| **HazardAssessment (Track B1)** | Per-telemetry, per-hazard | Independent per hazard | ✅ **A: COMPATIBLE** |
| **IncidentObservation** | Links observations to incidents | Correlation tracking | ✅ **A: COMPATIBLE** |

---

### 3.2 Contradiction Analysis

**Root Cause**: `Incident` model was designed as single-hazard container with universal scalars, not multi-hazard correlation container.

**Impact**:
1. **Cannot represent multi-hazard incidents** (FIRE + FLOOD simultaneously)
2. **Forces artificial aggregation** of incompatible hazard metrics
3. **Violates independence principle** — fire severity cannot be added to flood severity
4. **Breaks Track C integration** — fire-specific outputs have no hazard-specific home

**Evidence**:
- `Incident.hazard_type` is `String(32)`, not array/relationship
- Universal `severity_index` has no semantic meaning when mixing fire + flood
- API consumers receive scalar that doesn't represent any real hazard

---

## 4. CANONICAL DOMAIN MODEL

### 4.1 Core Entities

**Incident** (Correlation Container):
- Identity: `incident_id` (UUID)
- Purpose: Groups spatially/temporally correlated hazard observations
- Relationships: Contains multiple `HazardAssessment` entities
- Lifecycle: `state` (NEW → ACTIVE → ESCALATED → RESOLVED)
- **Does NOT own**: hazard-specific evidence, confidence, severity, risk

**HazardAssessment** (Hazard-Specific Intelligence):
- Identity: `assessment_id` (auto-increment)
- Belongs to: One `incident_id`
- Hazard Type: `hazard_type` (FIRE, FLOOD, STRUCTURAL, GAS, etc.)
- Owns:
  - `evidence`: Hazard-specific evidence index
  - `confidence`: Trust in assessment given available information
  - `severity`: Hazard intensity/consequence magnitude
  - `operational_risk`: Operational prioritization index
  - `state`: Lifecycle state (NORMAL, WATCH, SUSPECTED, CONFIRMED, CRITICAL, RESOLVED)
  - `information_condition`: Data quality (GOOD, DEGRADED, UNKNOWN)
- Hazard-Specific Data: JSONB field for fire geometry, flood depth, etc.

**Evidence** (Embedded in HazardAssessment):
- Source telemetry references
- Contributing node observations
- Quality/freshness metrics
- Provenance/version tracking

---

### 4.2 Entity Relationship Diagram

```
┌─────────────────────────────────────────────┐
│              Incident                        │
│  ┌───────────────────────────────────────┐  │
│  │ incident_id (UUID, PK)                │  │
│  │ state (NEW/ACTIVE/ESCALATED/RESOLVED) │  │
│  │ information_condition                  │  │
│  │ geometry (affected area)               │  │
│  │ centroid_lat, centroid_lon            │  │
│  │ first_observed_at                      │  │
│  │ last_observed_at                       │  │
│  │ resolved_at                            │  │
│  │ source_summary (contributing nodes)    │  │
│  │ created_by                             │  │
│  │ current_version                        │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
        │
        │ 1:N
        ▼
┌─────────────────────────────────────────────┐
│         HazardAssessment                     │
│  ┌───────────────────────────────────────┐  │
│  │ assessment_id (BigInt, PK)            │  │
│  │ incident_id (UUID, FK)                │  │
│  │ hazard_type (FIRE, FLOOD, etc.)       │  │
│  │ evidence (Double)                      │  │
│  │ confidence (Double)                    │  │
│  │ severity (Double)                      │  │
│  │ operational_risk (Double)              │  │
│  │ state (NORMAL/WATCH/.../RESOLVED)     │  │
│  │ information_condition                  │  │
│  │ hazard_specific_data (JSONB)          │  │
│  │ assessment_timestamp                   │  │
│  │ model_version                          │  │
│  │ created_at                             │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
        │
        │ N:M (via IncidentObservation)
        ▼
┌─────────────────────────────────────────────┐
│      TelemetryRecord / Node Observations     │
└─────────────────────────────────────────────┘
```

---

## 5. HAZARD ASSESSMENT OWNERSHIP

### 5.1 What Belongs to HazardAssessment

**Core Assessment**:
- `hazard_type`: FIRE, FLOOD, STRUCTURAL, GAS, etc.
- `evidence`: Numeric evidence index [0,1] or application-defined range
- `confidence`: Trust in assessment [0,1]
- `severity`: Hazard intensity/consequence [0,1] or application-defined
- `operational_risk`: Operational prioritization index [0,1]
- `state`: NORMAL, WATCH, SUSPECTED, CONFIRMED, CRITICAL, RESOLVED
- `information_condition`: GOOD, DEGRADED, UNKNOWN

**Provenance**:
- `assessment_timestamp`: When assessment was computed
- `model_version`: Algorithm/model version identifier
- `source_summary`: Contributing observations (node IDs, weights, counts)
- `created_at`: Database insertion timestamp

**Hazard-Specific Data** (JSONB):
- **FIRE**: `{ "geometry": {...}, "perimeter_m": 500, "spread_rate_m_s": 0.5, "ignition_source": "..." }`
- **FLOOD**: `{ "depth_m": 2.5, "flow_velocity_m_s": 3.0, "inundation_area_m2": 10000 }`
- **STRUCTURAL**: `{ "damage_type": "collapse_risk", "affected_floors": [1,2,3] }`

**Relationships**:
- `incident_id`: Which incident this assessment belongs to
- Links to contributing telemetry via `IncidentObservation`

---

### 5.2 What Does NOT Belong to HazardAssessment

**Not Stored**:
- Other hazards' metrics (fire assessment does NOT store flood data)
- Universal/cross-hazard aggregated scalars
- Operational response actions (belong to separate action/alert domain)
- Citizen-facing alert text (generated from assessment, not stored in it)

---

## 6. EVIDENCE MODEL

### 6.1 Evidence Representation

**Evidence** is embedded in `HazardAssessment`, not a separate table.

**Evidence Components**:
- **Primary Measurement**: Telemetry observation that triggered/updated assessment
- **Corroborating Observations**: Additional nodes/sensors supporting conclusion
- **Quality Metrics**: Sensor health, calibration status, data freshness
- **Provenance**: Source node IDs, observation timestamps, fusion weights

**Evidence Structure**:
```
HazardAssessment
├── evidence: 0.85 (numeric index)
├── confidence: 0.92 (trust in evidence)
├── source_summary: { "nodes": ["NODE-001", "NODE-042"], "weights": [0.6, 0.4], "count": 2 }
└── hazard_specific_data: { "primary_sensor": "temp_c", "primary_value": 75.0, ... }
```

**Evidence vs Confidence Distinction**:
- **Evidence**: "How much data supports the hazard hypothesis"
- **Confidence**: "How much we trust the data/assessment"
- High evidence + low confidence = "Sensors degraded, but reading is concerning"
- Low evidence + high confidence = "No hazard detected, sensors functioning well"

---

### 6.2 Evidence Quality Attributes

**Per Assessment**:
- `information_condition`: GOOD, DEGRADED, UNKNOWN
- Contributing node reliability (via `NodeStatus` tracking)
- Temporal freshness (decay function in regional fusion)
- Spatial agreement (multiple nodes vs single node)

**Stored in**:
- `HazardAssessment.information_condition`
- `HazardAssessment.source_summary` (JSONB with node weights/freshness)
- `RegionalHazardAssessment.freshness_index`
- `RegionalHazardAssessment.agreement_index`

---

## 7. CONFIDENCE / SEVERITY / RISK SEPARATION

### 7.1 Confidence

**Definition**: How trustworthy the assessment is given available information.

**Range**: [0, 1]

**Factors**:
- Sensor health/calibration status
- Data freshness
- Inter-node agreement
- Information condition (GOOD/DEGRADED/UNKNOWN)
- Historical reliability of contributing nodes

**What Confidence Is NOT**:
- NOT the probability the hazard exists
- NOT severity magnitude
- NOT operational priority

**Example Scenarios**:
- High confidence (0.9) + Low evidence (0.1) = "We confidently see nothing unusual"
- Low confidence (0.3) + High evidence (0.8) = "Sensors degraded, but readings are concerning"

---

### 7.2 Severity

**Definition**: Hazard intensity/consequence magnitude according to the hazard model.

**Range**: [0, 1] or hazard-specific range

**Factors** (Hazard-Dependent):
- **FIRE**: Temperature, spread rate, area, fuel load
- **FLOOD**: Water depth, flow velocity, inundation area
- **STRUCTURAL**: Damage extent, collapse risk
- **GAS**: Concentration, exposure duration, toxicity

**What Severity Is NOT**:
- NOT confidence level
- NOT operational risk (severity ignores exposure/context)
- NOT probability
- NOT universal across hazards (fire severity ≠ flood severity semantically)

**Example**:
- Fire severity 0.8 = "Intense fire, rapid spread"
- Flood severity 0.8 = "Deep water, high velocity"
- These cannot be directly compared or averaged

---

### 7.3 Operational Risk

**Definition**: Operational prioritization/decision index combining hazard state, exposure, timing, uncertainty.

**Range**: [0, 1]

**Factors**:
- Hazard severity
- Population exposure
- Infrastructure exposure
- Temporal urgency (spreading vs contained)
- Information uncertainty (confidence)
- Response capacity availability

**What Operational Risk Is NOT**:
- NOT a calibrated statistical probability
- NOT pure severity (includes exposure/context)
- NOT confidence (includes severity magnitude)
- NOT universal across hazards without explicit correlation rules

**Computation** (Application-Defined):
```
operational_risk = f(severity, exposure, urgency, confidence)
```

**Example**:
- Fire in unpopulated area: high severity (0.9), low risk (0.3)
- Small fire near hospital: low severity (0.2), high risk (0.8)

---

## 8. HAZARD STATE MACHINE

### 8.1 State Ownership

**States Belong To**: `HazardAssessment`, NOT `Incident`

**Hazard States**:
- **NORMAL**: Baseline, no hazard detected
- **WATCH**: Conditions monitored, not yet hazardous
- **SUSPECTED**: Potential hazard, low confidence/evidence
- **CONFIRMED**: Hazard confirmed, actionable
- **CRITICAL**: Severe hazard, immediate response required
- **RESOLVED**: Hazard no longer active

**Incident States** (Separate):
- **NEW**: Just created, pending assessment
- **ACTIVE**: One or more hazards confirmed
- **ESCALATED**: Hazard(s) reached critical or spreading
- **RESOLVED**: All constituent hazards resolved

---

### 8.2 State Transition Rules

**HazardAssessment State Transitions** (Per Reference Python State Machine):
- NORMAL → WATCH (elevated baseline, insufficient evidence)
- WATCH → SUSPECTED (evidence threshold crossed, confidence insufficient)
- SUSPECTED → CONFIRMED (confidence + evidence thresholds met, persistence satisfied)
- CONFIRMED → CRITICAL (severity threshold crossed)
- CRITICAL → RESOLVED (evidence dropped, hold period satisfied)
- RESOLVED → NORMAL (all clear, baseline unfrozen)

**State is Per-Hazard**:
```
Incident (state=ACTIVE)
├── HazardAssessment(FIRE, state=CRITICAL)
└── HazardAssessment(FLOOD, state=WATCH)
```

**Incident State Derivation**:
- `Incident.state = ACTIVE` if ANY hazard is CONFIRMED or CRITICAL
- `Incident.state = ESCALATED` if ANY hazard is CRITICAL
- `Incident.state = RESOLVED` if ALL hazards are RESOLVED

---

### 8.3 State Timestamp Tracking

**Per HazardAssessment**:
- `assessment_timestamp`: When current assessment was computed
- `created_at`: When assessment record was inserted
- State transition history: Optional `state_history` JSONB field

**Per Incident**:
- `first_observed_at`: When incident was created
- `last_observed_at`: When any hazard was last updated
- `resolved_at`: When all hazards resolved

---

## 9. INCIDENT ↔ HAZARDASSESSMENT RELATIONSHIP

### 9.1 Cardinality

**Incident : HazardAssessment = 1 : N**

- One `Incident` MAY contain multiple `HazardAssessment` entities
- One `HazardAssessment` belongs to exactly one `Incident`
- Multiple `HazardAssessment` entities of the SAME hazard type MAY belong to different incidents

**Examples**:

**Case 1: Single-Hazard Incident**
```
Incident A (FIRE)
└── HazardAssessment(FIRE, severity=0.8, state=CONFIRMED)
```

**Case 2: Multi-Hazard Incident**
```
Incident B (MULTI-HAZARD)
├── HazardAssessment(FIRE, severity=0.6, state=CONFIRMED)
└── HazardAssessment(FLOOD, severity=0.4, state=WATCH)
```

**Case 3: Separate Incidents, Same Hazard Type**
```
Incident C (FIRE, Location A)
└── HazardAssessment(FIRE, severity=0.7, state=CONFIRMED)

Incident D (FIRE, Location B)
└── HazardAssessment(FIRE, severity=0.5, state=SUSPECTED)
```

---

### 9.2 Correlation Logic

**When to Create New Incident vs Add to Existing**:

**Spatial-Temporal Correlation** (from `incident_correlation.py`):
- Same hazard type
- Within correlation radius (default 50m)
- Within correlation time window (default 30s)
→ Add to existing incident

**Clearly Separate**:
- Different hazard types (unless explicitly co-occurring)
- Beyond separation radius (default 5km)
- Beyond time window
→ Create new incident

**Multi-Hazard Co-Occurrence**:
- Same location + same time + different hazard types
→ Add both hazard assessments to same incident

---

### 9.3 Incident Identity

**Current**: `incident_id` (UUID)

**Future Deterministic Identity** (noted in `incident_correlation.py`):
- Hash of (hazard_type, spatial_key, temporal_window)
- Enables idempotent incident creation
- Out of scope for Phase 2C

---

## 10. MULTI-HAZARD CORRELATION MODEL

### 10.1 Correlation Without Universal Scalars

**Problem**: How to correlate events when hazards have independent metrics?

**Solution**: Correlation operates on observation metadata, NOT hazard-specific evidence.

**Correlation Factors**:
- **Spatial**: Location proximity (lat/lon within radius)
- **Temporal**: Observation time proximity (within window)
- **Source**: Contributing nodes/telemetry
- **NOT**: Severity magnitude, evidence strength, confidence level

**From `incident_correlation.py`**:
```python
def should_correlate_with_incident(
    observation_location: Tuple[float, float],
    observation_time: datetime,
    incident: IncidentCandidate,
    merge_radius_m: float,
    merge_window_s: float
) -> bool:
    # Spatial correlation
    if distance_m(observation_location, incident.centroid) <= merge_radius_m:
        # Temporal correlation
        if abs((observation_time - incident.last_observed_at).total_seconds()) <= merge_window_s:
            return True
    return False
```

**Key Insight**: Correlation does NOT require comparable severity/risk scalars.

---

### 10.2 Multi-Hazard Fusion

**Regional Fusion is Per-Hazard**:
- Each hazard type fused independently
- Fire observations fused into fire regional assessment
- Flood observations fused into flood regional assessment
- Results stored in separate `RegionalHazardAssessment` rows

**From `b2_coordinator.py`**:
```python
for hazard_type in hazard_types:
    await self._process_hazard_type(
        session=session,
        node_id=node_id,
        hazard_type=hazard_type,  # Process independently
        measurement_ts=measurement_ts
    )
```

**No Cross-Hazard Fusion**: Fire evidence does NOT influence flood confidence.

---

## 11. PERSISTENCE STRATEGY COMPARISON

### 11.1 Option A: JSONB-Only HazardAssessment

**Structure**:
```sql
CREATE TABLE hazard_assessments (
    assessment_id BIGINT PRIMARY KEY,
    incident_id UUID NOT NULL,
    hazard_type VARCHAR(32) NOT NULL,
    assessment_data JSONB NOT NULL,  -- Contains evidence, confidence, severity, risk, state, etc.
    created_at TIMESTAMP NOT NULL
);
```

**Pros**:
- Maximum flexibility for hazard-specific fields
- Easy schema evolution (add fields without migration)
- Fire can store geometry, flood can store depth without cross-contamination

**Cons**:
- ❌ **Loses type safety** (evidence could be string, null, object)
- ❌ **Loses queryability** (cannot index JSONB fields efficiently for range queries)
- ❌ **Loses PostgreSQL query optimization** (no statistics on JSONB subfields)
- ❌ **Breaks existing queries** (current code queries `severity`, `confidence` directly)
- ❌ **Harder to enforce NOT NULL constraints** on core fields
- ❌ **Violates NexAlert preference for relational over document stores**

**Verdict**: ❌ **REJECTED** — Flexibility does not justify loss of type safety and queryability.

---

### 11.2 Option B: Relational HazardAssessment Rows

**Structure**:
```sql
CREATE TABLE hazard_assessments (
    assessment_id BIGINT PRIMARY KEY,
    incident_id UUID NOT NULL,
    hazard_type VARCHAR(32) NOT NULL,
    evidence DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    severity DOUBLE PRECISION,
    operational_risk DOUBLE PRECISION,
    state VARCHAR(32),
    information_condition VARCHAR(32),
    assessment_timestamp TIMESTAMP NOT NULL,
    model_version VARCHAR(64),
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
);
CREATE INDEX idx_hazard_assess_incident_type ON hazard_assessments(incident_id, hazard_type);
CREATE INDEX idx_hazard_assess_state ON hazard_assessments(state);
```

**Pros**:
- ✅ **Type safety**: Evidence/confidence/severity are DOUBLE PRECISION
- ✅ **Queryable**: Can index and query `WHERE severity > 0.7`
- ✅ **PostgreSQL optimizations**: Statistics, query planner works correctly
- ✅ **Enforces NOT NULL** where required
- ✅ **Matches existing Track B1 HazardAssessment pattern**
- ✅ **Compatible with PostGIS** (can add Geography column for fire geometry)

**Cons**:
- ❌ **No place for hazard-specific data** (fire geometry, flood depth)
- ❌ **Rigid schema** (adding new core fields requires migration)

**Verdict**: ⚠️ **INCOMPLETE** — Solves core assessment persistence, but no place for hazard-specific data.

---

### 11.3 Option C: Hybrid Relational + JSONB (RECOMMENDED)

**Structure**:
```sql
CREATE TABLE hazard_assessments (
    assessment_id BIGINT PRIMARY KEY,
    incident_id UUID NOT NULL,
    hazard_type VARCHAR(32) NOT NULL,
    
    -- Core assessment (relational, queryable, indexed)
    evidence DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    severity DOUBLE PRECISION,
    operational_risk DOUBLE PRECISION,
    state VARCHAR(32),
    information_condition VARCHAR(32),
    
    -- Hazard-specific data (JSONB, flexible)
    hazard_specific_data JSONB,
    
    -- Provenance
    assessment_timestamp TIMESTAMP NOT NULL,
    model_version VARCHAR(64),
    source_summary JSONB,
    
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
);

CREATE INDEX idx_hazard_assess_incident_type ON hazard_assessments(incident_id, hazard_type);
CREATE INDEX idx_hazard_assess_state ON hazard_assessments(state);
CREATE INDEX idx_hazard_assess_severity ON hazard_assessments(severity) WHERE severity IS NOT NULL;
```

**Hazard-Specific Data Examples**:
```json
// FIRE
{
  "geometry": {"type": "Polygon", "coordinates": [...]},
  "perimeter_m": 500,
  "spread_rate_m_s": 0.5,
  "ignition_source": "electrical",
  "fuel_load": "high"
}

// FLOOD
{
  "depth_m": 2.5,
  "flow_velocity_m_s": 3.0,
  "inundation_area_m2": 10000,
  "source": "river_overflow"
}
```

**Pros**:
- ✅ **Type safety** for core assessment fields
- ✅ **Queryable** evidence/confidence/severity/risk
- ✅ **Indexed** for performance
- ✅ **Flexible** hazard-specific data
- ✅ **No cross-contamination** (fire data doesn't pollute flood schema)
- ✅ **Matches NexAlert architecture** (PostgreSQL + JSONB where appropriate)
- ✅ **Supports future hazards** without schema migration
- ✅ **Compatible with PostGIS** (fire geometry can be Geography column if needed)

**Cons**:
- ⚠️ **Hazard-specific JSONB not indexed** (acceptable, not queried directly)
- ⚠️ **Application must validate JSONB contents** (no schema enforcement)

**Verdict**: ✅ **RECOMMENDED** — Best balance of type safety, queryability, and flexibility.

---

## 12. RECOMMENDED PERSISTENCE DESIGN

### 12.1 Core Schema

**Incident Table** (MODIFIED from current):
```sql
CREATE TABLE incidents (
    incident_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Incident-level metadata (NO hazard-specific scalars)
    state VARCHAR(32) NOT NULL,  -- NEW, ACTIVE, ESCALATED, RESOLVED
    information_condition VARCHAR(32),  -- GOOD, DEGRADED, UNKNOWN
    
    -- Geometry (affected area)
    geometry GEOGRAPHY(GEOMETRY, 4326),
    centroid_lat DOUBLE PRECISION,
    centroid_lon DOUBLE PRECISION,
    
    -- Temporal tracking
    first_observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Provenance
    source_summary JSONB,  -- Contributing node IDs, observation counts
    created_by VARCHAR(32) NOT NULL,  -- SYSTEM, OPERATOR, CITIZEN_SOS
    resolution_reason VARCHAR(128),
    
    -- Versioning
    current_version BIGINT NOT NULL DEFAULT 1,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- REMOVED: hazard_type (incident can contain multiple hazards)
-- REMOVED: severity_index (belongs to HazardAssessment)
-- REMOVED: confidence_index (belongs to HazardAssessment)
-- REMOVED: risk_index (belongs to HazardAssessment)
```

**HazardAssessment Table** (NEW, based on Track B1 pattern):
```sql
CREATE TABLE hazard_assessments (
    assessment_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    incident_id UUID NOT NULL,
    hazard_type VARCHAR(32) NOT NULL,  -- FIRE, FLOOD, STRUCTURAL, GAS
    
    -- Core assessment (relational)
    evidence DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    severity DOUBLE PRECISION,
    operational_risk DOUBLE PRECISION,
    state VARCHAR(32),  -- NORMAL, WATCH, SUSPECTED, CONFIRMED, CRITICAL, RESOLVED
    information_condition VARCHAR(32),  -- GOOD, DEGRADED, UNKNOWN
    
    -- Hazard-specific data (JSONB, flexible)
    hazard_specific_data JSONB,
    
    -- Provenance
    assessment_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    model_version VARCHAR(64),
    source_summary JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id) ON DELETE CASCADE
);

CREATE INDEX idx_hazard_assess_incident ON hazard_assessments(incident_id);
CREATE INDEX idx_hazard_assess_type ON hazard_assessments(hazard_type);
CREATE INDEX idx_hazard_assess_state ON hazard_assessments(state);
CREATE INDEX idx_hazard_assess_incident_type ON hazard_assessments(incident_id, hazard_type);
```

**RegionalHazardAssessment Table** (UNCHANGED):
- Already correctly represents hazard-specific regional fusion
- Links to `incident_id`
- Stores per-hazard regional metrics

**IncidentObservation Table** (UNCHANGED):
- Correctly links telemetry/node observations to incidents
- Can link to `hazard_assessment_id` (FK to new table)

---

### 12.2 Migration Strategy

**Phase 2C Implementation Steps**:

1. **Add HazardAssessment table** (new relational structure)
2. **Migrate existing Incident data**:
   - For each `Incident` with `severity_index/confidence_index/risk_index`:
   - Create corresponding `HazardAssessment` row with same values
   - Link to `incident_id`
   - Preserve `hazard_type` in assessment
3. **Remove universal scalars from Incident**:
   - Drop columns: `severity_index`, `confidence_index`, `risk_index`, `hazard_type`
   - Keep: `state`, `information_condition`, geometry, temporal fields
4. **Update API contracts** to return hazard assessments array
5. **Update intelligence modules** to write to HazardAssessment table
6. **Update queries** to join through HazardAssessment

**Backward Compatibility**:
- Keep deprecated API fields temporarily (Phase 2C-2)
- Compute derived `severity_index` as `MAX(hazard_assessments.severity)` for legacy consumers
- Mark as deprecated in API documentation

---

## 13. API CONTRACT DESIGN

### 13.1 Canonical Incident Response

```typescript
interface IncidentResponse {
  incident_id: string;
  state: "NEW" | "ACTIVE" | "ESCALATED" | "RESOLVED";
  information_condition: "GOOD" | "DEGRADED" | "UNKNOWN";
  
  // Geometry
  geometry?: GeoJSON;
  centroid?: { lat: number; lon: number };
  
  // Temporal
  first_observed_at: string;  // ISO 8601
  last_observed_at: string;   // ISO 8601
  resolved_at?: string;
  
  // Hazard assessments (array, independent)
  hazard_assessments: HazardAssessmentResponse[];
  
  // Provenance
  source_summary?: { nodes: string[]; observation_count: number };
  created_by: string;
  current_version: number;
  created_at: string;
  updated_at: string;
}

interface HazardAssessmentResponse {
  assessment_id: number;
  hazard_type: "FIRE" | "FLOOD" | "STRUCTURAL" | "GAS";
  
  // Core assessment
  evidence?: number;
  confidence?: number;
  severity?: number;
  operational_risk?: number;
  state: "NORMAL" | "WATCH" | "SUSPECTED" | "CONFIRMED" | "CRITICAL" | "RESOLVED";
  information_condition: "GOOD" | "DEGRADED" | "UNKNOWN";
  
  // Hazard-specific data
  hazard_specific_data?: {
    // FIRE: { geometry, perimeter_m, spread_rate_m_s, ... }
    // FLOOD: { depth_m, flow_velocity_m_s, inundation_area_m2, ... }
    [key: string]: any;
  };
  
  // Provenance
  assessment_timestamp: string;
  model_version?: string;
  source_summary?: any;
  created_at: string;
}
```

---

### 13.2 API Endpoints

**GET /api/incidents**:
- Returns array of `IncidentResponse`
- Each includes `hazard_assessments` array
- Query params: `state`, `active_only`, `limit`

**GET /api/incidents/{incident_id}**:
- Returns single `IncidentResponse`
- Includes all hazard assessments for that incident

**GET /api/incidents/{incident_id}/hazards/{hazard_type}**:
- Returns filtered hazard assessments for specific type
- Example: `/incidents/123/hazards/FIRE`

**GET /api/hazards/{hazard_type}**:
- Returns all hazard assessments of given type across incidents
- Example: `/hazards/FIRE` returns all fire assessments

---

## 14. TRACK B2 COMPATIBILITY

### 14.1 Current Track B2 Dependencies

**Intelligence Modules**:
- `regional_fusion.py`: ✅ Compatible — returns per-hazard fusion results
- `incident_correlation.py`: ⚠️ Uses `IncidentCandidate` with scalar fields
- `b2_coordinator.py`: ⚠️ Creates incidents with scalar fields

**API**:
- `routes_b2.py`: ❌ Exposes `severity_index`, `confidence_index`, `risk_index`

**Tests**:
- `test_regional_fusion.py`: ✅ 10/10 pass — tests per-hazard fusion
- `test_mqtt_b2_integration.py`: ⚠️ May test incident creation with scalars

---

### 14.2 Required Adaptations

**Phase 2C-2 Changes**:

1. **`incident_correlation.py`**:
   - Update `IncidentCandidate` to remove scalar fields
   - Update `IncidentCreationResult` to remove scalar fields
   - Correlation logic unchanged (spatial/temporal only)

2. **`b2_coordinator.py`**:
   - After incident creation, create `HazardAssessment` row(s)
   - Link regional fusion results to hazard assessment, not incident scalars
   - Preserve per-hazard processing logic

3. **`routes_b2.py`**:
   - Update `IncidentResponse` to include `hazard_assessments` array
   - Optionally keep deprecated scalar fields (compute as MAX)
   - Mark deprecated fields in documentation

4. **Tests**:
   - Update test assertions to check `hazard_assessments` array
   - Verify multi-hazard incident creation
   - Verify independent hazard state tracking

---

### 14.3 Non-Breaking Migration Path

**Step 1**: Add `HazardAssessment` table (new)  
**Step 2**: Dual-write (write to both Incident scalars AND HazardAssessment)  
**Step 3**: Update consumers to read from `hazard_assessments` array  
**Step 4**: Remove Incident scalar fields (breaking change, major version bump)  

**Estimated Effort**: 2-3 days implementation + 1 day testing

---

## 15. TRACK C COMPATIBILITY

### 15.1 Track C Fire Spread Outputs

**Current Track C** (from plan, not fully implemented):
- Fire spread simulation produces fire geometry (Polygon/MultiPolygon)
- Outputs: current/warning/projection fire zones
- Risk surface generation (continuous operational risk index)
- Exposure calculation (population/infrastructure at risk)

**Track C Tables** (`models_c.py`):
- `FireSimulation`: Fire spread simulation metadata
- `FireGeometry`: Physical fire footprint and zones
- `RiskSurface`: Risk heatmap
- `Exposure`: Exposure metrics

---

### 15.2 Integration with Canonical Model

**Fire Spread → HazardAssessment Mapping**:

```
FireSimulation (Track C)
├── FireGeometry (current/warning/projection)
│   ├── physical_footprint (Polygon)
│   └── operational_buffer (Polygon)
└── RiskSurface (continuous risk index)

       ↓ Maps to ↓

HazardAssessment (Track B2)
├── hazard_type: "FIRE"
├── severity: (derived from fire spread metrics)
├── operational_risk: (from RiskSurface max or integrated risk)
├── state: (derived from fire extent/spread rate)
└── hazard_specific_data: {
      "geometry": FireGeometry.physical_footprint,
      "perimeter_m": ...,
      "spread_rate_m_s": ...,
      "zones": {
        "current": ...,
        "warning": ...,
        "projection": ...
      }
    }
```

**Key Insight**: Fire-specific outputs (geometry, spread rate, zones) live in `hazard_specific_data` JSONB, NOT as universal Incident fields.

---

### 15.3 Track C Does Not Break Generic Model

**What Track C Adds**:
- Fire-specific simulation logic
- Fire-specific geometry (stored in JSONB)
- Fire-specific risk surface

**What Track C Does NOT Add**:
- Universal geometry field (fire geometry is fire-specific)
- Universal spread rate field
- Universal zone concept

**Verification**: Flood hazard can be added later without modifying Track C or generic `HazardAssessment` structure.

---

## 16. VERSIONING AND PROVENANCE

### 16.1 Assessment Versioning

**Per HazardAssessment**:
- `assessment_timestamp`: When assessment was computed
- `model_version`: Algorithm/model version (e.g., "state_machine_v1.2", "fire_spread_v2.0")
- `created_at`: Database insertion timestamp

**Per Incident**:
- `current_version`: Incremented on each incident update
- `updated_at`: Last modification timestamp

**State Transition History** (Optional Future):
- `state_history` JSONB field with transition log:
  ```json
  [
    {"from": "WATCH", "to": "SUSPECTED", "timestamp": "...", "reason": "evidence threshold"},
    {"from": "SUSPECTED", "to": "CONFIRMED", "timestamp": "...", "reason": "confidence met"}
  ]
  ```

---

### 16.2 Evidence Provenance

**Per HazardAssessment**:
- `source_summary` JSONB:
  ```json
  {
    "nodes": ["NODE-001", "NODE-042"],
    "telemetry_ids": ["...", "..."],
    "weights": [0.6, 0.4],
    "observation_count": 2,
    "primary_node": "NODE-001"
  }
  ```

**Per IncidentObservation**:
- Links specific telemetry/hazard assessment to incident
- Tracks contribution weight
- Marks primary detection vs corroborating observation

---

### 16.3 Audit Trail

**Immutable Audit Events** (Existing Pattern):
- `audit_events` table (if exists) logs:
  - Incident creation
  - Hazard assessment creation/update
  - State transitions
  - Manual interventions

**Provenance Required For**:
- Algorithm version (reproducibility)
- Contributing observations (traceability)
- State transition reasons (explainability)
- Manual vs automated assessment (accountability)

---

## 17. SECURITY AND AUDIT CONSIDERATIONS

### 17.1 Assessment Source

**`created_by` Field**:
- `SYSTEM`: Automated intelligence pipeline
- `OPERATOR`: Manual operator override
- `CITIZEN_SOS`: Citizen-initiated emergency report
- `SIMULATION`: Test/training scenario

**Required**: Every hazard assessment MUST have provenance.

---

### 17.2 Immutability Requirements

**Immutable**:
- Historical hazard assessments (append-only)
- Telemetry records (already immutable)
- Incident creation event

**Mutable**:
- Incident state (lifecycle)
- Current hazard assessment (updated as evidence changes)
- Incident geometry (expands as observations added)

**Pattern**: Keep latest assessment in `hazard_assessments` table, optionally archive history to separate `hazard_assessment_history` table.

---

### 17.3 Access Control

**Out of Scope**: Detailed RBAC design

**Requirements**:
- Operators can view all incidents/assessments
- Operators can manually create/update assessments (with audit trail)
- Citizens see filtered/public assessments only
- Backend writes assessments as SYSTEM

---

## 18. MIGRATION STRATEGY

### 18.1 Phase 2C-2 Implementation Order

**Step 1: Database Schema**:
1. Create `hazard_assessments` table (hybrid relational + JSONB)
2. Keep existing `incidents` table temporarily
3. Run migration to copy existing incident scalars to hazard assessments

**Step 2: API Layer**:
1. Update `IncidentResponse` to include `hazard_assessments` array
2. Keep deprecated scalar fields (compute from assessments)
3. Mark deprecated fields in API documentation

**Step 3: Intelligence Modules**:
1. Update `b2_coordinator.py` to create hazard assessments
2. Update `incident_correlation.py` to remove scalar dependencies
3. Link regional fusion outputs to hazard assessments

**Step 4: Testing**:
1. Verify multi-hazard incident creation
2. Verify independent hazard state tracking
3. Verify Track B2 tests still pass
4. Add new multi-hazard test cases

**Step 5: Cleanup (Phase 2C-3)**:
1. Remove deprecated API fields (major version bump)
2. Remove Incident scalar columns from database
3. Update all consumers

---

### 18.2 Data Migration Script

**Pseudo-Code**:
```sql
-- For each existing incident
INSERT INTO hazard_assessments (
    incident_id,
    hazard_type,  -- From Incident.hazard_type
    evidence,     -- Derive from regional_hazard_assessments
    confidence,   -- From Incident.confidence_index
    severity,     -- From Incident.severity_index
    operational_risk,  -- From Incident.risk_index
    state,        -- From Incident.state (map to hazard state)
    information_condition,  -- From Incident.information_condition
    assessment_timestamp,   -- From Incident.last_observed_at
    model_version,
    created_at
)
SELECT 
    incident_id,
    hazard_type,
    NULL,  -- evidence (not stored at incident level currently)
    confidence_index,
    severity_index,
    risk_index,
    state,  -- May need state mapping
    information_condition,
    last_observed_at,
    'migrated_v1',
    created_at
FROM incidents
WHERE severity_index IS NOT NULL OR confidence_index IS NOT NULL;
```

**Validation**:
- Count incidents before = count hazard assessments after
- Spot-check values match

---

## 19. IMPLEMENTATION PHASES

### 19.1 Phase 2C-2: Core Implementation (Estimated: 3-5 days)

**Deliverables**:
1. ✅ Create `hazard_assessments` table (hybrid schema)
2. ✅ Data migration script
3. ✅ Update `IncidentResponse` API model
4. ✅ Update `b2_coordinator.py` to create hazard assessments
5. ✅ Update `incident_correlation.py` to remove scalars
6. ✅ Create/update tests for multi-hazard scenarios
7. ✅ Run existing Track B2 tests (verify no regressions)
8. ✅ Create Phase 2C-2 completion document

**Success Criteria**:
- Multi-hazard incident representable (FIRE + FLOOD simultaneously)
- All Phase 2C-1 acceptance cases (1-10) representable
- Track B2 tests pass
- No regressions

---

### 19.2 Phase 2C-3: Cleanup (Estimated: 1-2 days)

**Deliverables**:
1. Remove deprecated Incident scalar fields
2. Remove deprecated API response fields
3. Update all API consumers
4. Major version bump (breaking change)

**Success Criteria**:
- No legacy scalar fields remain
- API documentation reflects canonical model
- All tests pass

---

### 19.3 Phase 2C-4: Track C Integration (Estimated: 2-3 days)

**Deliverables**:
1. Map fire spread outputs to `hazard_specific_data`
2. Create fire hazard assessment from Track C simulation
3. Test fire + flood multi-hazard scenario

**Success Criteria**:
- Fire geometry stored in JSONB
- Flood can be added without modifying fire logic
- Track C tests pass

---

## 20. RISKS AND OPEN QUESTIONS

### 20.1 Risks

**Risk 1: API Breaking Change**
- **Impact**: HIGH — Existing API consumers break
- **Mitigation**: Deprecation period, dual-write, backward-compatible response

**Risk 2: Performance**
- **Impact**: MEDIUM — Join through HazardAssessment adds query complexity
- **Mitigation**: Proper indexing, test with realistic data volume

**Risk 3: Migration Data Loss**
- **Impact**: HIGH — Incorrect migration loses incident data
- **Mitigation**: Dry-run migration, validation checks, backup before migration

**Risk 4: Incomplete Hazard-Specific Data Schema**
- **Impact**: LOW — JSONB field has no enforced schema
- **Mitigation**: Application-level validation, document expected schema per hazard type

---

### 20.2 Open Questions

**Q1: How to aggregate hazard assessments for UI display?**
- **Answer**: UI displays per-hazard assessments independently, OR shows "most severe" hazard
- **Decision**: Defer to UI design phase

**Q2: How to compute incident-level operational risk from multiple hazards?**
- **Answer**: Application-defined aggregation (MAX, weighted sum, etc.)
- **Decision**: Document as application concern, not database schema concern

**Q3: Should state transition history be stored?**
- **Answer**: Optional `state_history` JSONB field, not required for MVP
- **Decision**: Add in Phase 2C-3 if needed

**Q4: How to handle hazard assessment expiration?**
- **Answer**: Track `assessment_timestamp`, application decides staleness threshold
- **Decision**: Out of scope for Phase 2C

---

## 21. ACCEPTANCE CRITERIA

### 21.1 The Design is Acceptable If It Can Represent

✅ **CASE 1**: One incident with only FIRE
```
Incident A
└── HazardAssessment(FIRE, severity=0.8, state=CONFIRMED)
```

✅ **CASE 2**: One incident with FIRE + FLOOD simultaneously
```
Incident B
├── HazardAssessment(FIRE, severity=0.6, state=CONFIRMED)
└── HazardAssessment(FLOOD, severity=0.4, state=WATCH)
```

✅ **CASE 3**: Two separate incidents involving the same hazard type
```
Incident C (Location A)
└── HazardAssessment(FIRE, severity=0.7)

Incident D (Location B)
└── HazardAssessment(FIRE, severity=0.5)
```

✅ **CASE 4**: A hazard assessment whose confidence changes without changing severity
```
HazardAssessment(FIRE)
├── t0: confidence=0.5, severity=0.7
└── t1: confidence=0.9, severity=0.7  (confidence improved, severity unchanged)
```

✅ **CASE 5**: A hazard whose severity changes without changing evidence identity
```
HazardAssessment(FIRE)
├── t0: severity=0.4, source_summary={nodes: ["NODE-001"]}
└── t1: severity=0.8, source_summary={nodes: ["NODE-001"]}  (same node, worse severity)
```

✅ **CASE 6**: Different operational risk for two hazards with similar severity
```
HazardAssessment(FIRE, severity=0.7, risk=0.9)  // High exposure
HazardAssessment(FLOOD, severity=0.7, risk=0.3)  // Low exposure
```

✅ **CASE 7**: Independent lifecycle states for FIRE and FLOOD within one incident
```
Incident E
├── HazardAssessment(FIRE, state=CRITICAL)
└── HazardAssessment(FLOOD, state=WATCH)
```

✅ **CASE 8**: Full evidence provenance for each hazard assessment
```
HazardAssessment(FIRE)
├── source_summary: {nodes: ["NODE-001", "NODE-042"], weights: [0.6, 0.4]}
├── assessment_timestamp: "2026-09-13T12:00:00Z"
└── model_version: "state_machine_v1.2"
```

✅ **CASE 9**: Track B2 can migrate without losing current functionality
- Existing incident scalars migrated to hazard assessments
- Regional fusion outputs linked to hazard assessments
- Correlation logic unchanged (spatial/temporal)

✅ **CASE 10**: Track C fire outputs can feed the model without making the generic model fire-specific
- Fire geometry stored in `hazard_specific_data` JSONB
- Generic `HazardAssessment` schema unchanged
- Flood can be added later without modifying fire logic

---

## 22. FINAL RECOMMENDATION

### 22.1 Classification: **A — READY FOR PHASE 2C IMPLEMENTATION**

**Rationale**:
1. ✅ **Canonical domain is internally consistent** — Hazard assessments own their metrics independently
2. ✅ **Existing architecture can migrate** — Clear migration path from current Incident scalars
3. ✅ **No unresolved contradictions** — Architectural contradiction identified and resolved in design
4. ✅ **Persistence strategy is justified** — Hybrid relational + JSONB balances type safety and flexibility
5. ✅ **Track B2 compatibility understood** — Clear adaptation requirements documented
6. ✅ **Track C compatibility understood** — Fire-specific data fits in JSONB without polluting generic schema
7. ✅ **All acceptance cases representable** — Cases 1-10 verified ✅

---

### 22.2 Design Summary

**Canonical Domain Model**:
- `Incident`: Correlation container with lifecycle state, geometry, temporal tracking
- `HazardAssessment`: Hazard-specific intelligence with evidence, confidence, severity, risk, state
- Each hazard assessment is independent
- Multi-hazard incidents supported (1:N relationship)

**Persistence Strategy**:
- **Hybrid Relational + JSONB**
- Core assessment fields relational (queryable, indexed, type-safe)
- Hazard-specific data in JSONB (flexible, no cross-contamination)

**Major Contradiction Resolved**:
- Current `Incident` model stores universal scalars at incident level
- Canonical design moves scalars to per-hazard `HazardAssessment`
- Migration path: Create hazard assessments, remove incident scalars

---

### 22.3 Next Steps (Phase 2C-2)

**Implementation Order**:
1. Create `hazard_assessments` table (hybrid schema)
2. Run data migration (Incident scalars → HazardAssessment rows)
3. Update API contracts (add `hazard_assessments` array)
4. Update intelligence modules (write to HazardAssessment)
5. Test multi-hazard scenarios
6. Verify Track B2 no regressions
7. Create Phase 2C-2 completion document

**Estimated Effort**: 3-5 days implementation + 1-2 days testing

---

## 23. TESTS RUN

### 23.1 Track B2 Regional Fusion Tests

**Command**: `python -m pytest tests/test_regional_fusion.py -v`

**Working Directory**: `services/backend`

**Results**:
- **Collected**: 10 tests
- **Passed**: 10 tests ✅
- **Failed**: 0 tests
- **Errors**: 0 tests
- **Skipped**: 0 tests
- **Duration**: 0.02s

**Test Coverage**:
- ✅ Freshness weight computation
- ✅ Spatial distance computation
- ✅ Spatial weight computation
- ✅ Trust weight computation
- ✅ Single node fusion
- ✅ Multiple nearby nodes fusion
- ✅ Stale observation handling
- ✅ Degraded information handling
- ✅ No observations handling
- ✅ Missing values preserved

**Verdict**: ✅ Track B2 regional fusion logic compatible with canonical multi-hazard model (per-hazard fusion already implemented correctly)

---

## 24. DOCUMENT CONTROL

**Version**: 1.0  
**Author**: Claude Code (sih code agent)  
**Created**: 2026-09-13  
**Status**: Design Complete — Ready for Implementation

**Related Documents**:
- `docs/implementation/IMPLEMENTATION_CONSTITUTION.md` — Authority hierarchy
- `docs/implementation/PHASE_1_ARCHITECTURE_FREEZE.md` — Locked decisions
- `docs/implementation/PHASE_2A_VERIFICATION_REPORT.md` — Contract enforcement baseline
- `docs/implementation/PHASE_2B_2_COMPLETION.md` — API canonical emission
- `services/backend/db/models_b2.py` — Current Track B2 models
- `services/backend/modules/intelligence/regional_fusion.py` — Regional fusion logic
- `services/backend/modules/intelligence/incident_correlation.py` — Correlation engine

---

**END OF PHASE 2C-1 MULTI-HAZARD DOMAIN DESIGN**

**CLASSIFICATION: A — READY FOR PHASE 2C IMPLEMENTATION**

**STOPPING AS INSTRUCTED — DESIGN ONLY, NO IMPLEMENTATION**
