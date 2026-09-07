__NEXALERT__

__TECHNICAL REQUIREMENTS DOCUMENT \(TRD\)__

Final V1 Engineering Requirements Baseline

__Document role  
__This TRD converts the frozen NexAlert architecture into testable technical requirements\. It defines what the implemented system must do, the conditions under which it must do it, what evidence proves compliance, and which behaviors are explicitly out of scope\. Exact technology choices are governed by the separate Technology Stack, Deployment & Compute Allocation specification\.

__Field__

__Value__

Product

NexAlert

Problem statement

SIH26178 — resilient AI\-powered environmental monitoring and early warning

Document

02 — Technical Requirements Document

Status

FINAL V1 REQUIREMENTS BASELINE

Primary audience

Software, AI, geospatial, embedded, backend, frontend, test and coding\-agent teams

Primary purpose

Requirements, acceptance criteria, traceability and implementation guardrails

Architecture authority

Document 01 — Master System Architecture & Architecture Invariants

__Requirement language  
__MUST = mandatory for V1 compliance\. SHOULD = strongly recommended but may be deferred with documented reason\. MAY = optional\. DEFERRED = deliberately outside V1\. A requirement is not considered complete until its acceptance evidence exists\.

# Document Control & Navigation

__Version__

__Status__

__Meaning__

1\.0

FINAL

Baseline derived from frozen architecture and adversarial review\.

1\.x

Controlled change

Only approved clarifications, parameter changes or genuine architecture changes\.

## Requirement taxonomy

__Type__

__Meaning__

FR

Functional Requirement — behavior the system performs\.

NFR

Non\-Functional Requirement — quality/performance/reliability/security constraint\.

DR

Data Requirement — data semantics, provenance, schema or source constraint\.

ER

Embedded/Edge Requirement — field\-node/edge behavior\.

GR

Geospatial Requirement — spatial/geometry/simulation behavior\.

UR

User/UX Requirement — citizen or authority interaction behavior\.

SR

Security Requirement — authentication, integrity, authorization and audit\.

VR

Verification Requirement — evidence needed to prove an implementation claim\.

CR

Constraint — explicit architectural boundary or non\-goal\.

## Cross\-document authority

__Question__

__Authority document__

What is NexAlert and how are responsibilities divided?

01 — Master Architecture & Invariants

What must the system do?

02 — this TRD

What technologies and compute targets are used?

03 — Technology Stack / Deployment

How exactly are intelligence quantities calculated?

04 — Mathematical Intelligence

How exactly is fire spread/geospatial simulation calculated?

05 — Fire/Geospatial

What enters from hardware?

06 — Hardware/Edge

How are APIs/data stored?

07 — Backend/API/DB

Where does validation/synthetic data come from?

08/09 — Data & Simulation

How are actions/alerts managed?

10 — Incident/Response

How does data travel and survive failure?

11 — Communication/Resilience

What does the product look like?

12 — UI/UX

What does the authority/citizen UI do?

13/14 — UI Functioning

How is correctness demonstrated?

17 — Validation

# 1\. System Objective

NexAlert MUST operate as a coherent disaster\-management decision\-support system rather than a collection of disconnected demos\. The implemented product MUST be able to accept real or synthetic environmental telemetry, establish data trust, reason about hazards, create and update incidents, produce geospatial impact information, evaluate exposure, recommend operational actions, communicate alerts, provide citizen safety guidance, support authority operations, and preserve a traceable audit history\.

## 1\.1 V1 product outcomes

- Detect developing fire conditions from real controlled sensor trials and produce a defensible hazard assessment\.
- Support a second flood pathway using the same reasoning architecture and appropriate evidence inputs\.
- Represent additional hazards independently where configured data is sufficient, without falsely claiming equal validation\.
- Continue essential local intelligence during loss of Master/cloud/internet connectivity to the degree supported by the deployed edge topology\.
- Turn a hazard into a spatially meaningful incident with current/warning/projected geometry where a valid model exists\.
- Provide population/infrastructure exposure using real sourced data when displayed\.
- Provide authority recommendations and workflow while keeping human approval mandatory for operational actions\.
- Provide an app\-free citizen emergency experience through web/local network paths\.
- Run synthetic scenarios through the same downstream processing path as real telemetry\.

## 1\.2 Core product question

__The system must answer  
__What is happening? → How trustworthy is the information? → How dangerous is it? → Where is it? → Who/what may be affected? → What should the authority do? → What should the citizen do?

# 2\. System Scope

## 2\.1 Included

__Domain__

