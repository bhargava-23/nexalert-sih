__NEXALERT__

__Validation, Verification & Acceptance Test Specification__

__FINAL IMPLEMENTATION SPECIFICATION  •  V1 / SIH 2026__

__Field__

__Value__

Document ID

NEX\-17\-VAL\-VERIFY

Status

FINAL / Implementation\-ready

Authority

Master Architecture \+ TRD \+ Mathematical Intelligence \+ Fire/Geospatial \+ Hardware \+ Data \+ Multi\-Hazard \+ Incident Operations \+ Resilience \+ UI \+ Security \+ Simulation

Purpose

Define how NexAlert is verified, validated, fault\-injected, performance\-tested, and accepted before SIH demonstration or controlled field use\.

Acceptance principle

No claim is accepted because it looks plausible\. Each safety\-relevant behavior requires measurable evidence, repeatability, and a recorded test result\.

__NON\-NEGOTIABLE  __Tests validate the real system path\. Simulation must use the same ingestion, reasoning, incident, alert, and UI paths as hardware; test harnesses must not bypass production logic\.

# DOCUMENT MAP

1\. Validation Philosophy & Scope

2\. Verification Levels and Evidence Model

3\. Requirements Traceability & Test IDs

4\. Golden Vectors and Deterministic Math Validation

5\. Hardware, Sensor & Edge\-Node Validation

6\. Telemetry, Backend & Data Integrity Validation

7\. Intelligence & Hazard Reasoning Validation

8\. Fire Spread, Geospatial & Risk Validation

9\. Multi\-Hazard & Synthetic Telemetry Validation

10\. Communication, Resilience & Offline Validation

11\. Security & Trust Validation

12\. Authority & Citizen UI Validation

13\. Performance, Reliability & Soak Validation

14\. Fault Injection, Recovery & Adversarial Scenarios

15\. Acceptance Gates, Evidence Pack & SIH Demo Readiness

16\. Test Case Templates and Execution Rules

17\. Final Release Checklist

# 1\. Validation Philosophy & Scope

NexAlert is a safety\-relevant distributed system\. Validation therefore covers not only whether a function returns an output, but whether the output is timely, attributable, honest about uncertainty, safe under failure, and consistent across edge, Master, backend, simulation, and user interfaces\.

The validation program is divided into verification \(did we build the system according to its specification?\) and validation \(does the implemented system behave usefully and safely under representative real conditions?\)\. Both are required for acceptance\.

## 1\.1 Scope

__• __ESP32 edge acquisition, diagnostics, health, quality, reliability, baseline/anomaly logic, local event generation, buffering and local emergency path\.

__• __Master ingestion, authentication, deduplication, incident correlation, distributed fusion, geospatial propagation, risk/exposure, alerts and response workflow\.

__• __Backend APIs, database integrity, event ordering, idempotency, audit records, data retention and replay\.

__• __Fire, flood, pollution, landslide, extreme heat and unknown\-hazard paths; multi\-hazard independence\.

__• __Authority dashboard, citizen safety UI and offline captive\-portal behavior\.

__• __Communication loss, Master failure, internet loss, stale data, node failure, conflicting evidence and security attacks\.

__• __Simulation/replay as a test instrument, not a source of decision labels\.

## 1\.2 Validation Principles

__Principle__

__Required behavior__

Same path

Synthetic telemetry enters the same ingestion and reasoning pipeline as field telemetry\.

Evidence first

Every safety\-relevant conclusion must be traceable to telemetry/evidence groups and their freshness\.

Fail honest

When evidence is insufficient, system reports DEGRADED/UNKNOWN rather than inventing certainty\.

Fail local

Loss of cloud/internet must not eliminate configured local emergency behavior\.

No silent rewrite

Historical incident/spread truth is immutable; changed environmental inputs create new future projections\.

Human authority

NexAlert recommends and escalates; authorized humans approve consequential operational actions\.

Repeatability

Deterministic mathematical paths produce stable outputs for fixed inputs, versions and configurations\.

Observable

Every accepted/rejected event has logs, timestamps, reason codes and correlation IDs\.

# 2\. Verification Levels and Evidence Model

__Level__

