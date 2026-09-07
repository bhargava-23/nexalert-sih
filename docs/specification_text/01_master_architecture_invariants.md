__NEXALERT__

__MASTER SYSTEM ARCHITECTURE & ARCHITECTURE INVARIANTS__

Final Engineering Specification — V1 Architecture Freeze Baseline

__Document purpose  
__This document is the master source of truth for the NexAlert product architecture\. It defines what the product is, how the complete system works end\-to\-end, which subsystem owns each responsibility, how data moves, how the system behaves under failure, and which architectural rules are non\-negotiable during implementation\.

__Field__

__Value__

Product

NexAlert

SIH Problem Statement

SIH26178 — Resilient AI\-powered environmental monitoring and early warning

Document

01 — Master System Architecture & Architecture Invariants

Status

FINAL ARCHITECTURE BASELINE

Audience

Engineering team, hardware team, software team, coding agents, reviewers, SIH judges

Primary use

Implementation reference and architectural guardrail

Scope

Prototype/V1 architecture with explicit V2/roadmap boundaries

__Implementation rule  
__No implementation decision may silently contradict this document\. If a real implementation constraint forces a change, the change must be documented, reviewed, and reflected here before downstream specifications are updated\.

# Document Control & Navigation

__Version__

__Status__

__Purpose__

1\.0

FINAL BASELINE

Architecture freeze after brainstorming and adversarial review

1\.x

Controlled change

Only approved clarifications or implementation\-driven changes

## How to use this document

1. Read this document first before implementing any NexAlert subsystem\.
2. Use the architecture invariants as hard constraints when making design or coding choices\.
3. Use subsystem\-specific final specifications for implementation detail\. Those documents must not redefine architecture in conflict with this document\.
4. Treat terms such as Incident, Hazard State, Physical Footprint, Operational Buffer, Confidence, Severity, Operational Risk, and Information Condition as canonical terms\.
5. Treat real hardware data and synthetic telemetry as two sources entering the same post\-ingestion processing pipeline\.

## Document map

__Section__

__Topic__

1

Product definition and design principles

2

System scope and responsibilities

3

Complete end\-to\-end product flow

4

Layered architecture

5

Field node and edge architecture

6

Master / local\-gateway architecture

7

Backend and cloud architecture

8

Intelligence architecture

9

Hazard, incident, and geospatial architecture

10

Exposure and operational decision architecture

11

Citizen and authority product surfaces

12

Communication and resilience

13

Simulation and replay

14

Security and trust

15

Persistence, events, and audit

16

Technology and deployment boundaries

17

Failure and degraded\-operation model

18

Canonical data\-flow contracts

19

Architecture invariants

20

V1 scope, non\-goals, and roadmap

21

Implementation ownership matrix

22

End\-to\-end example

23

Acceptance gates before calling architecture implemented

# 1\. Product Definition

## 1\.1 What NexAlert is

NexAlert is a resilient, distributed environmental monitoring and early\-warning platform designed to detect developing hazards from real sensor evidence, reason about the quality and reliability of that evidence, convert credible hazard states into geospatially meaningful impact information, and provide actionable information to authorities and nearby communities\.

The platform is intentionally designed as a complete decision\-support loop rather than a sensor dashboard\. A sensor reading by itself is not the product\. The product is the chain from sensing to trustworthy interpretation to spatial consequence to human action\.

__Product sentence  
__A disaster sensor network that keeps making trustworthy decisions even when it is operating with degraded connectivity, and clearly communicates uncertainty when the evidence is insufficient\.

## 1\.2 Product pillars

__Pillar__

__Meaning in the implemented system__

__Concrete evidence__

Access

People can reach emergency information without requiring a mandatory native app or permanent cloud dependency\.

Local NexAlert Wi\-Fi/captive portal path; web/PWA experience; accessible emergency page\.

Resilience

The system continues useful local operation during connectivity loss and supports store\-and\-forward recovery\.

Node/Master buffering, local networking, reconnection sync, explicit degraded state\.

Intelligence

The system evaluates health, quality, anomaly, evidence, confidence, severity, risk, and state rather than merely displaying readings\.

Health/quality/reliability pipeline; deterministic hazard reasoning; explainability\.

## 1\.3 Problem framing

NexAlert addresses a class of disaster\-management problem where environmental signals can be noisy, incomplete, delayed, contradictory, or locally unavailable\. The architecture therefore treats uncertainty and failure as first\-class operating conditions rather than exceptional bugs\.

- Distributed sensing provides localized evidence rather than relying on a single central observation\.
- Edge/local processing allows hazard reasoning to continue when upstream connectivity is lost\.
- Evidence quality and sensor reliability are kept separate from hazard severity and operational risk\.
- Geospatial reasoning turns an incident into a changing area, risk surface, exposure, and operational context\.
- Authority actions are recommended and tracked; NexAlert does not autonomously dispatch emergency responders\.
- Citizen communication is designed as a safety surface with explicit safe\-route and shelter\-in\-place fallbacks\.

# 2\. System Scope & Responsibility Boundaries

## 2\.1 System boundary

The system begins at physical/environmental sensing and ends at human\-facing warning, authority decision support, response workflow, and historical/audit evidence\. It includes field hardware, local connectivity, ingestion, intelligence, geospatial simulation, exposure analysis, response management, alert delivery, citizen interaction, authority dashboards, simulation, and persistence\.

The system does not claim to replace government command structures, field responders, official emergency communication authorities, or full operational wildfire/flood forecasting systems\.

## 2\.2 High\-level ownership

__Subsystem__

__Primary responsibility__

__Must NOT own__

Field Node

Sense, self\-test, basic filtering, diagnostics, local networking, buffering, authenticated telemetry\.

Large geospatial simulation, population analysis, authority dispatch decisions\.

Master / Local Gateway

Aggregate node data, local intelligence where enabled, local service continuity, buffering, synchronization\.

Permanent authority of truth for cloud history when disconnected; it reconciles on reconnect\.

Telemetry Ingestion

Validate, authenticate, normalize, timestamp, deduplicate, persist canonical telemetry\.

