# PHASE 2C-2 DEPENDENCY MAP

**Date**: 2026-09-13  
**Phase**: Phase 2C-2 Multi-Hazard Domain Implementation  
**Status**: PRE-IMPLEMENTATION AUDIT

---

## EXECUTIVE SUMMARY

This document maps all current dependencies on the legacy Track B2 `Incident` model's universal scalar fields (`severity_index`, `confidence_index`, `risk_index`, `hazard_type`) to guide the multi-hazard domain migration.

**Critical Finding**: The existing architecture uses `Incident` as BOTH a correlation container AND a hazard assessment holder, creating tight coupling across 10 files.

**Migration Strategy**: Staged migration preserving compatibility until all consumers are updated.

---

## 1. ARCHITECTURAL LAYERS

### Layer 1: Database Models (2 files)

**Track B1 Edge Intelligence**:
- `services/backend/db/models.py:118-142` — `HazardAssessment` (edge/telemetry level)
  - Per-telemetry, per-hazard intelligence output
  - Linked to `telemetry_id` (ForeignKey)
  - Fields: evidence, confidence, severity, risk, state, information_condition
  - **Status**: ✅ This is edge intelligence, NOT incident-level — MUST remain distinct

**Track B2 Regional Intelligence**:
- `services/backend/db/models_b2.py:17-82` — `Incident`
  - Regional incident correlation container
  - Fields with architectural contradiction:
    - `hazard_type` (line 31): Single hazard type per incident
    - `severity_index` (line 38): Universal scalar
    - `confidence_index` (line 40): Universal scalar
    - `risk_index` (line 39): Universal scalar
  - **Status**: ❌ Violates multi-hazard independence — requires migration

- `services/backend/db/models_b2.py:131-181` — `RegionalHazardAssessment`
  - Correctly stores per-hazard regional fusion results
  - Fields: `hazard_type`, `regional_evidence`, `regional_confidence`, `regional_severity`, `regional_risk`
  - **Status**: ✅ Compatible with canonical model

- `services/backend/db/models_b2.py:85-129` — `IncidentObservation`
  - Links telemetry/hazard assessments to incidents
  - **Status**: ✅ Compatible with canonical model

---

## 2. MIGRATION SCRIPTS (1 file)

**Track B2 Migration**:
- `services/backend/db/migrations_002_track_b2.py`
  - Creates `Incident`, `IncidentObservation`, `RegionalHazardAssessment`, `NodeStatus` tables
  - Defines `Incident` with universal scalar fields
  - **Status**: ⚠️ Requires new migration (003) to add incident-level HazardAssessment table

---

## 3. INTELLIGENCE MODULES (3 files)

### 3.1 Regional Fusion

**File**: `services/backend/modules/intelligence/regional_fusion.py`

**Usage**: None — correctly processes per-hazard fusion independently

**Key Functions**:
- `fuse_regional_hazard()` — returns `RegionalFusionResult` with hazard-specific metrics
- Returns: `regional_evidence`, `regional_confidence`, `regional_severity`, `regional_risk`
- **Status**: ✅ Compatible — no changes required

---

### 3.2 Incident Correlation

**File**: `services/backend/modules/intelligence/incident_correlation.py`

**Universal Scalar Dependencies** (6 locations):

| Line | Structure | Field | Usage |
|------|-----------|-------|-------|
| 51 | `IncidentCandidate` dataclass | `severity_index` | Carries incident severity for correlation |
| 52 | `IncidentCandidate` dataclass | `risk_index` | Carries incident risk for correlation |
| 61 | `IncidentCreationResult` dataclass | `severity_index` | Returns created incident severity |
| 62 | `IncidentCreationResult` dataclass | `risk_index` | Returns created incident risk |
| 230 | `create_or_update_incident()` | `severity_index=regional_fusion.regional_severity` | Sets incident severity from fusion |
| 231 | `create_or_update_incident()` | `risk_index=regional_fusion.regional_risk` | Sets incident risk from fusion |

**Analysis**:
- Correlation logic itself (spatial/temporal) does NOT depend on severity/risk scalars
- `IncidentCandidate` and `IncidentCreationResult` currently expect universal scalars
- Fusion results are directly assigned to `Incident` fields

**Migration Required**:
- [ ] Remove `severity_index`, `risk_index` from `IncidentCandidate`
- [ ] Remove `severity_index`, `risk_index` from `IncidentCreationResult`
- [ ] Change incident creation to create/update `HazardAssessment` instead of setting incident scalars
- [ ] Preserve spatial/temporal correlation logic (unchanged)

---

### 3.3 B2 Coordinator

**File**: `services/backend/modules/intelligence/b2_coordinator.py`

**Universal Scalar Dependencies** (6 locations):

