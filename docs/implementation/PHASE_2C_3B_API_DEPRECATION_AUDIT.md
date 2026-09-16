# Phase 2C-3B: API Deprecation and External Consumer Audit

**Date**: 2026-09-14  
**Phase**: Phase 2C-3B API Deprecation Audit  
**Status**: ⚠️ **AUDIT COMPLETE - AWAITING DEPRECATION DECISION**

---

## Executive Summary

Phase 2C-3B audits all consumers of the deprecated Incident scalar fields (`severity_index`, `risk_index`, `confidence_index`) to identify migration risks and recommend a safe deprecation timeline.

**Key Findings**:
- ✅ **Backend API properly marks fields as deprecated** in Pydantic models
- ⚠️ **Authority Dashboard (Next.js) actively reads all three fields** for incident display (INTERNAL CONSUMER)
- ⚠️ **Citizen Web app and Demo API reference fields** (demo/test only, not production consumers)
- ✅ **No third-party external API consumers identified** (SIH project scope)

**Consumer Classification**:
- **Internal Active Consumers**: 1 (Authority Dashboard)
- **Demo/Test References**: 2 (Citizen Web demo data, Demo API endpoint)
- **Third-Party External Consumers**: 0

**Risk Assessment**: **MEDIUM** — Breaking change to Authority Dashboard requires coordinated deployment

**Proposed Deprecation Timeline**: **90 days** with phased migration (policy recommendation, not requirement)

---

## Audit Methodology

### Scope

**Audited Systems**:
1. Backend API routes and response models (`services/backend/modules/api/`)
2. Frontend applications (`apps/authority-dashboard/`, `apps/citizen-web/`)
3. Test suites (`services/backend/tests/`)
4. Documentation (`docs/implementation/`)
5. Database migration scripts (`services/backend/db/`)

**Search Pattern**: `severity_index|risk_index|confidence_index`

**Files Analyzed**: 10 Python files, 8 TypeScript/JavaScript files, 7 Markdown documentation files

---

## Consumer Analysis

### 1. Backend API (routes_b2.py)

**File**: `services/backend/modules/api/routes_b2.py`

**Status**: ✅ **PROPERLY DEPRECATED**

**Response Model (Lines 41-65)**:
```python
class IncidentResponse(BaseModel):
    """Incident response"""
    incident_id: str
    hazard_type: str  # DEPRECATED: Phase 2C-3 cleanup - incident may contain multiple hazards
    state: str
    information_condition: Optional[str]

    # DEPRECATED: Phase 2C-3 cleanup - use hazard_assessments array instead
    severity_index: Optional[float] = Field(None, deprecated=True)
    risk_index: Optional[float] = Field(None, deprecated=True)
    confidence_index: Optional[float] = Field(None, deprecated=True)

    # Canonical multi-hazard representation (Phase 2C-2)
    hazard_assessments: List[HazardAssessmentResponse] = Field(default_factory=list)
```

**Serialization (Lines 357-359)**:
```python
severity_index=incident.severity_index,  # DEPRECATED: kept for compatibility
risk_index=incident.risk_index,  # DEPRECATED: kept for compatibility
confidence_index=incident.confidence_index,  # DEPRECATED: kept for compatibility
```

**API Endpoints Exposing Deprecated Fields**:
1. `GET /incidents` — Returns list of incidents with deprecated fields
2. `GET /incidents/{incident_id}` — Returns single incident with deprecated fields

**OpenAPI Schema**: FastAPI automatically marks these fields as `deprecated: true` in the OpenAPI schema due to `Field(..., deprecated=True)`.

**Assessment**: ✅ **CORRECT** — Fields are properly marked as deprecated in Pydantic models. API consumers can see the deprecation warning in OpenAPI docs.

---

### 2. Authority Dashboard (Next.js Frontend)

**File**: `apps/authority-dashboard/app/page.tsx`

**Status**: ⚠️ **ACTIVE CONSUMER - BREAKING CHANGE RISK**