Hazard interpretation\.

Intelligence Engine

Health, quality, reliability, baseline, anomaly, evidence, confidence, severity, risk, state\.

UI rendering, geospatial polygonization, autonomous dispatch\.

Incident Manager

Create, correlate, update, merge/split under defined policy, resolve incidents\.

Raw sensor correction\.

Fire/Geospatial Engine

Terrain, fuel, moisture, wind/slope, spread, arrival\-time field, footprint, buffer, risk surface, geometry\.

Sensor trust and authority response policy\.

Exposure Engine

Population, citizens, roads, schools, hospitals, infrastructure overlay\.

Hazard physics\.

Response Engine

Recommend response actions and priorities; track approval and operational progress\.

Autonomous dispatch\.

Alert Layer

Fan out canonical emergency events through available communication channels\.

Invent hazard state\.

Citizen UI

Display safe, plain\-language information and SOS controls\.

Recompute hazard or risk\.

Authority Dashboard

Operational visualization, acknowledgement, action workflow, investigation, audit\.

Recompute domain truth\.

Simulation

Generate synthetic telemetry/scenarios and replay them through the same pipeline\.

Use a parallel intelligence path\.

# 3\. Complete End\-to\-End Product Flow

## 3\.1 Master flow

REAL HARDWARE PATH  
Sensors → ESP32 Node → authenticated telemetry → Local/Master → Ingestion  
→ Health/Quality/Reliability → Baseline/Anomaly → Hazard Reasoning  
→ Incident Manager → Geospatial/Spread/Risk → Exposure  
→ Response Recommendation → Human Approval → Alerts/Actions  
→ Authority Dashboard \+ Citizen Experience → Audit/History  
  
SIMULATION PATH  
Scenario Generator → canonical telemetry payload → SAME INGESTION  
→ SAME INTELLIGENCE → SAME INCIDENT → SAME GEOSPATIAL  
→ SAME EXPOSURE → SAME RESPONSE → SAME UI/ALERT PATH  
  
OFFLINE PATH  
Sensors → Node → Local buffering / local intelligence → Local emergency network  
→ Local authority/citizen access  
→ reconnect → reconciliation → cloud synchronization

## 3\.2 The product loop in plain language

1. A field node measures environmental signals and reports them with timestamps, diagnostics, sequence information, and authenticated identity\.
2. The ingestion layer checks that the data is valid, not spoofed, not duplicated, and expressed in canonical units\.
3. The intelligence layer estimates whether each sensor is healthy, whether the signal is trustworthy, whether the measurement is anomalous relative to a baseline, and how those observations combine into hazard evidence\.
4. The hazard reasoning layer produces a hazard\-specific state such as NORMAL, WATCH, SUSPECTED, CONFIRMED, or CRITICAL plus confidence, severity, operational risk, and an information condition\.
5. The incident manager determines whether the event belongs to an existing incident or should create a new incident using deterministic spatial/temporal correlation\.
6. For fire, the geospatial engine calculates how the hazard can propagate using terrain, fuel, moisture, wind, and slope, then generates arrival times, footprints, projections, and derived risk surfaces\.
7. The exposure engine overlays hazard geometry with real population and infrastructure data and classifies current, warning, and projected exposure\.
8. The response engine converts the incident context into categorical operational recommendations such as MONITOR, VERIFY, NOTIFY, DISPATCH RECOMMENDATION, URGENT RESPONSE, or PUBLIC WARNING\.
9. A human authority operator approves or rejects actions\. NexAlert does not autonomously dispatch responders\.
10. The alert layer creates one canonical emergency event and delivers it through the available citizen/authority channels\.
11. The citizen surface provides simple action guidance, map context, safe\-place/route information, and SOS\. If no viable route exists, it returns SHELTER\_IN\_PLACE rather than inventing a dangerous route\.
12. Every important state change and operator action is recorded for auditability and later validation\.

## 3\.3 What makes this a product rather than a collection of demos

- All components share canonical entities and data contracts\.
- Simulation is not a second application; it is an alternate telemetry source\.
- The same incident can drive geospatial analysis, authority response, citizen alerts, and audit history\.
- Failure states are explicit and propagated rather than hidden behind zeros or silent fallbacks\.
- The authority and community experiences are both connected to the same underlying event\.

# 4\. Layered Architecture

## 4\.1 Twenty\-layer architecture

__\#__

__Layer__

__Inputs__

__Core logic__

__Outputs__

__Failure__

__Degraded behavior__

__Source of truth__

1

Field node \+ sensors

Raw sensor readings, diagnostics

Sampling, self\-test

Raw telemetry \+ diagnostics

Sensor dead

Hard\-gate failed sensor

Node hardware

2

Local connectivity \+ Master

LoRa/Wi\-Fi/local link

Routing, heartbeat, buffering

Delivered telemetry

Link lost

Local buffer/store\-forward

Link state

3

Telemetry ingestion

Raw signed payload

Validate, dedup, HMAC verify, normalize

Canonical telemetry

Malformed/spoofed

Reject \+ log

Ingestion record

4

Health/Quality/Reliability

Telemetry \+ diagnostics

H, Q, R computation

Reliability\-weighted signal

Diagnostic conflict

Lower reliability

Intelligence state

5

Baseline/Anomaly

Reliable readings

Robust baseline \+ anomaly logic

A\_i \+ baseline state

Baseline not ready

Learning / unavailable anomaly

Baseline state machine

6

Hazard reasoning

Features/anomaly/reliability

Hazard\-specific reasoning

E\_h,C\_h,S\_h,R\_h,state

Evidence conflict

DEGRADED/UNKNOWN

Hazard state

7

Incident manager

Node hazard states

Spatial/temporal correlation

Incident entity

Ambiguous merge

Create new incident \+ flag

Incident store

8

Fire spread engine

Ignition, wind, terrain, fuel, moisture

Directional ROS \+ arrival\-time propagation

Arrival\-time field

Missing input

Labeled assumption / degraded

Arrival field

9

Affected geometry

Arrival\-time field

Thresholding \+ polygonization \+ validity repair

Current/warning/projection \+ buffer