__V1 requirement boundary__

Field sensing

Distributed environmental sensors attached to ESP32\-class nodes\.

Edge intelligence

Local diagnostics, health, quality, reliability, baseline/anomaly and lightweight hazard reasoning as assigned\.

Master/local compute

Aggregation, regional fusion, geospatial computation, local backend services and synchronization\.

Backend/cloud

Canonical state, APIs, persistence, workers, targeting, alerts, audit and history\.

Geospatial

Fire spread, terrain, affected areas, hazard risk surfaces and exposure\.

Operations

Incident management, response recommendations, human approval, alerts, SOS and action tracking\.

Citizen

One\-page emergency UI, safe place/route guidance, SOS, offline/local emergency path\.

Authority

Command dashboard, evidence explanations, maps, response workflow, historical and audit views\.

Simulation

Synthetic telemetry, multi\-hazard scenarios, replay and failure injection\.

## 2\.2 Explicitly excluded from V1

- Full wildfire CFD/FIRETEC/WFDS\-class simulation\.
- Ember spotting and reignition physics\.
- Autonomous dispatch of emergency responders\.
- A universal algebraic multi\-hazard risk score\.
- Microservices/Kafka\-class streaming as a requirement\.
- Deep enterprise RBAC\.
- Mandatory native mobile app\.
- Satellite feed dependency for local hazard decisions\.
- LoRaWAN/NB\-IoT variants as core prototype dependencies\.
- 3D terrain visualization as a core requirement\.
- Production\-grade field deployment claims without field validation and regulatory work\.

# 3\. Actors & Trust Boundaries

__Actor/System__

__Primary role__

__Trust/permission boundary__

Field node

Sense and transmit

Authenticated device; cannot make authority dispatch decisions\.

Master/local gateway

Aggregate, compute and provide local continuity

Trusted local compute, but still validates node packets\.

Backend/domain services

Canonical source of domain state

Authoritative for persisted incidents/actions/alerts\.

Simulation engine

Generate synthetic input

Must not inject ground\-truth labels into intelligence\.

Authority operator

Review, approve/override actions

Only authorized human can transition recommended actions into operational action\.

Responder

Update response state where supported

Does not redefine hazard truth\.

Citizen

Receive safety information and submit SOS

Can send SOS/messages; cannot edit hazard state\.

Administrator

Configure system

May manage parameters/configuration subject to audit\.

## 3\.1 Trust boundary rules

- Node telemetry MUST be authenticated before entering canonical ingestion\.
- Citizen clients MUST treat signed/verified emergency events as the trusted event object\.
- Frontend clients MUST NOT become alternate sources of hazard truth\.
- Simulation MUST be permanently source\-labeled\.
- Operator overrides MUST be audited\.

# 4\. Functional Requirements

## 4\.1 Field node and telemetry

__ID__

__Area__

__Requirement__

__Acceptance evidence__

FR\-001

Node telemetry

The field node MUST send canonical telemetry containing node identity, sequence, measurement timestamp, measurements, diagnostics, battery state, source metadata, schema version and authentication metadata\.

Packet conforms to canonical telemetry schema; invalid fields rejected\.

FR\-002

Heartbeat

Each node MUST emit a heartbeat at the configured health\-report interval and provide enough status to determine node availability\.

Heartbeat observed; stale\-heartbeat test transitions node to unavailable/degraded\.

FR\-003

Diagnostics

Node telemetry MUST distinguish sensor health/diagnostics from battery/solar state\.

Dashboard shows independent health and power values\.

FR\-004

Missingness

Missing measurements MUST be represented as missing/null/explicit status, never as numeric zero\.

Missing sensor test leaves hazard reasoning aware that evidence is unavailable\.

FR\-005

Timestamp semantics

Telemetry MUST carry measurement time and receive time as distinct fields\.

Out\-of\-order/replay test demonstrates ordering and domain\-time separation\.

FR\-006

Sequence/idempotency

Telemetry MUST include sequence or equivalent event identity sufficient for duplicate detection\.

Duplicate packet generates no duplicate downstream incident/alert\.

FR\-007

Authentication

Node\-to\-Master/backend telemetry MUST be authenticated using per\-node credentials/HMAC for V1\.

Invalid/missing/tampered authentication is rejected and logged\.

## 4\.2 Intelligence

__ID__

__Area__

__Requirement__

__Acceptance evidence__

FR\-010

Health

The system MUST compute sensor health separately from battery state and apply hard failure gates\.

Dead sensor test drives health contribution to zero\.

FR\-011

Signal quality

