__NEXALERT__

__Implementation & Vibe\-Coding Execution Specification__

__FINAL IMPLEMENTATION SPECIFICATION  •  V1 / SIH 2026__

__PURPOSE  __Translate the locked NexAlert architecture into a disciplined implementation workflow: repository structure, build order, contracts, AI\-assisted coding, verification loops, merge gates, simulation\-first development, and SIH demo hardening\.

__Field__

__Locked Decision__

Implementation posture

Modular monolith \+ background workers \+ PostgreSQL/PostGIS; avoid premature microservices\.

Edge

ESP32\-S3\-class node with ESP\-IDF/C/C\+\+; Python is reference math, not embedded runtime\.

Master

Raspberry Pi\-class Linux compute; orchestration, fusion, geospatial simulation and local portal\.

Frontend

Authority dashboard \+ citizen safety UI; same backend contracts, distinct workflows\.

AI coding posture

AI proposes code; tests, contracts, review and runtime evidence decide whether it ships\.

Primary invariant

Simulation produces telemetry and conditions; NexAlert reasoning produces the decision\.

# DOCUMENT MAP

1\. Implementation Principles & Non\-Negotiables

2\. Repository and Module Structure

3\. Build Order and Vertical Slices

4\. Backend Implementation Workflow

5\. Edge Firmware Implementation Workflow

6\. Intelligence and Geospatial Execution

7\. Frontend Implementation Workflow

8\. Simulation, Replay and Scenario Control

9\. AI / Vibe\-Coding Operating Model

10\. Prompt Patterns and Review Protocols

11\. Testing, CI and Merge Gates

12\. Configuration and Feature Flags

13\. Observability, Debugging and Fault Injection

14\. Git, Branching, Commits and Release Discipline

15\. Milestones, Definition of Done and SIH Freeze

16\. Implementation Checklist

__AUTHORITY ORDER  __When implementation choices conflict, use this order: Master Architecture & Invariants \-> TRD \-> Math/Geospatial \-> Hardware \-> Backend/API \-> UI docs \-> Simulation \-> Security \-> Validation \-> this execution document\. Older legacy documents are historical reference only\.

# 1\. IMPLEMENTATION PRINCIPLES & NON\-NEGOTIABLES

- Build the smallest end\-to\-end slice first: sensor/simulator \-> telemetry ingestion \-> quality/reliability \-> hazard reasoning \-> incident \-> alert \-> dashboard/citizen projection\.
- Every major feature must exist behind a contract before the UI or hardware integration is expanded around it\.
- Keep deterministic domain logic separate from transport, storage, and presentation\. A math function should be callable from a unit test without a database or browser\.
- Never encode hazard truth in frontend animation\. Fire geometry comes from the actual spread engine; frontend only renders authoritative state\.
- Never let an LLM\-generated implementation become the source of truth\. Source\-of\-truth artifacts are schemas, configuration, deterministic tests, and observed runtime evidence\.
- Fail explicitly: UNKNOWN information condition beats invented confidence; stale data remains stale; missing is not zero; degraded communication is visible\.
- Human approval remains mandatory for authority dispatch/action\. NexAlert recommends; an authorized human approves operational actions\.
- Every new feature ships with tests, telemetry/logging, a rollback path, and a short operator explanation of failure behavior\.

__Rule__

__Implementation consequence__

Local autonomy

Critical node logic must run without cloud connectivity; local emergency path cannot depend on the public internet\.

Master vs internet failure

Model them as separate failure modes and test both independently\.

No fake probability

C\_h and R\_h are confidence/index values, never probability labels or confidence\-to\-probability claims\.

Independent hazards

Fire, flood, pollution, landslide and heat maintain independent state/evidence/risk vectors\.

Physical vs operational

Affected physical footprint and policy buffer remain separate layers and data objects\.

Current vs warning vs projection

All zones derive from arrival\-time state, never from decorative circles or arbitrary UI timers\.

Trust chain

Node HMAC, event signature where applicable, sequence/timestamp freshness and audit trail are first\-class\.

Synthetic separation

Simulator may know hidden ground truth; the telemetry pipeline must not receive that ground truth\.

# 2\. REPOSITORY AND MODULE STRUCTURE

Recommended monorepo structure\. The exact package names can change, but the separation of responsibilities should not\.

