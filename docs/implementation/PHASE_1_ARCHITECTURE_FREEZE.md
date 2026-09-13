# NexAlert Phase 1 Architecture Freeze

**Status**: APPROVED  
**Freeze Date**: 2026-09-13  
**Authority**: Human architectural decision session  
**Baseline**: 9c628d8 + CONTRACT_RECONCILIATION_V1.md audit  
**Purpose**: Lock critical architectural decisions, unblock Phase 2 implementation

---

## FREEZE STATUS: **APPROVED**

Phase 1 architectural decisions are LOCKED. Phase 2 implementation may proceed under the decisions below.

---

## PART 1: APPROVED ARCHITECTURAL DECISIONS

### DECISION 1: MASTER ARCHITECTURE (Q1 RESOLVED)

**Decision**: Raspberry Pi is the NexAlert **Master**. Cloud infrastructure is the **Backend**. Master and Backend are **distinct deployment responsibilities**.

**Clarification**:
- Master and Backend may share modular codebase/components where appropriate
- Distinction is deployment responsibility, not necessarily separate codebases
- Master MUST NOT collapse conceptually into Backend

**Master Responsibilities** (MUST provide):
- Local MQTT ingestion (nodes → Master)
- Local intelligence/fusion (Track B2 regional intelligence)
- Incident lifecycle management
- Local API (operations continue during internet failure)
- WebSocket/dashboard gateway
- **Mode B resilience**: Operation during internet failure

**Backend Responsibilities** (MUST provide):
- Cloud persistence (PostgreSQL + PostGIS)
- Long-term analytics
- External integrations (alerts, reporting)

**Deployment Model**:
```
ESP32 Nodes → MQTT → Raspberry Pi Master → Internet → Cloud Backend
                      ↓
                 Local Dashboard (Mode B: Master continues)
```

**Implementation Impact**:
- Current `services/backend/` codebase can serve both Master and Backend
- Deployment configuration distinguishes roles
- Master deployment: Raspberry Pi runs FastAPI + Track B2 locally
- Backend deployment: Cloud server runs FastAPI + persistence
- Clear separation in REPOSITORY_MAP.md required

**Acceptance Gate**:
- Master runs on Raspberry Pi without internet (Mode B test)
- Local dashboard connects to Master during internet failure
- Backend receives Master data when internet available

---

### DECISION 2: NODE IDENTITY FORMAT (Q2 RESOLVED)

**Decision**: Canonical protocol node_id pattern is `NODE-[0-9]{3,}` (3+ digits)

**Canonical Format**: NODE-001, NODE-002, NODE-003, ...NODE-042, NODE-1234

**Incorrect Formats**: 
- NEX-001 (wrong prefix)
- NODE-1 (too few digits)
- NODE-01 (too few digits)

**Separation of Concerns**:
- **node_id** (protocol): NODE-001 (canonical, immutable, schema-enforced)
- **display_name** (human-readable): "NEX-HW-PROTO-1", "Fire Station Alpha", etc. (separate field, optional)

**MQTT Topic**: `Nexalert/telemetry/<node_id>` → `Nexalert/telemetry/NODE-001`

**Implementation Impact**:
- Update validator to enforce full pattern (reject NODE-1, NODE-01)
- Demo code using NEX-001 acceptable as demo fixture (not protocol violation)
- Production nodes MUST use NODE-XXX format
- Add display_name field to node registry (separate from node_id)

**Acceptance Gate**:
- Validator rejects NODE-1, NODE-01
- Schema validation passes for NODE-001, NODE-042, NODE-1234
- Demo can continue using NEX-001 in DEMO FIXTURE context

---

### DECISION 3: HARDWARE / SIMULATION / DEMO BOUNDARIES (Q3 RESOLVED)

**Decision**: Three distinct concepts with clear boundaries

**HARDWARE** (live sensor telemetry):
- Real physical sensor readings
- Enters canonical ingestion path
- Schema validation required
- source: "HARDWARE"
- Full intelligence pipeline
- Database persistence

