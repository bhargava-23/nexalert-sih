# Phase 2C-3B: Incident Display Strategy Decision

**Date**: 2026-09-14  
**Decision**: Authority Dashboard Incident Metrics Display  
**Status**: ✅ **APPROVED FOR IMPLEMENTATION**

---

## Problem Statement

The Authority Dashboard currently displays incident-level aggregate metrics (Confidence, Severity, Risk) derived from the deprecated Incident scalar fields (`confidence_index`, `severity_index`, `risk_index`). 

Phase 2C-3B requires migrating to the canonical `hazard_assessments` array, where each hazard independently owns its metrics. **The question is: how should incident metrics be displayed when an incident may contain multiple hazards?**

---

## Architectural Constraint

**No incident-level aggregation semantics are defined in existing specifications.** The multi-hazard domain model (Phase 2C-2) explicitly states that:

1. Each `IncidentHazardAssessment` independently owns `evidence`, `confidence`, `severity`, `operational_risk`, and `state`
2. An Incident is a **correlation container**, not a hazard entity
3. Aggregation rules (e.g., max severity, weighted average confidence) are **not specified**

**Implication**: We cannot invent aggregation semantics without an explicit architectural decision.

---

## Display Strategy Options

### Option A: Per-Hazard Display (RECOMMENDED)

**Approach**: Display each hazard assessment independently in the incident card.

**UI Design**:
```
┌─────────────────────────────────────────────┐
│ FIRE / FLOOD                    [ACTIVE]    │
│ INC-001                                     │
│                                             │
│ FIRE Hazard:                                │
│   Confidence: 90%  Severity: 80%  Risk: 75% │
│                                             │
│ FLOOD Hazard:                               │
│   Confidence: 80%  Severity: 40%  Risk: 30% │
└─────────────────────────────────────────────┘
```

**Advantages**:
- ✅ **No invented semantics**: Displays canonical data directly
- ✅ **Correct multi-hazard representation**: Shows that FIRE and FLOOD are independent
- ✅ **No aggregation needed**: Each hazard's metrics are shown as-is
- ✅ **Extensible**: Works for 1, 2, or N hazards without special cases

**Disadvantages**:
- ⚠️ Requires more vertical space per incident
- ⚠️ Changes existing UI layout

**Backward Compatibility**: For single-hazard incidents, display is nearly identical to current (one hazard shown instead of aggregate).

---

### Option B: Incident-Level Aggregation (NOT RECOMMENDED)

**Approach**: Define aggregation rules to derive incident-level metrics from hazard assessments.

**Example Rules** (HYPOTHETICAL - not from specs):
- Severity: `max(hazard_assessments[].severity)`
- Risk: `max(hazard_assessments[].operational_risk)`
- Confidence: `weighted_average(hazard_assessments[].confidence)`

**Advantages**:
- ✅ Preserves existing UI layout
- ✅ Minimal visual change for single-hazard incidents

**Disadvantages**:
- ❌ **Invents semantics not in specifications**: No architectural decision supports this
- ❌ **Loses information**: Multi-hazard incidents collapse to single numbers
- ❌ **Misleading**: "Confidence 85%" for (FIRE 90% + FLOOD 80%) hides that FLOOD has lower confidence
- ❌ **Requires separate architectural decision**: Must be formally specified before implementation

**Status**: ❌ **REJECTED** — Cannot implement without explicit architectural approval

---

### Option C: Fallback During Transition (TEMPORARY)

**Approach**: Use deprecated fields during deprecation period, then migrate to per-hazard display.

**Advantages**:
- ✅ No immediate UI changes
- ✅ Works with current backend dual-write

**Disadvantages**:
- ❌ Does not migrate away from deprecated fields
- ❌ Postpones the problem instead of solving it
- ❌ Requires another migration later

**Status**: ⚠️ **FALLBACK ONLY** — Use only if Option A implementation is blocked

---

## Decision

**Selected Strategy**: **Option A (Per-Hazard Display)**

**Rationale**:
1. ✅ **No invented semantics**: Displays canonical data as defined in Phase 2C-2 specifications
2. ✅ **Correct multi-hazard representation**: Shows each hazard's independent assessment
3. ✅ **Future-proof**: Works for N hazards without requiring aggregation rules
4. ✅ **Clear information**: Authority operators see exactly what assessments exist