Invalid geometry

Repair or flag

Raster truth

10

Risk/heatmap

Arrival\-time \+ intensity

Spatial risk index

Hazard risk surface

Degraded info

Uncertain label

Risk surface

11

Exposure

Geometry \+ real datasets

Spatial overlay

Population/infrastructure counts

Dataset unavailable

Explicit unavailable

Source dataset

12

Response/action

Incident \+ exposure \+ SOS

Policy rules \+ categorical priority

Recommendation \+ actions

Ambiguous priority

VERIFY; never auto\-dispatch

Response state

13

Authority dashboard

Domain state

Render \+ interact

Operator UI

Stale data

Visible staleness

Backend domain state

14

Citizen interface

Incident \+ routing \+ alerts

Plain\-language render

Emergency experience

Route unavailable

SHELTER\_IN\_PLACE

Backend domain state

15

SOS

Citizen input

Tiering \+ dedup

SOS record

Repeated presses

Consolidate, preserve history

SOS store

16

Alerts/communications

Canonical event

Fan\-out \+ delivery tracking

Alert records

Channel failure

Fallback channel

Alert log

17

Persistence/audit

State changes

Immutable/append\-only records

History \+ audit

Write failure

Retry queue

Audit store

18

Offline/store\-forward

Buffered telemetry/events

Queue \+ reconciliation

Synced state

Master failure

Node/local gateway continuity

Local buffer

19

Security/auth

Keys \+ signatures

HMAC and event\-signing verification

Trust decisions

Invalid auth

Reject \+ flag

Key store

20

Simulation/replay

Synthetic telemetry

Same path as live

Same outputs, SIMULATION\-tagged

Mislabeled data

Persistent simulation banner

Source metadata

# 5\. Field Node & Edge Architecture

## 5\.1 Node responsibility

The ESP32\-class field node is the physical sensing and resilient edge endpoint\. It is deliberately kept lightweight\. Its job is to sense, validate basic electrical/sensor conditions, package trustworthy telemetry, maintain identity and communication, buffer data during outages, support local emergency networking where required, and run only those intelligence functions that are computationally appropriate for the embedded platform\.

## 5\.2 Node responsibilities

- Sensor acquisition and timestamping\.
- Basic filtering and signal conditioning where appropriate\.
- Sensor diagnostics and self\-test status\.
- Heartbeat reporting\.
- Battery reporting as a separate subsystem from sensor health\.
- Communication management and reconnect logic\.
- Per\-node authenticated telemetry using a provisioned secret and HMAC\.
- Sequence numbers for ordering/deduplication\.
- Local buffering during communication loss\.
- Local emergency page/gateway capability needed for Master\-independent citizen access\.
- Selected lightweight anomaly or threshold logic only when explicitly assigned to the embedded implementation\.

## 5\.3 Node non\-responsibilities

- No large fire\-spread raster simulation\.
- No population/infrastructure spatial analysis\.
- No route optimization across a geographic network\.
- No authority dispatch decision\.
- No replacement of the canonical backend intelligence model\.

__Embedded intelligence rule  
__The mathematical specification is shared, but implementation may differ by compute target\. Python is the reference implementation for server\-side intelligence; C/C\+\+ is the embedded implementation on ESP32 where local intelligence is required\. Golden\-vector tests must compare the two implementations within defined tolerances\.

# 6\. Master / Local Gateway Architecture

## 6\.1 Purpose

The Master is the local coordination and compute point for the field network\. In the prototype it may be a Raspberry Pi\-class computer\. It aggregates field data, can run the heavier local domain services, maintains local continuity, and synchronizes with the cloud/backend when connectivity is available\.

## 6\.2 Master responsibilities

- Receive authenticated node telemetry\.
- Maintain node/network status\.
- Run or host the modular backend services required for local autonomy\.
- Run geospatial computation locally when configured\.
- Persist local events required for continuity\.
- Expose authority\-local UI access\.
- Coordinate store\-and\-forward synchronization\.
- Publish updated incident and action state to connected clients\.

## 6\.3 Master failure model

Master failure is not equivalent to internet failure\. The architecture explicitly distinguishes them\. If the Master is powered off or otherwise dead, the local emergency citizen path must remain available through the field node or a lightweight local gateway function\. This is a mandatory resilience capability, not merely a demo convenience\.

CONNECTIVITY FAILURE  
Internet/cloud unavailable  
→ Master remains alive  
→ local intelligence and local service continue  
→ data buffered  
→ reconnect → reconcile → sync  
  
MASTER FAILURE  
Master physically unavailable  
→ node/local gateway remains available  
→ local emergency page remains reachable  
→ node buffers telemetry/events  
→ Master recovery → reconciliation  
  
NODE FAILURE  
One node unavailable  
→ other nodes continue  
→ stale/dead node marked unavailable  
→ incident confidence may degrade if that node was core evidence

# 7\. Backend & Cloud Architecture

## 7\.1 Deployment philosophy

For the SIH prototype, NexAlert uses a modular monolith with background workers rather than a distributed microservice deployment\. The architecture remains modular in code and domain ownership, but deployment complexity is intentionally limited\.

## 7\.2 Logical backend modules

backend/  
  ingestion/  
  security/  
  intelligence/  
  hazards/  
  incidents/  
  geospatial/  
    terrain/  
    fire\_spread/  
    affected\_area/  
    risk/  
    exposure/  
  response/  
  alerts/  
  sos/  
  simulation/  
  users/  
  audit/  
  api/  
  workers/  
  common/

## 7\.3 Synchronous vs asynchronous work

__Execution type__

__Typical work__

Near\-real\-time / synchronous

Telemetry validation, authentication, normalization, health/quality, anomaly/evidence update, incident state update\.

Background / asynchronous

Large spread calculations, population exposure, route computation, alert fan\-out, historical aggregation\.

Interactive

Dashboard drill\-down, citizen map, operator approval, simulation control\.

## 7\.4 Source\-of\-truth rule

The backend/domain state is authoritative for incident, hazard, response, and exposure status\. Frontends may cache and render this state, but they must not independently create a competing version of the truth\.