The system MUST compute current signal quality separately from long\-term health\.

Synthetic noise/saturation test changes quality without inventing a health failure\.

FR\-012

Reliability

The hazard evidence pipeline MUST use reliability\-weighted inputs\.

Low\-reliability sensor contributes less than equivalent healthy sensor\.

FR\-013

Baseline readiness

A new node MUST progress through explicit baseline states; anomaly outputs must respect readiness\.

Fresh\-node test shows LEARNING/initializing behavior rather than false certainty\.

FR\-014

Robust anomaly

Short\-window environmental anomalies MUST use the defined robust baseline logic; sensor\-specific modalities MAY use specialized methods\.

Reference\-vector tests match expected anomaly behavior\.

FR\-015

Baseline freeze

Confirmed/critical hazard states MUST prevent the baseline from learning the hazard as normal\.

Post\-event baseline remains controlled\.

FR\-016

Correlated evidence

Correlated sensors MUST be grouped appropriately when computing agreement/coverage\.

Correlated\-input test does not double\-count equivalent evidence\.

FR\-017

Core evidence floor

Hazard confidence MUST respect core\-evidence coverage requirements\.

Remove core sensor from test; confidence becomes appropriately constrained\.

FR\-018

Evidence/confidence separation

Evidence and evidence confidence MUST remain distinct quantities\.

UI/API exposes both concepts separately\.

FR\-019

Severity/risk separation

Severity and operational risk MUST remain distinct from evidence confidence and probability\.

No downstream component multiplies confidence into risk as a surrogate probability\.

FR\-020

Information condition

The system MUST expose GOOD/DEGRADED/UNKNOWN information condition when freshness/completeness changes\.

Stale data test produces degraded/unknown condition\.

FR\-021

Unknown state

The system MUST support insufficient evidence/UNKNOWN without manufacturing a hazard decision\.

Contradictory/missing evidence produces UNKNOWN or defined cautious behavior\.

## 4\.3 Hazard reasoning & incidents

__ID__

__Area__

__Requirement__

__Acceptance evidence__

FR\-030

Hazard independence

Each configured hazard MUST be evaluated independently and retain its own state/evidence/confidence/severity/risk\.

Fire\+flood test shows independent states\.

FR\-031

Deterministic\-first

V1 fire reasoning MUST be deterministic/calibrated and MUST NOT require a trained fire classifier\.

No fire ML classifier dependency in code path\.

FR\-032

Hazard state machine

Hazard state MUST use the defined lifecycle and hysteresis/persistence rules\.

State\-transition test suite passes\.

FR\-033

Incident creation

A new incident MUST be created when no matching existing incident satisfies the spatial/temporal correlation rule\.

Separated synthetic reports create separate incidents\.

FR\-034

Incident merge

Same hazard reports within configured spatial radius and time window MUST attach to the same incident\.

50 m/30 s test merges\.

FR\-035

Incident separation

Reports outside either spatial or temporal threshold MUST create or remain separate incidents\.

5 km test separates\.

FR\-036

Incident history

Incident changes MUST be recorded as timestamped events or equivalent audit records\.

Timeline reconstructs incident lifecycle\.

## 4\.4 Fire spread & geospatial

__ID__

__Area__

__Requirement__

__Acceptance evidence__

FR\-040

Fire spread inputs

The fire engine MUST consume ignition location plus defined terrain, fuel, moisture/context and wind inputs\.

Controlled input test shows all required inputs are represented\.

FR\-041

Wind convention

Meteorological FROM direction MUST be converted to propagation direction before vector use\.

Wind\-rotation test confirms correct direction\.

FR\-042

Terrain

Slope/aspect MUST derive from the configured DEM according to the geospatial specification\.

Known DEM fixture matches expected values\.

FR\-043

Directional ROS

Fire spread MUST use the approved directional ROS formulation with wind/slope directionality\.

Wind/slope sensitivity tests pass\.

FR\-044

Grid distance

Orthogonal and diagonal propagation MUST use correct distances, including diagonal √2 factor on a square grid\.

Uniform calm\-wind test avoids diamond/star artifact\.

FR\-045

Arrival time

The engine MUST calculate an arrival\-time field using event/priority\-queue propagation\.

Known synthetic field yields expected arrival ordering\.

FR\-046

Recompute

Changing environmental conditions MUST trigger future\-wavefront recomputation from the current perimeter\.

Mid\-run wind\-change test changes future projection without rewriting elapsed history\.

FR\-047

Footprint

Physical footprint MUST be derived from arrival\-time truth\.