| Line | Context | Field | Usage |
|------|---------|-------|-------|
| 327 | `_query_existing_incidents()` | `severity_index=inc.severity_index` | Reads incident severity |
| 328 | `_query_existing_incidents()` | `risk_index=inc.risk_index` | Reads incident risk |
| 365 | `_create_new_incident()` | `severity_index=fusion_result.regional_severity` | Sets new incident severity |
| 366 | `_create_new_incident()` | `risk_index=fusion_result.regional_risk` | Sets new incident risk |
| 367 | `_create_new_incident()` | `confidence_index=fusion_result.regional_confidence` | Sets new incident confidence |
| 460 | `_update_existing_incident()` | `inc.severity_index = fusion_result.regional_severity` | Updates incident severity |
| 461 | `_update_existing_incident()` | `inc.risk_index = fusion_result.regional_risk` | Updates incident risk |
| 462 | `_update_existing_incident()` | `inc.confidence_index = fusion_result.regional_confidence` | Updates incident confidence |

**Analysis**:
- B2 coordinator is the PRIMARY writer of incident scalars
- Directly assigns regional fusion results to `Incident` fields
- Both incident creation and update paths affected

**Migration Required**:
- [ ] Change `_create_new_incident()` to create `HazardAssessment` row(s) instead of setting incident scalars
- [ ] Change `_update_existing_incident()` to update `HazardAssessment` row(s) instead of incident scalars
- [ ] Link fusion results to hazard assessments, not incident
- [ ] Preserve per-hazard processing loop (already correct)

---

## 4. API LAYER (2 files)

### 4.1 Track B2 API

**File**: `services/backend/modules/api/routes_b2.py`

**Universal Scalar Dependencies** (6 locations):

| Line | Context | Field | Usage |
|------|---------|-------|-------|
| 29 | `IncidentResponse` model | `severity_index: Optional[float]` | API response field |
| 30 | `IncidentResponse` model | `risk_index: Optional[float]` | API response field |
| 31 | `IncidentResponse` model | `confidence_index: Optional[float]` | API response field |
| 306 | `_incident_to_response()` | `severity_index=incident.severity_index` | Serializes incident severity |
| 307 | `_incident_to_response()` | `risk_index=incident.risk_index` | Serializes incident risk |
| 308 | `_incident_to_response()` | `confidence_index=incident.confidence_index` | Serializes incident confidence |

**Analysis**:
- API currently exposes universal scalars as canonical representation
- Serializer reads directly from `Incident` database model
- Public API contract exposed to external consumers

**Migration Required**:
- [ ] Add `hazard_assessments: List[HazardAssessmentResponse]` to `IncidentResponse`
- [ ] Create `HazardAssessmentResponse` model with per-hazard fields
- [ ] Update `_incident_to_response()` to serialize hazard assessments
- [ ] **Compatibility**: Keep deprecated scalar fields temporarily (mark as deprecated)
- [ ] Derive deprecated scalars (e.g., MAX(severity) across hazards) if retained

---

### 4.2 Demo API (Non-Production)

**File**: `services/backend/modules/api/routes_demo.py`

**Universal Scalar Dependencies** (3 locations):

| Line | Context | Field | Usage |
|------|---------|-------|-------|
| 103 | Mock incident data | `"severity_index": 0.91` | Hardcoded demo data |
| 104 | Mock incident data | `"confidence_index": 0.89` | Hardcoded demo data |
| 105 | Mock incident data | `"risk_index": 0.87` | Hardcoded demo data |

**Analysis**:
- Non-production demo endpoint
- Hardcoded mock data

**Migration Required**:
- [ ] Update mock data to include `hazard_assessments` array
- [ ] Remove or deprecate mock scalar fields

---

## 5. TESTS (2 files)

### 5.1 B2 Integration Tests

**File**: `services/backend/tests/validate_b2_integration.py`

**Universal Scalar Dependencies** (2 locations):

| Line | Context | Field | Usage |
|------|---------|-------|-------|
| 172 | Test data | `severity_index=0.7` | Creates test incident |
| 173 | Test data | `risk_index=0.65` | Creates test incident |

**Analysis**:
- Integration test creates incidents with universal scalars
- Tests B2 pipeline behavior

**Migration Required**:
- [ ] Update test to create `HazardAssessment` rows
- [ ] Verify multi-hazard incident creation
- [ ] Add tests for independent hazard metrics

---

### 5.2 Regional Fusion Tests

**File**: `services/backend/tests/test_regional_fusion.py`

**Universal Scalar Dependencies**: None

**Analysis**:
- Tests regional fusion logic in isolation
- Correctly tests per-hazard fusion outputs
- **Status**: ✅ No changes required — already compatible