nexalert/  
  apps/  
    authority\-web/          \# Authority dashboard  
    citizen\-web/            \# Citizen safety UI / PWA  
    local\-portal/            \# Offline emergency portal surface  
  services/  
    api/                     \# HTTP API \+ auth \+ command endpoints  
    workers/                 \# incident, alert, replay, analytics jobs  
    simulation/              \# synthetic telemetry \+ scenario runner  
    geospatial/              \# fire spread, raster/vector, exposure  
  packages/  
    domain/                  \# entities, enums, state transitions  
    intelligence/            \# health, quality, reliability, anomaly, evidence  
    fire\-model/              \# portable fire math \+ golden vectors  
    contracts/               \# JSON schemas / API DTOs / event envelopes  
    config/                  \# versioned parameter registry  
    security/                \# HMAC, signatures, replay/freshness helpers  
  firmware/  
    esp32\-node/              \# production ESP\-IDF firmware  
    golden\-vectors/          \# vectors shared with Python/backend tests  
  db/  
    migrations/              \# SQL migrations  
    seeds/                   \# local/demo data only  
  tests/  
    unit/  
    integration/  
    e2e/  
    fault\-injection/  
    golden/  
  docs/  
    architecture/  
    runbooks/  
    demo/  
  infra/  
    docker/  
    systemd/  
    deploy/  
  scripts/  
    dev/  
    qa/  
    release/  


__Layer__

__Must own__

__Must not own__

Contracts

schemas, versioning, envelopes, validation

business decisions or UI formatting

Domain

state machines, entities, deterministic transitions

HTTP, SQL, browser APIs

Intelligence

health/quality/anomaly/evidence/confidence/index math

database queries, rendering

Geospatial

raster/vector operations, fire arrival\-time engine, exposure joins

alert wording, auth

Workers

asynchronous orchestration, retries, scheduled jobs

core math definitions

API

authorization, request validation, command/query boundary

duplicated hazard logic

Frontend

interaction, display, accessibility, local cache

inventing hazard state

Firmware

sampling, diagnostics, edge inference, buffering, HMAC

GIS/fire spread/population routing

## 2\.1 Canonical data flow

Sensor / Simulator  
    \-> telemetry envelope validation  
    \-> authentication \+ replay check  
    \-> storage / event bus  
    \-> health \+ quality \+ reliability  
    \-> baseline \+ anomaly  
    \-> hazard evidence \+ confidence  
    \-> severity \+ operational risk  
    \-> hazard state transition  
    \-> incident correlation  
    \-> alert candidate  
    \-> human approval \(where operational action is required\)  
    \-> channel delivery  
    \-> audit \+ metrics  
    \-> Authority / Citizen projections

__IMPLEMENTATION TEST  __At every arrow above, there should be one observable contract: an event/table/DTO with a schema version, timestamp semantics, and trace identifier\.

# 3\. BUILD ORDER AND VERTICAL SLICES

Do not implement the system strictly page\-by\-page\. Implement vertically so every stage becomes demonstrably real before the next layer is expanded\.

__Phase__

__Build__

__Evidence required__

__Exit gate__

0

Repo \+ tooling \+ config registry

local dev boots; lint/test commands documented

one\-command developer bootstrap

1

Telemetry contract \+ DB

simulator packet stored and queryable

schema \+ migration tests pass

2

Health / quality / reliability

bad sensor affects downstream trust

golden\-vector parity

3

Anomaly \+ hazard reasoning

synthetic scenarios trigger correct states

deterministic scenario tests

4

Incident \+ alerts

duplicate signals correlate and alerts persist

50m/30s correlation behavior verified

5

Authority vertical slice

overview \-> incident \-> explain \-> acknowledge

operator E2E passes

6

Citizen vertical slice

emergency page \+ action \+ SOS

online/offline E2E passes

7

Fire geospatial slice

live/sim spread uses real arrival\-time engine

known\-case vector \+ geometry checks

8

Resilience slice

Master, internet, node and DB failures exercised

fault injection passes

9

Security hardening

HMAC/replay/signature/RBAC/audit

negative tests pass

10

Demo freeze

scripted scenario \+ evidence capture

release candidate signed off

## 3\.1 First executable milestone

1. Start the API, database, simulation runner and Authority web locally\.
2. Launch a single synthetic node and emit normal telemetry every configured interval\.
3. Observe the packet in the DB/API and show measurement timestamp separately from receive timestamp\.
4. Inject a fire\-like correlated change in temperature \+ PM/smoke \+ gas while humidity changes support the event\.
5. Confirm health/quality/reliability are present before anomaly/evidence calculations\.
6. Confirm the hazard state moves through the configured persistence/hysteresis path instead of jumping directly from normal to critical\.
7. Correlate the event into one incident and render it in the Authority dashboard\.
8. Generate a citizen projection without requiring a native mobile app\.