Current geometry matches cells with arrival <= now\.

FR\-048

Zones

Current/warning/projected zones MUST be derived from the same arrival\-time field\.

Zone nesting test passes\.

FR\-049

Operational buffer

Any operational danger buffer MUST be distinct from the physical footprint and labeled as policy\.

UI shows separate footprint and buffer\.

FR\-050

Geometry validity

Generated polygons MUST support MultiPolygon and undergo validity checks/repair\.

Self\-intersection and disconnected\-region tests pass\.

FR\-051

CRS

Area/distance calculations MUST use appropriate projected/geodesic methods and MUST NOT treat raw lat/lon as planar metres\.

Known\-distance/area fixture within declared tolerance\.

FR\-052

Risk surface

Hazard risk heatmap MUST remain separate from physical footprint and exposure\.

Toggle test shows independent layers\.

FR\-053

Multi\-hazard layers

Different hazard risk surfaces MUST remain independent and never be algebraically collapsed into one universal risk number\.

Code/config inspection and integration test\.

## 4\.5 Exposure

__ID__

__Area__

__Requirement__

__Acceptance evidence__

FR\-060

Real exposure data

Displayed population/infrastructure values MUST come from real sourced datasets or be explicitly labeled synthetic\.

Provenance shown for displayed values\.

FR\-061

Zone semantics

Current/warning/projected exposure MUST remain semantically distinct and MUST NOT be naively summed\.

Nested\-zone test catches double\-counting\.

FR\-062

Unavailable data

Unavailable population/infrastructure data MUST display as unavailable/unknown, not zero\.

Data\-source failure test\.

FR\-063

Citizen exposure

Registered citizen points MUST be classified against active hazard geometry when location permission/data exists\.

Point\-in\-polygon test\.

FR\-064

Infrastructure

Roads, schools, hospitals and other configured assets MUST be spatially intersected/classified consistently\.

Known geometry fixture passes\.

## 4\.6 Response, alerts and SOS

__ID__

__Area__

__Requirement__

__Acceptance evidence__

FR\-070

Recommendation

Response engine MUST produce categorical recommendations such as MONITOR/VERIFY/NOTIFY/URGENT RESPONSE based on configured policy\.

Fixed input matrix produces deterministic recommendation\.

FR\-071

Human approval gate

No operational notification/dispatch action MUST transition into an approved/executed state without explicit human approval\.

Automated test blocks unapproved action\.

FR\-072

Priority tiers

Operational actions MUST use categorical priority tiers rather than fake\-precision scores\.

UI shows P1/P2/P3/P4 or equivalent\.

FR\-073

Escalation

Unacknowledged high\-priority actions MUST support configured escalation\.

Timeout test escalates\.

FR\-074

Stand\-down

Resolved incidents MUST generate explicit stand\-down/resolution state rather than silently disappearing\.

Resolve test produces visible stand\-down\.

FR\-075

Canonical emergency event

A single canonical emergency event MUST drive supported citizen delivery channels\.

Online/offline representations share event ID and semantics\.

FR\-076

Targeting

Online targeting MUST use authorized recent location/geofence data; offline targeting MUST use local network participation/range\.

Targeting integration test\.

FR\-077

Alert authenticity

Emergency events MUST be verifiable locally using trusted signing material where supported\.

Tampered event fails verification\.

FR\-078

SOS

SOS MUST remain available independent of active hazard state\.

SOS test outside hazard succeeds\.

FR\-079

SOS dedup

Repeated SOS presses from the same citizen/event MUST be consolidated without erasing history\.

Duplicate SOS test\.

FR\-080

Shelter\-in\-place

When no viable safe route exists, the citizen system MUST return SHELTER\_IN\_PLACE rather than an unsafe route\.

All\-directions\-hazard scenario\.

# 5\. Non\-Functional Requirements

## 5\.1 Reliability & resilience

__ID__

__Requirement class__

__Requirement__

NFR\-001

Resilience

Essential local intelligence MUST NOT require internet/cloud availability\.

NFR\-002

Resilience

The local emergency citizen path MUST have an architecture path that survives Master failure\.

NFR\-003

Resilience

Temporary communication loss MUST buffer telemetry/events and reconcile after reconnect\.

NFR\-004

Reliability

Retried or duplicated messages MUST NOT create duplicate domain side effects\.

NFR\-005

Reliability

Missing/stale inputs MUST lower information condition or capability explicitly rather than silently producing false values\.

NFR\-006

Recovery

Post\-outage recovery MUST preserve ordering/deduplication and avoid corrupting incident history\.

