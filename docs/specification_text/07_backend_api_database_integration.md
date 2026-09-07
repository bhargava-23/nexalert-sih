__NEXALERT__

__FINAL 07__

__Backend, API, Database & Integration Specification__

*Implementation\-ready domain, persistence, service, API and integration contract*

__Status: FINAL CORE SPECIFICATION__

Authority: Final NexAlert architecture \+ technical requirements \+ implementation/configuration specifications

__Document Control & Scope__

__Item__

__Value__

Document ID

NexAlert\-FINAL\-07

Primary scope

Backend domain model, HTTP/WebSocket API, persistence, workers, integrations, sync and observability

Target deployment

Raspberry Pi\-class local Master \+ optional cloud backend; modular monolith with background workers

Primary database

PostgreSQL \+ PostGIS

Canonical API prefix

/api/v1

Canonical telemetry input

POST /api/v1/telemetry

Source of truth

Backend domain state; frontends are projections/cache, not authorities

Simulation rule

Simulation uses the same ingestion and domain pipeline as LIVE; it must remain explicitly marked

Related specifications

01, 02, 03, 04, 05, 06, 08, 09, 10, 11, 15, 16, 17, 18, 19

__Purpose__

This document converts the frozen NexAlert architecture into an executable backend contract\. It defines what the API accepts, what the database stores, how domain state changes, where asynchronous workers are used, how LIVE and SIMULATION remain separated, and how the Master, field nodes, web clients and future integrations communicate without creating competing sources of truth\.

__Locked backend principle__

A successful HTTP response is not equivalent to an operational decision\. The API persists validated facts, emits domain events, and exposes authoritative read models\. Hazard reasoning, incident correlation, response approval and alert issuance remain explicit domain stages\.

__1\. Backend Architecture & Responsibility Boundary__

NexAlert V1 uses a modular monolith rather than microservices\. Modules have strict domain boundaries but run in one deployable backend process or one local application bundle\. Background workers handle jobs whose latency or reliability characteristics differ from the synchronous API path\.

__Layer__

__Responsibilities__

__Must not own__

API / Transport

HTTP request validation, authentication, idempotency, response shaping, WebSocket publication boundary

Safety semantics, ad\-hoc incident state

Domain

Telemetry acceptance, intelligence, hazards, incidents, alerts, response, SOS, simulation control

UI layout or transport\-specific logic

Persistence

Immutable facts, mutable domain state, read models, spatial indexes, audit records

Decision meaning outside domain transactions

Workers

Async correlation, alert delivery, replay, analytics, reconciliation, external fetches

Silent mutation without audit/event trace

Integration adapters

LoRa/MQTT bridge, Web Push, maps/data providers, future SACHET/cell broadcast adapters

Bypassing domain authorization

Read projections

Dashboard/citizen optimized views and live streams

Independent source\-of\-truth state

__1\.1 Repository target__

services/api/  
services/workers/  
packages/domain/  
packages/schemas/  
packages/db/  
packages/security/  
services/geospatial/  
services/simulation/  
services/integrations/  
apps/authority\-web/  
apps/citizen\-web/  
apps/local\-portal/

__1\.2 Runtime topology__

ESP32 nodes \-> authenticated telemetry ingress \-> Master API/domain \-> PostgreSQL/PostGIS  
                                     |  
                                     \+\-> workers \-> alerts / geospatial / analytics / external adapters  
                                     |  
                                     \+\-> WebSocket / read API \-> Authority UI  
                                     \+\-> emergency\-event projection \-> Citizen UI / local portal

__2\. Canonical Data & Domain Model__

The backend distinguishes immutable observations/events from mutable operational state\. A telemetry record can be retained even when its downstream interpretation changes after a configuration or bug fix\.

__Entity__

__Purpose__

__Mutability__

__Primary key__

Node

Registered sensing/edge identity, location, capabilities, firmware

Mostly mutable metadata

node\_id

TelemetryRecord

Canonical validated measurement packet

Immutable

telemetry\_id

SensorAssessment

Health/quality/reliability evaluation for a telemetry cycle

Immutable result

assessment\_id

HazardAssessment

Per\-hazard evidence/confidence/severity/risk/state assessment