---

## 6. NAMING COLLISION ANALYSIS

### Critical Distinction

**TWO DIFFERENT `HazardAssessment` CONCEPTS**:

1. **Track B1 Edge HazardAssessment** (`db.models.HazardAssessment`)
   - Per-telemetry intelligence output
   - Lives at edge/node level
   - Linked to `telemetry_id`
   - Created by edge intelligence pipeline
   - Already exists, MUST NOT be modified

2. **NEW: Regional/Incident HazardAssessment** (to be created)
   - Per-incident intelligence aggregation
   - Lives at regional/incident level
   - Linked to `incident_id`
   - Created by regional fusion/correlation
   - Does NOT exist yet

**Resolution Strategy**:

**Option A: Separate Table Name**
- Edge: `HazardAssessment` (unchanged)
- Regional: `IncidentHazardAssessment` (new)
- **Pros**: Clear distinction, no ambiguity
- **Cons**: Longer name

**Option B: Namespace Separation**
- Edge: `models.HazardAssessment`
- Regional: `models_b2.HazardAssessment`
- **Pros**: Both can use same class name
- **Cons**: Import ambiguity risk

**RECOMMENDED**: **Option A** — Use `IncidentHazardAssessment` for the new regional/incident-level table to eliminate all ambiguity.

---

## 7. DEPENDENCY GRAPH

```
ESP32 Telemetry
    ↓
MQTT Ingestion
    ↓
TelemetryRecord (persistence)
    ↓
Edge Intelligence Pipeline
    ↓
models.HazardAssessment (Track B1, per-telemetry)
    ↓
Regional Fusion (per-hazard)
    ↓
RegionalHazardAssessment (Track B2, correct)
    ↓
Incident Correlation
    ↓
Incident (Track B2, WRONG — has universal scalars)
    ↓
B2 API (routes_b2.py)
    ↓
External Consumers
```

**Migration Flow**:
```
RegionalHazardAssessment (per-hazard fusion)
    ↓
Incident Correlation
    ↓
Incident (correlation container ONLY)
    + IncidentHazardAssessment (NEW, per-hazard metrics)
    ↓
B2 API (updated)
    ↓
External Consumers
```

---

## 8. MIGRATION RISK ASSESSMENT

### High Risk

1. **API Breaking Change**
   - External consumers may depend on `severity_index`, `confidence_index`, `risk_index` fields
   - **Mitigation**: Deprecation period, compute derived scalars temporarily

2. **Data Migration**
   - Existing incidents must map to new `IncidentHazardAssessment` rows
   - **Mitigation**: Careful migration script with validation

3. **B2 Coordinator Complexity**
   - Creates/updates incidents in multiple code paths
   - **Mitigation**: Systematic refactor of all incident write paths

### Medium Risk

4. **Test Coverage**
   - Existing tests assume universal scalars
   - **Mitigation**: Update tests incrementally, verify no regressions

5. **Incident State Derivation**
   - Incident state may need derivation from constituent hazard states
   - **Mitigation**: Clear state derivation rules documented in Phase 2C-1

### Low Risk

6. **Regional Fusion Module**
   - Already correctly processes per-hazard
   - **Mitigation**: None required — compatible as-is

7. **Edge Intelligence**
   - Completely separate from incident-level changes
   - **Mitigation**: Preserve existing `models.HazardAssessment` unchanged

---

## 9. CONSUMER CLASSIFICATION

### Internal Consumers (Can Be Updated)

| Consumer | Type | Coupling Level | Migration Effort |
|----------|------|----------------|------------------|
| `incident_correlation.py` | Intelligence | High | 2 dataclasses + 2 functions |
| `b2_coordinator.py` | Intelligence | High | 3 functions (create/update/query) |
| `routes_b2.py` | API | High | 1 model + 1 serializer |
| `routes_demo.py` | Demo | Low | Mock data only |
| `validate_b2_integration.py` | Test | Medium | Test data creation |

### External Consumers (Unknown)

- Frontend dashboard (`apps/authority-dashboard/`)
- Potential external API consumers
- **Mitigation**: Deprecation period for API fields

---

## 10. STAGED MIGRATION SEQUENCE

### Stage 1: Database Foundation (Non-Breaking)
1. Add `IncidentHazardAssessment` table (new)
2. Keep existing `Incident` fields temporarily
3. Dual-write: Create both incident scalars AND hazard assessment rows
4. Migration script: Backfill existing incidents

### Stage 2: Internal Consumer Migration (Non-Breaking)
1. Update B2 coordinator to write to hazard assessments
2. Update incident correlation to use hazard assessments
3. Keep incident scalar fields populated (dual-write)
4. Verify existing tests still pass