## 5\.2 Performance

Exact numeric performance targets are intentionally parameterized and will be fixed after benchmarking on target hardware and deployment\. The following are mandatory measurement requirements\.

__ID__

__Measure__

__Requirement__

NFR\-010

End\-to\-end latency

Measure from physical/synthetic telemetry creation to citizen\-visible/authority\-visible state update\.

NFR\-011

ESP32 concurrency

Measure sensing \+ Wi\-Fi AP \+ telemetry \+ local processing under representative load\.

NFR\-012

Geospatial runtime

Measure fire\-spread computation time for configured demo grid size/horizon on actual Master/cloud target\.

NFR\-013

Database latency

Measure representative telemetry/incident/action read\-write operations\.

NFR\-014

Web UI update latency

Measure backend event publication to rendered dashboard update\.

NFR\-015

Reconnect recovery

Measure time from restored link to complete buffer reconciliation under defined packet volume\.

## 5\.3 Scalability

__ID__

__Requirement__

NFR\-020

Schemas and APIs MUST be designed for N nodes even though the physical prototype may contain one or two nodes\.

NFR\-021

Node identification MUST be unique and configuration\-driven\.

NFR\-022

Incident correlation MUST work for multiple concurrent nodes without requiring a redesign of the entity model\.

NFR\-023

Hazard evaluation MUST support multiple hazards per observation\.

NFR\-024

The architecture SHOULD permit additional workers or compute nodes without changing canonical data contracts\.

NFR\-025

V1 claims MUST distinguish demonstrated scale from architectural scalability\.

## 5\.4 Security

__ID__

__Requirement__

NFR\-030

Node telemetry MUST be authenticated before ingestion\.

NFR\-031

Emergency events MUST support integrity/authenticity verification\.

NFR\-032

Replay protection MUST use event identity plus timestamp/sequence/nonce semantics as specified\.

NFR\-033

Secrets/keys MUST not be embedded in frontend source or publicly exposed configuration\.

NFR\-034

Unauthorized response actions MUST be blocked by the approval gate\.

NFR\-035

Security failures MUST be auditable\.

NFR\-036

Citizen location data MUST be retained only to the extent required by the consented feature and documented retention policy\.

# 6\. Data Requirements

## 6\.1 Canonical telemetry fields

__Field__

__MUST exist?__

__Requirement__

telemetry\_id

YES

Globally unique/idempotent record identifier\.

node\_id

YES

Stable device identity\.

sequence

YES

Monotonic or equivalent ordering identifier within node\.

measurement\_timestamp

YES

Time measurement was observed/generated\.

receive\_timestamp

YES

Time system received the packet\.

location

YES when node is location\-aware

Latitude/longitude or configured geospatial identity\.

measurements

YES

Canonical sensor values with explicit units\.

diagnostics

YES

Health/quality/calibration/stability/availability/saturation where applicable\.

battery

YES for node health operations

Separate power state\.

source

YES

HARDWARE or SIMULATION at minimum\.

schema\_version

YES

Versioned contract\.

auth

YES for network ingestion

HMAC/authentication metadata\.

## 6\.2 Data semantics

- Missing MUST remain missing; zero is a measured value only when the sensor actually reports zero\.
- Source metadata MUST survive downstream storage and API responses\.
- Measurement time MUST be used for domain reasoning; receive time and sequence support ordering/deduplication\.
- Units MUST be normalized before intelligence\.
- Data provenance MUST be retained for external datasets used in exposure/geospatial computation\.
- Synthetic ground\-truth labels MUST remain outside the intelligence input path\.

# 7\. Interface Requirements

## 7\.1 Minimum API surface

__Endpoint family__

__Required behavior__

POST /api/v1/telemetry

Accept canonical authenticated telemetry from hardware/simulation\.

GET /api/v1/nodes

Return node/network state\.

GET /api/v1/nodes/\{node\_id\}

Return detailed node status/diagnostics\.

GET /api/v1/incidents

Return filtered incident list\.

GET /api/v1/incidents/\{incident\_id\}

Return canonical incident context\.

GET /api/v1/incidents/\{id\}/spread

Return current/projection geospatial outputs\.

GET /api/v1/incidents/\{id\}/exposure

Return current/warning/projection exposure\.

GET /api/v1/incidents/\{id\}/actions

Return response recommendations/actions\.

POST /api/v1/actions/\{id\}/approve

Explicit operator approval gate\.

POST /api/v1/actions/\{id\}/status

Update response lifecycle state\.

GET /api/v1/alerts