__Name__

__Primary question__

__Evidence__

L0

Static / schema

Is the artifact internally consistent?

Schema validation, lint, static checks, configuration validation

L1

Unit

Does one function implement its specification?

Unit tests, boundary tests, golden vectors

L2

Component

Does a subsystem work end\-to\-end?

Node, telemetry, intelligence, GIS, alert component tests

L3

Integration

Do subsystem contracts remain correct together?

Edge→Master→backend→UI traces, API contract tests

L4

System

Does the whole platform behave correctly?

Scenario runs, fault injection, replay, multi\-node tests

L5

Field / operational

Does the behavior hold in representative real environments?

Controlled trials, calibration records, environmental trials, operator acceptance

## 2\.1 Evidence Classes

__Evidence class__

__Examples__

__Acceptance rule__

Automated

pytest, firmware unit tests, API contract tests, schema validation

Must pass deterministically in CI before release candidate\.

Golden vector

Known input/output pairs for health, z\-score, anomaly, confidence, spread, geometry

No unexplained drift; intended tolerances recorded per function\.

Replay

Saved telemetry packet stream with fixed clock/config/version

Same run produces same state transitions and event IDs where deterministic\.

Fault injection

Drop packets, stale timestamps, kill Master, corrupt HMAC, disconnect internet

Expected safe state must occur; recovery behavior recorded\.

Physical trial

Sensor calibration and controlled environmental/fire observations

Raw evidence preserved with conditions, hardware revision and operator notes\.

Human acceptance

Authority/operator and citizen usability walkthroughs

Critical workflows completed without hidden implementation knowledge\.

__EVIDENCE RETENTION  __Every release candidate should retain test run ID, code commit, firmware build, configuration/parameter version, dataset/simulation seed, hardware revision, environment, result, logs and artifacts\.

# 3\. Requirements Traceability & Test IDs

Every requirement in Documents 01–16 must be mapped to at least one verification method and acceptance test\. Safety\-critical requirements require at least one automated test and one integrated/system\-level test unless explicitly waived with rationale\.

__Prefix__

__Domain__

__Examples__

VAL\-MATH

Mathematical intelligence

baseline, anomaly, confidence, severity, risk, hysteresis

VAL\-EDGE

Edge node

sampling, health, local inference, buffering, AP

VAL\-API

Backend/API/DB

schema, idempotency, ordering, audit

VAL\-GEO

Fire/geospatial

DEM gradients, wind vector, ROS, arrival time, polygons

VAL\-MHZ

Multi\-hazard

hazard separation, correlation, conflict

VAL\-COMM

Communication/resilience

offline, failover, store\-forward

VAL\-SEC

Security

HMAC, Ed25519, replay, RBAC, privacy

VAL\-UIA

Authority UI

overview, incident command, alerts, degraded states

VAL\-UIC

Citizen UI

emergency viewport, SOS, safe place, offline portal

VAL\-PERF

Performance/reliability

latency, throughput, soak, recovery

VAL\-SIM

Simulation/replay

determinism, scenario truth separation, checkpoints

## 3\.1 Criticality Classes

__Class__

__Meaning__

__Release rule__

C0

Safety / trust boundary

Must pass\. No open critical defect\.

C1

Core operational

Must pass or have documented, time\-bounded waiver approved by technical lead\.

C2

Supporting / UX

Pass required for final demo; minor visual issues may be tracked\.

C3

Nice\-to\-have

May be deferred without blocking core acceptance\.

# 4\. Golden Vectors and Deterministic Math Validation

The Python reference implementation is the numerical oracle for shared mathematical behavior where the embedded implementation intentionally reproduces the same bounded subset\. C/C\+\+ or optimized implementations must pass golden\-vector parity before deployment\.

## 4\.1 Core Golden Vector Set

__ID__

__Function__

__Representative cases__

__Expected checks__

GV\-H01

Health

All diagnostics nominal; one hard failure; weighted degradation

Range \[0,1\], hard gate to zero, monotonic degradation

GV\-Q01

Quality

Fresh/stable; stale; high jitter; missing samples

Quality decreases as integrity/stability degrade; no missing=zero assumption