**SIMULATION** (synthetic telemetry for testing):
- Synthetic telemetry data
- Enters canonical ingestion path (same as HARDWARE)
- Schema validation required (same as HARDWARE)
- source: "SIMULATION"
- Full intelligence pipeline (same as HARDWARE)
- Database persistence
- **Truth separation required**: Simulator MUST NOT leak ground truth into operational intelligence (Constitution §18)

**DEMO FIXTURE** (presentation/testing data):
- Presentation data for demos
- Does NOT enter canonical ingestion path
- `services/backend/modules/api/routes_demo.py` is DEMO FIXTURE
- Frontend demo mode fallback is DEMO FIXTURE
- No schema validation requirement (outside operational system)
- No truth-separation requirement (not operational simulation)

**Implementation Impact**:
- `routes_demo.py` remains as-is (DEMO FIXTURE confirmed)
- Dashboard demo mode acceptable (clearly labeled)
- Future operational simulation (Track C) MUST enter canonical path with source="SIMULATION"
- REPOSITORY_MAP.md documents three-way distinction

**Acceptance Gate**:
- HARDWARE telemetry enters canonical ingestion
- SIMULATION telemetry (when implemented) uses same pipeline
- DEMO FIXTURE stays separate (no conflation with operational simulation)

---

### DECISION 4: MULTI-HAZARD INDEPENDENCE (Q3 PARTIAL)

**Decision**: Design canonical HazardAssessment domain model BEFORE schema implementation. Do NOT choose JSONB merely to close audit item.

**Requirements** (from Document 04 Section 6):

Each hazard type **independently** owns:
- Evidence (E_h)
- Confidence (C_h)
- Severity (S_h)
- Operational Risk (R_h)
- Hazard State (NORMAL/WATCH/SUSPECTED/CONFIRMED/CRITICAL/RESOLVED)

**No Universal Combined Scalar**: Fire + flood + pollution cannot combine into single confidence/severity/risk

**Incident → HazardAssessment Relationship**:
- A regional incident may reference one or more independent hazard assessments
- Each hazard assessment maintains independent state
- No aggregation across hazard types

**Implementation Approach** (Phase 2 design task):
1. Design canonical HazardAssessment domain model (domain layer)
2. Map domain model to database schema (persistence layer)
3. Options after domain design:
   - Option A: JSONB column `hazard_metrics: {hazard_type: {confidence, severity, risk}}`
   - Option B: Separate HazardAssessment rows per hazard type
   - Option C: Hybrid (incident summary + detail rows)
4. Choose based on domain model requirements, NOT convenience

**Implementation Impact**:
- Phase 2A: Design HazardAssessment domain model
- Phase 2B: Database schema design based on domain model
- Phase 2C: Update Track B2 fusion to preserve per-hazard independence
- Current single-scalar schema acceptable until design complete

**Acceptance Gate**:
- Domain model designed and approved
- Schema supports independent per-hazard state
- Track B2 fusion preserves hazard independence
- Fire + flood incident can coexist with independent reasoning

---

### DECISION 5: TELEMETRY SCHEMA ENFORCEMENT

**Decision**: `schemas/telemetry-envelope.schema.json` is THE authoritative telemetry contract. No frontend normalization of alternative shapes in production.

**Schema Authority**:
- Schema defines 18 required fields, typed units, null semantics
- All telemetry ingestion MUST validate against schema
- Non-conforming payloads MUST be rejected at boundary

**Frontend Normalization**:
- Current dashboard normalization layer (`data.telemetry || data.sensors`) is symptom of upstream non-compliance
- Acceptable as temporary mitigation for demo
- MUST be removed in production (accept only canonical shape)

**Implementation Impact**:
- Add backend validator middleware to ALL telemetry ingestion endpoints
- REJECT non-conforming payloads (400 + schema violation details)
- Verify firmware emits canonical shape
- Remove frontend normalization layer in production

**Acceptance Gate**:
- Backend enforces schema at all ingestion boundaries
- Non-conforming payload rejected with clear error
- Frontend expects only canonical shape (no normalization)
- Firmware emits valid canonical telemetry

---

### DECISION 6: TIMESTAMP SEMANTICS (CONFIRMED)

**Decision**: Two distinct timestamps REQUIRED (already implemented correctly)