# 8\. Intelligence Architecture

## 8\.1 Intelligence chain

Canonical telemetry  
  ↓  
Validation \+ authentication  
  ↓  
Sensor Health H\_i  
  ↓  
Signal Quality Q\_i  
  ↓  
Reliability R\_i  
  ↓  
Baseline state B\_i  
  ↓  
Anomaly A\_i  
  ↓  
Hazard evidence E\_h  
  ↓  
Evidence confidence C\_h  
  ↓  
Severity S\_h  
  ↓  
Operational risk R\_h  
  ↓  
Hazard state  
  ↓  
Information Condition  
  ↓  
Incident Manager

## 8\.2 Canonical conceptual quantities

__Quantity__

__Meaning__

__Must not be confused with__

H\_i

Sensor health based on diagnostics/hard\-failure state\.

Battery percentage or signal anomaly\.

Q\_i

Signal quality/integrity/stability\.

Hazard confidence\.

R\_i

Evidence reliability after health, quality, and calibration/context factors\.

Operational risk\.

A\_i

Bounded anomaly magnitude relative to an appropriate baseline\.

Probability of hazard\.

E\_h

Hazard\-specific evidence from the relevant sensor/features\.

Calibrated probability unless explicitly calibrated\.

C\_h

Confidence in the evidence assessment\.

Severity\.

S\_h

Hazard severity index\.

Probability\.

R\_h

Operational risk index considering consequence/context\.

Physical intensity or probability\.

Information Condition

How trustworthy/current/complete the available information is\.

Hazard severity\.

Hazard State

Operational state of the hazard evidence\.

Response action\.

__Mathematical authority  
__The complete formulas and parameter definitions live in Document 04 — Mathematical Intelligence & Hazard Reasoning Specification\. This master document fixes ownership and conceptual separation; it does not redefine those formulas\.

# 9\. Hazard, Incident & Geospatial Architecture

## 9\.1 Hazard vector

Each telemetry assessment may evaluate multiple hazards independently\. A single sample can result in a vector such as Fire=CONFIRMED, Flood=NORMAL, Pollution=WATCH, Landslide=UNKNOWN\. Multi\-hazard behavior is not represented by a single universal hazard score\.

## 9\.2 Incident entity

An Incident is the persistent representation of a real\-world or simulated hazard situation\. It may receive evidence from multiple nodes and across time\. Its lifecycle is independent from the lifecycle of any individual sensor packet\.

## 9\.3 Incident correlation rule

For V1, reports of the same hazard type are correlated into one incident when they fall within a configured spatial radius and temporal window\. If either boundary is exceeded, a new incident is created\. This is deterministic and intentionally avoids a complex clustering model during the SIH prototype\.

same hazard  
AND distance\(report, existing\_incident\) <= spatial\_threshold  
AND time\_delta <= temporal\_threshold  
→ attach to existing incident  
  
otherwise  
→ create new incident

## 9\.4 Fire geospatial chain

Ignition  
  ↓  
DEM → slope/aspect  
Fuel raster → fuel behavior  
Moisture/context → moisture response  
Wind → FROM→TO conversion \+ midflame adjustment  
  ↓  
Wind/slope vector combination  
  ↓  
Directional ROS  
  ↓  
Arrival\-time field  
  ↓  
Current footprint / warning / projection  
  ↓  
Geometry validity \+ MultiPolygon  
  ↓  
Operational safety buffer \(policy, not physics\)  
  ↓  
Hazard Risk Surface / heatmap  
  ↓  
Exposure overlays

## 9\.5 Geometry truth

The arrival\-time raster/field is the primary geometric source of truth\. Polygons are derived representations for display, targeting, and area statistics\. The physical fire footprint is distinct from any operational buffer or policy margin\.

## 9\.6 Risk truth

The Hazard Risk Surface is an operational index derived from spatial urgency/time\-to\-arrival and local hazard intensity/trend inputs\. It is not a calibrated probability unless a future version is explicitly validated as one\.

__Multi\-hazard rule  
__Each hazard risk surface remains independently addressable and toggleable\. The system must never create a misleading universal multi\-hazard scalar by algebraically adding or averaging unrelated hazard risk surfaces\.

# 10\. Exposure & Operational Decision Architecture

## 10\.1 Exposure

Exposure is a consequence/context layer, not the same thing as physical hazard intensity\. Population, registered citizens, buildings, roads, schools, hospitals, and other infrastructure are spatially overlaid against current, warning, and projected geometries\.

- Current, warning, and projected exposure are kept separately\.
- Nested zones must not be naively summed\.
- Unavailable population/infrastructure data must never be represented as numeric zero\.
- Real datasets are required for any displayed real\-world exposure number\.

## 10\.2 Response

The response engine converts incident state, severity, operational risk, trend, information condition, exposure, SOS context, and response status into an operational recommendation\. It does not directly dispatch responders\.

INCIDENT CONTEXT  
    ↓  
Response Recommendation  
    ↓  
Human Approval Gate  
    ↓  
Approved Action  
    ↓  
Notification / Assignment / Response Tracking

__Hard product invariant  
__NexAlert recommends\. A human approves and acts\. There is no autonomous dispatch path, including no special 'demo mode' exception\.

# 11\. Product Surfaces

## 11\.1 Authority experience

The authority dashboard is an operational command surface\. Its primary question is: What needs my attention now, why, where, how certain is the information, what is exposed, and what action is pending?

- Overview: live operational map, active incidents, nodes, Master/network health, risk overlays, SOS, current alerts\.
- Incidents: incident list, command card, evidence explanation, timeline, state and information condition\.
- Fire Spread: LIVE/SIMULATION, current footprint, projected spread, time controls, environment context\.
- Affected Area & Impact: current/warning/projection zones, population, roads, schools, hospitals, critical infrastructure\.
- Multi\-Hazard & Simulation: independent hazard layers plus same\-pipeline synthetic scenarios\.
- Nodes & Network: health, battery, link state, heartbeat, topology/isolation\.
- Telemetry & Intelligence: raw telemetry through the intelligence chain\.
- Citizen SOS: map, queue, categorical priority, profile/contact actions\.
- Alert Management: issued alerts, delivery state, escalation/stand\-down\.
- Historical Analysis: incidents, trends, response times, node reliability, outcomes\.
- Response & Actions: approved actions and operational state\.
- Audit Trail: immutable history of system/operator changes\.
- System: configuration and system health\.

