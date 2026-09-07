# NexAlert Development Workflow

**Version**: 1.0  
**Status**: ACTIVE  
**Last Updated**: 2026-09-07  
**Purpose**: Step-by-step process for planning, implementing, verifying, reviewing, and committing NexAlert code

---

## Table of Contents

1. [Workflow Overview](#workflow-overview)
2. [Phase 1: Planning](#phase-1-planning)
3. [Phase 2: Implementation](#phase-2-implementation)
4. [Phase 3: Verification](#phase-3-verification)
5. [Phase 4: Review](#phase-4-review)
6. [Phase 5: Commit](#phase-5-commit)
7. [Phase 6: Architecture-Change Procedure](#phase-6-architecture-change-procedure)
8. [AI Coding Workflow (Four-Role Loop)](#ai-coding-workflow-four-role-loop)
9. [Test-Before-Done Rule](#test-before-done-rule)
10. [Evidence Requirements](#evidence-requirements)
11. [Rollback and Recovery](#rollback-and-recovery)

---

## Workflow Overview

**Core Principle**: No task is "complete" until relevant tests pass.

### Six Workflow Phases

```
Planning → Implementation → Verification → Review → Commit → (Architecture-Change if needed)
   ↓            ↓              ↓            ↓         ↓
 Design      Build          Test        Check    Merge
```

### When to Use Each Phase

| **Phase** | **Trigger** | **Output** |
|---|---|---|
| **Planning** | New feature, bug fix, refactoring | Design document, task breakdown, affected subsystems |
| **Implementation** | Plan approved | Code changes in working branch |
| **Verification** | Code written | Tests passing, evidence collected |
| **Review** | Tests pass | Approved PR or explicit human approval |
| **Commit** | Review approved | Merged to main, CI passes |
| **Architecture-Change** | Specification conflict discovered | Proposed resolution, human decision, updated DECISIONS.md |

---

## Phase 1: Planning

**Goal**: Understand requirements, design approach, identify risks

### Step 1.1: Understand Requirements

**For feature work:**
- Read relevant specification sections (Documents 01-20)
- Identify which subsystems affected (use REPOSITORY_MAP.md)
- Check IMPLEMENTATION_CONSTITUTION.md for non-negotiable invariants
- Check DECISIONS.md for prior architectural decisions

**For bug fixes:**
- Reproduce the issue
- Identify root cause
- Determine which invariants violated (if any)
- Check if this is a specification conflict vs implementation bug

### Step 1.2: Design Approach

**Questions to answer:**
- Which files will change?
- Which subsystems involved?
- Does this respect ESP32 boundaries? (REPOSITORY_MAP.md Section 4)
- Does this preserve non-negotiable invariants? (CONSTITUTION.md Section 3)
- What tests are needed? (L0/L1/L2/L3/L4/L5)
- What golden vectors affected? (if mathematical)
- Is this safety-critical code? (CONSTITUTION.md Section 23)

**Output**: Written plan (in code comments, PR description, or separate design doc)

### Step 1.3: Identify Risks

- **Architecture deviation**: Does this conflict with locked architecture?
- **Parity regression**: Will golden vectors still pass?
- **Security impact**: Does this touch authentication, authorization, secrets?
- **Breaking change**: Will old nodes/clients still work?
- **Performance impact**: Will this affect telemetry latency, alert latency, or soak stability?

**If HIGH risk**: Propose approach before implementing (Phase 6: Architecture-Change)

---

## Phase 2: Implementation

**Goal**: Write code that implements the plan

### Step 2.1: Create Working Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/<short-description>
# OR: git checkout -b fix/<issue-description>
```

**Branch naming:**
- `feature/*` - New features
- `fix/*` - Bug fixes
- `refactor/*` - Code restructuring without behavior change
- `test/*` - Test-only changes
- `demo/*` - SIH demonstration preparation
- `docs/*` - Documentation updates

### Step 2.2: Implement Changes

**Follow:**
- IMPLEMENTATION_CONSTITUTION.md (all 26 sections)
- REPOSITORY_MAP.md (correct subsystem, correct directory)
- Specification requirements (Documents 01-20)
- Existing code style (linters will enforce)

**Preserve:**
- Non-negotiable invariants (CONSTITUTION Section 3)
- Subsystem boundaries (CONSTITUTION Sections 4-6)
- Golden vector parity (CONSTITUTION Section 8)
- Security invariants (CONSTITUTION Section 19)

### Step 2.3: Write Tests (Test-First or Test-Alongside)

**Test-first (preferred for new features):**
1. Write failing test that captures requirement
2. Implement feature until test passes
3. Refactor while keeping test green

**Test-alongside (acceptable for exploratory work):**
1. Implement feature incrementally
2. Write tests as you go
3. Verify tests pass before claiming done

**Required test levels** (depending on change):
- **L0 (static/schema)**: Always (linters, schema validation)
- **L1 (unit)**: For any new function or modified logic
- **L2 (component)**: For subsystem-level changes
- **L3 (integration)**: For changes crossing subsystems
- **L4 (system)**: For scenario-level behavior
- **L5 (field)**: For hardware/sensor changes (calibration, trials)

### Step 2.4: Run Tests Locally

```bash
# Python backend/Master
cd services/backend
pytest tests/ -v

# Firmware
cd firmware
idf.py build
idf.py test

# Frontend
cd apps/authority-dashboard
npm test

# Golden vectors
cd tests/golden-vectors
pytest test_*.py -v
```

**Do NOT proceed to Phase 3 if tests fail.**

---

## Phase 3: Verification

**Goal**: Prove the implementation works correctly

### Step 3.1: Run Full Test Suite

**Backend:**
```bash
cd services/backend
pytest tests/ --cov=modules --cov-report=term-missing
black --check .
flake8 .
mypy modules/
```

**Firmware:**
```bash
cd firmware
idf.py build
# Run golden vector parity tests
python3 ../scripts/validation/check_parity.py
```

**Frontend:**
```bash
cd apps/authority-dashboard
npm run lint
npm run type-check
npm test -- --coverage
npm run build  # Verify build succeeds
```

### Step 3.2: Run Affected Golden Vectors

**If mathematical changes** (H_i, Q_i, R_i, baseline, A_i, C_h, S_h, R_h, fire spread):

```bash
cd tests/golden-vectors
pytest test_health.py -v          # GV-H01
pytest test_quality.py -v         # GV-Q01
pytest test_reliability.py -v     # GV-R01
pytest test_baseline.py -v        # GV-B01
pytest test_anomaly.py -v         # GV-A01
pytest test_confidence.py -v      # GV-C01
pytest test_severity_risk.py -v   # GV-S01
pytest test_hysteresis.py -v      # GV-HZ01
pytest test_gradient.py -v        # GV-GEO01
pytest test_fire_spread.py -v     # GV-FIRE01
pytest test_geometry.py -v        # GV-GEO02
```

**Golden vector regression = BLOCKED merge**

### Step 3.3: Run Security Tests (If Security-Relevant)

**If authentication, authorization, secrets, or safety-critical**:

```bash
cd tests/security
pytest test_hmac_authentication.py -v       # SEC-01, SEC-02
pytest test_replay_protection.py -v         # SEC-03, SEC-04
pytest test_signature_verification.py -v    # SEC-06, SEC-07
pytest test_rbac.py -v                      # SEC-08
```

### Step 3.4: Run Integration Tests (If Cross-Subsystem)

**If Edge↔Master, Master↔Backend, Backend↔Frontend**:

```bash
cd tests/integration
pytest test_telemetry_to_incident.py -v
pytest test_incident_to_alert.py -v
pytest test_e2e_trace.py -v
```

### Step 3.5: Evidence Collection

**Collect:**
- Test output (copy terminal output or save JUnit XML)
- Coverage report (if coverage changed significantly)
- Golden vector results (if mathematical)
- Performance metrics (if performance-critical)
- Manual verification screenshots (if UI change)

**Store evidence**: Attach to PR description or save to `docs/validation/<feature-name>/`

---

## Phase 4: Review

**Goal**: Verify correctness, architecture compliance, test coverage

### Step 4.1: Self-Review

**Before requesting review, check:**
- [ ] All tests pass locally
- [ ] Linters pass (black, flake8, mypy, eslint, clang-format)
- [ ] Golden vectors pass (if mathematical)
- [ ] Code follows existing patterns in subsystem
- [ ] No secrets in code (check with `git diff | grep -i secret`)
- [ ] IMPLEMENTATION_CONSTITUTION.md preserved (all 26 sections)
- [ ] REPOSITORY_MAP.md boundaries respected
- [ ] Test coverage adequate (new code has tests)
- [ ] Commit messages descriptive (see Phase 5.1)

### Step 4.2: Create Pull Request

```bash
git push origin feature/<short-description>
# Then create PR via GitHub/GitLab UI
```

**PR title**: Short imperative statement (e.g., "Add HMAC replay protection", "Fix baseline freeze during CONFIRMED")

**PR description template:**

```markdown
## Summary
One-paragraph description of what changed and why.

## Specification Reference
- Document X, Section Y (requirement FR-XXX or NFR-XXX)
- Addresses architectural invariant Z (if applicable)

## Changes
- Subsystem A: what changed
- Subsystem B: what changed

## Tests
- [ ] Unit tests: `pytest tests/test_X.py`
- [ ] Golden vectors: GV-H01, GV-Q01 (list affected)
- [ ] Integration tests: (if applicable)
- [ ] Security tests: SEC-01 (if applicable)

## Evidence
- Test output: (attach or link)
- Golden vector results: (attach or link)
- Manual verification: (screenshots if UI)

## Risks
- (List any known risks or limitations)

## Checklist
- [ ] Tests pass
- [ ] Linters pass
- [ ] Golden vectors pass (if mathematical)
- [ ] Architecture compliance verified
- [ ] No secrets in code
- [ ] Commit messages descriptive
```

### Step 4.3: CI/CD Verification

**CI pipeline MUST include:**
- Lint/format checks (black, flake8, eslint)
- Unit tests
- Golden vectors (if mathematical code present)
- Build verification (firmware, backend, frontend all build)
- Security tests (if security-relevant code present)

**CI failure = BLOCKED merge**

### Step 4.4: Human Review

**Reviewer checks:**
- Architecture compliance (CONSTITUTION + REPOSITORY_MAP)
- Test coverage adequate
- No architectural deviation without approval
- No security regression
- Code quality acceptable
- Documentation updated (if public API changed)

**Safety-critical code** (CONSTITUTION Section 23) **requires**:
- Technical lead or designated safety reviewer approval
- Explicit verification that relevant acceptance gates still pass

### Step 4.5: Address Feedback

- Make requested changes in same branch
- Push new commits (do NOT force-push, preserve review history)
- Re-run tests
- Request re-review

---

## Phase 5: Commit

**Goal**: Merge approved changes to main branch

### Step 5.1: Commit Message Format

**Structure:**
```
<type>: <short summary (50 chars max)>

<body: detailed explanation, wrapped at 72 chars>

- What changed
- Why it changed
- What specification/requirement addresses

Refs: Document X Section Y, FR-XXX
Co-Authored-By: Claude Code <noreply@anthropic.com>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring without behavior change
- `test`: Test-only changes
- `docs`: Documentation updates
- `chore`: Build/tooling changes
- `perf`: Performance improvements
- `security`: Security improvements

**Example:**
```
feat: Add HMAC-SHA256 node telemetry authentication

Implement per-node HMAC-SHA256 authentication for canonical
telemetry ingestion. Includes replay protection via sequence
number + timestamp validation within 120s window.

- Add HMAC generation in firmware (components/security/)
- Add HMAC verification in backend (modules/security/)
- Add replay protection (modules/ingestion/)
- Add security tests SEC-01, SEC-02

Refs: Document 16 Section 3, NFR-030, NFR-032
Co-Authored-By: Claude Code <noreply@anthropic.com>
```

### Step 5.2: Merge to Main

**Merge strategy: Squash and merge (preferred) OR Merge commit (if preserving history)**

```bash
# After PR approved
git checkout main
git pull origin main
git merge --squash feature/<short-description>
git commit  # Use PR description as commit message
git push origin main
```

**Protected main branch:**
- No direct commits (PR required)
- CI must pass
- At least one approval required (for safety-critical: designated reviewer)
- Golden vector parity maintained

### Step 5.3: Post-Merge Verification

**Verify:**
- CI passes on main branch
- Integration tests still pass
- No regressions in unrelated tests

**If CI fails on main**: Immediate rollback (see Phase 11: Rollback)

### Step 5.4: Delete Feature Branch

```bash
git branch -d feature/<short-description>
git push origin --delete feature/<short-description>
```

---

## Phase 6: Architecture-Change Procedure

**Goal**: Surface specification conflicts, propose resolution, document decision

### When to Use

**Trigger architecture-change procedure when:**
- Specification X requires Y, but implementation constraint Z prevents it
- Two specifications conflict
- Implementation reveals specification assumption is invalid
- Locked architecture conflicts with discovered reality

### Step 6.1: Stop Implementation

**Do NOT proceed with implementation if architecture conflict discovered.**

### Step 6.2: Document Conflict

**In PR or issue, describe:**
1. **Specification requirement**: "Document X, Section Y requires Z"
2. **Implementation constraint**: "But constraint W prevents Z because..."
3. **Evidence**: "Demonstrated by [test result / hardware limitation / external dependency]"

### Step 6.3: Propose Resolution Options

**Provide 2-3 options with tradeoffs:**

**Option A**: Modify specification (requires human approval)
- **What changes**: Specification X, Section Y
- **Why**: Constraint W is immovable
- **Impact**: Relaxes requirement Z, affects subsystems...
- **Risks**: May violate acceptance gate...

**Option B**: Modify constraint (implementation work)
- **What changes**: Workaround for constraint W
- **Why**: Preserve specification requirement Z
- **Impact**: Additional complexity, performance cost...
- **Risks**: May introduce...

**Option C**: Alternative approach (different implementation)
- **What changes**: Different technical approach
- **Why**: Satisfies specification Z without hitting constraint W
- **Impact**: Requires redesign of...
- **Risks**: Unknown unknowns...

**Recommendation**: (State which option you recommend and why)

### Step 6.4: Wait for Human Decision

**Do NOT:**
- Proceed with implementation
- Choose resolution on your own
- "Temporarily" work around conflict

**DO:**
- Wait for explicit human approval of chosen option
- Answer clarifying questions
- Provide additional evidence if requested

### Step 6.5: Document Resolution

**After decision made, update `docs/implementation/DECISIONS.md`:**

```markdown
### <Decision Name> [RESOLVED YYYY-MM-DD]

**Decision**: <Chosen option>

**Rationale**: <Why this option was chosen>

**Implementation**: <What will change>

**Status**: LOCKED - <Brief constraint or rule>

**Related Specifications**: Document X Section Y, Document Z Section W

**Conflict Resolved**: <Brief description of original conflict>
```

### Step 6.6: Resume Implementation

**After decision recorded:**
- Resume Phase 2: Implementation with approved approach
- Update plan if approach changed
- Proceed through Phases 3-5 as normal

---

## AI Coding Workflow (Four-Role Loop)

**Reference**: Document 18, IMPLEMENTATION_CONSTITUTION.md Section 24

### Four Roles

```
Architect → Builder → Red Team → Verifier
   ↓          ↓          ↓          ↓
 Plan      Code    Challenge    Test
```

### Role 1: Architect (Design/Plan)

**Responsibilities:**
- Understand requirements from specifications
- Design approach
- Identify affected subsystems
- Check architecture compliance
- Surface ambiguities

**Output**: Written plan (Phase 1: Planning)

**AI Assistant MUST:**
- Reference specification sources (Document X, Section Y)
- Check CONSTITUTION + REPOSITORY_MAP
- Propose before implementing (if architecture deviation)
- Surface ambiguities explicitly

### Role 2: Builder (Implement)

**Responsibilities:**
- Write code following plan
- Follow existing patterns
- Preserve invariants
- Write tests

**Output**: Code changes (Phase 2: Implementation)

**AI Assistant MUST:**
- Use documented config parameters (no invented thresholds)
- Reuse reference math or validate parity (no duplicate definitions)
- Implement same engine for LIVE/SIMULATION (no decorative behavior)
- Test before claiming done

### Role 3: Red Team (Adversarial Review)

**Responsibilities:**
- Challenge assumptions
- Find edge cases
- Identify security risks
- Check architecture compliance

**Questions to ask:**
- What if sensor fails? Missing data handled?
- What if Master disconnects during incident?
- What if sequence numbers rollover?
- Does this preserve missing≠zero?
- Does this respect ESP32 boundaries?
- Does this maintain golden vector parity?

**Output**: List of risks, edge cases, compliance issues

### Role 4: Verifier (Test/Validate)

**Responsibilities:**
- Run tests
- Check golden vectors
- Verify evidence requirements met
- Collect test output

**Output**: Evidence (Phase 3: Verification)

**AI Assistant MUST:**
- Run relevant tests (L0/L1/L2/L3/L4/L5)
- Check golden vectors (if mathematical)
- Run security tests (if security-relevant)
- Collect evidence before claiming done

### Loop Iteration

**For each task:**
1. **Architect**: Design approach
2. **Builder**: Implement one piece
3. **Red Team**: Challenge implementation
4. **Verifier**: Test that piece
5. **Repeat** until feature complete

**Never skip Verifier**: Test-before-done is mandatory

---

## Test-Before-Done Rule

**Core Principle**: No task is "complete" until relevant tests pass.

### What "Done" Means

| **Change Type** | **Done = Tests Pass** |
|---|---|
| **New function** | Unit tests pass |
| **Mathematical formula** | Golden vectors pass |
| **Cross-subsystem** | Integration tests pass |
| **Security-relevant** | Security tests pass |
| **UI change** | Component tests + manual verification |
| **Firmware change** | Golden vector parity + concurrency benchmark |

### Tests Required Per Change

**Always required (L0):**
- Linters pass (black, flake8, mypy, eslint, clang-format)
- Schema validation passes
- Build succeeds

**Function/module changes (L1):**
- Unit tests for modified functions
- Boundary tests (edge cases, null, empty, max)

**Mathematical changes (L1 + golden vectors):**
- Affected golden vectors pass (GV-H01 through GV-GEO02)
- Python reference ↔ C/C++ embedded parity maintained

**Subsystem changes (L2):**
- Component tests (subsystem end-to-end)

**Cross-subsystem changes (L3):**
- Integration tests (Edge→Master, Master→Backend, Backend→Frontend)

**Security changes (L3 + security tests):**
- SEC-01 through SEC-14 as relevant

**System-level changes (L4):**
- Scenario tests (G01-G15 as relevant)
- Fault injection (FI-01 through FI-14 as relevant)

### When Tests Fail

**If tests fail:**
1. **Fix the code** (not the test, unless test is wrong)
2. **Re-run tests**
3. **Repeat until green**

**Do NOT:**
- Claim "done" with failing tests
- Skip tests because "it's obvious it works"
- Defer tests to "later"
- Comment out failing tests

**Exception**: Test infrastructure broken (CI down, dependency issue) - document in PR, fix separately

---

## Evidence Requirements

**Goal**: Prove implementation correctness before merge

### Evidence Per Change Type

| **Change Type** | **Evidence Required** |
|---|---|
| **Feature** | Test output (unit + integration), coverage report |
| **Bug fix** | Before/after behavior demonstration, test that reproduces bug |
| **Mathematical** | Golden vector results (all affected vectors) |
| **Security** | Security test output (SEC-01 through SEC-14) |
| **Performance** | Latency measurements (p95), soak test results |
| **UI** | Screenshots/video of before/after, accessibility check |
| **Firmware** | Golden vector parity results, concurrency benchmark |

### Evidence Format

**Test output:**
```
pytest tests/test_health.py -v
============================= test session starts ==============================
collected 5 items

tests/test_health.py::test_health_all_nominal PASSED                    [ 20%]
tests/test_health.py::test_health_one_failure PASSED                    [ 40%]
tests/test_health.py::test_health_weighted PASSED                       [ 60%]
tests/test_health.py::test_health_bounds PASSED                         [ 80%]
tests/test_health.py::test_health_diagnostics PASSED                    [100%]

============================== 5 passed in 0.42s ===============================
```

**Golden vector results:**
```
GV-H01 (Health): PASS (tolerance: 1e-6)
  - All nominal: computed=1.000000, expected=1.000000, diff=0.000000
  - One hard failure: computed=0.000000, expected=0.000000, diff=0.000000
  - Weighted degradation: computed=0.750000, expected=0.750000, diff=0.000000
```

**Coverage report:**
```
Name                                Stmts   Miss  Cover
-------------------------------------------------------
modules/intelligence/health.py         45      2    96%
modules/intelligence/quality.py        38      0   100%
-------------------------------------------------------
TOTAL                                  83      2    98%
```

### Where to Store Evidence

- **PR description**: Summary of test results
- **CI artifacts**: Full test output, coverage reports
- **docs/validation/<feature>/**: Detailed evidence for major features or gates

---

## Rollback and Recovery

**Goal**: Quickly restore working state if merge breaks main

### When to Rollback

**Immediate rollback triggers:**
- CI fails on main after merge
- Integration tests fail on main
- Golden vectors regress on main
- Production deployment fails

### Rollback Procedure

**Step 1: Revert merge commit**
```bash
git revert <merge-commit-sha>
git push origin main
```

**Step 2: Verify main stable**
```bash
# CI must pass after revert
# Integration tests must pass
# Golden vectors must pass
```

**Step 3: Investigate failure**
- Reproduce failure locally
- Identify root cause
- Determine fix

**Step 4: Fix in feature branch**
```bash
git checkout -b fix/<original-feature>-v2
# Apply fix
# Re-run all tests
# Create new PR
```

**Step 5: Re-merge after fix verified**

### Recovery from Lost Work

**If local changes lost (uncommitted):**
- No recovery (commits are atomic; uncommitted work is disposable)
- Lesson: Commit frequently

**If feature branch deleted prematurely:**
```bash
git reflog  # Find deleted branch commit
git checkout -b feature/<name>-recovered <commit-sha>
```

**If merge conflict:**
```bash
git checkout main
git pull origin main
git checkout feature/<name>
git merge main
# Resolve conflicts
git commit
git push origin feature/<name>
```

---

## Summary

### Quick Reference

| **Phase** | **Key Question** | **Pass Criteria** |
|---|---|---|
| **Planning** | What are we building? | Plan written, risks identified |
| **Implementation** | Does code follow plan? | Code written, tests written |
| **Verification** | Do tests pass? | All relevant tests pass |
| **Review** | Is code correct? | PR approved, CI passes |
| **Commit** | Is main stable? | Merged, post-merge CI passes |
| **Architecture-Change** | Does spec conflict? | Decision documented, approved |

### Golden Rules

1. **Test-before-done**: No task complete until tests pass
2. **Architecture compliance**: Check CONSTITUTION + REPOSITORY_MAP before merging
3. **Golden vector parity**: Mathematical changes MUST maintain parity
4. **Security gates**: Security-relevant changes MUST pass security tests
5. **Surface ambiguity**: When specification unclear, ask (don't guess)
6. **Rollback fast**: If main breaks, revert immediately

### For AI Assistants

**MUST:**
- Run tests before claiming done
- Reference specifications (Document X, Section Y)
- Preserve non-negotiable invariants
- Surface specification conflicts
- Collect evidence

**MUST NOT:**
- Skip tests
- Invent thresholds not in config
- Silently redesign architecture
- Resolve ambiguities without asking
- Claim "done" with failing tests

---

**END OF DEVELOPMENT WORKFLOW**