Immutable result

assessment\_id

Incident

Persistent real/simulated hazard situation

Mutable lifecycle \+ immutable history

incident\_id

IncidentEvent

Event describing an incident transition or operational fact

Immutable append\-only

incident\_event\_id

HazardGeometry

Current/warning/projection/risk geometry versions

Immutable versions

geometry\_id

Alert

Canonical emergency/authority alert record

Mutable delivery lifecycle \+ history

alert\_id

AlertDelivery

Per\-channel/per\-recipient delivery attempt

Append\-only attempts

delivery\_id

ResponseAction

Human\-approved operational action lifecycle

Mutable state \+ audit history

action\_id

SOSRequest

Citizen distress/contact request

Mutable operational state \+ audit

sos\_id

SimulationRun

Scenario execution and replay metadata

Mutable run state

run\_id

AuditEvent

Actor/system action audit record

Immutable

audit\_event\_id

ConfigVersion

Validated configuration profile/hash

Immutable versions

config\_version

__2\.1 Canonical identifiers__

- Use opaque stable IDs \(UUID/ULID\) for domain entities exposed to clients\.
- Use node\_id as a human\-readable registered identifier \(e\.g\. NODE\-001\), but never use display names as primary keys\.
- Use telemetry\_id for deduplication; sequence is node\-scoped ordering evidence, not a global identity\.
- Use trace\_id across a telemetry\-to\-incident\-to\-alert chain; preserve it in worker and audit records\.
- Every retryable write endpoint accepts an idempotency key or a deterministic canonical key\.

__2\.2 LIVE vs SIMULATION__

__Field__

__LIVE__

__SIMULATION__

source

HARDWARE

SIMULATION

Required provenance

node identity \+ authenticated packet

scenario\_id \+ seed \+ simulator provenance

Operational effect

May mutate LIVE operational state when accepted by policy

Creates SIMULATED operational state only

External alerts

Allowed only through configured human\-approved path

Disabled by SIH profile

Ground truth

Not available to reasoning

Hidden from reasoning and transmitted nowhere in telemetry

Replay

Normal history/reprocessing path

Deterministic run/replay path

__3\. PostgreSQL / PostGIS Schema__

PostgreSQL is the system\-of\-record target\. PostGIS stores node positions, incident geometries and hazard polygons as spatial types rather than JSON\-only geometry blobs\. SQLite may be used for narrow local development only when a feature does not depend on spatial semantics\.

__Table__

__Key columns__

__Indexes / constraints__

nodes

node\_id, status, location geography\(Point,4326\), firmware\_version, config\_version

PK node\_id; GIST location; status index

telemetry\_records

telemetry\_id, node\_id, sequence, measurement\_ts, receive\_ts, source, measurements\_jsonb, diagnostics\_jsonb, location geography\(Point,4326\)

PK; UNIQUE\(node\_id, sequence\); BTREE\(node\_id, measurement\_ts\); GIST\(location\)

sensor\_assessments

assessment\_id, telemetry\_id, node\_id, sensor\_type, health, quality, reliability, baseline\_state, anomaly

BTREE\(node\_id, measurement\_ts\); telemetry FK

hazard\_assessments

assessment\_id, telemetry\_id, hazard\_type, evidence, confidence, severity, risk, state, information\_condition

BTREE\(hazard\_type, created\_at\); telemetry FK

incidents

incident\_id, hazard\_type, state, severity, information\_condition, origin, current\_geometry geography\(Geometry,4326\), response\_status, created\_at, updated\_at

BTREE\(state,updated\_at\); GIST\(current\_geometry\)

incident\_events

incident\_event\_id, incident\_id, event\_type, occurred\_at, actor\_type, trace\_id, payload\_jsonb

BTREE\(incident\_id,occurred\_at\)

hazard\_geometries

geometry\_id, incident\_id, geometry\_type, version, valid\_from, valid\_to, geometry geography\(Geometry,4326\)

UNIQUE\(incident\_id,geometry\_type,version\); GIST\(geometry\)

alerts

alert\_id, incident\_id, alert\_type, state, issued\_at, expires\_at, message\_jsonb, signature, config\_hash