## 11\.2 Citizen experience

The citizen experience is intentionally one\-page and action\-first\. In emergency mode, the first viewport shows hazard, severity, state, distance/direction, freshness, and the most important recommended action\. The map then shows incident/affected/projected geometry, safe place and route when available\.

- Normal state: nearby status, recent alerts, map, SOS\.
- Emergency state: one clear action, hazard context, live map, safe destination guidance\.
- No viable safe route: SHELTER\_IN\_PLACE\.
- SOS remains available independent of whether a known hazard is active\.
- Plain\-language labels replace raw internal scores by default\.

# 12\. Communication & Resilience Architecture

## 12\.1 Canonical communication graph

Field Node  
  ├─→ Master / local gateway  
  │      ├─→ Local authority UI  
  │      ├─→ Local citizen Wi\-Fi/captive portal  
  │      └─→ Cloud synchronization when online  
  └─→ buffered telemetry/events  
  
Cloud/backend  
  ├─→ Authority dashboard  
  ├─→ Web/push alert channels  
  └─→ Historical/audit storage

## 12\.2 Normal operation

Telemetry moves upward from nodes to the Master/backend\. Domain state changes are then distributed to connected authority clients and alert channels\. One canonical emergency event may drive multiple delivery channels\.

## 12\.3 Offline operation

Offline behavior is designed around useful local autonomy, not the claim that every cloud feature remains available\. Core local detection, local incident state, local emergency access, and buffering continue to the degree supported by the deployed hardware\. Cloud\-dependent history and external notification are clearly marked unavailable until reconnection\.

## 12\.4 Store\-and\-forward

packet generated  
→ sequence \+ measurement timestamp  
→ local buffer  
→ connectivity returns  
→ authenticate  
→ order using receive timestamp \+ sequence rules  
→ deduplicate  
→ domain processing uses measurement timestamp  
→ persist / publish reconciled state

## 12\.5 Degraded information

Degraded connectivity must not silently convert into false freshness\. The system should surface stale data, missing feeds, and information condition changes explicitly\.

# 13\. Simulation & Replay Architecture

## 13\.1 Purpose

Simulation exists to bootstrap software development, validate deterministic logic, rehearse multi\-hazard behavior, inject failure cases, and support a controlled SIH demonstration\. It is not allowed to create a second intelligence implementation\.

## 13\.2 Simulation contract

Scenario definition  
→ synthetic telemetry  
→ POST /api/v1/telemetry  
→ identical validation  
→ identical intelligence  
→ identical incident creation/update  
→ identical geospatial engine  
→ identical exposure  
→ identical response  
→ identical dashboard/citizen outputs

## 13\.3 Synthetic scenario capabilities

- Normal baseline periods\.
- Slow and rapid hazard onset\.
- Correlated multi\-sensor escalation\.
- Sensor noise and drift\.
- Missing measurements and stale packets\.
- Sensor failure and diagnostics changes\.
- Communication outage and recovery\.
- Multi\-node corroboration\.
- Contradictory sensor evidence\.
- Multi\-hazard combinations without collapsing them into one risk number\.

__Simulation honesty  
__Synthetic data can demonstrate that the system behaves correctly under a specified scenario\. It cannot, by itself, validate real\-world sensor accuracy or prove operational disaster prediction accuracy\.

# 14\. Security & Trust Architecture

## 14\.1 Node\-to\-Master trust

Every field node must have a provisioned identity/secret\. Telemetry is authenticated with an HMAC before entering the canonical ingestion pipeline\. Invalid, missing, or tampered authentication is rejected and logged\.

## 14\.2 Citizen/authority event trust

Emergency events may be signed so local clients can verify authenticity and reject stale/replayed messages\. Event IDs, timestamps, nonces/sequence values, and signature verification are part of the trust boundary\.

## 14\.3 Replay/tamper model

tampered packet  
→ HMAC verification fails  
→ reject  
→ audit/security log  
  
replayed packet  
→ sequence/timestamp/idempotency checks  
→ reject duplicate/stale delivery  
  
invalid emergency event signature  
→ reject locally  
→ mark untrusted

## 14\.4 Security scope

V1 uses practical prototype\-grade security: per\-node credentials, HMAC telemetry authentication, application authentication/authorization, signed emergency events, replay protection, and auditable operator actions\. Full enterprise PKI, sophisticated zero\-trust service meshes, and deep RBAC are roadmap items rather than V1 blockers\.

# 15\. Persistence, Events & Audit

## 15\.1 Core entities

__Entity__

__Purpose__

Node

Field device identity, configuration, network status\.

Sensor

Sensor identity, type, calibration/diagnostic metadata\.

Telemetry

Canonical measurement record\.

Sensor Diagnostics

Health/quality inputs and diagnostics\.

Hazard Assessment

Per\-node/per\-hazard reasoning output\.

Incident

Persistent hazard situation\.

Incident Event

Immutable change or occurrence in an incident lifecycle\.

Spread Run

Geospatial fire simulation context and result\.

Exposure Snapshot

Spatial exposure counts by zone and time\.

Action

Authority response recommendation/approved action\.

Alert

Canonical emergency communication event/delivery record\.

Citizen

NexAlert user/contact entity\.

SOS

Citizen distress request\.

Simulation Scenario

Synthetic scenario control and metadata\.

Audit Event

Operator/system action history\.

## 15\.2 Incident vs event

An Incident persists across time\. An Incident Event describes something that happened to that incident: created, state changed, spread updated, exposure increased, action approved, alert issued, response completed, or resolved\.

## 15\.3 Idempotency

Every canonical record that can be retried must have an identifier or deterministic key allowing duplicate detection\. A duplicated telemetry packet must not create a duplicated anomaly event, incident, alert, or action\.

## 15\.4 Auditability