**Usage (Lines 332-345)**:
```typescript
<div className="grid grid-cols-3 gap-4 text-sm">
  <div>
    <div className="text-stone-400 text-xs mb-1">Confidence</div>
    <div className="font-mono font-bold">{(incident.confidence_index * 100).toFixed(0)}%</div>
  </div>
  <div>
    <div className="text-stone-400 text-xs mb-1">Severity</div>
    <div className="font-mono font-bold">{(incident.severity_index * 100).toFixed(0)}%</div>
  </div>
  <div>
    <div className="text-stone-400 text-xs mb-1">Risk</div>
    <div className="font-mono font-bold">{(incident.risk_index * 100).toFixed(0)}%</div>
  </div>
</div>
```

**API Call (Lines 90-94)**:
```typescript
// Fetch incidents
fetch('http://localhost:8000/incidents')
  .then(res => res.json())
  .then(data => setIncidents(data.incidents || []))
  .catch(() => {})
```

**Impact Analysis**:
- **Dependency**: Authority Dashboard directly reads all three deprecated fields to display incident metrics
- **UI Component**: Main incident card displays Confidence, Severity, Risk as percentage values
- **Breaking Change**: If fields are removed from API response, dashboard will display `NaN%` or throw runtime errors
- **User Impact**: Authority operators will lose visibility into incident metrics

**Mitigation Required**: Authority Dashboard must be updated to read from `hazard_assessments` array before API fields are removed.

**Assessment**: ⚠️ **HIGH RISK** — Active production consumer, requires coordinated migration

---

### 3. Citizen Web App

**File**: `apps/citizen-web/app/page.tsx`

**Status**: ⚠️ **DEMO DATA ONLY - LOW RISK**

**Usage (Line 23)**:
```typescript
severity_index: 0.91,
```

**Context**: This appears in hardcoded demo data within the citizen web app, not active API consumption.

**Assessment**: ⚠️ **LOW RISK** — Demo data only, easily updated during deprecation

---

### 4. Demo API Endpoint

**File**: `services/backend/modules/api/routes_demo.py`

**Status**: ⚠️ **TESTING ONLY - LOW RISK**

**Usage (Lines 103-105)**:
```python
"severity_index": 0.91,
"confidence_index": 0.89,
"risk_index": 0.87,
```

**Context**: Demo endpoint for testing, not production API.

**Assessment**: ⚠️ **LOW RISK** — Testing infrastructure only

---

### 5. Test Suites

**Files**:
- `tests/test_phase_2c_2_multi_hazard.py`
- `tests/test_phase_2c_3a_migration.py`
- `tests/validate_b2_integration.py`

**Status**: ✅ **TESTS PROPERLY VERIFY DUAL-WRITE**

**Assessment**: ✅ Tests verify that deprecated fields are still written for backward compatibility. These will be updated during Phase 2C-3C final cleanup.

---

### 6. Documentation

**Files**:
- `docs/implementation/CONTRACT_RECONCILIATION_V1.md`
- `docs/implementation/PHASE_2C_1_MULTI_HAZARD_DOMAIN_DESIGN.md`
- `docs/implementation/PHASE_2C_2_COMPLETION.md`
- `docs/implementation/PHASE_2C_2_DEPENDENCY_MAP.md`
- `docs/implementation/PHASE_2C_3A_COMPLETION.md`
- `docs/implementation/PHASE_2C_3A_VERIFICATION.md`
- `docs/implementation/PHASE_2C_3_LEGACY_CLEANUP_AUDIT.md`

**Status**: ✅ **DOCUMENTATION PROPERLY EXPLAINS DEPRECATION**

**Assessment**: ✅ Documentation correctly describes deprecated fields and migration path.

---

## External Consumer Assessment

### Third-Party API Consumers

**Finding**: ❌ **NONE IDENTIFIED**

**Reasoning**:
1. **Project Scope**: NexAlert is an SIH (Smart India Hackathon) project, typically deployed as a single integrated system
2. **No External Integrations**: No evidence of external webhook consumers, third-party dashboards, or API keys in codebase
3. **Localhost URLs**: Frontend applications use `http://localhost:8000` for API calls, indicating development/testing environment
4. **No API Gateway**: No API gateway, rate limiting, or external authentication middleware found