__DEFINITION OF A REAL SLICE  __A feature is not complete when a component renders\. It is complete when an input, stored state, decision, user\-visible output, failure mode, and test all agree on the same contract\.

# 4\. BACKEND IMPLEMENTATION WORKFLOW

## 4\.1 API boundary

Use a versioned HTTP API for commands/queries and an internal event model for asynchronous work\. Avoid putting long\-running fire spread, replay or bulk analytics in synchronous request handlers\.

__Concern__

__Pattern__

Telemetry ingest

POST endpoint accepts canonical telemetry envelope; returns receipt/validation result quickly\.

Queries

GET endpoints return read models; no hazard computation in serializers\.

Commands

Explicit POST action endpoints; authorized role required; idempotency key required where retried\.

Workers

Incident correlation, alert fan\-out, replay and heavy geospatial work run asynchronously\.

Idempotency

Use event/command IDs plus uniqueness constraints; retries must not create duplicate incidents or alerts\.

Transactions

Atomic state transition \+ audit record when an operational state changes\.

Pagination

Cursor\-based for telemetry, incidents, alerts and audit streams where data can grow large\.

## 4\.2 Canonical request envelope

\{  
  "schema\_version": "telemetry\.v1",  
  "telemetry\_id": "\.\.\.",  
  "node\_id": "NODE\-001",  
  "sequence": 1842,  
  "measurement\_timestamp": "2026\-09\-07T07:45:18Z",  
  "received\_timestamp": "2026\-09\-07T07:45:19Z",  
  "location": \{"lat": 13\.12, "lon": 77\.58\},  
  "measurements": \{"temp\_c": 42\.1, "pm25\_ug\_m3": 182\.0\},  
  "diagnostics": \{"uptime\_s": 88211\},  
  "power": \{"battery\_pct": 71\},  
  "source": "SIMULATION",  
  "auth": \{"hmac": "\.\.\."\}  
\}

## 4\.3 Database implementation rules

- Use migrations for every schema change; never alter production schema manually during the demo build\.
- Use PostgreSQL/PostGIS as the target architecture\. SQLite may be used for narrow local development only when the feature does not depend on spatial/query semantics\.
- Keep immutable telemetry/event records separate from mutable read models\.
- Use spatial types for node locations, incident geometry and hazard polygons; do not store operational geometry only as JSON blobs\.
- Add indexes for node\_id \+ timestamp, incident state \+ updated\_at, spatial lookup fields, and audit actor \+ timestamp\.
- Use explicit enum/reference tables for states where operators depend on stable semantics\.

# 5\. EDGE FIRMWARE IMPLEMENTATION WORKFLOW

The ESP32 node is a concurrent real device, not a thin sensor script\. The firmware must preserve autonomy under transport failures and bounded compute/memory\.

__Task__

__Firmware behavior__

__Measurement__

Sampling

scheduler/task per sensor group; timestamps captured at measurement

sample latency, missed reads

Diagnostics

fast internal health checks; detailed report on configured cadence

fault detection time

Quality

integrity \+ stability checks; no invented zero for missing data

Q\_i by signal

Reliability

H\_i Q\_i K\_i after health/quality gates

R\_i and downstream weighting

Anomaly

portable reference math subset where appropriate

z / A\_i parity

Local hazard

configured lightweight deterministic evidence only

state latency

Buffering

bounded ring buffer with retry/backoff; priority handling for critical events

queue depth, drop count

Security

per\-node HMAC; sequence/timestamp freshness

verify latency, replay reject

Local AP

serve emergency state page/gateway path when required

time\-to\-serve, concurrency

## 5\.1 Firmware task model

Sensor tasks  
  \-> sample \+ validate \-> queue  
Diagnostics task  
  \-> health metrics \-> queue  
Intelligence task  
  \-> quality \-> reliability \-> baseline \-> anomaly \-> local evidence/state  
Comms task  
  \-> sign/authenticate \-> transmit \-> ACK \-> buffer on failure  
Local portal task  
  \-> cached emergency state \-> minimal UI/API  
Supervisor  
  \-> watchdog, queue pressure, heap watermark, task health