BTREE\(incident\_id,state\); BTREE\(expires\_at\)

alert\_deliveries

delivery\_id, alert\_id, channel, target\_ref, state, attempt\_no, provider\_ref, attempted\_at

BTREE\(alert\_id\); BTREE\(state,attempted\_at\)

response\_actions

action\_id, incident\_id, action\_type, state, owner, approved\_by, approved\_at, completed\_at

BTREE\(incident\_id,state\)

sos\_requests

sos\_id, created\_at, location geography\(Point,4326\), priority, state, citizen\_ref\_hash, hazard\_context\_jsonb

BTREE\(state,created\_at\); GIST\(location\)

simulation\_runs

run\_id, scenario\_id, seed, mode, status, start\_time, end\_time, manifest\_jsonb

BTREE\(status,created\_at\)

audit\_events

audit\_event\_id, actor\_id, actor\_type, action, resource\_type, resource\_id, occurred\_at, trace\_id, details\_jsonb

BTREE\(resource\_type,resource\_id,occurred\_at\); BTREE\(actor\_id,occurred\_at\)

config\_versions

config\_version, profile, config\_hash, payload\_jsonb, created\_at, approved\_by

UNIQUE\(config\_hash\)

__4\. Transaction & Persistence Rules__

- Validate schema, authenticate and perform replay/idempotency checks before any operational state mutation\.
- Persist the canonical telemetry fact before or atomically with the domain event that records acceptance; do not emit an event for data that was never committed\.
- Use a transactional outbox for domain events that must reach workers or live clients reliably\.
- Immutable telemetry, incident events, alert delivery attempts and audit events are append\-only\.
- Mutable domain records \(incident, alert, response action\) update current state while retaining transition history as events\.
- Database migrations are mandatory for schema changes\. No manual production\-table editing during the build/demo cycle\.
- All timestamps are stored in UTC\. Client display timezone is a presentation concern\.
- Measurement timestamp and receive timestamp remain distinct; late or stale packets never overwrite receive time\.
- Missing is represented as NULL/absent, never as a fabricated zero\.

__4\.1 Canonical telemetry acceptance transaction__

1\. Parse envelope  
2\. Schema/type/unit validation  
3\. Authenticate HMAC  
4\. Validate node identity \+ status  
5\. Replay/idempotency check  
6\. Persist telemetry record  
7\. Create sensor/intelligence assessments  
8\. Persist hazard assessments  
9\. Correlate incident \(same hazard \+ spatial \+ temporal rule\)  
10\. Persist incident event\(s\)  
11\. Create alert candidate if policy threshold is met  
12\. Commit transaction/outbox  
13\. Workers deliver async side effects

__4\.2 Failure semantics__

__Failure__

__Expected result__

Schema invalid

HTTP 422; no domain mutation; validation audit/metric

Authentication invalid

HTTP 401/403 depending endpoint; security event; no telemetry acceptance

Replay / duplicate

Idempotent success or explicit duplicate response; no duplicate incident/alert

DB unavailable

HTTP 503; packet remains on node/local buffer for retry

Worker unavailable

Synchronous domain state remains committed; outbox remains pending

External provider unavailable

Alert state becomes delivery\-pending/failed; retry policy applies; incident state is not silently altered

Spatial service failure

Core incident state may persist with geospatial status degraded; do not invent geometry

__5\. API Conventions__

__Convention__

__Contract__

Base URL

/api/v1

Content\-Type

application/json

Errors

application/json with stable error\_code, message, details, trace\_id

Auth

Node HMAC for telemetry; session/JWT/OIDC\-equivalent for human/API clients; signed events for canonical emergency objects

Idempotency

Idempotency\-Key header on retryable commands; telemetry also dedupes by telemetry\_id and node sequence

Pagination

cursor\-based for large event/telemetry lists; explicit limit

Filtering

field filters plus time windows; no unbounded query endpoints

ETag/versioning

Recommended for read\-model resources and configuration

Time

ISO\-8601 UTC timestamps

Geometry

GeoJSON for API transport; EPSG:4326 coordinates at the API boundary

Rate limiting

Per\-client and endpoint class; emergency/SOS endpoints have reserved capacity