**measurement_timestamp**:
- Edge node acquisition time (when sensor sampled)
- UTC ISO 8601
- Node's own clock (may drift)
- MUST NOT be trusted as server receive time

**received_timestamp**:
- Server/Master-assigned receive time (when backend received message)
- UTC ISO 8601
- Server authoritative clock
- Server-assigned (node CANNOT set this)

**Implementation Status**: ✅ Already correct
- Schema defines both (lines 41-49)
- Database models define both columns (measurement_ts, receive_ts)
- Constitution §12 satisfied

**No Action Required**: Implementation correct, decision confirms design

---

### DECISION 7: MISSING ≠ ZERO (CONFIRMED)

**Decision**: null/absent means unavailable. Zero is a measurement value. Never convert missing to zero.

**Representation**:
- Missing: `null` or absent field
- Zero measurement: `0` (legitimate value, e.g., 0°C is freezing)

**Implementation Status**: ✅ Correct in dashboard and schema
- Dashboard renders null as "—" (dimmed)
- Schema types all measurements `["number", "null"]`
- Validator warns on zero (legitimate but flagged for review)

**Remaining Verification**:
- Firmware sensor drivers (do they emit null or 0 for missing?)
- Backend Track B2 fusion (preserves null through pipeline?)

**No Schema Changes Required**: Implementation correct, verify firmware/backend only

---

### DECISION 8: EDGE INTELLIGENCE INTEGRATION (DEFERRED TO PHASE 2)

**Decision**: Do NOT rewrite intelligence mathematics unless parity tests prove it is wrong. Inspect existing implementation first.

**Current State**:
- Intelligence modules exist: `firmware/components/intelligence/` (baseline, anomaly, confidence, severity, risk, hazard_state)
- Unit tests exist for each module
- `main.c` comment claims "Complete Intelligence Pipeline" (line 9)
- **BUT**: main.c does NOT invoke intelligence modules in execution flow

**Phase 2 Investigation Required** (BEFORE modifying):
1. Inspect existing intelligence modules
2. Compare against reference Python golden vectors
3. Determine exactly WHY main.c is not invoking them:
   - Integration complexity?
   - Missing data flow?
   - Testing incomplete?
   - Intentional deferral?
4. Propose **minimum integration** required (not full rewrite)