__CONCURRENCY GATE  __Do not tune from intuition\. Run a real benchmark with sensing \+ Wi\-Fi AP/local service \+ telemetry \+ HMAC \+ buffering \+ local inference active\. Record latency/jitter, free heap, CPU load, queue depth, packet loss and power impact\.

## 5\.2 Python/C\+\+ parity workflow

1. Implement the canonical math first in a readable Python reference module\.
2. Create fixed golden vectors with expected intermediate values, not just final output\.
3. Port the approved subset to C/C\+\+ on ESP32\.
4. Run the same vectors through both implementations\.
5. Allow small numeric tolerances only where floating\-point/platform differences require them\.
6. Block firmware merge when vector parity regresses without an explicitly reviewed change to the mathematical spec\.

# 6\. INTELLIGENCE AND GEOSPATIAL EXECUTION

## 6\.1 Intelligence implementation order

health \-> quality \-> reliability \-> baseline readiness  
        \-> robust baseline / trend baseline  
        \-> anomaly A\_i  
        \-> weighted aggregate A\_h  
        \-> hazard evidence E\_h  
        \-> confidence C\_h  
        \-> severity S\_h  
        \-> operational risk R\_h  
        \-> state machine / hysteresis  
        \-> incident correlation

__Module__

__Implementation note__

__Required tests__

health\.py / health\.cpp

soft health weighted sum \+ hard failure gate

fault vectors, hard\-zero behavior

quality\.\*

integrity × stability; stale/missing explicit

missing, stale, noisy, outlier tests

reliability\.\*

H × Q × K; battery excluded

boundary \+ weighting tests

baseline\.\*

readiness state \+ robust stats \+ freeze/recover

INIT/LEARNING/READY/FROZEN/RECOVERING

anomaly\.\*

bounded robust score; trend\-relative where needed

cap/lambda vectors

evidence\.\*

hazard\-specific deterministic rule groups

core coverage \+ contradiction cases

confidence\.\*

coverage/agreement/temporal/baseline composition

N/A threshold \+ correlated group test

state\.\*

persistence/hysteresis/escalation/stand\-down

all transition edges

## 6\.2 Fire geospatial execution

- Use a projected metric CRS for raster distance and geometry operations\. Do not treat raw latitude/longitude degrees as meters\.
- Convert meteorological wind FROM direction to propagation TO direction before using it in spread\.
- Compute terrain slope and aspect with central differences using cell spacing\.
- Combine wind and slope directionally as vectors; apply fuel/moisture/base ROS factors through explicit, reviewable functions\.
- Propagate arrival times with a min\-priority queue over 8\-neighbor connections using orthogonal and diagonal distances\.
- Retain raw arrival\-time raster and threshold geometry as source of truth; only simplify display geometry\.
- Use current, warning and projection sets from arrival\-time thresholds at time t; never use frontend\-only motion\.
- On environmental updates, preserve historical truth, reseed from the current frontier, recompute future arrival times and increment projection version\.

## 6\.3 Risk/exposure separation

Keep three distinct objects: physical hazard risk surface, operational buffer geometry, and downstream exposure\. Population/infrastructure affects exposure and operational analysis; it should not be silently injected into the underlying physical hazard model\.

# 7\. FRONTEND IMPLEMENTATION WORKFLOW

Build the UI from state and contracts outward, not from screenshots inward\.

__Step__

__Authority Dashboard__

__Citizen UI__

1\. State model

overview/incident/node/alert/action view state

normal/watch/emergency/resolved \+ connectivity

2\. Data contract

read models for map, command card, telemetry

minimal emergency projection \+ safe place \+ SOS

3\. Rendering

map layers \+ cards \+ tables \+ audit

first viewport \+ action \+ live map \+ safe place

4\. Failure state

unknown/degraded/stale badges

offline/local\-portal/offline\-cache path

5\. Action model

approve/escalate/stand down/assign

SOS/acknowledge safety instructions

6\. Accessibility

keyboard, focus, labels, color\-independent meaning

large targets, screen\-reader labels, plain language

## 7\.1 Frontend data rules

- Never duplicate hazard equations in TypeScript/JavaScript\. Consume backend projections and only perform display transformations\.
- Every map overlay carries a source timestamp and information condition\.
- Use stable IDs for incidents/nodes/alerts; do not key React/Vue lists from array positions\.
- Keep network/cache state separate from hazard state\. An old alert displayed from cache must be visibly identified as cached/stale\.
- Citizen UI must prioritize actionability over analytical detail\. Raw confidence/severity/risk indices remain hidden by default\.
- Offline portal must use the same emergency content schema as the online experience, but serve from local/cacheable data\.