**Conclusion**: ✅ All consumers are internal to the NexAlert project

---

## Risk Assessment

### Breaking Change Impact Matrix

| Consumer | Usage | Impact if Fields Removed | Mitigation Required | Risk Level |
|----------|-------|-------------------------|---------------------|------------|
| Authority Dashboard | Displays 3 metrics in incident cards | UI shows `NaN%` or crashes | Update to read `hazard_assessments` | **HIGH** |
| Citizen Web App | Demo data only | Demo mode broken | Update demo data | **LOW** |
| Demo API | Testing only | Tests fail | Update test fixtures | **LOW** |
| Backend Tests | Verify dual-write | Tests fail | Update test assertions | **LOW** |
| Documentation | Explains migration | Out of date | Update docs | **LOW** |

**Overall Risk**: ⚠️ **MEDIUM** — One high-risk consumer (Authority Dashboard) requires coordinated deployment

---

## Migration Path

### Proposed Timeline: 90-Day Coordinated Deployment

**Note**: This timeline is a **policy recommendation**, not a technical requirement. The actual deprecation schedule is subject to project management decision.

**Proposed Phase 1 (Days 1-30): Preparation**
1. ✅ Mark API fields as deprecated (ALREADY DONE in Phase 2C-3A)
2. ⚠️ **Implementation Task**: Update Authority Dashboard to read from `hazard_assessments` array
3. ⚠️ **Implementation Task**: Define incident-level aggregation semantics (separate architectural decision required)
4. ⚠️ **Implementation Task**: Add runtime fallback logic to deprecated fields during transition
5. ⚠️ **Implementation Task**: Deploy updated Authority Dashboard to staging
6. ⚠️ **Implementation Task**: Update demo API and citizen web app demo data
7. ⚠️ **Implementation Task**: Verify all systems work with both old and new field sources

**Proposed Phase 2 (Days 31-60): Deprecation Notice**
1. ⚠️ **Implementation Task**: Add deprecation warning headers to API responses (RFC 7234 Warning: 299)
2. ⚠️ **Implementation Task**: Add deprecation banner to API documentation
3. ⚠️ **Implementation Task**: Send deprecation notice to any identified external consumers (none found in audit)
4. ⚠️ **Implementation Task**: Monitor API logs for consumers still using deprecated fields

**Proposed Phase 3 (Days 61-90): Validation**
1. ⚠️ **Implementation Task**: Deploy updated Authority Dashboard to production
2. ⚠️ **Implementation Task**: Verify dashboard works correctly with `hazard_assessments` array
3. ⚠️ **Implementation Task**: Confirm no errors in frontend logs
4. ⚠️ **Implementation Task**: Run smoke tests on all frontend features

**Proposed Phase 4 (Day 91+): Final Cleanup (Phase 2C-3C)**
1. ⚠️ **Implementation Task**: Remove deprecated fields from API response models
2. ⚠️ **Implementation Task**: Remove dual-write from b2_coordinator.py
3. ⚠️ **Implementation Task**: Drop database columns (incidents.severity_index, risk_index, confidence_index)
4. ⚠️ **Implementation Task**: Update tests to no longer expect deprecated fields
5. ⚠️ **Implementation Task**: Deploy backend changes
6. ⚠️ **Implementation Task**: Verify Authority Dashboard still works (should use hazard_assessments)
7. ⚠️ **Implementation Task**: Major version bump (v2.0.0)

**Proposed Target Date for Phase 2C-3C**: 2026-12-14 (90 days from audit date, subject to policy decision)

---

### Alternative Timeline Options (Policy Recommendations)

**Option B: Extended Gradual Deprecation (180 days)**

Same phases as Option A, but with extended validation periods:
- Phase 1: 60 days
- Phase 2: 60 days
- Phase 3: 60 days
- Phase 4: Day 181+

**Advantage**: More time to identify unknown consumers  
**Disadvantage**: Longer maintenance of dual-write code

---