GV\-R01

Reliability

H, Q, calibration factor combinations

R=H×Q×K, bounded \[0,1\]

GV\-B01

Baseline

INITIALIZING→LEARNING→READY; contamination; recovery

Readiness state and freeze/recovery transitions correct

GV\-A01

Anomaly

z=0, ±1, ±z\_cap, extreme

Symmetric magnitude behavior, bounded \[0,1\]

GV\-C01

Confidence

Coverage/agree/temp/base edge combinations

N/A below evidence floor; group\-aware aggregation

GV\-S01

Severity/Risk

Boundary and weighted extremes

Bounded \[0,1\], weights normalized/validated, no probability claim

GV\-HZ01

Hysteresis

Trigger, persistence, clear, escalation

No chatter around threshold; fast escalation path works

GV\-GEO01

Gradient

Flat, plane, edge conditions

Correct central differences and aspect conventions

GV\-FIRE01

ROS/arrival

No wind, wind\-aligned, crosswind, uphill/downhill, barrier

Directional effect, diagonal distance, non\-burnable barrier behavior

GV\-GEO02

Geometry

Single blob, holes, disjoint zones

Valid Polygon/MultiPolygon; repair/simplification does not change source raster

## 4\.2 Numerical Tolerances

Each numerical test must declare its tolerance\. Use exact equality only for integer/state outputs or explicitly deterministic operations\. Floating\-point comparisons should use absolute and/or relative tolerance appropriate to units and algorithm\. Tolerance changes require review because they can hide implementation drift\.

__Artifact__

__Default comparison approach__

__Notes__

Scalar reference math

abs/rel tolerance

Choose per quantity; document units\.

State machine

exact

State, reason code and event transition must match\.

Geometry

topological \+ area/shape tolerance

Raw raster remains canonical; display simplification is separate\.

Arrival raster

cellwise/time tolerance

Check reachable cells, barriers and arrival ordering\.

Probabilities

N/A

NexAlert confidence/risk are operational indices unless a distinct probabilistic model is introduced\.

# 5\. Hardware, Sensor & Edge\-Node Validation

Physical validation must be performed with the exact sensor modules, wiring, power system, enclosure and firmware configuration intended for the demonstration\. A simulator cannot replace calibration evidence for physical sensors\.

## 5\.1 Sensor Validation Matrix

__Sensor class__

__Validation__

__Acceptance evidence__

Temperature

Known\-point comparison over operating range; warm\-up behavior

Calibration record, error distribution, timestamped samples

Humidity

Controlled reference comparison; drift observation

Relative error record and hysteresis note

PM2\.5/PM10

Reference instrument side\-by\-side under controlled conditions

Correlation/error record, warm\-up and saturation behavior

Gas

Gas\-species\-specific calibration and cross\-sensitivity review

Chosen sensor rationale, calibration/driver evidence; do not label generic response as ppm without calibration

Water level

Known\-depth references, zero offset, repeatability

Depth error record and installation geometry

Rainfall

Known flow/rain simulator or reference gauge comparison

Rate/cumulative error and resolution record

Soil moisture

Reference media/moisture conditions, installation\-specific calibration

Calibration curve/lookup and depth/location assumptions

Vibration

Known excitation or repeatable test fixture

Sensor output consistency and unit calibration

## 5\.2 Edge Functional Tests

__Test ID__

__Scenario__

__Pass criterion__

VAL\-EDGE\-001

Boot and sensor enumeration

Node boots, enumerates required sensors, records missing/failed devices without fabricating values\.

VAL\-EDGE\-002

Heartbeat

Heartbeat contains node identity, firmware/config version, diagnostics and freshness\.

VAL\-EDGE\-003

Local inference

Configured baseline/anomaly path runs at target cadence without blocking acquisition\.

VAL\-EDGE\-004

Buffer saturation

Bounded ring buffer drops/compacts according to policy; newest safety\-critical data remains prioritized where configured\.

VAL\-EDGE\-005

Clock anomaly

Backward/invalid timestamps are flagged; measurement time remains distinct from receive time\.

VAL\-EDGE\-006

AP/emergency path

Local emergency page remains reachable during configured Master/backend failure path\.