## 7\.2 Map implementation contract

MapProjection = \{  
  timestamp,  
  information\_condition,  
  nodes\[\],  
  incidents\[\],  
  hazard\_layers: \{  
    fire: \{ current, warning, projection, risk\_surface, version \},  
    flood: \{ \.\.\. \},  
    pollution: \{ \.\.\. \}  
  \},  
  operational\_buffers\[\],  
  exposure\_summary  
\}

__VISUAL INTEGRITY  __The UI may interpolate camera motion or animate transitions, but the geometry itself must come from authoritative state\. Replay mode may animate time; it must not fabricate spatial truth\.

# 8\. SIMULATION, REPLAY AND SCENARIO CONTROL

Simulation is the main bridge between architecture and proof\. It must exercise the exact same ingest and reasoning paths used by hardware wherever practical\.

## 8\.1 Scenario schema

\{  
  "scenario\_id": "FIRE\-CORRELATED\-03",  
  "seed": 42,  
  "start\_time": "\.\.\.",  
  "duration\_s": 900,  
  "nodes": \["NODE\-001", "NODE\-002", "NODE\-003"\],  
  "hazards": \["FIRE"\],  
  "telemetry\_profile": "fire\_ramp\_v2",  
  "faults": \[  
    \{"type":"missing","node\_id":"NODE\-002","start\_s":240,"duration\_s":60\},  
    \{"type":"contradiction","node\_id":"NODE\-003","start\_s":360\}  
  \],  
  "hidden\_ground\_truth": \{"kept\_out\_of\_telemetry":true\}  
\}

## 8\.2 Replay rules

1. Persist the scenario seed and configuration snapshot\.
2. Replay telemetry with the original measurement timestamps\.
3. Preserve receive\-time behavior when transport delay is simulated\.
4. Never inject labels such as hazard=true, confirmed=true or severity=critical into the reasoning path\.
5. Checkpoint after significant state changes so an operator can time\-travel without recomputing unrelated state\.
6. Compare replay output against expected state/event sequences as well as UI screenshots where useful\.

## 8\.3 Required scenario families

__Family__

__Must demonstrate__

Normal baseline

stable telemetry, READY baseline, no false incident

Rapid fire

correlated temp \+ smoke/PM \+ gas escalation; fast state escalation

Slow flood onset

water trend \+ rainfall context \+ persistence

Pollution plume

PM/gas spatial concentration with wind/context

Landslide/vibration

vibration anomalies \+ supporting environmental evidence

Extreme heat

temperature persistence \+ exposure\-aware operational view

Contradiction

one node disagrees; confidence/Information Condition degrade without erasing valid local truth

Sensor failure

hard failure/flatline/drift/stale; reliability downweights evidence

Network partition

node buffers locally; reconnect deduplicates and drains

Master failure

local emergency path remains available where designed

Internet failure

Master/local node path remains operational; cloud\-dependent actions visibly degrade

Multi\-hazard

two hazards coexist independently; no fake combined scalar

# 9\. AI / VIBE\-CODING OPERATING MODEL

AI is treated as a high\-speed implementation partner inside a controlled engineering system\. The workflow must reduce coding time without transferring architectural authority to the model\.

## 9\.1 Four\-role loop

__Role__

__Human/AI behavior__

__Output__

Architect

human defines invariant, contract and acceptance criteria

task card \+ contract \+ tests

Builder

AI drafts implementation within the bounded contract

code \+ tests \+ notes

Red team

independent model/person attempts to break assumptions

defect list \+ adversarial cases

Verifier

tools \+ tests \+ runtime evidence decide acceptance

pass/fail evidence \+ merge decision

## 9\.2 Model selection policy

- Use the strongest reasoning model available for architecture reconciliation, difficult math/geospatial reviews, security review and red\-team analysis\.
- Use a faster coding model for bounded implementation tasks, repetitive test generation, refactors and UI boilerplate when the contract is already locked\.
- Never ask a coding model to simultaneously redesign the architecture, change schemas, implement the feature and self\-certify correctness\.
- Keep AI\-generated commits small enough that a human can inspect the diff and map it to one acceptance criterion\.

## 9\.3 Vibe\-coding loop

1\. Write TASK\.md with:  
   \- objective  
   \- files allowed to change  
   \- invariants  
   \- API/data contract  
   \- tests required  
   \- explicit non\-goals  
  