__6\. Core API Surface__

__Method__

__Endpoint__

__Purpose__

__Class__

POST

/api/v1/telemetry

Canonical telemetry ingress

WRITE / NODE

GET

/api/v1/nodes

Node inventory/status

READ

GET

/api/v1/nodes/\{node\_id\}

Node detail \+ diagnostics

READ

GET

/api/v1/incidents

Incident list/filter

READ

GET

/api/v1/incidents/\{incident\_id\}

Incident command record

READ

GET

/api/v1/incidents/\{incident\_id\}/timeline

Incident event history

READ

POST

/api/v1/incidents/\{incident\_id\}/acknowledge

Authority acknowledgment

COMMAND

POST

/api/v1/incidents/\{incident\_id\}/resolve

Resolve incident

COMMAND

GET

/api/v1/hazards/\{hazard\_type\}/layers

Current/warning/projection/risk layers

READ / GEO

GET

/api/v1/fire/\{incident\_id\}/spread

Fire spread state \+ geometry versions

READ / GEO

POST

/api/v1/response/actions

Create human\-reviewable response action

COMMAND

POST

/api/v1/response/actions/\{action\_id\}/approve

Human approval gate

COMMAND / HIGH RISK

POST

/api/v1/alerts

Create alert candidate / approved alert path

COMMAND / HIGH RISK

GET

/api/v1/alerts/\{alert\_id\}

Alert lifecycle

READ

POST

/api/v1/sos

Citizen SOS

WRITE / PUBLIC

GET

/api/v1/sos

Authority SOS queue

READ / AUTHORITY

POST

/api/v1/simulation/runs

Create simulation run

COMMAND

POST

/api/v1/simulation/runs/\{run\_id\}/control

Pause/resume/reset/seek

COMMAND

GET

/api/v1/system/status

Master/backend/service health

READ

GET

/api/v1/map/overview

Authority map projection

READ / GEO

__7\. Telemetry API Contract__

The telemetry endpoint is the canonical ingestion boundary for both hardware\-derived and synthetic telemetry\. The payload contract must remain versioned and stable\.

POST /api/v1/telemetry  
Idempotency\-Key: <optional\-but\-recommended>  
Content\-Type: application/json  
  