Return alert lifecycle records\.

POST /api/v1/alerts/\{id\}/standdown

Stand\-down where authorized\.

POST /api/v1/sos

Create authenticated SOS\.

GET /api/v1/sos

Return SOS queue according to authorization\.

POST /api/v1/simulation/scenarios

Create scenario\.

POST /api/v1/simulation/scenarios/\{id\}/start

Start synthetic telemetry generation\.

POST /api/v1/simulation/scenarios/\{id\}/stop

Stop scenario\.

## 7\.2 Real\-time

The authority dashboard SHOULD use an event stream such as WebSocket/SSE for live state changes\. Event messages MUST identify the event type, target entity, timestamp and relevant payload/version\. The citizen page SHOULD update without full reload while preserving a visible freshness indicator\.

## 7\.3 API ownership rules

- Backend owns canonical domain calculations\.
- Frontend can transform presentation format but MUST NOT create competing domain calculations\.
- Geospatial service outputs are derived from authoritative backend/domain state\.
- Simulation control creates telemetry/events; it does not directly mutate dashboard state\.

# 8\. User & UI Requirements

## 8\.1 Authority

__ID__

__Requirement__

UR\-001

Overview MUST answer what needs attention now\.

UR\-002

Information Condition MUST be visible on incident command cards\.

UR\-003

Explain MUST show operator\-readable evidence reasons and optionally advanced technical values\.

UR\-004

Map MUST distinguish nodes, incidents, physical footprints, operational buffers, risk surfaces, exposure, SOS and projections\.

UR\-005

LIVE/SIMULATION mode MUST be visually persistent when simulation is active\.

UR\-006

Risk/heatmap layers MUST be overlays, not a misleading standalone 'risk score' page\.

UR\-007

Critical actions and SOS MUST remain reachable without deep navigation\.

UR\-008

Stale/degraded/unknown data MUST be visible\.

## 8\.2 Citizen

__ID__

__Requirement__

UR\-020

Emergency experience MUST be a single\-page, action\-first interface\.

UR\-021

First viewport MUST prioritize hazard, urgency, state, distance/direction, freshness and immediate action\.

UR\-022

Raw anomaly/confidence/risk formulas MUST NOT be the default citizen presentation\.

UR\-023

Recommended safe route MUST be clearly differentiated from an official authority route\.

UR\-024

No viable route MUST yield SHELTER\_IN\_PLACE\.

UR\-025

SOS MUST remain accessible\.

UR\-026

Resolved/stand\-down state MUST be explicit\.

UR\-027

Offline/local mode MUST use the same emergency event semantics as online mode\.

# 9\. Operational State Requirements

## 9\.1 Hazard state

__State__

__Required semantics__

NORMAL

No current actionable abnormality\.

WATCH

Evidence warrants observation\.

SUSPECTED

Potential hazard; still requires verification\.

CONFIRMED

Evidence supports a credible hazard assessment\.

CRITICAL

Immediate life\-safety/operational attention may be required\.

RESOLVED

Hazard condition has been cleared under configured policy/authority workflow\.

## 9\.2 Response state

__State__

__Meaning__

RECOMMENDED

System has suggested an action\.

APPROVED

Authorized human approved action\.

NOTIFIED

Target was notified\.

ACKNOWLEDGED

Recipient acknowledged where supported\.

ASSIGNED

Response responsibility assigned\.

EN\_ROUTE

Responder is moving\.

ON\_SCENE

Responder arrived\.

COMPLETED

Action completed\.

REJECTED

Operator declined recommendation\.

CANCELLED

Approved action cancelled\.

EXPIRED

Action validity window ended\.

__Approval invariant  
__RECOMMENDED is not execution\. No system path may bypass APPROVED before operational notification/dispatch state transitions\.

# 10\. Resilience & Degraded Behavior Requirements

__Scenario__

__MUST happen__

__MUST NOT happen__

Internet unavailable

Local node/Master capabilities continue where designed; data buffers\.

Silent loss of state or false 'live' indicator\.

Master unavailable

Node/local gateway still serves the local emergency page path\.

Citizen emergency access depending exclusively on Master\.

One node fails

Other nodes continue; failed node becomes stale/unavailable\.

Regional system crashing because of one node\.

Sensor unavailable

Contribution becomes unavailable/low reliability\.

Missing value converted to zero\.

Wind unavailable

Explicit calm/assumed\-wind policy may be used if configured and labeled\.

Stale/unknown wind silently treated as fresh\.

DEM unavailable