2\. Ask AI to implement only the task\.  
3\. Run formatter \+ linter \+ unit tests\.  
4\. Review the diff manually\.  
5\. Run integration / scenario tests\.  
6\. Ask a separate reviewer to attack the implementation\.  
7\. Fix findings\.  
8\. Re\-run the full required gate\.  
9\. Commit with one coherent message\.  
10\. Update the implementation note / evidence link\.

__NON\-NEGOTIABLE  __Do not copy an AI answer directly into a production branch when it introduces an unreviewed dependency, changes a contract, bypasses a test, weakens authentication, or silently changes mathematical semantics\.

# 10\. PROMPT PATTERNS AND REVIEW PROTOCOLS

## 10\.1 Implementation prompt template

You are implementing one bounded NexAlert task\.  
Authority: \[document/section\]\.  
Task: \[single objective\]\.  
Allowed files: \[paths\]\.  
Contracts: \[schema/API/event\]\.  
Invariants: \[exact rules\]\.  
Non\-goals: \[what you must not change\]\.  
Required tests: \[test IDs / scenarios\]\.  
Failure behavior: \[explicit\]\.  
Return: code changes \+ tests \+ concise implementation note\.  
Do not redesign adjacent modules or invent new semantics\.

## 10\.2 Red\-team prompt template

Review this NexAlert implementation as an adversarial senior engineer\.  
Assume the architecture is locked\. Do not redesign it\.  
Look for: contract drift, duplicate logic, race conditions, stale data errors,  
false confidence, replay/idempotency holes, offline failure, UI invention of state,  
spatial unit errors, fire model mistakes, security regressions, memory leaks\.  
For each finding give: severity, exact location, reproduction, expected behavior,  
and the smallest safe fix\.

## 10\.3 Math review prompt

Compare the implementation to the exact equations and definitions in  
\[document/section\]\. Check units, domains, bounds, missing\-data behavior,  
edge cases, numerical stability, coordinate conventions, and state transitions\.  
List any mismatch even if tests currently pass\. Propose only testable fixes\.

## 10\.4 UI review prompt

Review the screen against the locked UI contract\. Verify that every displayed  
status is sourced from an authoritative field, stale/degraded state is visible,  
no probability is implied where none exists, emergency actions are dominant,  
accessibility remains intact, and offline behavior is honest\.

# 11\. TESTING, CI AND MERGE GATES

Every pull request must move through deterministic gates\. CI is not merely a quality check; it is a defense against architecture drift\.

__Gate__

__Runs__

__Blocks merge when__

Formatting

formatter / format check

format drift exists

Lint

Python \+ TypeScript \+ firmware lint where available

new lint errors exist

Unit

domain/intelligence/math/config

required unit test fails

Golden vectors

Python \+ C/C\+\+ parity

approved vector differs beyond tolerance

Integration

API \+ DB \+ workers

contract or transaction fails

Scenario

synthetic multi\-hazard suite

expected state/event sequence differs

Security

auth/replay/RBAC/input validation

negative test succeeds unexpectedly

E2E

Authority \+ Citizen critical flows

operator/citizen action path fails

Performance

selected smoke budgets

latency/memory/queue budget exceeded

Build

frontend \+ API \+ firmware artifacts

artifact cannot be produced reproducibly

## 11\.1 Minimum commands

\# backend  
python \-m pytest tests/unit tests/integration \-q  
  
\# frontend  
npm run lint  
npm run test  
npm run build  
  
\# firmware \(example shape; keep project\-native commands authoritative\)  
idf\.py build  
idf\.py flash monitor  
  
\# scenario / regression  
python \-m nexalert\.simulation run \-\-scenario FIRE\-CORRELATED\-03  
python \-m nexalert\.simulation replay \-\-run\-id <ID>  
  
\# containerized full stack  
docker compose up \-d  
python scripts/qa/smoke\_stack\.py

__CI PRINCIPLE  __Do not make one giant end\-to\-end test the only proof\. Small deterministic tests should localize failure; a few high\-value E2E tests should prove that the pieces integrate\.

# 12\. CONFIGURATION AND FEATURE FLAGS

All operational thresholds that were identified as configurable belong in a versioned registry, not scattered magic numbers\.

__Parameter family__

__Examples__

__Change policy__

Health/quality

weights, stale windows, stability limits

versioned config; golden\-vector review

Baseline

window lengths, readiness thresholds, recovery timing

versioned; scenario regression required

Anomaly