VAL\-EDGE\-007

Concurrency benchmark

Sensing \+ local service \+ telemetry \+ HMAC \+ buffering meet measured CPU/heap/latency targets on target hardware\.

VAL\-EDGE\-008

Power cycle

After abrupt reset, node recovers without corrupting persistent queue/state beyond declared limits\.

# 6\. Telemetry, Backend & Data Integrity Validation

__Area__

__Representative tests__

__Acceptance criteria__

Schema

Required/missing/extra fields; units; schema\_version

Invalid payload rejected or quarantined; accepted payload is normalized\.

Authentication

Valid/invalid HMAC; wrong key; replay

Invalid/unauthenticated event rejected; replay not processed twice\.

Idempotency

Same telemetry\_id/sequence submitted repeatedly

Single logical event in state; duplicate acknowledged or safely ignored\.

Ordering

Out\-of\-order telemetry; delayed packets

Late data retained with timestamps and does not silently rewrite historical state\.

Clock/freshness

Old, future\-skewed, missing receive time

Freshness classification remains correct; no false recency\.

Transactions

Partial incident/alert write failure

Atomicity or explicit recovery path; no impossible half\-state\.

Audit

Alert create/edit/standdown; config change; role change

Actor, time, action, reason and correlation ID persisted\.

Migration

Schema/config upgrade on representative backup

Data preserved or migration failure is explicit and recoverable\.

## 6\.1 End\-to\-End Trace Test

A canonical trace should be executed for every release candidate: sensor measurement → edge packet → Master verification → ingestion normalization → quality → anomaly → evidence/confidence → incident state → alert decision → authority UI → citizen delivery/offline UI → audit record\. The test harness must retain a single correlation identifier so an evaluator can follow the event through all layers\.

# 7\. Intelligence & Hazard Reasoning Validation

The intelligence layer is validated as a chain, not as one opaque score\. Each stage must expose reason codes and intermediate values in diagnostic/test mode\.

__Stage__

__Validation focus__

__Failure that must be caught__

Health

Soft diagnostics, hard failures, normalized health

Dead sensor treated as healthy

Quality

Integrity/stability and freshness

Stale packet treated as current evidence

Reliability

H×Q×K and bounds

Unreliable sensor dominates node anomaly

Baseline

Readiness, contamination control, freeze/recovery

Incident values poison baseline

Anomaly

Robust baseline or hazard\-specific feature

One spike instantly becomes confirmed hazard

Evidence

Core coverage, agreement, temporal behavior

Supportive signals override missing core evidence

Confidence

Evidence threshold, correlation groups, N/A behavior

Confidence displayed as probability

Severity

Impact/exposure/trajectory or configured contributors

Severity silently mixed with confidence

Operational risk

Expected\-response/usefulness index

Risk presented as calibrated probability

State machine

Persistence, hysteresis, fast escalation, clear

Chatter / stuck alerts / impossible transitions

## 7\.1 Key Negative Tests

__• __One sensor stuck high while the remaining independent group is normal\.

__• __Two correlated sensors fail together; coverage must not be treated as two independent votes\.

__• __One valid sensor detects a sharp change while supporting sensors are unavailable\.

__• __Conflicting core evidence from two spatially close nodes\.

__• __Baseline is not READY when a threshold crossing occurs\.

__• __Confidence falls below the assessment threshold; system must expose UNKNOWN/N/A rather than fabricate a value\.

__• __Multi\-hazard conditions occur simultaneously; each hazard remains an independent vector and alert path\.

# 8\. Fire Spread, Geospatial & Risk Validation

Fire validation is designed as a defensible cellular/arrival\-time simulation, not a visual animation\. Controlled trials validate the telemetry and hazard\-detection path; the geospatial spread engine is validated against deterministic synthetic cases and known physical directional expectations\.

__Test__

__Input__

__Expected__

VAL\-GEO\-001

Flat DEM, zero wind, uniform fuel

Symmetric/consistent propagation subject to configured directional model\.

VAL\-GEO\-002

Uniform wind from north

Propagation bias is toward south after FROM→TO conversion\.

VAL\-GEO\-003