Operator overrides, response approvals, action changes, alert issuance/stand\-down, simulation mode transitions, and system security failures must be auditable\.

# 16\. Technology & Deployment Boundaries

## 16\.1 Technology posture

__Area__

__Primary direction__

__Reason__

ESP32 firmware

ESP\-IDF \+ C/C\+\+

Predictable embedded control, networking, timing, memory behavior\.

Reference intelligence / geospatial

Python

Fast iteration, scientific stack, testing, simulation\.

Master software

Python services

Local compute and reusable backend logic\.

Backend API

FastAPI\-style Python backend

Typed API contracts and rapid development\.

Database

PostgreSQL \+ PostGIS

Transactional state plus native spatial operations\.

Frontend

React/Next\.js \+ TypeScript

Componentized operational UI and strong tooling\.

Styling

Tailwind/CSS

Controlled visual system; glassmorphism design system\.

Real\-time

WebSocket/SSE

Low\-latency operational updates\.

Simulation

Python

Scenario generation and scientific workflows\.

Deployment

Modular monolith \+ workers; containerized where useful

Scope appropriate to a six\-person SIH team\.

## 16\.2 Python vs ESP32

Python is not copied wholesale onto the ESP32 as the default embedded architecture\. Where lightweight intelligence is required on the device, the relevant mathematics is reimplemented in C/C\+\+ against the same specification\. The Python implementation is the reference implementation\. Golden\-vector tests verify equivalence within tolerance\. This prevents the embedded version from becoming an undocumented fork\.

## 16\.3 Compute allocation

__Computation__

__ESP32__

__Master__

__Cloud/backend__

Sensor acquisition

YES

NO

NO

Basic diagnostics

YES

YES/aggregate

YES/aggregate

Heartbeat/buffering

YES

YES

YES

Lightweight embedded anomaly logic

OPTIONAL

YES

YES

Full intelligence chain

LIMITED

YES

YES

Fire spread raster simulation

NO

YES

YES

Population/infrastructure overlay

NO

YES

YES

Routing

NO

YES

YES

Authority workflow

NO

YES

YES

# 17\. Failure, Degraded\-Mode & Recovery Model

__Failure__

__Expected behavior__

__User\-visible condition__

Sensor dead

Hard\-fail the sensor contribution; other evidence continues\.

Sensor unhealthy; information may degrade\.

Sensor drift

Lower quality/reliability or trigger baseline recovery path\.

Evidence confidence may degrade\.

Stale telemetry

Stop silently trusting it; mark stale and update information condition\.

Stale/degraded indicator\.

Contradictory sensors

Use reliability/agreement logic; do not force certainty\.

Preliminary/unclear information\.

Internet down

Local Master/node operation and buffering continue\.

Cloud unavailable/degraded\.

Master dead

Node/local gateway provides emergency page and buffers data\.

Local emergency mode\.

Cloud unavailable

Local domain remains useful; synchronize on return\.

Cloud status unavailable\.

Missing DEM

Use flat\-terrain fallback only if explicitly configured and label it\.

Terrain unavailable\.

Missing wind

Use explicit calm/assumed wind policy; never silent stale substitution\.

Wind assumption/degraded\.

Missing population

Do not display zero; report data unavailable\.

Exposure unavailable\.

Invalid geometry

Attempt geometry validity repair; flag if repair fails\.

Geometry warning\.

No safe route

Return SHELTER\_IN\_PLACE\.

No safe route available\.

Invalid HMAC

Reject packet and log security event\.

Rejected/unauthenticated\.

Duplicate telemetry

Deduplicate without duplicate downstream events\.

No visible duplication\.

Fire reaches map boundary

Clip to domain and state that output is domain\-limited\.

Projection domain edge\.

# 18\. Canonical Data\-Flow Contracts

## 18\.1 Telemetry

TelemetryRecord  
  telemetry\_id  
  node\_id  
  sequence  
  measurement\_timestamp  
  receive\_timestamp  
  location  
  measurements\[\]  
  diagnostics\[\]  
  battery  
  source  
  schema\_version  
  auth

Ordering/deduplication uses receive\_timestamp plus sequence semantics\. Domain reasoning uses measurement\_timestamp\. This distinction is mandatory\.

## 18\.2 Hazard assessment

HazardAssessment  
  node\_id  
  hazard\_type  
  evidence  
  confidence  
  severity  
  operational\_risk  
  information\_condition  
  state  
  contributing\_evidence\_groups\[\]  
  timestamp

## 18\.3 Incident

Incident  
  incident\_id  
  hazard\_type  
  state  
  severity  
  information\_condition  
  origin  
  contributing\_nodes\[\]  
  created\_at  
  updated\_at  
  current\_geometry  
  response\_status

## 18\.4 Canonical emergency event

EmergencyEvent  
  alert\_id  
  incident\_id  
  hazard\_type  
  state  
  severity  
  information\_condition  
  affected\_geometry  
  recommended\_action  
  issued\_at  
  expires\_at  
  signature

## 18\.5 Simulation metadata

Every synthetic event is permanently tagged with source=SIMULATION and the scenario ID\. The authority and citizen surfaces must make simulation status impossible to confuse with a live event\.

# 19\. Architecture Invariants — NON\-NEGOTIABLE

__READ THIS SECTION BEFORE CODING  
__These rules are the architectural guardrails\. Any implementation that violates one of them is not considered conformant to the NexAlert V1 architecture\.

__1\. __Missing does not mean zero\.

__2\. __Measurement timestamp is not receive timestamp\.

__3\. __Receive timestamp \+ sequence govern ordering/deduplication; measurement timestamp governs domain reasoning\.

__4\. __Node state is not the same as regional incident state\.

__5\. __Sensor health is not battery health\.

__6\. __Signal quality is not hazard confidence\.

__7\. __Hazard evidence is not hazard probability unless separately calibrated\.

__8\. __Confidence is not severity\.

__9\. __Severity is not operational risk\.

__10\. __Operational risk is not probability\.

__11\. __Information Condition is separate from hazard severity and state\.

__12\. __Correlated sensors are grouped appropriately; they are not blindly treated as independent votes\.