lambda, z\-cap, trend thresholds

versioned; deterministic vectors

Evidence

core groups, support rules, contradiction rules

versioned; reasoning review

Confidence

coverage/agreement/temporal/baseline weights; N/A threshold

versioned; no probability wording

State machine

persistence, hysteresis, escalation timers

versioned; transition tests

Incident correlation

spatial radius, temporal window

versioned; duplicate\-event tests

Fire model

WAF, fuel coefficients, moisture factors, spread intervals

versioned; geometry and vector tests

Alerting

targeting windows, escalation timing, retry policy

versioned; alert outcome tests

UI

display/refresh intervals, feature visibility

feature flags; no hidden truth changes

## 12\.1 Registry shape

\{  
  "config\_version": "2026\.09\.07\-demo\.1",  
  "fire": \{  
    "propagation\_interval\_s": 10,  
    "projection\_horizon\_s": 900  
  \},  
  "incident": \{  
    "merge\_radius\_m": 50,  
    "merge\_window\_s": 30  
  \},  
  "anomaly": \{  
    "z\_cap": 8\.0,  
    "lambda": 2\.0  
  \}  
\}

__CONFIG RULE  __A parameter change that affects a deterministic output should produce a new config version and rerun the relevant validation suite\. Never hot\-edit a threshold during the SIH demo without recording the change\.

# 13\. OBSERVABILITY, DEBUGGING AND FAULT INJECTION

## 13\.1 Trace identity

Every telemetry\-driven path should be traceable across ingestion, reasoning, incident correlation and alerts\.

trace\_id  
  telemetry\_id  
    \-> reasoning\_run\_id  
      \-> incident\_id  
        \-> alert\_id  
          \-> delivery\_id  
            \-> audit\_event\_id

## 13\.2 Required operational metrics

__Subsystem__

__Minimum metrics__

Node

sampling latency, sensor failures, free heap, CPU, queue depth, HMAC rejects, reconnects

Transport

packets sent/received, retry count, latency, packet loss, buffered count, drain rate

API

request rate, p50/p95/p99 latency, errors, timeout count, idempotency conflicts

Reasoning

baseline state, anomaly counts, evidence coverage, confidence N/A count, state transitions

Incidents

created/merged/split, active duration, correlation misses

Alerts

issued/delivered/opened/acknowledged/unreachable, retry outcomes

Geospatial

grid size, propagation runtime, cells processed, geometry repair count

UI

load time, API error rate, stale\-data indicator count, offline entry count

## 13\.3 Fault injection matrix

__Failure__

__Inject__

__Expected behavior__

Sensor missing

drop field / omit packet

missing remains missing; quality/reliability fall; no zero substitution

Sensor drift

slow offset

baseline/anomaly behavior visible; false certainty avoided

Sensor contradiction

one node conflicts

confidence/evidence may degrade; local valid state preserved

Node offline

stop telemetry

stale state \+ buffered/reconnect behavior

Network partition

block transport

store\-forward; local path remains

Master down

power off Master in test

node/local emergency path follows resilience design

Internet down

block WAN

local operation survives; cloud\-dependent features degrade visibly

DB unavailable

stop DB

API fails safely; no silent data loss claims

Spoof packet

invalid HMAC

reject \+ audit; never enter reasoning

Replay packet

duplicate old sequence/timestamp

reject or deduplicate according to contract

Worker crash

kill background process

supervisor restart \+ idempotent recovery

# 14\. GIT, BRANCHING, COMMITS AND RELEASE DISCIPLINE

## 14\.1 Branch strategy

__Branch__

__Purpose__

main

always releasable; protected

feature/\*

one bounded implementation slice

fix/\*

specific defect with regression test

demo/\*

short\-lived hardening branch for scripted SIH scenarios

release/\*

final candidate stabilization; no architectural redesign

## 14\.2 Commit format

feat\(incident\): add deterministic spatial\-temporal correlation  
fix\(edge\): reject replayed telemetry sequences  
test\(fire\): add arrival\-time diagonal golden vector  
refactor\(api\): isolate read model from domain state  
docs\(impl\): record SIH release evidence

- One conceptual change per commit\.
- Include the regression test in the same commit as the bug fix whenever practical\.
- Do not mix generated formatting churn with a logic change\.
- Link every release\-critical change to a requirement/test ID in the PR description\.

## 14\.3 Pull\-request checklist