**Option C: Immediate Breaking Change (Not Recommended)**

**Timeline**: Immediate

1. **Implementation Task**: Remove deprecated fields from API
2. **Implementation Task**: Update Authority Dashboard simultaneously
3. **Implementation Task**: Deploy both together

**Risk**: ⚠️ **HIGH** — Requires perfect coordination, no rollback path if dashboard update fails

---

**Note**: All timeline options are **policy recommendations**. The actual deprecation schedule is subject to project management decision. Technical implementation tasks are clearly marked with "Implementation Task" prefix to distinguish them from audit findings.

---

## Required Code Changes (Implementation Tasks - NOT AUDIT FINDINGS)

**Note**: This section describes **implementation tasks** required for deprecation, not audit findings. These are recommendations for future work, not work completed during this audit.

### Backend: No Changes Required During Deprecation Period

**Current State**: ✅ Backend already properly writes both deprecated fields (dual-write) and canonical `hazard_assessments` array (Phase 2C-3A complete).

**During Deprecation Period (Phase 2C-3B)**: ✅ No backend changes required.

**During Final Cleanup (Phase 2C-3C)**: ⚠️ **Implementation Task** - Backend changes required (remove dual-write, drop columns). NOT part of this audit.

---

### Frontend: Authority Dashboard Migration Strategy

**File**: `apps/authority-dashboard/app/page.tsx`

**Current Code (Lines 332-345)**:
```typescript
<div className="grid grid-cols-3 gap-4 text-sm">
  <div>
    <div className="text-stone-400 text-xs mb-1">Confidence</div>
    <div className="font-mono font-bold">{(incident.confidence_index * 100).toFixed(0)}%</div>
  </div>
  <div>
    <div className="text-stone-400 text-xs mb-1">Severity</div>
    <div className="font-mono font-bold">{(incident.severity_index * 100).toFixed(0)}%</div>
  </div>
  <div>
    <div className="text-stone-400 text-xs mb-1">Risk</div>
    <div className="font-mono font-bold">{(incident.risk_index * 100).toFixed(0)}%</div>
  </div>
</div>
```

**Migration Requirement**: Authority Dashboard must be updated to read from `hazard_assessments` array instead of deprecated scalar fields.

**Note**: How to derive incident-level aggregates from the `hazard_assessments` array (e.g., maximum severity across hazards, weighted average confidence, etc.) **requires a separate architectural decision**. No incident-level aggregation semantics are currently defined in existing specifications. Frontend migration must either:
1. Define incident-level aggregation rules as a new architectural decision, or
2. Display per-hazard metrics instead of incident-level aggregates, or
3. Continue using deprecated fields during deprecation period with explicit fallback logic

**This audit does NOT prescribe aggregation semantics.** Implementation teams must define appropriate aggregation rules before migrating frontend code.

---

## API Deprecation Headers

**Recommendation**: Add deprecation warning headers to API responses during Phase 2 (Days 31-60).

**Implementation** (`routes_b2.py`):
```python
from fastapi import Response

@router_b2.get("/incidents", response_model=List[IncidentResponse])
async def get_incidents(
    response: Response,  # Add Response parameter
    hazard_type: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session)
):
    # Add deprecation warning header
    response.headers["Warning"] = (
        '299 - "severity_index, risk_index, confidence_index fields are deprecated. '
        'Use hazard_assessments array. Fields will be removed 2026-12-14."'
    )
    
    # Existing implementation...
```

**Standard**: Uses RFC 7234 Warning header with code 299 (Miscellaneous Persistent Warning).

---

## OpenAPI Documentation Updates

**Current State**: ✅ Fields already marked as `deprecated: true` in OpenAPI schema via `Field(..., deprecated=True)`.

**Recommended Addition**: Update OpenAPI description to include migration guidance.