__13\. __A core\-evidence coverage floor prevents missing critical evidence from being hidden by total sensor count\.

__14\. __Synthetic telemetry MUST enter the same ingestion endpoint/pipeline as hardware telemetry\.

__15\. __The frontend MUST NOT calculate canonical intelligence or domain truth\.

__16\. __The simulation layer MUST NOT bypass canonical ingestion\.

__17\. __Incident correlation is deterministic and explicit in V1\.

__18\. __Physical fire footprint comes from the arrival\-time field\.

__19\. __Operational danger buffers are policy outputs, not physics\.

__20\. __Current, warning, and projected exposure are not naively summed\.

__21\. __Multi\-hazard risk surfaces remain separate and independently toggleable\.

__22\. __Real\-world exposure numbers require real sourced data\.

__23\. __Fire spread runs on Master/cloud compute, not the ESP32\.

__24\. __Wind directions reported as FROM must be converted to TO before being used as propagation vectors\.

__25\. __Diagonal grid propagation uses the correct geometric distance\.

__26\. __Area/distance calculations use an appropriate projected/geodesic method, never raw lat/lon treated as planar metres\.

__27\. __Changing environmental conditions invalidate the untouched future portion of an old arrival field; recomputation begins from the current fire perimeter\.

__28\. __MultiPolygon geometry is supported\.

__29\. __Invalid geometry is repaired or explicitly flagged; it is not silently used\.

__30\. __NexAlert recommends; a human approves and acts\. There is no autonomous dispatch path\.

__31\. __If no viable citizen safe route exists, the system returns SHELTER\_IN\_PLACE\.

__32\. __Spoofed/tampered node telemetry is rejected before domain ingestion\.

__33\. __Master failure and internet failure are treated as distinct failure modes\.

__34\. __Local emergency access must not depend exclusively on the Master being alive\.

__35\. __Operator and system actions that change operational state are auditable\.

__36\. __Simulation mode must always be visibly and persistently identified\.

__37\. __Do not introduce microservices, Kafka\-class streaming, 3D, or heavy ML simply because they are technically possible; architecture complexity must earn its place\.

# 20\. V1 Scope, Non\-Goals & Roadmap

## 20\.1 V1 / prototype\-critical

- Real fire sensing and controlled trials\.
- Fire \+ flood as the primary multi\-hazard pathways; other hazards supported at framework level where data allows\.
- Health/quality/reliability\-aware intelligence\.
- Deterministic incident correlation\.
- Physics\-informed geospatial fire spread with documented assumptions\.
- Affected\-area geometry and hazard risk heatmap\.
- Real population/infrastructure exposure where displayed\.
- Human\-approved response workflow\.
- Authority dashboard\.
- Citizen emergency experience and SOS\.
- Store\-and\-forward and local emergency access\.
- Node\-to\-Master HMAC\.
- Real \+ synthetic telemetry parity\.

## 20\.2 Explicitly deferred / roadmap

- Full multi\-hop self\-healing mesh\.
- LoRaWAN/NB\-IoT variants beyond the chosen prototype transport\.
- Satellite data integration\.
- Full CFD wildfire physics\.
- Ember spotting/reignition\.
- Advanced supervised ML without sufficient real labeled data\.
- Deep enterprise RBAC\.
- Microservices/Kafka\-scale streaming\.
- 3D terrain visualization\.
- Large\-scale operational agency deployment certification\.
- Native mobile app unless core product is already stable and time remains\.

## 20\.3 Claims boundary

__Avoid saying__

__Say instead__

AI predicts disasters\.

Local intelligence detects developing hazards from real\-time sensor evidence\.

We predict exact fire spread\.

We model probable spread direction/rate from terrain, fuel, moisture, and wind assumptions and update with changing conditions\.

Risk is a probability\.

The displayed risk is an operational index unless separately calibrated\.

We detect every disaster\.

We provide a multi\-hazard framework with data\-appropriate confidence; fire is the best\-validated prototype pathway\.

Every phone receives alerts\.

People within the node's local network can receive local emergency information; subscribed online users can receive supported push alerts\.

Self\-healing network\.

The prototype supports buffering and reconnection; full self\-healing mesh is roadmap\.

Production accurate\.

Prototype\-scale validation with clearly stated limits\.

# 21\. Implementation Ownership Matrix

__Subsystem__

__Primary team owner__

__Depends on__

__Primary output__

Firmware/Node

Hardware \+ embedded

Sensor contracts, security

Authenticated telemetry \+ local services

Intelligence

Software/AI

Telemetry \+ diagnostics

Hazard assessment

Incident Manager

Backend

Hazard assessment

Incident state

Fire/Geo

Software/Geo

Environmental data \+ incident

Spread \+ geometry \+ risk

Exposure

Software/Data

Geometry \+ datasets

Impact statistics

Response

Backend/Product

Incident \+ exposure \+ SOS

Recommended/approved actions

Communication

Backend/Systems

Event contracts

Delivery status

Authority UI

Frontend

Domain APIs/WebSocket

Operator experience

Citizen UI

Frontend/Product

Alert \+ routing APIs

Emergency experience

Simulation

Software/AI

Telemetry contract

Synthetic events

Validation

Whole team

All modules

Evidence of correctness

# 22\. End\-to\-End Example: Real Fire Event

## 22\.1 Initial sensing

An ESP32 node observes a combination of temperature increase, PM/smoke increase, gas elevation, and supporting humidity conditions\. It packages measurements, diagnostics, battery state, timestamps, sequence number, node identity, and HMAC\.

## 22\.2 Ingestion

The Master/backend authenticates the packet, validates schema and ranges, records measurement and receive timestamps, normalizes units, and deduplicates\.

## 22\.3 Intelligence

The intelligence layer evaluates sensor health, quality, reliability, baseline readiness, anomaly strength, and fire\-specific evidence\. Correlated evidence is grouped appropriately\. The system may move the fire state to CONFIRMED or CRITICAL depending on the defined thresholds and evidence persistence\.

## 22\.4 Incident