**Implementation Approach**:
- Read intelligence module code
- Read reference Python implementation
- Compare algorithms
- Run existing unit tests
- Determine gap between "modules exist" and "modules invoked"
- Minimal integration patch (wire existing modules, don't rewrite math)

**Do NOT**:
- Rewrite intelligence algorithms without proof of incorrectness
- Delete existing intelligence modules
- Skip comparison to reference Python

**Acceptance Gate**:
- Intelligence modules invoked in main.c execution flow
- Parity tests pass (firmware output matches reference Python within tolerance)
- Golden-vector validation complete

---

### DECISION 9: RESILIENCE MODES (CONFIRMED + DEFERRED)

**Decision**: Master failure and internet failure remain distinct failure modes. Edge local emergency behavior is mandatory but implementation deferred.

**Failure Modes** (Constitution §17 LOCKED):
1. **Node Failure**: Individual sensor/node stops
2. **Sensor Failure**: One sensor on node fails, others continue
3. **Internet Failure (Mode B)**: Node↔Master works, Master↔Cloud fails
4. **Master Failure (Mode C)**: Master down, node continues local emergency

**Mode B (Internet Failure)** — MUST VERIFY:
- Master continues local intelligence without internet
- Local dashboard connects to Master
- Master buffers data for cloud sync when internet returns

**Mode C (Master Failure)** — DEFERRED:
- Edge node local emergency path (buzzer, LED, captive portal)
- **DO NOT IMPLEMENT YET** (per freeze decision)
- Requirements documented, implementation deferred to post-demo

**Implementation Impact**:
- Phase 2: Verify Mode B (Master continues during internet failure)
- Mode C: Document requirements, defer implementation
- No firmware changes for Mode C until explicitly approved

**Acceptance Gate** (Phase 2):
- Mode B verified: Master operates without internet
- Mode C requirements documented (implementation deferred)

---

## PART 2: RESOLVED QUESTIONS

### Q1: Master Architecture → RESOLVED

**Question**: Is Master=Backend (Raspberry Pi runs FastAPI) or Master≠Backend (separate services)?

**Resolution**: Master≠Backend (distinct deployment responsibilities, may share codebase)

**Impact**: Unblocks resilience verification, clarifies deployment model

---

### Q2: Node Identity Format → RESOLVED

**Question**: Is NEX-001 (demo) acceptable deviation or violation of NODE-XXX (schema)?

**Resolution**: NODE-XXX canonical, NEX-001 acceptable as DEMO FIXTURE (not protocol)

**Impact**: Validator enforcement clear, demo exception documented

---

### Q3: DEMO vs SIMULATION → RESOLVED

**Question**: Is `routes_demo.py` "simulation" (requires truth-separation) or "demo fixture"?

**Resolution**: DEMO FIXTURE (out of operational scope, no truth-separation required)

**Impact**: Constitution §18 does not apply to demo code, operational simulation distinct

---

### Q4: Multi-Hazard Schema → PARTIAL (Design Phase)

**Question**: JSONB column vs separate rows for per-hazard state?

**Resolution**: Design canonical domain model first, then choose schema approach

**Impact**: Phase 2 design task, no premature schema commitment

---

### Q5: Sensor Calibration → DEFERRED

**Question**: Do firmware sensor drivers contain hard-coded calibration constants?

**Resolution**: Deferred to Phase 2 sensor driver inspection

**Impact**: Non-blocking for Phase 2A work packages

---

## PART 3: REMAINING QUESTIONS

### Q6: Backend Confidence/Risk Formula Parity

**Question**: Do backend confidence/risk computations match reference Python definitions exactly?

**Status**: Open (low priority)

**Investigation Required**:
- Compare `regional_fusion.py` formulas to reference Python
- Unit test parity (backend output vs reference Python output)

**Impact**: Non-blocking (likely correct, verification needed)

**Resolution Timeline**: Phase 2B (after critical path complete)

---

### Q7: Firmware Sensor Calibration

**Question**: Do sensor drivers (DHT22, BMP280, MQ-135) contain hard-coded calibration?

**Status**: Open (non-blocking)

**Investigation Required**:
- Inspect `firmware/components/sensors/` driver code
- Check for hard-coded constants vs per-node configuration

**Impact**: Non-blocking for demo, required for deployment

**Resolution Timeline**: Phase 2C or Phase 3

---

### Q8: Missing≠Zero Firmware Verification

**Question**: Do firmware sensor drivers emit null or 0 for missing sensor reads?

**Status**: Open (non-blocking)

**Investigation Required**:
- Review sensor driver error handling
- Check telemetry envelope generation for missing values

**Impact**: Non-blocking (dashboard handles correctly, verify source)

**Resolution Timeline**: Phase 2B

---

## PART 4: PHASE 2 WORK PACKAGES

### Package 2A: Contract Enforcement (Week 1, 5 days)

**Owner**: Backend Engineer  
**Dependencies**: None (can start immediately)

**Tasks**:
1. **Telemetry Schema Enforcement** (2 days)
   - Add validator middleware to all telemetry ingestion endpoints
   - Enforce canonical schema at boundary
   - Reject non-conforming payloads (400 + violation details)
   - Test: send non-conforming payload, verify rejection

2. **Node Identity Validator** (1 day)
   - Update validator to enforce full NODE-[0-9]{3,} pattern
   - Reject NODE-1, NODE-01
   - Test: validator accepts NODE-001, rejects NODE-1

3. **Frontend Normalization Removal** (1 day)
   - Remove `normalizeTelemetry()` multi-shape support
   - Accept only canonical telemetry shape
   - Test: dashboard renders canonical telemetry correctly

4. **Firmware Telemetry Verification** (1 day)
   - Verify firmware emits canonical schema shape
   - Check measurement_timestamp vs received_timestamp
   - Check null handling for missing sensors

**Acceptance Criteria**:
- ✅ Backend rejects non-conforming telemetry at boundary
- ✅ Validator enforces NODE-[0-9]{3,} fully
- ✅ Frontend expects only canonical shape
- ✅ Firmware emits valid canonical telemetry

**Deliverables**:
- Validator middleware implementation
- Updated dashboard (no normalization)
- Test suite (schema enforcement)

---

### Package 2B: Multi-Hazard Domain Model (Week 1-2, 5 days)

**Owner**: Domain Architect + Backend Engineer  
**Dependencies**: None (can run parallel to 2A)

**Tasks**:
1. **Domain Model Design** (2 days)
   - Design canonical HazardAssessment entity
   - Define hazard-type independence semantics
   - Map to persistence requirements
   - Document: `docs/implementation/HAZARD_ASSESSMENT_DOMAIN_MODEL.md`

2. **Schema Design** (1 day)
   - Choose persistence approach (JSONB, separate rows, hybrid)
   - Design migration from current single-scalar schema
   - Define backward compatibility strategy

3. **Track B2 Fusion Update Design** (1 day)
   - Map fusion logic changes to preserve per-hazard independence
   - Define incident→hazard-assessment relationship

4. **Review & Approval** (1 day)
   - Present domain model for approval
   - Review schema design
   - Approve implementation approach

**Acceptance Criteria**:
- ✅ Domain model documented and approved
- ✅ Schema design supports per-hazard independence
- ✅ Fusion logic design preserves hazard state
- ✅ Migration strategy defined

**Deliverables**:
- HAZARD_ASSESSMENT_DOMAIN_MODEL.md
- Database schema design document
- Track B2 fusion update plan

**Blocking**: Schema implementation (Package 2C) until approved

---

### Package 2C: Multi-Hazard Implementation (Week 2-3, 5 days)

**Owner**: Backend Engineer  
**Dependencies**: Package 2B approved

**Tasks**:
1. **Database Migration** (1 day)
   - Implement approved schema design
   - Write Alembic migration
   - Test migration on development database

2. **Domain Model Implementation** (2 days)
   - Implement HazardAssessment entity
   - Update database models
   - Add per-hazard state tracking

3. **Track B2 Fusion Update** (2 days)
   - Update regional fusion to preserve per-hazard state
   - Update incident correlation
   - Preserve hazard independence through pipeline

**Acceptance Criteria**:
- ✅ Database schema supports per-hazard state
- ✅ Fire + flood incident coexists with independent reasoning
- ✅ Track B2 fusion preserves hazard independence
- ✅ API returns per-hazard metrics

**Deliverables**:
- Database migration (migrations_004_multi_hazard.py)
- Updated models_b2.py
- Updated regional_fusion.py, incident_correlation.py
- Integration tests

---

### Package 2D: Edge Intelligence Integration (Week 2-3, 5 days)

**Owner**: Firmware Engineer  
**Dependencies**: None (can run parallel)

**Tasks**:
1. **Intelligence Module Inspection** (1 day)
   - Read existing intelligence module code
   - Compare to reference Python implementation
   - Run existing unit tests
   - Document current state vs required state

2. **Integration Gap Analysis** (1 day)
   - Determine why main.c not invoking modules
   - Identify missing data flow
   - Design minimal integration patch

3. **Main.c Integration** (2 days)
   - Wire intelligence pipeline in main.c execution flow
   - sensor → H_i/Q_i/R_i → baseline → anomaly → evidence → confidence → severity → risk → hazard_state
   - Add intelligence outputs to telemetry envelope

4. **Golden-Vector Validation** (1 day)
   - Run firmware intelligence against reference Python golden vectors
   - Verify parity within tolerance
   - Document any deviations

**Acceptance Criteria**:
- ✅ Intelligence modules invoked in main.c
- ✅ Parity tests pass (firmware vs reference Python)
- ✅ Telemetry envelope includes intelligence outputs
- ✅ Golden-vector validation complete

**Deliverables**:
- Updated main.c (intelligence pipeline wired)
- Intelligence integration documentation
- Golden-vector test results

---

### Package 2E: Master Resilience Verification (Week 3, 3 days)

**Owner**: Systems Engineer + Backend Engineer  
**Dependencies**: Package 2A complete (telemetry contract enforced)

**Tasks**:
1. **Master Deployment Configuration** (1 day)
   - Document Master vs Backend deployment distinction
   - Configure Master deployment for Raspberry Pi
   - Configure Backend deployment for cloud

2. **Mode B Verification** (1 day)
   - Deploy Master on Raspberry Pi
   - Simulate internet failure (disconnect Master from internet)
   - Verify: Master continues local intelligence
   - Verify: Local dashboard connects to Master
   - Verify: Master buffers data for sync when internet returns

3. **Mode C Documentation** (1 day)
   - Document edge local emergency path requirements
   - Design local buzzer/LED alert logic
   - Design local captive portal emergency page
   - Mark as DEFERRED (do not implement yet)

**Acceptance Criteria**:
- ✅ Master runs on Raspberry Pi independently
- ✅ Mode B verified (Master continues during internet failure)
- ✅ Local dashboard connects to Master (no internet)
- ✅ Mode C requirements documented (implementation deferred)

**Deliverables**:
- Master deployment documentation
- Mode B test results
- Mode C requirements specification

---

### Package 2F: Documentation & Validation (Week 4, 3 days)

**Owner**: Tech Lead  
**Dependencies**: Packages 2A-2E complete

**Tasks**:
1. **REPOSITORY_MAP.md Update** (1 day)
   - Document Master vs Backend distinction
   - Document HARDWARE/SIMULATION/DEMO boundaries
   - Document node_id vs display_name
   - Document multi-hazard domain model

2. **Golden-Vector Test Harness** (1 day)
   - Create `services/backend/tests/golden_vectors/` structure
   - Add reference Python parity tests for backend
   - Document golden-vector methodology

3. **Phase 2 Completion Audit** (1 day)
   - Verify all acceptance criteria met
   - Run full test suite (reference Python, backend, firmware)
   - Document remaining gaps (if any)

**Acceptance Criteria**:
- ✅ REPOSITORY_MAP.md reflects Phase 2 changes
- ✅ Golden-vector harness operational
- ✅ All Phase 2 acceptance gates passed

**Deliverables**:
- Updated REPOSITORY_MAP.md
- Golden-vector test harness
- Phase 2 completion report

---

## PART 5: DEPENDENCIES

### Critical Path

```
START
  ↓
2A: Contract Enforcement (Week 1) ────────────┐
  ↓                                            ↓
2B: Multi-Hazard Domain Design (Week 1-2) ────┤
  ↓                                            ↓
2C: Multi-Hazard Implementation (Week 2-3)    ↓
  ↓                                            ↓
2D: Edge Intelligence (Week 2-3, parallel) ───┤
  ↓                                            ↓
2E: Master Resilience (Week 3) ───────────────┤
  ↓                                            ↓
2F: Documentation (Week 4) ───────────────────┘
  ↓
PHASE 2 COMPLETE
```

### Parallel Work

- **2A + 2B**: Can run in parallel (different codebases)
- **2C + 2D**: Can run in parallel (backend vs firmware)
- **2E**: Requires 2A complete (telemetry contract enforced)
- **2F**: Requires all packages complete

### Blocking Dependencies

- **2C** blocked by **2B approval** (domain model must be approved before implementation)
- **2E** blocked by **2A** (schema enforcement needed for resilience testing)
- **2F** blocked by **all** (documentation integrates all changes)

---

## PART 6: ACCEPTANCE GATES

### Gate 2A: Contract Enforcement

**Criteria**:
- [ ] Backend validator middleware enforces canonical schema
- [ ] Non-conforming telemetry rejected with 400 + details
- [ ] Validator enforces NODE-[0-9]{3,} fully (rejects NODE-1, NODE-01)
- [ ] Frontend accepts only canonical shape (no normalization)
- [ ] Firmware emits valid canonical telemetry envelope

**Verification**:
- Manual test: Send non-conforming payload → verify rejection
- Manual test: Send NODE-1 → verify rejection
- Manual test: Dashboard with canonical telemetry → renders correctly
- Automated test: Full schema validation test suite passes

**Sign-off**: Backend Engineer + QA

---

### Gate 2B: Multi-Hazard Domain Model

**Criteria**:
- [ ] Domain model documented (HAZARD_ASSESSMENT_DOMAIN_MODEL.md)
- [ ] Schema design supports per-hazard independence
- [ ] Fusion logic design preserves hazard state
- [ ] Migration strategy defined (backward compatibility)
- [ ] Design approved by domain architect

**Verification**:
- Review: Domain model document complete
- Review: Schema design reviewed and approved
- Review: Fusion logic design reviewed

**Sign-off**: Domain Architect + Tech Lead

---

### Gate 2C: Multi-Hazard Implementation

**Criteria**:
- [ ] Database migration succeeds (development database)
- [ ] Fire + flood incident coexists with independent state
- [ ] Track B2 fusion preserves per-hazard independence
- [ ] API returns per-hazard confidence/severity/risk
- [ ] Integration tests pass

**Verification**:
- Manual test: Create fire incident → verify independent state
- Manual test: Create flood incident → verify independent state
- Manual test: Fire+flood coexist → verify no scalar conflation
- Automated test: Track B2 integration tests pass

**Sign-off**: Backend Engineer + QA

---

### Gate 2D: Edge Intelligence Integration

**Criteria**:
- [ ] Intelligence modules invoked in main.c execution flow
- [ ] Parity tests pass (firmware vs reference Python within tolerance)
- [ ] Telemetry envelope includes intelligence outputs (diagnostics, hazard_assessment)
- [ ] Golden-vector validation complete
- [ ] Firmware compiles and runs without errors

**Verification**:
- Manual test: Flash firmware → verify intelligence invoked
- Automated test: Golden-vector tests pass (firmware vs reference)
- Manual test: Telemetry includes H_i, Q_i, R_i, confidence, severity, risk

**Sign-off**: Firmware Engineer + QA

---

### Gate 2E: Master Resilience Verification

**Criteria**:
- [ ] Master deployed on Raspberry Pi
- [ ] Mode B verified: Master continues during internet failure
- [ ] Local dashboard connects to Master (no internet required)
- [ ] Master buffers data for cloud sync when internet returns
- [ ] Mode C requirements documented (implementation deferred)

**Verification**:
- Manual test: Deploy Master on Pi → verify startup
- Manual test: Disconnect internet → verify Master continues
- Manual test: Open local dashboard → verify connection to Master
- Manual test: Reconnect internet → verify buffered data syncs
- Review: Mode C requirements document complete

**Sign-off**: Systems Engineer + Tech Lead

---

### Gate 2F: Documentation & Validation

**Criteria**:
- [ ] REPOSITORY_MAP.md reflects all Phase 2 changes
- [ ] Golden-vector test harness operational (backend)
- [ ] All Phase 2 acceptance gates passed (2A-2E)
- [ ] No regressions (reference Python 219 tests still pass)
- [ ] Phase 2 completion report documents remaining gaps

**Verification**:
- Review: REPOSITORY_MAP.md updated
- Automated test: Golden-vector harness runs successfully
- Automated test: Full test suite passes (no regressions)
- Review: Phase 2 completion report reviewed

**Sign-off**: Tech Lead + Project Manager

---

### PHASE 2 EXIT GATE

**Phase 2 is COMPLETE when**:

✅ All work packages (2A-2F) delivered  
✅ All acceptance gates (2A-2F) passed  
✅ No critical regressions introduced  
✅ Documentation reflects implementation state  
✅ Remaining gaps documented (not blocking)

**Phase 3 Ready**: Track C fire spread implementation (if applicable) or deployment preparation

---

## PART 7: RISK REGISTER

### Risk 1: Intelligence Module Integration Complexity

**Risk**: Intelligence modules may require significant refactoring to integrate (not just wiring)

**Probability**: Medium  
**Impact**: High (delays Package 2D)

**Mitigation**:
- Inspect modules BEFORE committing to timeline
- Compare to reference Python early (Week 1)
- Escalate if integration more complex than expected

**Contingency**: Extend Package 2D timeline if needed (non-critical path if parallel to 2C)

---

### Risk 2: Multi-Hazard Schema Migration Breaks Existing Data

**Risk**: Database migration may fail on existing incident data

**Probability**: Low  
**Impact**: High (data loss)

**Mitigation**:
- Test migration on development database first
- Backup production database before migration
- Design backward-compatible migration strategy

**Contingency**: Rollback migration, redesign schema approach

---

### Risk 3: Master Raspberry Pi Performance Insufficient

**Risk**: Raspberry Pi cannot handle local intelligence load (Mode B)

**Probability**: Low  
**Impact**: High (architectural failure)

**Mitigation**:
- Benchmark Master performance early (Week 3)
- Profile Track B2 fusion under load
- Monitor resource usage (CPU, memory)

**Contingency**: Optimize fusion algorithm, reduce local intelligence scope, or upgrade hardware

---

### Risk 4: Firmware Golden-Vector Parity Fails

**Risk**: Firmware intelligence output does not match reference Python

**Probability**: Medium  
**Impact**: Medium (requires algorithm debugging)

**Mitigation**:
- Compare algorithms early (Package 2D Task 1)
- Run unit tests before integration
- Document deviations with justification

**Contingency**: Fix firmware algorithms to match reference (extend Package 2D timeline)

---

### Risk 5: Frontend Normalization Removal Breaks Dashboard

**Risk**: Removing normalization causes dashboard to fail on existing telemetry

**Probability**: Low  
**Impact**: Medium (demo breakage)

**Mitigation**:
- Verify firmware emits canonical shape BEFORE removing normalization
- Test dashboard with canonical telemetry
- Keep normalization in demo mode as fallback

**Contingency**: Revert frontend change, enforce schema at backend instead

---

## PART 8: REMAINING BLOCKERS (NONE)

### Phase 1 Blockers → RESOLVED

1. ✅ Master Architecture (Q1) → APPROVED (Decision 1)
2. ✅ Node Identity (Q2) → APPROVED (Decision 2)
3. ✅ DEMO vs SIMULATION (Q3) → APPROVED (Decision 3)
4. ✅ Multi-Hazard (Q3) → APPROVED (Decision 4 — design first)
5. ✅ Telemetry Schema → APPROVED (Decision 5)

### Phase 2 Blockers → NONE

All architectural decisions approved. Implementation may proceed.

**Open Questions** (non-blocking):
- Q6: Backend formula parity (verification task, not blocker)
- Q7: Sensor calibration (inspection task, not blocker)
- Q8: Missing≠Zero firmware (verification task, not blocker)

---

## PART 9: CHANGE CONTROL

### Freeze Scope

**LOCKED** (cannot change without explicit approval):
- Master vs Backend distinction
- NODE-[0-9]{3,} canonical format
- HARDWARE/SIMULATION/DEMO boundaries
- Multi-hazard independence requirement
- Telemetry schema authority
- Two-timestamp semantics
- Missing≠Zero principle

**FLEXIBLE** (implementation details):
- Multi-hazard schema implementation approach (after domain model approved)
- Intelligence module integration mechanics (minimal change preferred)
- Master deployment configuration details
- Golden-vector test harness structure

### Change Request Process

**If implementation discovers**:
- Architectural decision conflicts with technical reality
- Frozen decision causes implementation deadlock
- Specification ambiguity not covered by freeze

**Then**:
1. STOP implementation
2. Document conflict with evidence
3. Propose resolution options
4. Request human approval
5. Update freeze document

**Do NOT**:
- Silently deviate from frozen decisions
- Choose "easier" approach without approval
- Rationalize convenience as necessity

---

## DOCUMENT CONTROL

**Version**: 1.0  
**Status**: APPROVED  
**Freeze Date**: 2026-09-13  
**Next Review**: After Phase 2 completion (estimated 2026-10-11)

**Approval Authority**: Human architectural decision session  
**Implementation Authority**: This freeze document + Contract Reconciliation V1

**Revision Policy**:
- Frozen decisions require explicit human approval to change
- Implementation details can be refined within frozen boundaries
- Clarifications can be added without changing decisions

---

## PHASE 1 ARCHITECTURE FREEZE: **APPROVED**

**All architectural decisions locked.**  
**All blockers resolved.**  
**Phase 2 implementation ready to proceed.**

**Next Action**: Begin Package 2A (Contract Enforcement) immediately

---

**END OF PHASE 1 ARCHITECTURE FREEZE**