### Stage 3: API Migration (Deprecation)
1. Add `hazard_assessments` array to API response
2. Mark `severity_index`, `confidence_index`, `risk_index` as deprecated
3. Compute deprecated fields from hazard assessments (e.g., MAX(severity))
4. Update API tests

### Stage 4: Cleanup (Breaking Change — Phase 2C-3)
1. Remove incident scalar fields from database
2. Remove deprecated API fields
3. Major version bump
4. Remove dual-write logic

---

## 11. FILES REQUIRING MODIFICATION

### Must Modify (7 files)

1. `services/backend/db/models_b2.py` — Add `IncidentHazardAssessment` table
2. `services/backend/db/migrations_003_track_b2_multi_hazard.py` — New migration (CREATE)
3. `services/backend/modules/intelligence/incident_correlation.py` — Remove scalar dependencies
4. `services/backend/modules/intelligence/b2_coordinator.py` — Write to hazard assessments
5. `services/backend/modules/api/routes_b2.py` — Add hazard_assessments to API
6. `services/backend/tests/validate_b2_integration.py` — Update test data
7. `services/backend/modules/api/routes_demo.py` — Update mock data

### Must NOT Modify (2 files)

1. `services/backend/db/models.py` — Edge `HazardAssessment` MUST remain unchanged
2. `services/backend/modules/intelligence/regional_fusion.py` — Already compatible

### May Require Updates (1 file)

1. `services/backend/tests/test_regional_fusion.py` — Verify compatibility (likely no changes)

---

## 12. IMPORT IMPACT ANALYSIS

### Current Imports

**Track B1 HazardAssessment**:
- `services/backend/modules/api/routes.py`
- `services/backend/tests/test_mqtt_b2_integration.py`
- `services/backend/modules/api/routes_b2.py`
- `services/backend/db/__init__.py`

**Track B2 Incident**:
- `services/backend/modules/intelligence/b2_coordinator.py`
- `services/backend/modules/api/routes_b2.py`
- `services/backend/db/__init__.py`

### New Imports Required

**IncidentHazardAssessment** (new):
- `services/backend/modules/intelligence/b2_coordinator.py` — Will write to new table
- `services/backend/modules/api/routes_b2.py` — Will serialize to API
- `services/backend/db/__init__.py` — Will export new model

**No Import Conflicts Expected** — New class name eliminates ambiguity.

---

## 13. TRACK C COMPATIBILITY

**Track C Dependencies**: None direct

**Track C Fire Spread** (from plan):
- Takes confirmed incident locations as ignition points
- Produces fire-specific geometry (Polygon/MultiPolygon)
- Generates risk surfaces
- Calculates exposure

**Integration Point**:
- Track C will need to link fire spread outputs to `IncidentHazardAssessment` with `hazard_type="FIRE"`
- Fire-specific data (geometry, spread rate, perimeter) will use `hazard_specific_data` JSONB
- **Status**: ✅ Compatible with canonical design — no Track C modifications required for Phase 2C-2

---

## 14. ACCEPTANCE CRITERIA FOR DEPENDENCY MAP

This dependency map is complete when:

- [x] All files using `Incident.severity_index` identified
- [x] All files using `Incident.confidence_index` identified
- [x] All files using `Incident.risk_index` identified
- [x] All files using `Incident.hazard_type` identified
- [x] Edge vs Regional `HazardAssessment` distinction clarified
- [x] Naming collision resolution strategy defined
- [x] Staged migration sequence documented
- [x] Risk assessment complete
- [x] Consumer classification complete
- [x] Import impact analysis complete
- [x] Track C compatibility verified

---

## 15. NEXT STEPS

**After Dependency Map Approval**:

1. Proceed to STEP 2: Implement `IncidentHazardAssessment` database model
2. Proceed to STEP 3: Create migration script (003)
3. Proceed to STEP 4: Migrate existing incident data
4. Proceed to STEP 5: Adapt Track B2 intelligence modules
5. Proceed to STEP 6: Adapt incident correlation
6. Proceed to STEP 7: Update API contract
7. Proceed to STEP 8: Update tests
8. Proceed to STEP 9: Verify no regressions

---

**DEPENDENCY MAP COMPLETE**

**STATUS**: READY FOR PHASE 2C-2 IMPLEMENTATION

**MIGRATION STRATEGY**: STAGED (4 stages, non-breaking until Stage 4)

**RECOMMENDED TABLE NAME**: `IncidentHazardAssessment` (eliminates naming collision)

**ESTIMATED FILES TO MODIFY**: 7 production files + 1 migration

**ESTIMATED TEST FILES TO UPDATE**: 2 files

**TRACK C COMPATIBILITY**: ✅ VERIFIED