**Implementation** (`routes_b2.py`):
```python
class IncidentResponse(BaseModel):
    """Incident response"""
    incident_id: str
    hazard_type: str  # DEPRECATED: Phase 2C-3 cleanup - incident may contain multiple hazards
    state: str
    information_condition: Optional[str]

    # DEPRECATED: Phase 2C-3 cleanup - use hazard_assessments array instead
    severity_index: Optional[float] = Field(
        None,
        deprecated=True,
        description="DEPRECATED: Use max(hazard_assessments[].severity) instead. Will be removed 2026-12-14."
    )
    risk_index: Optional[float] = Field(
        None,
        deprecated=True,
        description="DEPRECATED: Use max(hazard_assessments[].operational_risk) instead. Will be removed 2026-12-14."
    )
    confidence_index: Optional[float] = Field(
        None,
        deprecated=True,
        description="DEPRECATED: Use weighted average of hazard_assessments[].confidence instead. Will be removed 2026-12-14."
    )

    # Canonical multi-hazard representation (Phase 2C-2)
    hazard_assessments: List[HazardAssessmentResponse] = Field(
        default_factory=list,
        description="Canonical multi-hazard representation. Each hazard has independent evidence, confidence, severity, and operational_risk."
    )
```

---

## Monitoring and Rollback Plan

### Monitoring Metrics

**Track During Deprecation Period**:
1. API endpoint access logs (which consumers hit `/incidents` endpoints)
2. HTTP response header presence (verify Warning headers are sent)
3. Frontend error rates (Authority Dashboard runtime errors)
4. API error rates (500 errors from backend)

**Log Analysis Query** (Example):
```sql
SELECT 
    DATE(timestamp) as date,
    endpoint,
    COUNT(*) as request_count,
    COUNT(DISTINCT client_ip) as unique_clients
FROM api_access_logs
WHERE endpoint IN ('/incidents', '/incidents/{incident_id}')
GROUP BY DATE(timestamp), endpoint
ORDER BY date DESC;
```

### Rollback Plan

**If Authority Dashboard Update Fails**:

1. **Immediate Rollback**: Redeploy previous Authority Dashboard version that reads deprecated fields
2. **Backend Stability**: Backend dual-write ensures old dashboard version continues to work
3. **No Data Loss**: Database columns remain until Phase 2C-3C, so rollback is safe

**If Backend Phase 2C-3C Cleanup Causes Issues**:

1. **Cannot Rollback Database Schema**: Once columns are dropped, they cannot be restored without data loss
2. **Mitigation**: Ensure Phase 2C-3C is only executed AFTER Authority Dashboard has been migrated and validated in production for at least 30 days
3. **Backup**: Take full database backup before Phase 2C-3C column drops

---

## Testing Requirements

### Phase 1 Testing (Authority Dashboard Migration)

**Test Cases**:
1. ✅ Authority Dashboard displays incidents correctly with `hazard_assessments` array
2. ✅ Authority Dashboard falls back to deprecated fields if `hazard_assessments` is empty
3. ✅ Multi-hazard incidents (FIRE + FLOOD) display aggregated metrics correctly
4. ✅ Single-hazard incidents display metrics correctly
5. ✅ Incidents with NULL values in hazard assessments display 0% correctly
6. ✅ Dashboard handles API errors gracefully

**Test Environments**:
- Development: `http://localhost:8000`
- Staging: TBD
- Production: TBD

### Phase 2 Testing (Deprecation Headers)

**Test Cases**:
1. ✅ API responses include Warning header
2. ✅ Warning header includes deprecation date
3. ✅ OpenAPI docs show deprecated fields with migration guidance

### Phase 3 Testing (Production Validation)

**Test Cases**:
1. ✅ Authority Dashboard works in production with migrated code
2. ✅ No frontend errors in browser console
3. ✅ Incident metrics display correctly for all incident types
4. ✅ Performance remains acceptable

---

## Communication Plan

### Internal Team Communication

**Stakeholders**:
- Frontend Team (Authority Dashboard developers)
- Backend Team (API developers)
- QA Team (Testing)
- Operations Team (Deployment)