Uniform slope with no wind

Propagation bias follows configured slope vector\.

VAL\-GEO\-004

Wind \+ slope

Wind and slope combine directionally through vector model; no arbitrary scalar multiplication of unrelated directions\.

VAL\-GEO\-005

Non\-burnable strip

Arrival\-time propagation routes around barrier; ROS=0 in non\-burnable cells\.

VAL\-GEO\-006

Diagonal\-only route

Travel distance uses Δ√2 for diagonal neighbor\.

VAL\-GEO\-007

Dynamic environment update

Past truth frozen; current frontier reseeded; future projection version changes\.

VAL\-GEO\-008

Raster→geometry

Current/warning/projection zones support Polygon/MultiPolygon and remain topologically valid after repair\.

VAL\-GEO\-009

Operational buffer

Buffer is visibly distinct from physical footprint and is labeled as policy/operational\.

VAL\-GEO\-010

Risk surface

Hazard risk remains separate from exposure/population; multi\-hazard risks not collapsed into fake combined probability\.

## 8\.1 Spatial Accuracy and CRS Checks

__• __All cell distances used in propagation are derived from a metric grid or valid projected CRS, not raw latitude/longitude degrees treated as meters\.

__• __DEM gradients use central differences where neighbors exist and explicit edge handling where they do not\.

__• __Wind direction semantics are documented as FROM for meteorological input and converted to TO for propagation\.

__• __Geometry generated for display may be simplified, but source raster/arrival surfaces remain the analytical truth\.

__• __Population, roads, schools and hospitals are downstream impact/exposure layers and must not alter physical fire arrival unless an explicitly configured interaction model is added\.

# 9\. Multi\-Hazard & Synthetic Telemetry Validation

Synthetic telemetry exists to exercise the system repeatedly across controlled scenarios\. It is not allowed to encode the final decision as if it were observed truth\. Ground truth remains private to the simulator/test harness and is used only for evaluation\.

__Scenario family__

__Required variations__

__Checks__

Normal

Stable, seasonal trend, moderate noise

No false incident; baseline learns correctly\.

Slow onset

Gradual water/heat/pollution change

Persistence/trend path detects change without excessive chatter\.

Rapid onset

Sharp water rise, smoke/PM spike, gas event

Fast escalation and short\-latency path works\.

Contradiction

Core vs supporting sensors disagree

Information Condition and evidence explanation degrade appropriately\.

Correlated failure

Two sensors share common\-mode failure

Group\-aware evidence prevents fake corroboration\.

Missing/stale

Drop or delay selected streams

Reliability/confidence degrade; unknown states are honest\.

Communication loss

Partition node from Master then recover

Store\-forward and replay/idempotency function\.

Multi\-node

Spatially correlated plume/flood/fire signatures

Incident correlation merges physically plausible events, not distant unrelated events\.

Multi\-hazard

Fire \+ pollution; flood \+ landslide; heat \+ pollution

Independent hazard states/risks remain visible; UI avoids one misleading combined scalar\.

Unknown

Pattern not matching configured hazard pathways

Unknown hazard remains observable with evidence and uncertainty, not silently forced into a known class\.

# 10\. Communication, Resilience & Offline Validation

__Failure injection__

__Expected system behavior__

__Evidence__

Internet down

Local network/control path continues; cached/emergency functions follow policy

UI capture \+ logs

Master process down

Local node emergency path survives; node autonomy remains operational

Timed outage test

Master power removed

Node\-local emergency behavior remains reachable where hardware deployment provides the required path

Physical power\-off test

Packet loss

Quality/freshness degrade; no false zero; retransmission/backoff as configured

Packet capture \+ telemetry log

Out\-of\-order delivery

Ordering metadata prevents stale overwrite

Replay trace

Reconnect

Buffered data drains with idempotency and order metadata

Queue depth before/after

Offline citizen access

Known local Wi\-Fi AP/captive portal exposes current emergency page

Phone test \+ screenshot/video

No viable safe route

Citizen UI presents SHELTER\_IN\_PLACE rather than an unsafe destination

Scenario replay \+ UI evidence

Partitioned nodes

Local states continue; Master fuses only available evidence and shows degraded information