- The PR states the exact contract changed \(if any\)\.
- No architecture invariant is weakened or silently reinterpreted\.
- Tests cover happy path, boundary, missing/stale and failure behavior\.
- Logs/metrics are sufficient to diagnose the feature in the demo\.
- AI\-generated code has been reviewed and its dependencies are understood\.
- No secret, personal data, or temporary debug endpoint is included\.
- Rollback/revert impact is understood\.

# 15\. MILESTONES, DEFINITION OF DONE AND SIH FREEZE

## 15\.1 Milestone sequence

__Milestone__

__What must be real__

__Demo evidence__

M1 Core loop

telemetry \-> reasoning \-> incident

single deterministic scenario

M2 Authority

operator overview \+ explain \+ incident actions

screen recording \+ live run

M3 Citizen

emergency first viewport \+ SOS \+ safe place

mobile browser \+ local portal

M4 Fire

real arrival\-time spread \+ geometry \+ risk

time slider \+ controlled scenario

M5 Resilience

offline, partition, replay, local autonomy

fault injection recording

M6 Security

HMAC/replay/RBAC/audit

negative\-test dashboard/log

M7 Final

all critical acceptance gates

single scripted SIH run \+ evidence folder

## 15\.2 Definition of Done

1. Requirement mapped to a document section and/or test ID\.
2. Contract is explicit and versioned where needed\.
3. Implementation is in the correct module boundary\.
4. Unit tests and deterministic golden tests pass\.
5. Integration scenario passes through the real path\.
6. Failure behavior is tested and visible\.
7. Observability exists for the important state transition\.
8. Security requirements are satisfied\.
9. UI displays the authoritative projection without fabricating semantics\.
10. Documentation/runbook is updated\.
11. PR reviewed, CI green, commit merged\.

## 15\.3 SIH freeze rules

- Freeze architecture before final dress rehearsal\. After freeze, only correctness, safety, performance, UI clarity, and demo reliability fixes are allowed\.
- Freeze the configuration snapshot and scenario seeds used in the final demo\.
- Freeze hardware wiring/pin mapping and sensor calibration constants before the final full\-stack run\.
- Keep one known\-good rollback artifact for firmware, backend, database schema and frontend\.
- Run the final demo at least once with internet blocked, once with a sensor/node fault, and once from a clean boot\.
- Keep the demo script honest: label simulation as simulation, synthetic data as synthetic, and recommendation as recommendation\.

__FINAL PRINCIPLE  __NexAlert wins by being believable\. A smaller system that survives faults, explains its information condition and shows real causality is stronger than a larger system whose behavior is decorative or unverifiable\.

# 16\. IMPLEMENTATION CHECKLIST

☐ Architecture invariants copied into TASK\.md templates and code\-review checklist\.

☐ Modular monolith repository created with clear package boundaries\.

☐ Database migrations \+ spatial types established\.

☐ Canonical telemetry envelope validated at API boundary\.

☐ HMAC/replay/freshness checks enforced before reasoning\.

☐ Health, quality, reliability implemented and golden\-tested\.

☐ Baseline/anomaly/evidence/confidence/severity/risk/state logic implemented from locked equations\.

☐ Deterministic incident correlation implemented: same hazard \+ spatial radius \+ temporal window\.

☐ Fire spread engine uses metric CRS, wind TO conversion, terrain derivatives, directional vector combination, 8\-neighbor arrival\-time propagation\.

☐ Current/warning/projection geometry and operational buffer stored as distinct layers\.

☐ Simulation feeds telemetry only; hidden ground truth remains outside reasoning path\.

☐ Authority dashboard reads authoritative projections and exposes Information Condition\.

☐ Citizen emergency UI supports online \+ offline/local portal behavior\.

☐ Shelter\-in\-place fallback exists when no viable safe route is available\.

☐ Master failure and internet failure tested independently\.

☐ Node store\-and\-forward \+ reconnect dedupe verified\.

☐ ESP32 concurrency benchmark completed\.

☐ Config registry versioned and frozen for demo\.

☐ CI gates cover lint, unit, golden, integration, scenario, security, E2E and build\.

☐ AI coding uses bounded prompts, review and red\-team loop\.

☐ Final SIH scenario is deterministic, rehearseable and auditable\.

__RELEASE GATE  __Do not declare NexAlert implementation complete until the checklist, the validation specification and the final scripted demonstration agree on the same behavior\. The final artifact is not the code alone; it is code \+ configuration \+ data provenance \+ tests \+ runtime evidence \+ operator workflow\.