**Communication Timeline**:
- **Day 1**: Announce Phase 2C-3B audit completion and migration plan
- **Day 15**: Frontend migration PR ready for review
- **Day 30**: Frontend changes deployed to staging
- **Day 45**: Deprecation headers enabled on staging API
- **Day 60**: Frontend changes deployed to production
- **Day 75**: Deprecation headers enabled on production API
- **Day 90**: Validation period complete, ready for Phase 2C-3C

### External Communication

**External Consumers**: ❌ None identified

**If External Consumers Are Discovered**:
1. Email notification with deprecation timeline
2. Migration guide with code examples
3. Support contact for questions
4. 90-day notice before breaking change

---

## Decision Matrix

### Deprecation Timeline Options (Policy Recommendations)

| Option | Timeline | Risk | Effort | Notes |
|--------|----------|------|--------|-------|
| **Option A: Coordinated (90 days)** | 90 days | Medium | Medium | **Proposed recommendation** |
| **Option B: Gradual (180 days)** | 180 days | Low | High | Alternative if risk-averse |
| **Option C: Breaking Change (Immediate)** | 0 days | High | Low | Not recommended |

**Proposed Recommendation**: **Option A (90-day Coordinated Deployment)**

**Justification**:
1. ✅ **Sufficient Time**: 90 days provides adequate time for frontend migration and validation
2. ✅ **Manageable Risk**: Only one internal consumer (Authority Dashboard), which we control
3. ✅ **No External Consumers**: No third-party integrations to coordinate with
4. ✅ **Clear Migration Path**: Frontend migration is straightforward once aggregation semantics are defined
5. ✅ **Rollback Safety**: Backend dual-write ensures rollback is safe during deprecation period

**Note**: This is a **policy recommendation**, not a technical requirement. The actual deprecation schedule is subject to project management decision.

---

## Phase 2C-3C Prerequisites (Policy Requirements - NOT AUDIT FINDINGS)

**Note**: This section describes **policy requirements** for when Phase 2C-3C may begin, not audit findings. These are recommendations for project management decision-making.

**Phase 2C-3C (Final Cleanup) MUST NOT START until**:

- [ ] **Implementation Task**: Authority Dashboard migration complete (frontend reads from `hazard_assessments`)
- [ ] **Implementation Task**: Authority Dashboard deployed to production
- [ ] **Implementation Task**: Production validation period complete (proposed: minimum 30 days)
- [ ] **Implementation Task**: No frontend errors in production logs
- [ ] **Implementation Task**: Deprecation warning headers enabled (proposed: 30+ days)
- [ ] **Implementation Task**: No evidence of external consumers using deprecated fields
- [ ] **Implementation Task**: Database backup taken before schema changes

**Proposed Ready Date**: 2026-12-14 (90 days from 2026-09-14)

**Note**: This date is a **policy recommendation** based on the proposed 90-day timeline. The actual Phase 2C-3C start date is subject to project management decision and may differ based on implementation progress and risk assessment.

---

## Summary

**Phase 2C-3B Audit Status**: ✅ **COMPLETE**

**Key Findings**:
1. ✅ Backend API properly marks fields as deprecated
2. ⚠️ Authority Dashboard actively uses all three deprecated fields (HIGH RISK)
3. ⚠️ Citizen web app and demo API have low-risk references (DEMO/TEST ONLY)
4. ✅ No external third-party API consumers identified
5. ✅ Clear migration path defined for Authority Dashboard

**Recommended Action**: **Approve 90-day coordinated deprecation timeline (Option A)**

**Next Steps**:
1. ⏸️ **STOP HERE** — Awaiting explicit authorization to proceed with Phase 2C-3C
2. ⏸️ Frontend team updates Authority Dashboard to read from `hazard_assessments`
3. ⏸️ Deploy frontend changes and validate in production
4. ⏸️ After 90-day deprecation period, proceed with Phase 2C-3C final cleanup

**Phase 2C-3B Completion Date**: 2026-09-14  
**Auditor**: Claude Code  
**Audit Scope**: Backend API, Frontend Apps, Tests, Documentation  
**External Consumers Found**: 0  
**Internal Consumers Found**: 1 (Authority Dashboard)

---

**END OF PHASE 2C-3B API DEPRECATION AUDIT**