Multi\-node partition test

## 10\.1 Availability vs Information Condition

The test suite must distinguish service availability from evidentiary quality\. A system can be reachable while information is DEGRADED or UNKNOWN\. Conversely, a node can retain a local emergency function while disconnected from the cloud\. Tests must assert both dimensions independently\.

# 11\. Security & Trust Validation

__Test__

__Attack/condition__

__Pass criteria__

VAL\-SEC\-001

Valid node HMAC

Accepted and authenticated\.

VAL\-SEC\-002

Modified payload

Rejected; reason code recorded\.

VAL\-SEC\-003

Wrong secret

Rejected\.

VAL\-SEC\-004

Replay of valid packet

Rejected/ignored as duplicate or stale; no second logical event\.

VAL\-SEC\-005

Timestamp/sequence rollback

Rejected or quarantined according to freshness policy\.

VAL\-SEC\-006

Signed emergency event

Valid Ed25519 signature verifies and UI shows trust state\.

VAL\-SEC\-007

Forged event

Signature invalid; no trusted badge; no consequential action\.

VAL\-SEC\-008

Unauthorized role action

Blocked and audited\.

VAL\-SEC\-009

Credential rotation

Old credential revoked/expired as designed; new credential accepted\.

VAL\-SEC\-010

Sensitive citizen data access

Only authorized actors can access; audit trail records access where required\.

__THREAT\-MODEL RULE  __Testing a spoofed Wi\-Fi SSID is not the same as proving it can be prevented\. NexAlert’s prototype security claim is authenticity of signed content and authorized actions, not control over every RF spoofing possibility\.

# 12\. Authority & Citizen UI Validation

## 12\.1 Authority Dashboard

__Workflow__

__Acceptance checks__

Overview

Nodes/incidents/SOS/risk layers visible; colors are not the sole status channel; freshness/system state visible\.

Incident Command Card

Information Condition visible; evidence explanation can be expanded; confidence is not mislabeled probability\.

Fire Spread

LIVE/SIMULATION switch, time controls, current/warning/projection layers, affected impact layers and wind/context visible\.

Nodes & Network

Node panel shows health, battery/power, communication, telemetry freshness and diagnostics\.

Alerts

Issued/targeted/delivered/opened/acknowledged/unreachable states visible; human approval gates consequential action\.

Response

Recommendation→acknowledged→notified→assigned→en route→resolved lifecycle is consistent\.

Audit

User/action/time/reason/correlation data accessible for safety\-relevant actions\.

## 12\.2 Citizen Safety UI

__Workflow__

__Acceptance checks__

Emergency first viewport

Hazard, severity/state, distance/direction/freshness and clear action appear before secondary content\.

Safe place

Ranking considers hazard exposure/route/capacity and can return SHELTER\_IN\_PLACE when no viable route exists\.

SOS

Press\-and\-hold/tap duration requirement works; repeat attempts are consolidated rather than silently rejected\.

Offline

Local portal renders emergency content without cloud dependency on supported deployment path\.

Trust

Signed event / verification state is understandable without exposing cryptographic details as the primary message\.

Accessibility

Core actions operable by keyboard/touch; status not color\-only; text remains legible at supported viewport sizes\.

Degraded evidence

UI explicitly shows stale/degraded/unknown conditions and never implies certainty that backend does not have\.

# 13\. Performance, Reliability & Soak Validation

Performance values below are engineering targets for the prototype release\. They are not claims of measured production performance until the corresponding tests are executed on the target hardware and deployment environment\.

__Metric__

__Prototype target__

__Measurement method__

Telemetry ingestion latency

p95 ≤ 500 ms on local network for normal load

Timestamp at edge \+ receiver \+ processing completion

Critical alert decision latency

p95 ≤ 2 s after required evidence is available

Correlated event timestamps

Local emergency page

Initial render ≤ 2 s on target phone/local AP

Screen trace / browser performance capture

Node queue recovery

Buffered backlog drains without duplicate logical events

Queue depth over time \+ event counts

Master restart recovery

Service returns to healthy state within configured target; record actual measured time

Process/container restart test

Edge memory stability

