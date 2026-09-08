# NexAlert Architectural Decisions

**Version**: 1.0  
**Status**: ACTIVE  
**Last Updated**: 2026-09-07  
**Purpose**: Record of architectural decisions, clarifications, and resolved questions

---

## Overview

This document records architectural decisions made during NexAlert implementation. Each decision is binding until explicitly revised.

**Decision Format:**
```markdown
### <Decision Name> [STATUS YYYY-MM-DD]

**Decision**: <What was decided>

**Rationale**: <Why this decision was made>

**Implementation**: <How this will be implemented>

**Status**: <LOCKED | IMPLEMENTATION DECISION | OPEN>

**Related Specifications**: <Document references>

**Additional Context**: <Background, alternatives considered, etc.>
```

---

## Table of Contents

1. [Decision Status Definitions](#decision-status-definitions)
2. [Resolved Clarifications (C1, C2, C3)](#resolved-clarifications)
3. [Unresolved Questions](#unresolved-questions)
4. [Deferred Implementation Details](#deferred-implementation-details)
5. [Decision Change Process](#decision-change-process)

---

## Decision Status Definitions

| **Status** | **Meaning** | **Can Change?** |
|---|---|---|
| **LOCKED** | Non-negotiable architectural decision | Only with explicit human approval + specification update |
| **IMPLEMENTATION DECISION** | Implementation choice within specification constraints | Yes, with technical justification + PR |
| **OPEN** | Question not yet resolved | Will become LOCKED or IMPLEMENTATION DECISION once resolved |

---

## Resolved Clarifications

The following clarifications were resolved during the architectural reconnaissance phase (Phase 1).

### C1: Edge Intelligence Boundary [LOCKED 2026-09-07]

**Decision**: ESP32 firmware MUST implement complete lightweight edge-intelligence capability: health (H_i), quality (Q_i), reliability (R_i), baseline (median/MAD), anomaly (A_i), configured hazard evidence, confidence (C_h), severity (S_h), operational risk (R_h), and local hazard state machine (NORMAL/WATCH/SUSPECTED/CONFIRMED/CRITICAL/RESOLVED).

**Rationale**: 
- Local autonomy requirement: Master failure must not eliminate all intelligence
- Resilience: Local emergency path requires local hazard state assessment
- Documents 06, 11, 14 specify node-local emergency capability survives Master failure

**Implementation**:
- **Capability MUST be implemented** in firmware (`firmware/components/intelligence/`)
- **Deployment configuration MAY disable** explicitly designated optional modules for resource constraints
- **Disabled state MUST be observable** (diagnostics endpoint, configuration query)
- **Effective configuration MUST be versioned** (node reports active config version in heartbeat)
- **Information Condition MUST degrade honestly** when modules disabled (e.g., confidence → DEGRADED, hazard state → UNKNOWN)

**Status**: LOCKED - Implementation mandatory

**Related Specifications**: 
- Document 06 (Hardware/Edge Node), Sections 9-10
- Document 11 (Communication/Resilience), Section 7
- Document 18 (Implementation), Section 5.2
- Resolves ambiguity between "MUST run" and "optional configured subset"

**Additional Context**:
- Original ambiguity: Documents stated Edge "MUST run" lightweight intelligence BUT also described modules as "optional configured subset"
- Clarification distinguishes: "MUST have capability" vs "MAY disable in specific deployments"
- Example deployment configurations:
  * **Full capability** (default): All modules enabled
  * **Minimal capability** (resource-constrained): Baseline/anomaly disabled, edge reports degraded state
  * **Hardware-only** (testing): All intelligence disabled, node functions as pure sensor sampler

---

### C2: Calibration Ownership [LOCKED 2026-09-07]

**Decision**: Per-node calibration is a versioned provisioning/configuration artifact associated with `node_id`. Calibration constants MUST NOT be hard-coded into sensor drivers.

**Rationale**:
- Sensor-specific variation: Each sensor has unique calibration characteristics
- Field recalibration support: Sensors may require recalibration after deployment or replacement
- Audit trail: Calibration history must be traceable for validation and compliance
- Separation of concerns: Sensor drivers implement measurement logic; calibration data is external configuration

**Implementation**:
- **Calibration constants include**: Offset, gain, response curve, gas species mapping, warm-up timing
- **Storage location**: TBD during Phase 4 (Node Enrollment + HMAC Authentication)
  * Candidates: Secure provisioning store (alongside HMAC secrets), database table, JSON files
- **Versioning**: Each calibration profile has version identifier + timestamp + calibration method
- **Provisioning workflow**: TBD (script-driven, manual, automated field calibration)
- **Sensor driver interface**: Reads calibration from external store, applies to raw measurements

**Status**: LOCKED - Hard-coding prohibited; exact provisioning mechanism is IMPLEMENTATION DECISION

**Related Specifications**:
- Document 06 (Hardware/Edge Node), Section 6 (sensor classes)
- Document 17 (Validation), Section 5 (hardware validation, calibration records)
- Document 19 (Configuration), Section 3.2 (sensor parameters)
- Resolves ambiguity about where calibration constants are stored and versioned

**Additional Context**:
- Original ambiguity: Sensor calibration requirements clear, but storage/versioning location not explicit
- Hard-coding prohibition: Prevents firmware recompilation for each sensor unit
- Calibration record requirements (from Document 17):
  * Known-point comparison over operating range (temperature)
  * Reference instrument side-by-side (PM2.5/PM10, gas)
  * Known-depth references (water level)
  * Calibration curve/lookup (soil moisture)
- **Deferred**: Exact storage format, provisioning workflow → UID-1 below

---

### C3: Fire Spread Compute Offload [LOCKED 2026-09-07]

**Decision**: Master-local fire spread computation is MANDATORY for V1 resilience. Backend/cloud offload is OPTIONAL implementation capacity. No automatic area/load threshold will be invented yet. V1 does not depend on backend offload for correctness.

**Rationale**:
- Resilience requirement: Master MUST function during internet loss (Mode B failure)
- Documents 05, 11 specify Master as PRIMARY location for fire spread engine
- Document 03 states Backend offload is "optional" extension
- V1 prototype scope: Master-local computation sufficient for ~25 km² target area

**Implementation**:
- **Master MUST implement**: Arrival-time propagation engine (8-neighbor, directional ROS, wind FROM→TO conversion)
- **Master location**: `services/master-service/fire_engine/`
- **Backend MAY implement**: Same fire spread engine for large-area offload (future optimization)
- **Backend location** (if implemented): `services/backend/modules/geospatial/fire_spread.py`
- **Offload trigger**: TBD during performance testing (Phase 5 or later)
  * Candidates: Area threshold (e.g., >100 km²), manual operator request, computational load metric
- **API contract** (if offload implemented): Master submits fire state + environmental inputs → Backend returns updated arrival-time raster

**Status**: LOCKED - Master mandatory, offload optional; trigger mechanism is IMPLEMENTATION DECISION (deferred)

**Related Specifications**:
- Document 05 (Fire Spread Geospatial), Section 3 (arrival-time propagation)
- Document 03 (Technology Stack), Section 10.3 (Master PRIMARY, Backend optional)
- Document 11 (Communication/Resilience), Section 4.2 (Mode B: Internet lost, Master continues)
- Document 18 (Implementation), Section 5.5 (Fire Geospatial Engine)
- Resolves ambiguity about when fire spread computation runs on Master vs Backend

**Additional Context**:
- Original ambiguity: Document 03 said "Master PRIMARY" with "Backend optional offload"; Document 05 described Master/Backend as unified
- V1 scope: ~25 km² fire simulation area, ~10-50 nodes → Master-local sufficient
- Future optimization: Large-area scenarios (>100 km²) may benefit from backend offload
- **Deferred**: Offload trigger conditions, performance threshold → UID-2 below

---

## Unresolved Questions

**Currently: NONE**

All questions necessary for Phase 3 (Repository Initialization) have been resolved. Future implementation phases may surface new questions.

---

## Deferred Implementation Details

The following implementation details are DEFERRED to later phases. These are NOT architectural conflicts—the ownership rules and constraints are LOCKED; only the specific mechanisms are deferred.

### UID-1: Calibration Provisioning Mechanism [DEFERRED]

**Question**: What is the exact storage format (JSON file, database table, secure key-value store) and provisioning workflow for per-node calibration profiles?

**Current Status**: OPEN (deferred to Phase 4: Node Enrollment + HMAC Authentication)

**What is Locked**:
- Calibration is versioned provisioning artifact associated with node_id (C2 decision)
- Calibration constants MUST NOT be hard-coded in sensor drivers (C2 decision)
- Calibration includes: offset, gain, response curve, gas species mapping

**What Needs Resolution**:
- Storage format: JSON file vs database table vs secure key-value store
- Provisioning workflow: Script-driven vs manual vs automated field calibration
- Versioning scheme: How calibration versions are identified and tracked
- Access control: How firmware retrieves calibration (API endpoint, local file, provisioned at flash time)

**Why Deferred**: 
- C2 establishes ownership rule (what, why); exact mechanism needs security/DevOps context
- Provisioning workflow depends on node enrollment design (Phase 4)
- Storage choice affects secret management architecture (also Phase 4)

**Decision Criteria** (when resolving):
- **Security**: Calibration data integrity (tampering detection)
- **Auditability**: Calibration history traceable
- **Field recalibration**: Easy to update after sensor replacement
- **Integration**: Compatible with secret provisioning workflow (HMAC secrets)

**Candidates**:
1. **Database table** (`calibration_profiles` table with `node_id` foreign key)
   - Pros: Centralized, versioned, auditable
   - Cons: Requires database connection for firmware provisioning
   
2. **JSON files** (`calibration/<node_id>.json` in secure provisioning store)
   - Pros: Simple, file-based audit trail
   - Cons: Manual versioning, no transactional updates
   
3. **Secure key-value store** (AWS Secrets Manager, HashiCorp Vault)
   - Pros: Integrated with secret management, access-controlled
   - Cons: Additional infrastructure dependency

---

### UID-2: Fire Spread Offload Trigger [DEFERRED]

**Question**: Under what conditions (area threshold, load threshold, manual trigger) does Master offload fire spread computation to Backend?

**Current Status**: OPEN (deferred to Phase 5: Fire Geospatial Engine or later during performance testing)

**What is Locked**:
- Master-local fire spread computation MANDATORY for V1 (C3 decision)
- Backend offload OPTIONAL (C3 decision)
- V1 does not depend on backend offload for correctness (C3 decision)

**What Needs Resolution**:
- Trigger conditions: Area threshold (e.g., >100 km²), computational load metric, manual operator request
- Performance threshold: What Master resource utilization justifies offload
- Fallback behavior: If backend unavailable, Master continues locally (per resilience requirement)

**Why Deferred**:
- C3 establishes Master mandatory, offload optional; V1 scope does not require offload
- Performance characteristics unknown until fire engine implemented and benchmarked
- Threshold depends on Master hardware specifications (Raspberry Pi model, memory, CPU)

**Decision Criteria** (when resolving):
- **Master performance**: Measured latency/throughput for different fire simulation areas
- **Resilience**: Backend offload must NOT compromise Master-local capability
- **Operator control**: Manual trigger option for known large-area scenarios
- **Simplicity**: V1 may skip offload entirely if Master performance adequate

**Candidates**:
1. **No offload in V1** (simplest)
   - Pros: Simpler architecture, fewer failure modes
   - Cons: May limit maximum simulation area
   
2. **Area threshold** (e.g., area >100 km² → offload)
   - Pros: Automatic, predictable
   - Cons: Arbitrary threshold, may not reflect actual load
   
3. **Computational load metric** (e.g., propagation time >500ms → offload)
   - Pros: Adaptive to actual performance
   - Cons: Complex, requires runtime monitoring
   
4. **Manual operator request** (operator selects "large-area mode")
   - Pros: Simple, explicit, no automatic decisions
   - Cons: Requires operator knowledge

---

### UID-3: Configuration File Format [DEFERRED]

**Question**: YAML vs JSON vs TOML for configuration registry files?

**Current Status**: OPEN (deferred to Phase 1: Canonical Telemetry Contract + Database when configuration schema is implemented)

**What is Locked**:
- Configuration registry structure from Document 19
- Configuration classes: CONST, TUNABLE, POLICY, LIMIT, ENUM, FLAG, SECRET, PROFILE
- Configuration namespaces: edge.*, sensor.*, intelligence.*, hazard.*, fire.*, incident.*, alert.*, comm.*, security.*, sim.*, ui.*, deploy.*, flag.*

**What Needs Resolution**:
- File format: YAML (.yaml), JSON (.json), TOML (.toml)
- Schema validation approach
- Comment support (for human-readable config documentation)

**Why Deferred**:
- Registry structure locked (Document 19); file format is implementation detail
- Depends on Python/TypeScript library choices (pydantic, zod, etc.)
- Format choice does NOT affect configuration semantics

**Decision Criteria** (when resolving):
- **Human readability**: Configuration files may be hand-edited
- **Schema validation**: Strong typing, validation library support
- **Comment support**: Inline documentation of parameters
- **Tooling**: Python/TypeScript ecosystem support

**Candidates**:
1. **YAML** (.yaml)
   - Pros: Human-readable, comment support, widely used
   - Cons: Parsing complexity, subtle indentation errors
   
2. **JSON** (.json)
   - Pros: Simple parsing, strong tooling, widely supported
   - Cons: No comments, less human-readable (quotes, no trailing commas)
   
3. **TOML** (.toml)
   - Pros: Human-readable, comment support, simple parsing
   - Cons: Less common, fewer validation libraries

---

### UID-4: Golden Vector Test Framework [DEFERRED]

**Question**: pytest vs unittest, tolerance-checking library, test data format?

**Current Status**: OPEN (deferred to Phase 1: Golden Vector Framework establishment)

**What is Locked**:
- 11 golden vector sets (GV-H01 through GV-GEO02) from Document 17
- Numerical tolerances required (absolute/relative, per quantity)
- State machine: exact match
- Geometry: topological + area tolerance

**What Needs Resolution**:
- Test framework: pytest (preferred) vs unittest
- Tolerance checking: numpy.allclose, custom assertions, dedicated library
- Test data format: JSON, YAML, Python dictionaries, CSV

**Why Deferred**:
- Requirements clear (11 vector sets, numerical tolerances); tooling choice is implementation detail
- Depends on Python environment setup (Phase 1)
- Format choice does NOT affect validation semantics

**Decision Criteria** (when resolving):
- **Developer familiarity**: Team's existing testing experience
- **IDE support**: Test discovery, debugging, parametrization
- **Tolerance expressiveness**: Flexible tolerance specification (absolute, relative, per-field)
- **Readability**: Test failures clearly show expected vs actual

**Candidates**:
1. **pytest** (preferred)
   - Pros: Modern, flexible, excellent parametrization, clear failure output
   - Cons: Additional dependency (but widely used)
   
2. **unittest** (Python standard library)
   - Pros: No additional dependency, built-in
   - Cons: More verbose, less flexible parametrization

---

## Decision Change Process

### Changing a LOCKED Decision

**LOCKED decisions require:**
1. **Explicit human approval**
2. **Specification update** (if decision came from specification)
3. **Impact analysis**: Which subsystems affected, which tests affected
4. **Migration path**: How existing code transitions
5. **Update DECISIONS.md**: Record change with rationale

**Process:**
1. Create issue/PR describing proposed change
2. Reference original decision (this document, section number)
3. Explain why change needed (specification conflict, discovered constraint)
4. Propose resolution options (see DEVELOPMENT_WORKFLOW.md Phase 6)
5. Wait for explicit human approval
6. Update this document with new decision + change log
7. Update IMPLEMENTATION_CONSTITUTION.md if invariants affected

### Changing an IMPLEMENTATION DECISION

**IMPLEMENTATION DECISION changes require:**
1. **Technical justification** (why change improves implementation)
2. **PR with tests** demonstrating improvement
3. **No architecture deviation** (CONSTITUTION + REPOSITORY_MAP preserved)

**Process:**
1. Create PR with proposed change
2. Reference original decision (this document)
3. Justify why change improves implementation
4. Demonstrate tests pass
5. Normal PR review process
6. Update this document after merge

### Resolving an OPEN Question

**OPEN questions become decisions when:**
1. Implementation phase reaches decision point
2. Sufficient context available (performance data, hardware specs, etc.)
3. Options evaluated with decision criteria

**Process:**
1. Evaluate candidates using decision criteria
2. Make recommendation
3. Get human approval (if LOCKED) or technical review (if IMPLEMENTATION DECISION)
4. Update this document: Move from "Unresolved" or "Deferred" to "Resolved"
5. Record decision with format above

---

---

## Phase 4 Decisions

### D1: H_i Missing Diagnostic Behavior [IMPLEMENTATION DECISION 2026-09-08]

**Decision**: When required diagnostic dimensions D_ij are missing (absent/None), H_i computation returns `(None, False)` where the boolean flag signals incomplete diagnostics.

**Rationale**:
- Preserves missing ≠ zero invariant (IMPLEMENTATION_CONSTITUTION.md Section 3)
- Provides honest signal degradation: incomplete diagnostic data = incomplete health assessment
- Explicit signaling via return tuple allows downstream consumers to detect and handle degraded information
- Strictest information honesty: ensures incomplete diagnostic state is never silently treated as healthy

**Implementation**:
- `compute_health()` returns `Tuple[Optional[float], bool]`
- First value: H_i in [0,1] or None when diagnostics incomplete
- Second value: `diagnostics_complete` flag (True = all required diagnostics present)
- Implementation: `reference/python/nexalert_reference/health.py`

**Status**: IMPLEMENTATION DECISION - approved for Phase 4

**Related Specifications**:
- Document 04, Section 3.1 (Sensor Health H_i) - specifies formula but not missing diagnostic behavior
- IMPLEMENTATION_CONSTITUTION.md, Section 3 (Missing ≠ zero invariant)
- IMPLEMENTATION_CONSTITUTION.md, Section 11 (Explicit handling requirement)

**Additional Context**:
- **Specification gap**: Document 04 Section 3.1 specifies H_i formula `H_i^soft = Σ_j w_ij · D_ij` but does NOT define behavior when D_ij is missing
- **Alternative considered**: Compute partial H_i using only available diagnostics with renormalized weights
  * Rejected: Would produce degraded score without explicit signal that computation was incomplete
- **Alternative considered**: Treat specific diagnostics as optional vs required (configuration-driven)
  * Deferred: Requires configuration registry (Phase 5); current implementation assumes all weighted diagnostics are required
- **Phase 4 scope**: Reference implementation establishes honest degradation pattern; production systems (Phase 5+) may add configuration to distinguish required vs optional diagnostics

---

## Change Log

### 2026-09-08: Phase 4 Decisions
- **Added D1**: H_i missing diagnostic behavior (IMPLEMENTATION DECISION)
- Documents human-approved Phase 4 decision for missing diagnostic handling

### 2026-09-07: Initial Version
- Created DECISIONS.md
- Recorded resolved clarifications C1, C2, C3 from architectural reconnaissance
- Documented deferred implementation details UID-1, UID-2, UID-3, UID-4
- Established decision change process

---

## Summary

**Resolved Decisions**: 4 (C1, C2, C3, D1)  
**Unresolved Questions**: 0  
**Deferred Implementation Details**: 4 (UID-1, UID-2, UID-3, UID-4)

**All decisions necessary for Phase 3 (Repository Initialization) are resolved.**

---

**END OF ARCHITECTURAL DECISIONS**