Configured flat\-terrain fallback may be used if explicitly enabled and labeled\.

Terrain\-dependent output presented as exact\.

Population source unavailable

Exposure shown as unavailable\.

Exposure shown as zero\.

Malformed telemetry

Reject and log\.

Malformed data reaching hazard engine\.

Invalid HMAC

Reject and log security event\.

Processing untrusted packet\.

Stale alert

Mark stale and show freshness state\.

Present stale state as live\.

No safe route

Return SHELTER\_IN\_PLACE\.

Generate route through danger\.

# 11\. Verification & Acceptance Requirements

Every MUST requirement requires evidence\. Evidence can be an automated test, integration test, hardware benchmark, recorded demonstration, dataset provenance record, or code/configuration inspection where appropriate\.

__Evidence type__

__Use__

Unit test

Formula/state/schema logic in isolation\.

Integration test

Module\-to\-module contracts\.

System test

End\-to\-end behavior through canonical pipeline\.

Hardware test

Real ESP32/sensor/network behavior\.

Geospatial fixture test

Known terrain/geometry/distance/area cases\.

Security test

HMAC/signature/replay/authorization cases\.

Performance benchmark

Latency/runtime/resource measurements\.

Demo acceptance test

Judge\-visible critical workflows\.

Provenance record

External dataset source/version/processing\.

## 11\.1 Mandatory pre\-freeze verification gates

- Gas sensor component finalized and documented\.
- ESP32 concurrency benchmark completed with sensing \+ Wi\-Fi AP \+ telemetry \+ local processing\.
- Node\-to\-Master HMAC implemented and invalid/replay behavior verified\.
- Incident merge/split rules implemented and tested\.
- Master\-death local emergency access verified by physically powering off the Master\.
- Human approval gate verified to block unapproved operational actions\.
- SHELTER\_IN\_PLACE behavior verified in a no\-safe\-route scenario\.
- Fire\-spread mathematical corrections verified: FROM→TO, √2 diagonal, wind\+slope vectoring, projected CRS, mid\-run recomputation\.
- Operational buffer is visually and semantically separate from physical footprint\.
- Multi\-hazard risk surfaces remain separate\.
- Synthetic telemetry passes through the same ingestion path as hardware\.

# 12\. Requirement Traceability

__Requirement group__

__Primary implementation spec__

__Primary verification source__

FR\-001–007

06 Hardware/Edge \+ 07 Backend

17 Validation

FR\-010–021

04 Intelligence

17 Validation

FR\-030–036

10 Incident/Response

17 Validation

FR\-040–053

05 Fire/Geospatial

17 Validation

FR\-060–064

08 Data \+ Exposure modules

17 Validation

FR\-070–080

10 Incident/Response \+ 11 Communication \+ 14 Citizen

17 Validation

NFR\-001–006

01 Master \+ 11 Communication

17 Validation

NFR\-010–025

03 Technology/Deployment \+ 17 Validation

17 Validation

NFR\-030–036

16 Security

17 Validation

UR\-001–008

13 Dashboard \+ 12 UI/UX

17 Validation

UR\-020–027

14 Citizen \+ 11 Communication \+ 12 UI/UX

17 Validation

# 13\. Coding\-Agent / Vibe\-Coding Rules

## 13\.1 General implementation rules

- Implement requirements by ID rather than by vague feature name\.
- Before changing a shared data contract, check all consumers and update the canonical contract first\.
- Do not introduce a second representation of an incident, hazard state, or emergency event unless the architecture explicitly calls for a view model\.
- Keep tunable parameters in configuration rather than hard\-coding them across modules\.
- Do not introduce an ML model simply to satisfy the term 'AI' when deterministic reasoning is the locked V1 choice\.
- Do not invent data when a source is unavailable; return unavailable/unknown according to the specified failure behavior\.
- Do not compute canonical risk, spread, exposure, or response decisions in the frontend\.
- Do not bypass the telemetry ingestion path for simulations\.
- Do not bypass the human approval gate\.
- Record source metadata for synthetic vs hardware vs external data\.
- If a requirement cannot be met on the chosen compute target, stop and document the constraint before replacing the architecture\.
- When Python and embedded C/C\+\+ implement the same mathematical function, use the Python version as the reference implementation and verify embedded results using golden test vectors\.
- Every new domain state or event type must have an explicit state\-transition rule and persistence/audit behavior\.
- Every user\-visible failure state must have a defined UX representation\.

## 13\.2 Definition of Done for a requirement