**Implementation Approach**:
1. Update incident card UI to display each hazard assessment separately
2. Add fallback logic to handle deprecated fields during transition (backward compatibility)
3. Handle edge cases: empty `hazard_assessments` array, single hazard, multiple hazards

---

## Implementation Specification

### Data Access

**Preferred (Canonical)**:
```typescript
incident.hazard_assessments: Array<{
  assessment_id: number
  hazard_type: string
  evidence: number | null
  confidence: number | null
  severity: number | null
  operational_risk: number | null
  state: string | null
  information_condition: string | null
}>
```

**Fallback (Deprecated - for backward compatibility)**:
```typescript
incident.confidence_index: number | null  // DEPRECATED
incident.severity_index: number | null    // DEPRECATED
incident.risk_index: number | null        // DEPRECATED
incident.hazard_type: string              // DEPRECATED (single hazard only)
```

---

### UI Component Structure

**Incident Card Layout**:

```typescript
function IncidentCard({ incident }: { incident: any }) {
  return (
    <div className="incident-card">
      {/* Header: incident ID + state */}
      <IncidentHeader incident={incident} />
      
      {/* Hazard Assessments: per-hazard display */}
      <HazardAssessmentsList 
        assessments={incident.hazard_assessments}
        fallback={{
          hazard_type: incident.hazard_type,
          confidence: incident.confidence_index,
          severity: incident.severity_index,
          risk: incident.risk_index
        }}
      />
    </div>
  )
}
```

---

### Edge Cases

**Case 1: Empty `hazard_assessments` array**

**Scenario**: Incident exists but has no hazard assessments (should not happen, but defensive).

**Behavior**: Fall back to deprecated fields if available, otherwise display "No assessment data".

---

**Case 2: Single hazard in `hazard_assessments`**

**Scenario**: Most common case — one hazard per incident.

**Behavior**: Display one hazard assessment. UI is nearly identical to current layout.

---

**Case 3: Multiple hazards in `hazard_assessments`**

**Scenario**: Multi-hazard incident (e.g., FIRE + FLOOD simultaneously).

**Behavior**: Display each hazard assessment independently, stacked vertically.

---

**Case 4: NULL values in hazard assessment metrics**

**Scenario**: A hazard assessment exists but has NULL `severity`, `confidence`, or `operational_risk`.

**Behavior**: Display as "—" (em dash) to indicate missing data, not zero.

**Specification**: Phase 2C-2 states "NULL = missing (NOT zero)". Do not render NULL as 0%.

---

**Case 5: API returns deprecated fields but no `hazard_assessments`**

**Scenario**: Backend API continues dual-write, but `hazard_assessments` array is missing from response.

**Behavior**: Fall back to deprecated fields and log a warning to console.

---

## Backward Compatibility Strategy

**During Deprecation Period** (Phase 2C-3B):

1. **Try canonical first**: If `incident.hazard_assessments` exists and is non-empty, display per-hazard metrics.
2. **Fall back to deprecated**: If `hazard_assessments` is missing or empty, fall back to `confidence_index`, `severity_index`, `risk_index`.
3. **Log fallback usage**: Console.warn when deprecated fields are used (for monitoring).

**After Phase 2C-3C** (deprecated fields removed):

1. **Canonical only**: Display `hazard_assessments` exclusively.
2. **Remove fallback**: Delete deprecated field access code.

---

## Testing Requirements

### Test Cases

1. ✅ **Single-hazard incident with `hazard_assessments`**: Display one hazard's metrics
2. ✅ **Multi-hazard incident (FIRE + FLOOD)**: Display both hazards independently
3. ✅ **Empty `hazard_assessments` with deprecated fields**: Fall back to deprecated display
4. ✅ **NULL values in hazard metrics**: Display "—" not "0%"
5. ✅ **Missing `hazard_assessments` array**: Fall back gracefully
6. ✅ **Incident with zero hazards**: Display "No assessment data"

### Visual Regression Tests

- [ ] Compare current UI (deprecated fields) with new UI (single hazard) — should be nearly identical
- [ ] Verify multi-hazard display is readable and fits in incident card
- [ ] Verify mobile/narrow layout works correctly

---

## Decision Approval

**Decision**: Use **per-hazard display** (Option A) without inventing aggregation semantics.

**Approved By**: Phase 2C-3B implementation (architectural decision follows Phase 2C-2 canonical model)

**Implementation Status**: ✅ **READY TO IMPLEMENT**

---

**END OF DISPLAY STRATEGY DECISION**