\{  
  "schema\_version": "telemetry\.v1",  
  "telemetry\_id": "01J\.\.\.",  
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

__Response__

\{  
  "accepted": true,  
  "telemetry\_id": "01J\.\.\.",  
  "duplicate": false,  
  "trace\_id": "tr\_01J\.\.\.",  
  "ingestion\_status": "ACCEPTED"  
\}

__Rules__

- Measurement timestamp must not be trusted as server receive time\. Server assigns receive\_timestamp\.
- Node sequence rollback or duplicate is accepted only when the packet is an exact already\-seen duplicate; conflicting reuse is rejected and logged\.
- Authenticated packet acceptance must happen before intelligence or incident mutation\.
- The simulator must call the same endpoint or same internal application service contract; it must not write directly into domain incident tables\.

__8\. Incident API & Correlation Contract__

Incident correlation remains deterministic in V1\. For an incoming hazard assessment, the incident manager searches eligible open/active incidents of the same hazard type within the configured spatial radius and temporal window\. The exact values live in the configuration registry\.

same hazard\_type  
AND distance\(new\_evidence, incident\.origin/current\_reference\) <= incident\.merge\_radius\_m  
AND time\_delta <= incident\.merge\_window\_s  
    \-> attach evidence to existing incident  
otherwise  
    \-> create new incident

__Incident response example__

\{  
  "incident\_id":"INC\-\.\.\.",  
  "hazard\_type":"FIRE",  
  "state":"CONFIRMED",  
  "severity":0\.82,  
  "information\_condition":"GOOD",  
  "origin":"LIVE",  
  "contributing\_nodes":\["NODE\-001","NODE\-002"\],  
  "created\_at":"\.\.\.",  
  "updated\_at":"\.\.\.",  
  "current\_geometry":\{\.\.\.\},  
  "response\_status":"PENDING\_APPROVAL"  
\}

__9\. Hazard & Geospatial API Contract__

__Resource__

__Read model must contain__

__Important invariant__

Fire spread

current footprint, warning area, projection, arrival\-time metadata, version, environmental context

Geometry comes from the spread engine; frontend does not draw a competing propagation model

Affected area

physical footprint, operational buffer, population/infrastructure exposure summaries

Physical footprint and policy buffer are separate layers

Risk surface

cell/feature risk index, freshness/version, information condition

Risk is an operational index, not probability; multi\-hazard layers remain independent

Map overview

nodes, incidents, hazard layers, buffers, SOS markers, information condition

All layers are projections of domain state; no decorative hazard truth

__10\. WebSocket / Live Update Contract__

Authority and citizen clients need low\-latency updates without polling the entire database\. WebSocket topics are projections, not write channels\.

__Topic__

__Publisher__

__Payload types__

__Client action__

incidents

backend/domain

incident\_created, incident\_updated, state\_changed

Refresh incident projection

alerts

alert manager

alert\_issued, alert\_updated, standdown

Update alert banner/state

nodes

edge/network

node\_online, node\_stale, node\_recovered

Update node panel/map

geospatial

geospatial worker

geometry\_versioned, spread\_updated

Swap geometry version

sos

SOS module

sos\_created, sos\_updated

Refresh authority queue

system

health monitor

service\_state, information\_condition

Show degraded banner

Every pushed message carries trace\_id, event\_id, occurred\_at and resource version\. Clients must tolerate out\-of\-order delivery by comparing resource versions/timestamps\.

__11\. Background Workers__

__Worker__

__Trigger__

__Responsibilities__

__Retry/Failure__

Incident worker

accepted telemetry/outbox

correlation, lifecycle transitions, persistence

exponential retry; no duplicate event on replay

Geospatial worker

confirmed/changed fire incident or simulation clock

spread recomputation, geometry versioning, affected area

retain last known good; mark stale/degraded

Alert worker

approved alert candidate

fan\-out delivery, retries, receipts

per\-channel retry; dead\-letter after bounded attempts

Replay worker

simulation/replay command

deterministic timestamped telemetry emission

checkpoint \+ resumable state

Analytics worker

scheduled / requested

historical aggregates, response statistics

rebuildable read models

Integration worker

external context refresh

weather/population/map/provider pulls

cache with source timestamp; never fabricate

Reconciliation worker

startup / reconnect

store\-forward packets, local\-to\-cloud state reconciliation

idempotent merge; conflict rules from source\-of\-truth policy

__12\. Transactional Outbox & Event Model__

domain mutation  
   \-> DB transaction  
      \-> current state row\(s\)  
      \-> immutable domain event  
      \-> outbox row  
   COMMIT  
      \-> worker publishes / executes side effect  
      \-> delivery / audit recorded

__Event type__

__Source__

__Consumers__

TelemetryAccepted

ingestion

intelligence, metrics, replay audit

HazardAssessmentCreated

intelligence

incident manager, telemetry UI

IncidentCreated/Updated

incident manager

geospatial, alerts, dashboards, audit

SpreadUpdated

geospatial

map projection, exposure, dashboard/citizen

AlertApproved/Issued

alert manager

channel adapters, audit

ResponseActionApproved

authority command

assignment/notifications, audit

SOSCreated/Updated

SOS module

authority queue, response workflow

ConfigVersionActivated

config

all affected domain modules, audit

__13\. Authentication, Authorization & Integration Trust__

__Actor__

__Authentication__

__Authorization__

ESP32 node

per\-node HMAC secret; timestamp/sequence replay checks

node may submit only its own telemetry and approved diagnostics/commands

Authority user

authenticated session/token

RBAC permission \+ resource scope

Citizen

anonymous/local or verified identity as available

only permitted citizen operations; no authority commands

Simulator

service credential \+ explicit SIMULATION source

cannot issue LIVE alerts or write live state

External provider

adapter credential/API key

least\-privilege provider\-specific scope

__Security boundary rule__

HMAC/signature verification happens before telemetry or event data can mutate operational state\. External integrations never write directly to incident or alert tables; they enter through typed adapters and domain services\.

__14\. External Integration Architecture__

__Integration__

__Direction__

__Canonical adapter contract__

__V1 posture__

ESP32 \-> Master

Ingress

TelemetryEnvelope

Core

LoRa/MQTT bridge

Ingress

TelemetryEnvelope after bridge validation

Core/optional transport

Web Push

Egress

EmergencyEvent \-> DeliveryRequest

Prototype online channel

Local Wi\-Fi portal

Local egress

EmergencyEvent projection/cache

Core resilience path

Weather/context provider

Ingress

ContextSnapshot

Optional, timestamped

Population/geospatial datasets

Ingest/build

Versioned spatial layer

Required where used for exposure

SACHET / cell broadcast

Egress

Authorized emergency broadcast adapter

Future integration; not core prototype

Satellite / external command systems

Bidirectional future

Explicit adapter contract

Future

__15\. Offline, Reconnect & Reconciliation__

The backend must distinguish internet loss from Master loss\. Local operation continues to the extent supported by the deployed Master/node topology, and the local emergency portal is not allowed to depend on the cloud API being reachable\.

__Condition__

__Backend/local behavior__

__User\-visible information condition__

Internet unavailable, Master alive

local API/domain and local portal continue; sync queue grows

DEGRADED if external context/online alerts unavailable

Master unavailable

node/local emergency path remains reachable; local page can serve cached emergency state

DEGRADED/UNKNOWN depending cache freshness

Node disconnected

last telemetry retained; node becomes stale/unavailable after threshold

DEGRADED if incident relies on it

Reconnect

dedupe/store\-forward, process missing telemetry in timestamp order, preserve evidence timestamps

GOOD after validated recovery

Conflicting stale update

newer domain version wins unless event is an immutable fact; conflict is audited

DEGRADED during reconciliation if uncertainty exists

__15\.1 Reconciliation algorithm__

1\. ingest buffered packets idempotently  
2\. preserve original measurement\_timestamp  
3\. recompute receive\_timestamp at arrival  
4\. append missing telemetry facts only once  
5\. re\-run deterministic domain processing where policy allows  
6\. version geospatial projections instead of rewriting history  
7\. reconcile alert delivery receipts without duplicating alerts  
8\. emit audit event for reconciliation completion/failure

__16\. Read Models for UI__

__Read model__

__Optimized for__

__Must expose__

AuthorityOverview

map \+ active incidents

nodes, incidents, risk layers, information condition, last alert/SOS status

IncidentCommandCard

operator action

state, severity, information condition, evidence groups, exposure, response status, timestamps

CitizenEmergencyView

one\-page safety

hazard, severity, state, distance/direction, freshness, action, geometry, safe place if available

NodeDetail

diagnostics

health, quality, reliability, battery, link, heartbeat, latest telemetry, firmware/config

AlertStatus

delivery operations

issued, target zone, channel, delivery/opened/acknowledged/unreachable, retries

HistoricalSummary

analysis

incident frequency, node reliability, response times, alert outcomes, trends

__17\. API Error Contract__

\{  
  "error\_code":"TELEMETRY\_REPLAYED",  
  "message":"Telemetry sequence conflicts with an existing record",  
  "details":\{"node\_id":"NODE\-001","sequence":1842\},  
  "trace\_id":"tr\_01J\.\.\."  
\}

__Class__

__Examples__

__HTTP__

VALIDATION

INVALID\_SCHEMA, UNIT\_INVALID, GEOMETRY\_INVALID

400/422

AUTH

AUTH\_INVALID, AUTH\_REPLAYED

401/403/409

NOT\_FOUND

NODE\_NOT\_FOUND, INCIDENT\_NOT\_FOUND

404

CONFLICT

VERSION\_CONFLICT, COMMAND\_NOT\_ALLOWED

409

RATE

RATE\_LIMITED

429

DEPENDENCY

GEO\_SERVICE\_UNAVAILABLE, PROVIDER\_UNAVAILABLE

503

INTERNAL

INTERNAL\_ERROR

500

__18\. Performance & Capacity Targets__

Targets are implementation gates, not claims about present hardware\. Benchmark on the actual Raspberry Pi/ESP32 configuration and chosen deployment profile\.

__Path__

__Target__

__Measurement__

Telemetry validation/authentication

p95 < 100 ms local Master path

API latency

Telemetry persistence \+ domain enqueue

p95 < 250 ms local

end\-to\-end ingest acknowledgment

Incident projection update

p95 < 500 ms after accepted evidence

event\-to\-read\-model latency

WebSocket update

p95 < 250 ms after projection commit

commit\-to\-client receipt

SOS acceptance

p95 < 250 ms local path

API acknowledgment

Alert queue creation

p95 < 500 ms after human approval

command\-to\-queued

Spatial query

p95 < 300 ms common map lookup

DB query telemetry

Soak

24 h target scenario with no unbounded memory/queue growth

CPU/RAM/queue/latency

__18\.1 Capacity design rules__

- Prefer bounded queues over unlimited in\-memory buffers\.
- Batch historical queries; never load unbounded telemetry into API memory\.
- Use PostGIS indexes and bounding\-box prefilters for map queries\.
- Keep write paths narrow and push notifications/external providers to workers\.
- Record queue depth, DB connection saturation and worker lag as first\-class operational metrics\.

__19\. Observability & Traceability__

trace\_id  
  \-> telemetry\_id  
     \-> reasoning\_run\_id  
        \-> incident\_id  
           \-> alert\_id  
              \-> delivery\_id  
                 \-> audit\_event\_id

__Metric__

__Purpose__

telemetry\_accept\_rate

Input quality / transport health

telemetry\_reject\_auth

Security signal

replay\_reject\_count

Replay/clock integrity

incident\_correlation\_rate

Correlation behavior review

incident\_open\_duration

Operational analysis

alert\_issue\_to\_delivery\_latency

Communication performance

worker\_lag\_seconds

Async system health

db\_query\_latency

Persistence health

websocket\_clients\_connected

Projection load

local\_portal\_requests

Offline path usage

sos\_accept\_latency

Citizen safety path

information\_condition\_state

Trust/availability awareness

__20\. Security & Data Governance Integration__

- Store hashed/pseudonymous citizen references where full identity is unnecessary\.
- Do not expose node HMAC secrets, signature private keys or provider credentials through API responses or logs\.
- Redact sensitive fields from structured logs\.
- Audit all operator commands that can change incident state, issue alerts, approve response, alter configuration or access sensitive SOS information\.
- Configuration hash is attached to telemetry metadata, incident records, alerts, simulation manifests and audit trail where applicable\.
- Retention policy is configurable; immutable evidence required for SIH evaluation must be exportable and traceable\.

__21\. Integration Tests & Acceptance Matrix__

__Test ID__

__Scenario__

__Pass condition__

API\-001

Valid hardware telemetry

accepted, persisted, assessed, no duplicate

API\-002

Valid simulation telemetry

same domain path; source remains SIMULATION

API\-003

Bad HMAC

rejected before operational mutation; security event

API\-004

Replay same telemetry

idempotent/no duplicate domain effects

API\-005

Conflicting sequence reuse

rejected and audited

API\-006

Same hazard within merge radius/window

same incident

API\-007

Same hazard outside merge radius

new incident

API\-008

Different hazard co\-located

independent hazard vectors/incidents per policy

API\-009

DB outage during ingest

no false success; node can retry/store\-forward

API\-010

Worker outage after commit

outbox remains pending; no lost event

API\-011

WebSocket out\-of\-order messages

client converges to newest resource version

API\-012

Master internet loss

local operation continues; degraded info shown

API\-013

Master physical failure

local emergency path survives as designed

API\-014

Human approval gate

no operational dispatch/alert side effect before approval

API\-015

External provider outage

delivery retries/fails visibly; incident truth preserved

API\-016

Geometry version update

past geometry remains immutable; new version visible

API\-017

Migration test

forward/back migration procedure validated in test environment

API\-018

Soak test

no unbounded queue/heap/DB growth; target latency maintained

__22\. Implementation Sequence__

Build the backend in vertical slices\. Do not begin by implementing every table and endpoint before proving the domain loop\.

__Phase__

__Deliverable__

__Exit criterion__

1\. Contract skeleton

Pydantic/JSON schemas, error model, /health, /api/v1/telemetry

Valid packet can be accepted/rejected deterministically

2\. Persistence

migrations \+ core tables \+ indexes

Telemetry and nodes persist correctly

3\. Intelligence bridge

health/quality/reliability \-> anomaly \-> hazard assessment

Golden vectors pass

4\. Incident manager

deterministic spatial/temporal correlation

Incident lifecycle tests pass

5\. Read models

overview, incident, node, map projections

Authority UI can render real state

6\. Workers/outbox

async geospatial/alert/replay jobs

Retries and idempotency proven

7\. Offline/reconnect

local portal projection \+ reconciliation

Network/master fault tests pass

8\. Security

node HMAC \+ human auth \+ audit

Security acceptance tests pass

9\. Simulation

scenario runner emits telemetry only

Simulation equals live pipeline semantics

10\. SIH hardening

observability, soak, demo profile, rollback

Validation matrix green

__23\. Vibe\-Coding Guardrails for Backend__

- One bounded implementation task per AI coding session\.
- Always state the authoritative specification section, allowed files, contracts, invariants, tests and non\-goals\.
- Never let an AI model invent an endpoint, field name or state transition without updating the schema/config/test contract\.
- Generated database migrations require human review before apply\.
- Generated security code must be reviewed against the security specification and tested with negative cases\.
- Every API feature includes at least one happy\-path, one validation/failure, one idempotency/retry, and one audit/trace test where applicable\.

Prompt pattern:  
Authority: FINAL\-07 §7 Telemetry API  
Task: implement POST /api/v1/telemetry validation \+ idempotency  
Allowed files: services/api/telemetry/\*, packages/schemas/telemetry\.py, tests/api/test\_telemetry\.py  
Invariants: HMAC before mutation; source explicit; measurement \!= receive timestamp  
Non\-goals: redesign incident correlation  
Required tests: API\-001\.\.API\-005

__24\. Locked Backend Invariants__

• Backend domain state is the authoritative operational source of truth\.

• Simulation and LIVE share the same post\-ingestion domain pipeline but remain explicitly distinguishable\.

• Telemetry authentication/replay checks happen before operational mutation\.

• Immutable telemetry and event facts are never rewritten as a shortcut\.

• Incident correlation is deterministic in V1: same hazard \+ spatial threshold \+ temporal threshold\.

• Alert issuance and operational dispatch remain behind the configured human\-approval boundary\.

• PostGIS stores real geometry; frontend code cannot create competing hazard geometry\.

• Physical hazard footprint and operational buffer are separate domain/read\-model concepts\.

• Multi\-hazard risks remain independent; no fake universal combined scalar is persisted as truth\.

• All retryable effects are idempotent and traceable\.

• No cloud\-only dependency may silently disable the local emergency path\.

• Configuration is versioned, validated and auditable rather than hidden in application code\.

__Appendix A \- Minimal Internal Service Interfaces__

TelemetryService\.accept\(envelope, actor\_context\) \-> TelemetryAcceptance  
IntelligenceService\.assess\(telemetry\_id\) \-> AssessmentBundle  
IncidentService\.correlate\(assessment\_bundle\) \-> IncidentDecision  
GeospatialService\.update\(incident\_id, clock\) \-> GeometryVersion  
AlertService\.create\_candidate\(incident\_id\) \-> AlertCandidate  
AlertService\.issue\(alert\_id, approval\_context\) \-> AlertIssued  
ResponseService\.approve\(action\_id, authority\_context\) \-> ActionApproved  
SyncService\.reconcile\(node\_id, buffered\_records\) \-> ReconciliationResult  
AuditService\.record\(event\) \-> AuditEvent

__Appendix B \- Source\-of\-Truth Hierarchy__

__Priority__

__Source__

__Meaning__

1

Immutable telemetry/event facts

What the system actually received/recorded

2

Domain state \+ versioned projections

Current operational truth derived from facts

3

Configuration registry

Approved interpretation/control parameters

4

Read models/cache

Efficient client projection

5

UI\-local state

Presentation only; never operational truth

6

AI\-generated code/comments

Implementation aid only; never authority

__END OF FINAL 07 SPECIFICATION__