No unbounded heap growth during sustained representative workload

Heap sampling over soak test

8\+ hour soak

No unexplained crash, leak, state corruption or queue divergence

Automated telemetry \+ health logs

24 hour extended soak

Preferred pre\-demo validation

Long\-run scenario \+ fault injection

## 13\.1 Concurrency Benchmark

The ESP32 benchmark must run sensing, diagnostics, heartbeat, local AP/service, HMAC generation/verification where applicable, bounded buffering and local inference concurrently\. Record CPU load, free heap, queue depth, task latency/jitter, dropped packets and power draw\. The result becomes the evidence for the chosen sampling cadence and feature set\.

# 14\. Fault Injection, Recovery & Adversarial Scenarios

__Scenario__

__Injected fault__

__Expected safe outcome__

FI\-01

One sensor hard\-fails

Health gates sensor; hazard logic does not trust it; information state reflects impact\.

FI\-02

One sensor drifts

Quality/reliability decline; baseline/anomaly behavior does not self\-confirm the drift as a hazard without evidence\.

FI\-03

Two related sensors fail together

Correlation group logic limits apparent independent corroboration\.

FI\-04

Node disappears

Master shows stale/offline node; incident state remains based on surviving evidence\.

FI\-05

Master disappears

Local edge emergency path continues where deployed; no false claim of cloud availability\.

FI\-06

Internet disappears

Local services continue; online delivery is correctly marked unavailable\.

FI\-07

Database write failure

No silent loss of safety\-critical transition; retry/queue or explicit degraded state\.

FI\-08

Clock skew

Freshness and replay checks prevent false recency\.

FI\-09

Configuration corruption

System fails closed for invalid privileged configuration; previous valid config retained where policy supports atomic activation\.

FI\-10

Forged event

Untrusted event cannot become confirmed trusted alert\.

FI\-11

Alert flood

Rate/frequency safeguards prevent UI fatigue and repeated spam while preserving safety\-critical escalation\.

FI\-12

No safe destination

Citizen path resolves to SHELTER\_IN\_PLACE\.

FI\-13

Simulated false label injection

Decision engine does not consume simulator ground truth\.

FI\-14

Environmental change during fire projection

Historical truth remains frozen; future projection is versioned/recomputed from current frontier\.

## 14\.1 Recovery Rules

__• __Recovery is a state transition with evidence, not simply process restart\.

__• __After reconnect, buffered data is replayed idempotently and stale data is labeled as historical rather than masquerading as current\.

__• __Baseline recovery uses the defined RECOVERING path; previously contaminated baseline is not silently trusted\.

__• __Incident stand\-down requires the same event/authority/audit discipline as activation\.

__• __Any security compromise requires credential/key revocation and re\-enrollment before the node returns to trusted operation\.

# 15\. Acceptance Gates, Evidence Pack & SIH Demo Readiness

__Gate__

__Minimum evidence__

__Release decision__

Gate A — Build integrity

Static checks, unit tests, schema validation, firmware build verification

PASS / BLOCK

Gate B — Mathematical parity

Golden vectors \+ Python↔embedded parity

PASS / BLOCK

Gate C — Hardware readiness

Sensor calibration, edge concurrency benchmark, power\-cycle and local path tests

PASS / BLOCK

Gate D — End\-to\-end path

Canonical telemetry→incident→alert→UI trace

PASS / BLOCK

Gate E — Resilience

Internet loss, Master loss, reconnect/store\-forward, offline citizen path

PASS / BLOCK

Gate F — Security

HMAC, replay, signed event, RBAC tests

PASS / BLOCK

Gate G — Geo/fire

Directional, barrier, dynamic recompute, geometry/risk checks

PASS / BLOCK

Gate H — Scenario coverage

Normal \+ rapid \+ slow \+ contradiction \+ correlated failure \+ multi\-hazard

PASS / BLOCK

Gate I — Soak/performance

Representative soak \+ latency measurements \+ resource stability

PASS / BLOCK

Gate J — Demo readiness

Operator walkthrough, citizen walkthrough, scripted failure injection

PASS / BLOCK

## 15\.1 SIH Demonstration Test Sequence