1. Requirement implementation exists in the correct module\.
2. Input/output contract is documented and typed/validated\.
3. Failure/degraded behavior exists\.
4. Automated or recorded verification evidence exists\.
5. Relevant UI/API/data contract is updated\.
6. No architecture invariant is violated\.
7. Requirement ID is marked complete in the implementation tracker\.

# 14\. Requirements vs Parameters

This TRD intentionally does not freeze arbitrary scientific constants\. Requirements define structural behavior; the separate configuration/parameter registry will define tunable values after validation\.

__Example__

__Requirement\-level rule__

__Parameter\-level value__

Incident correlation

Same hazard within configured spatial \+ temporal window merges\.

Spatial radius / time window\.

Heartbeat

Node MUST report heartbeat and stale state MUST be detectable\.

Heartbeat interval / stale timeout\.

Risk surface

Must use defined urgency/intensity/trend inputs\.

Weights / thresholds\.

Fire projection

Projection derives from arrival\-time field\.

Projection horizon\.

SHELTER\_IN\_PLACE

No viable safe route MUST trigger fallback\.

Route hazard threshold\.

Baseline

Confirmed/critical MUST freeze baseline adaptation\.

Learning rates / windows\.

Response escalation

Unacknowledged action MAY escalate\.

Timeouts\.

__No magic numbers  
__Thresholds, weights, timeout windows, grid size, projection horizon, heartbeat interval, retry limits and similar tunables MUST have a named configuration entry with unit, rationale, owner, range and validation status\.

# 15\. V1 Scope Freeze

__Feature__

__V1 status__

__Requirement consequence__

Fire detection \+ reasoning

MUST

Primary validated hazard\.

Flood pathway

MUST

Second validation pathway using same framework\.

Other hazards

FRAMEWORK\-SUPPORTED

Only claim what evidence supports\.

Fire spread

MUST

Physics\-informed, documented assumptions\.

Risk/heatmap

MUST

Separate operational index, not probability\.

Exposure

MUST where displayed

Requires sourced datasets\.

Authority dashboard

MUST

Core product surface\.

Citizen web/local experience

MUST

Core product surface\.

SOS

MUST

Core safety capability\.

Human response approval

MUST

Hard safety/product invariant\.

Master\-death local page

MUST

Resilience requirement\.

Native app

DEFERRED

Does not block prototype\.

Advanced ML

DEFERRED

Only where data justifies\.

Full self\-healing mesh

ROADMAP

Basic buffering/reconnect in V1\.

Satellite live feeds

DEFERRED

No dependency for local intelligence\.

3D

OUT

Not required\.

Microservices/Kafka

OUT

Not required for V1\.

# 16\. Final TRD Compliance Checklist

__☐ 01  __All MUST functional requirements implemented and tested\.

__☐ 02  __All critical non\-functional requirements have measurable verification evidence\.

__☐ 03  __Telemetry schema and timestamp semantics are consistent end\-to\-end\.

__☐ 04  __Node\-to\-Master HMAC is active\.

__☐ 05  __Incident correlation merge/split is deterministic and tested\.

__☐ 06  __Fire\-spread mathematical fixes are implemented, not merely documented\.

__☐ 07  __Physical footprint and operational buffer are separate\.

__☐ 08  __Risk surfaces remain independently toggleable\.

__☐ 09  __Exposure values use real/provenanced data or explicit unavailability/synthetic labels\.

__☐ 10  __Response recommendations cannot execute without human approval\.

__☐ 11  __Citizen no\-safe\-route behavior returns SHELTER\_IN\_PLACE\.

__☐ 12  __Master failure does not eliminate the local emergency page path\.

__☐ 13  __Simulation enters the same telemetry ingestion and downstream pipeline\.

__☐ 14  __Dashboard and citizen surfaces use backend domain truth\.

__☐ 15  __Configuration contains named tunable parameters; no unexplained magic constants\.

__☐ 16  __Validation evidence is linked to requirement IDs\.

# 17\. Final Position

__TRD baseline  
__This TRD is the requirements contract between the frozen NexAlert architecture and the implementation team\. It intentionally separates mandatory behavior from tunable parameters and separates domain truth from presentation\. The implementation should proceed by requirement ID, with the downstream mathematical, hardware, data, backend, resilience, UI and validation specifications providing the detailed how\.

The next engineering document is Document 03 — Technology Stack, Deployment & Compute Allocation\. That document will lock exact technologies, runtime boundaries, ESP32 versus Raspberry Pi responsibilities, Python reference versus embedded C/C\+\+ implementation, database/frontend/backend choices, packaging, environments, and deployment topology\.