The incident manager either attaches the assessment to an existing nearby fire incident or creates a new incident using the configured spatial/temporal correlation rule\.

## 22\.5 Geospatial response

The fire spread engine reads ignition location, DEM, fuel, moisture/context, and wind\. Wind direction is converted from FROM to TO\. Wind and slope influence are combined directionally\. The engine propagates an arrival\-time field and derives current, warning, and projection geometries\.

## 22\.6 Exposure

The exposure engine intersects the relevant geometries with population and infrastructure data and reports current/warning/projected exposure separately\.

## 22\.7 Response

The response engine sees the incident state, severity, risk, information condition, exposure, trend, and any SOS requests\. It generates a categorical recommendation such as P1 / URGENT RESPONSE and identifies target organizations\.

## 22\.8 Human approval

An authority operator reviews the command card and approves or rejects the recommended action\. Only after approval can the action move into notification/assignment states\.

## 22\.9 Citizen

A canonical emergency event drives the supported citizen alert channels\. The citizen sees the hazard, severity, affected area, recommended action, route/safe\-place guidance, and SOS\.

## 22\.10 Audit

The system records telemetry provenance, hazard state transitions, incident updates, spread calculations, exposure snapshots, alert issuance, operator approval, and response completion\.

# 23\. Architecture Implementation Gates

## 23\.1 Mandatory pre\-freeze execution items

__Gate__

__Required evidence__

Gas sensor selection

Confirmed component, calibration approach, cross\-sensitivity considerations, ESP32 compatibility\.

ESP32 concurrency benchmark

Measured timing/jitter/resource behavior with sensing \+ Wi\-Fi AP \+ telemetry \+ local processing\.

Incident correlation

Automated tests for merge/non\-merge cases\.

Master\-death resilience

Physical Master power\-off test with local emergency page still reachable\.

Human\-approval response gate

Test that dispatch/notification action cannot proceed without approval\.

Node HMAC

Invalid/missing/tampered/replayed packet tests\.

Shelter\-in\-place

Synthetic all\-directions\-hazard test returns SHELTER\_IN\_PLACE\.

Fire\-spread corrections

FROM→TO, diagonal distance, vector wind/slope, projected CRS, recomputation behavior verified\.

Geometry

No self\-intersecting output; MultiPolygon and boundary cases verified\.

Exposure

Sourced population/infrastructure data and no double\-counting\.

Simulation parity

Identical processing path proven for synthetic vs hardware\-origin telemetry\.

## 23\.2 Definition of architecture implemented

The architecture is considered implemented only when the team can trace a real or synthetic event through the canonical path without a parallel shortcut, can explain every state transition, can identify which subsystem owns each calculation, and can demonstrate the key failure behaviors listed in the final validation specification\.

# Appendix A — Canonical Vocabulary

__Term__

__Canonical meaning__

Telemetry

A time\-stamped sensor/data record entering the canonical ingestion path\.

Sensor Health

Condition of the sensor/device signal source\.

Signal Quality

Quality/integrity/stability of the measurement signal\.

Reliability

Trust weight applied to evidence after health/quality/context\.

Anomaly

Deviation from an appropriate baseline or modality\-specific expectation\.

Evidence

Hazard\-specific support derived from observed signals/features\.

Confidence

How strongly the available evidence supports the assessment\.

Severity

How severe the hazard condition is considered\.

Operational Risk

Consequence/context\-oriented index for operational prioritization\.

Information Condition

Good/degraded/unknown view of the completeness and freshness of available information\.

Hazard State

Normal/watch/suspected/confirmed/critical/resolved lifecycle\.

Incident

Persistent representation of a real or simulated hazard situation\.

Physical Footprint

Geometry derived from the arrival\-time field or analogous physical hazard model\.

Operational Buffer

Policy\-defined safety margin around a physical footprint\.

Exposure

Population/infrastructure/citizen consequence within a geometry\.

Response Recommendation

System\-generated suggested action for a human operator\.

Approved Action

Operational action explicitly approved by an authorized human\.

Emergency Event

Canonical alert payload derived from an incident/action state\.

Simulation

Synthetic input/scenario using the same downstream pipeline as live data\.

Degraded

System has reduced information or capability but continues with known limitations\.

Unknown

System lacks sufficient information to make a trustworthy assessment\.

# Appendix B — Architecture at a Glance

                         NEXALERT  
                             │  
                  ┌──────────┴──────────┐  
                  │                     │  
              REAL DATA             SIMULATION  
                  │                     │  
                  └──────────┬──────────┘  
                             ▼  
                    CANONICAL TELEMETRY  
                             │  
                     AUTH \+ VALIDATION  
                             │  
                             ▼  
              HEALTH → QUALITY → RELIABILITY  
                             │  
                 BASELINE → ANOMALY  
                             │  
               EVIDENCE → CONFIDENCE  
                             │  
                 SEVERITY → RISK → STATE  
                             │  
                    INCIDENT MANAGER  
                             │  
              ┌──────────────┼──────────────┐  
              ▼              ▼              ▼  
         FIRE/GEOSPATIAL  EXPOSURE       RESPONSE  
              │              │              │  
              └──────────────┼──────────────┘  
                             ▼  
                      CANONICAL EVENT  
                             │  
                   ┌─────────┴─────────┐  
                   ▼                   ▼  
              AUTHORITY             CITIZEN  
             DASHBOARD             EXPERIENCE  
                   │                   │  
                   └─────────┬─────────┘  
                             ▼  
                           AUDIT  
                             │  
                           HISTORY

# Appendix C — Master Rule for Future Changes

When implementation begins, every new requirement should be classified before code is written: \(1\) clarification of an existing rule, \(2\) parameter change, \(3\) bug fix, \(4\) data limitation, or \(5\) genuine architecture change\. Only category 5 changes the architecture itself\. This prevents normal coding friction from reopening the entire product design\.

__Final architecture position  
__The NexAlert architecture is now treated as frozen at the conceptual level\. Remaining work is implementation, empirical validation, parameter calibration, and closing explicitly identified execution gaps\. The team should now build against this document and the downstream final specifications rather than continuing open\-ended architecture brainstorming\.