__• __Step 1: Boot node and show health/heartbeat\.

__• __Step 2: Inject normal environmental telemetry; show LEARNING→READY baseline state\.

__• __Step 3: Inject controlled fire\-like sensor pattern; show anomaly → evidence → incident state\.

__• __Step 4: Open Fire Spread and show simulation driven by the same backend state\.

__• __Step 5: Issue an alert through human\-approved workflow; show audit trail\.

__• __Step 6: Open citizen UI and show emergency\-first viewport\.

__• __Step 7: Disable internet; reconnect phone to NexAlert local Wi\-Fi and show offline emergency page\.

__• __Step 8: Kill Master/network path; show node\-local emergency behavior and honest degraded state\.

__• __Step 9: Restore connectivity; demonstrate store\-forward recovery and idempotent replay\.

__• __Step 10: Inject contradictory/corrupted input; show the system refuses to overclaim certainty\.

__• __Step 11: Finish with unresolved/open issues shown transparently on the engineering evidence sheet\.

__DEMO INTEGRITY  __Never precompute a visual result that the production path did not generate during the demo\. Any scripted sequence must still exercise the real ingestion, reasoning and UI contracts\.

# 16\. Test Case Templates and Execution Rules

__Field__

__Required content__

Test ID

Unique ID from domain prefix\.

Requirement link

Document/section/requirement being verified\.

Criticality

C0–C3\.

Preconditions

Hardware, firmware, configuration, network, database, seed/dataset\.

Stimulus

Exact telemetry, failure injection, user action or environmental condition\.

Expected

Observable result, timing, state and reason code\.

Observed

Measured result and artifact reference\.

Pass rule

Exact threshold or qualitative condition\.

Evidence

Log, screenshot, video, trace, dataset, calibration record, benchmark\.

Environment

Machine, OS, firmware build, commit, time base and versions\.

Owner/Date

Person executing and execution timestamp\.

Defect reference

Issue ID when failed\.

Notes/Waiver

Rationale for deviations; approval and expiry if waived\.

## 16\.1 Execution Rules

__• __Clean test data and intentionally contaminated test data must be separated and labeled\.

__• __Randomized scenarios must record seed/configuration so failures are reproducible\.

__• __Every failure receives a defect ID; tests are not deleted because they are inconvenient\.

__• __Flaky tests are quarantined with root\-cause investigation, never silently retried until green\.

__• __Hardware trials record sensor part numbers, calibration state, power configuration and environmental conditions\.

__• __Time\-sensitive tests must capture both event time and receive/processing time\.

__• __Acceptance cannot depend on a single screenshot when logs or traces are available\.

__• __Any waived C0/C1 requirement requires explicit approval and a follow\-up date; a waiver is not a pass\.

# 17\. Final Release Checklist

__Area__

__Checklist item__

__Status__

Architecture

Current docs 01–16 used as authoritative design inputs

□

Math

Golden vectors pass; parity checked

□

Edge

Sensor validation \+ concurrency \+ power\-cycle pass

□

Data/API

Schema/idempotency/auth/audit pass

□

Intelligence

Evidence/confidence/state tests pass including negative cases

□

Fire/Geo

Propagation, barrier, dynamic recompute, geometry, risk pass

□

Multi\-hazard

Independent hazard vectors verified

□

Resilience

Master/internet/local/offline failure tests pass

□

Security

HMAC/replay/signature/RBAC tests pass

□

Authority UI

Critical operator workflows pass

□

Citizen UI

Emergency/offline/SOS/safe\-place workflows pass

□

Performance

Latency \+ resource \+ soak evidence recorded

□

Traceability

All C0/C1 requirements mapped to executed tests

□

Demo

Scripted demo reproduces from clean state

□

Evidence pack

Logs, screenshots, videos, calibration records and reports archived

□

## Release Decision Statement

A NexAlert release candidate is accepted only when all applicable C0 requirements pass, all mandatory acceptance gates pass, no critical defect is open, and the evidence pack is reproducible\. The final status should be recorded as ACCEPTED, ACCEPTED WITH EXPLICIT WAIVERS, or NOT ACCEPTED\. “Looks correct” is not an acceptance state\.

