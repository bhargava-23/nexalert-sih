__NEXALERT__

__TECHNOLOGY STACK, DEPLOYMENT & COMPUTE ALLOCATION__

Final V1 Engineering Baseline

__Document role  
__This specification locks the implementation technology families, runtime boundaries, compute allocation, repository/deployment posture, embedded\-vs\-Python intelligence strategy, data/runtime dependencies, and environment rules for NexAlert V1\. It is subordinate to Document 01 \(Master Architecture\) and Document 02 \(TRD\), and it is used by the implementation/vibe\-coding specification\.

__Field__

__Value__

Product

NexAlert

Problem

SIH26178 — resilient, AI\-powered environmental monitoring and early warning

Document

03 — Technology Stack, Deployment & Compute Allocation

Status

FINAL V1 TECHNOLOGY BASELINE

Primary hardware

ESP32\-S3\-class field node \+ Raspberry Pi\-class Master

Primary software

C/C\+\+ embedded \+ Python backend/intelligence/geospatial \+ TypeScript frontend

Data store

PostgreSQL \+ PostGIS

Deployment posture

Modular monolith \+ background workers; local/edge profile \+ cloud profile

__Versioning policy  
__Technology families are locked here\. Exact patch versions MUST be pinned in firmware/toolchain configuration, Python lock files, frontend lock files, container image digests/tags, and deployment manifests at implementation freeze\. Do not silently upgrade a major dependency during implementation\.

# 1\. Technology Architecture Principles

## 1\.1 Principle: one architecture, multiple compute targets

NexAlert is a distributed product, not a single process\. The same domain concepts cross several runtimes, but each runtime has a bounded responsibility\.

FIELD NODE  
ESP32\-S3 / C or C\+\+  
  sensors → diagnostics → local intelligence → HMAC → communication → local emergency gateway  
  
MASTER / LOCAL EDGE  
Raspberry Pi / Linux / Python  
  aggregation → regional fusion → local backend → geospatial compute → local UI/service → buffering/sync  
  
CLOUD / CENTRAL BACKEND  
Linux / Python  
  canonical APIs → persistence → workers → targeting → alerts → historical/audit  
  
FRONTEND  
Browser / TypeScript  
  authority dashboard \+ citizen emergency experience  
  
OPTIONAL NATIVE APP  
Android/iOS endpoint only; same canonical event semantics

## 1\.2 Principle: Python is the reference implementation; C/C\+\+ is the embedded implementation

The environmental intelligence mathematics is specified independently of programming language\. Python is the reference implementation used for rapid development, simulation, validation and server\-side execution\. Only the lightweight subset explicitly assigned to the ESP32 is reimplemented in C/C\+\+ for deterministic embedded execution\. The C/C\+\+ implementation is verified against Python using shared golden\-vector fixtures\.

__Do not copy Python code blindly onto the ESP32  
__MicroPython can run on ESP32\-class devices, but NexAlert V1 does not depend on it\. The default embedded architecture is ESP\-IDF \+ C/C\+\+ because the node must simultaneously handle sensors, networking, buffering, authentication, timing and local intelligence with predictable resource usage\.

# 2\. Final Technology Stack

__Layer__

__Technology / family__

__V1 lock__

__Notes__

MCU firmware

ESP\-IDF \+ C/C\+\+

LOCKED

Official Espressif development framework; C/C\+\+ application\.

Embedded RTOS

FreeRTOS through ESP\-IDF

LOCKED

Use tasks/queues/event groups/timers only where needed; avoid unnecessary concurrency\.

Embedded crypto

ESP\-IDF crypto/security facilities \+ vetted component/library

LOCKED

HMAC telemetry authentication; secure key handling\.

Embedded DSP

ESP\-DSP where useful

OPTIONAL/APPROVED

Use only where signal\-processing workload justifies it\.

Master OS

Linux on Raspberry Pi\-class computer

LOCKED

Local compute and service host\.

Master/backend language

Python

LOCKED

Same domain modules can run locally and in cloud profile\.

Backend framework

FastAPI

LOCKED

REST \+ WebSocket/SSE\-facing API layer\.

Validation/model schemas

Pydantic\-style typed schemas

LOCKED

Canonical API/data validation\.

Scientific stack

NumPy / SciPy\-compatible Python stack

LOCKED

Mathematical calculations and simulation\.

Geospatial Python

GeoPandas / Shapely / Rasterio\-class stack

LOCKED

Vector/raster preparation and geometry operations\.

Spatial database

PostgreSQL \+ PostGIS

LOCKED

Canonical spatial persistence/query layer\.

Task execution

Python worker process/task queue

LOCKED CONCEPT

Specific lightweight worker implementation chosen during build; no Kafka\-class infrastructure\.

Frontend

Next\.js \+ React \+ TypeScript

LOCKED

App Router preferred; strongly typed UI\.

Styling

Tailwind CSS \+ CSS custom properties

LOCKED

Dark grey/black glassmorphism design system\.

Map

MapLibre GL JS

LOCKED

Interactive WebGL map; backend\-provided GeoJSON/raster/vector sources\.

Charts

Lightweight React chart library

APPROVED

Exact library chosen during UI implementation; avoid unnecessary dependencies\.

Real\-time

WebSocket; SSE fallback where appropriate

LOCKED

Dashboard/citizen live updates\.

API client

Typed frontend API layer

LOCKED CONCEPT

Prefer generated/hand\-maintained types from canonical schema\.

Containerization

Docker \+ Docker Compose for development/demo

LOCKED

Local reproducible stack\.

Reverse proxy

Nginx/Caddy or platform ingress

DEPLOYMENT CHOICE

Use only when needed; simple demo can expose app directly behind secure ingress\.

Testing

pytest \+ frontend test framework \+ firmware unit/integration tests

LOCKED

Tests traced to TRD requirements\.

CI

GitHub Actions or equivalent

SHOULD

Lint/test/build on push; exact provider is not architecture\-critical\.

The MapLibre choice is appropriate for the interactive map requirements: its official documentation supports GeoJSON polygons, raster/COG\-style sources, realtime updates, layer interactivity and browser rendering through WebGL\. citeturn169935search1turn169935search3

PostGIS extends PostgreSQL with spatial storage, indexing and functions for geometry measurement/intersection/buffering and raster support, matching NexAlert's spatial data needs\. citeturn169935search5turn169935search6

# 3\. Compute Allocation — What Runs Where

## 3\.1 Allocation matrix

__Workload__

__ESP32\-S3__

__Raspberry Pi Master__

__Cloud/backend__

Sensor acquisition

PRIMARY

NO

NO

Sensor self\-test/diagnostics

PRIMARY

Aggregate

Aggregate

Battery/solar monitoring

PRIMARY

Aggregate

Aggregate

Heartbeat

PRIMARY

Track

Track

Basic filtering

PRIMARY

Optional

Optional

Signal quality

PRIMARY

Recompute/verify if required

Recompute/verify if required

Sensor health

PRIMARY

Aggregate/track

Aggregate/track

Reliability

PRIMARY

Aggregate/track

Aggregate/track

Baseline readiness

PRIMARY

Read/aggregate

Read/aggregate

Short\-window anomaly

PRIMARY

YES

YES

Hazard evidence

PRIMARY for configured lightweight hazards

YES / regional fusion

YES

Evidence confidence

PRIMARY

Regional enrichment

Regional enrichment

Edge severity

PRIMARY

Regional enrichment

Regional enrichment

Edge operational risk

PRIMARY

Regional enrichment

Regional enrichment

Local hazard state/action

PRIMARY

Regional state

Regional state

Cross\-node fusion

NO

PRIMARY

YES

Incident correlation

NO

PRIMARY

PRIMARY

Fire spread raster simulation

NO

PRIMARY

PRIMARY

DEM processing

NO

PRIMARY

PRIMARY

Fuel raster handling

NO

PRIMARY

PRIMARY

Risk heatmap generation

NO

PRIMARY

PRIMARY

Population/infrastructure exposure

NO

PRIMARY

PRIMARY

Routing

NO

PRIMARY

PRIMARY

Authority workflow

NO

PRIMARY

PRIMARY

Cloud history/audit

NO

Local buffer only

PRIMARY

## 3\.2 Rule for edge AI

The ESP32 is an autonomous sensing/reasoning endpoint, but it is not a miniature GIS server\. The edge AI boundary stops before heavy geospatial computation\. This supports the Qualcomm/edge\-intelligence framing without forcing scientifically inappropriate workloads onto a constrained MCU\.

## 3\.3 Rule for Master vs cloud

The Master and cloud use the same domain model where practical\. The Master is the local continuity profile; the cloud is the centralized persistence and broad\-scale coordination profile\. A network outage must not require rewriting domain logic or creating a special dashboard truth\.

# 4\. ESP32\-S3 Firmware Architecture

## 4\.1 Why ESP\-IDF \+ C/C\+\+

ESP\-IDF is Espressif's official development framework for ESP32 devices and explicitly supports C\+\+ applications\. The ESP32\-S3 documentation covers C\+\+ support, FreeRTOS\-backed threading, toolchain behavior, and device\-specific development\. citeturn424934search0turn424934search8

## 4\.2 Firmware module structure

firmware/  
  main/  
    app\_main\.cpp  
  components/  
    sensors/  
      sensor\_manager\.\*  
      temp\_sensor\.\*  
      humidity\_sensor\.\*  
      pm\_sensor\.\*  
      gas\_sensor\.\*  
      water\_level\_sensor\.\*  
      rainfall\_sensor\.\*  
      soil\_sensor\.\*  
      vibration\_sensor\.\*  
    diagnostics/  
      self\_test\.\*  
      health\.\*  
      signal\_quality\.\*  
    intelligence/  
      baseline\.\*  
      anomaly\.\*  
      hazard\_reasoning\.\*  
      confidence\.\*  
      severity\.\*  
      risk\.\*  
      state\_machine\.\*  
    telemetry/  
      telemetry\_model\.\*  
      encoder\.\*  
      validator\.\*  
      sequence\.\*  
    security/  
      hmac\_auth\.\*  
      key\_store\.\*  
      replay\_guard\.\*  
    network/  
      transport\.\*  
      reconnect\.\*  
      wifi\_ap\.\*  
      optional\_radio\_adapter\.\*  
    storage/  
      ring\_buffer\.\*  
      flash\_store\.\*  
    system/  
      watchdog\.\*  
      time\_sync\.\*  
      config\.\*  
      logging\.\*  
  test/  
  sdkconfig\.defaults  
  CMakeLists\.txt

## 4\.3 Firmware task model

Task: sensor\_task  
  acquire measurements on configured cadence  
        ↓  
Task: diagnostics\_task  
  update self\-test / stability / availability  
        ↓  
Task: intelligence\_task  
  update baseline / anomaly / hazard reasoning  
        ↓  
Task: telemetry\_task  
  serialize canonical packet → HMAC → queue/send  
        ↓  
Task: network\_task  
  connection/reconnect \+ local AP service  
        ↓  
Task: storage\_task  
  buffer unsent telemetry/events  


The exact task decomposition is subject to the ESP32 concurrency benchmark\. Do not create a task per sensor by default\. Prefer a small bounded task set and queues to prevent unnecessary scheduling overhead\.

# 5\. Embedded Intelligence Strategy

## 5\.1 Same specification, two implementations

__Function__

__Python reference__

__ESP32 C/C\+\+__

Normalization

Reference

Equivalent deterministic implementation

Health H\_i

Reference

Implemented where diagnostics exist locally

Signal quality Q\_i

Reference

Implemented

Reliability R\_i

Reference

Implemented

Baseline readiness B\_i

Reference

Implemented

Median/MAD or selected baseline

Reference

Lightweight implementation

Anomaly A\_i

Reference

Implemented

Hazard reasoning

Reference

Implemented for configured lightweight hazards

Confidence

Reference

Implemented

Severity

Reference

Implemented

Operational risk

Reference

Implemented

Hazard state machine

Reference

Implemented

Fire spread GIS

Reference/server

NOT ON ESP32

Population/infrastructure

Reference/server

NOT ON ESP32

## 5\.2 Golden\-vector validation

For every embedded mathematical function that must match the Python reference, create a fixture containing inputs, expected intermediate values where useful, final output and tolerance\.

golden\_vectors/  
  health/  
  quality/  
  reliability/  
  baseline/  
  anomaly/  
  fire\_reasoning/  
  confidence/  
  severity/  
  risk/  
  state\_machine/  
  
Example:  
input:  
  temperature\_c = 42\.4  
  baseline = 31\.2  
  scale = 3\.4  
expected:  
  z = \.\.\.  
  anomaly = \.\.\.  
python\_result = \.\.\.  
esp32\_result = \.\.\.  
assert abs\(python\_result \- esp32\_result\) <= tolerance

__Definition of parity  
__Parity does not mean bit\-for\-bit equality for every floating\-point computation\. It means the embedded implementation stays within an explicitly declared numerical tolerance and produces the same qualitative state transition under the same test vector\.

# 6\. Raspberry Pi Master Architecture

## 6\.1 Master role

The Raspberry Pi\-class Master is the local control/compute center\. It receives node telemetry, can run the complete Python intelligence stack, performs cross\-node fusion and incident correlation, hosts heavy geospatial services, exposes the local dashboard/API, supports local citizen access where configured, and synchronizes with the cloud\.

## 6\.2 Master software profile

Linux  
  ↓  
Python runtime  
  ↓  
FastAPI application  
  ├── ingestion  
  ├── intelligence  
  ├── hazard reasoning  
  ├── incident manager  
  ├── geospatial/fire spread  
  ├── exposure  
  ├── response  
  ├── alerts  
  ├── SOS  
  ├── simulation  
  └── audit  
  
PostgreSQL \+ PostGIS  
  ↓  
background workers  
  ↓  
local UI / local API clients  
  ↓  
optional cloud sync

## 6\.3 Local\-first requirement

The Master profile must be deployable without cloud access\. The local instance should be able to ingest node data, run essential intelligence, maintain incident state, and expose the authority UI locally\. Cloud\-specific functions should fail gracefully rather than blocking the core local safety loop\.

# 7\. Backend Software Architecture

## 7\.1 Modular monolith

NexAlert V1 uses a modular monolith\. Domain modules are separated in code and APIs, but they run in one deployable backend process/profile plus background workers\. Do not prematurely split them into microservices\.

backend/  
  app/  
    api/  
    core/  
    config/  
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
    workers/  
    repositories/  
    models/  
    schemas/  
    services/  
  tests/  
    unit/  
    integration/  
    system/  
    fixtures/  


## 7\.2 Recommended Python environment

__Area__

__Choice__

__Rule__

Python

Current stable compatible Python; freeze exact version in project configuration

As of Sep 2026, Python 3\.14 is a stable release; pin exact minor/patch for the project after compatibility testing\. citeturn424934search4

API

FastAPI

Use typed request/response schemas and explicit API versioning\.

Schema validation

Pydantic\-style models

One canonical schema per domain object\.

ORM/data access

SQLAlchemy\-style typed data access

Avoid database logic in route handlers\.

Migrations

Alembic\-style migrations

Every schema change is versioned\.

Geospatial

Shapely/GeoPandas/Rasterio\-class tools

Use PostGIS for persistent/query\-heavy spatial operations\.

Math

NumPy/SciPy\-class tools

Keep deterministic reference math testable\.

HTTP client

httpx\-style async/sync client

External services have timeout/retry policies\.

Testing

pytest

Every TRD requirement maps to a test where possible\.

FastAPI's official deployment guidance treats production deployment as running the API behind a suitable server/deployment setup rather than the development server; the NexAlert deployment specification follows that separation\. citeturn424934search2

# 8\. Frontend Technology & Application Architecture

## 8\.1 Framework

Use Next\.js with React and TypeScript for both authority and citizen web applications, either as two route groups in one frontend repository or two apps sharing a component package\. The default recommendation for V1 is one frontend codebase with explicit authority and citizen route boundaries to reduce duplication\.

Next\.js is a React framework for full\-stack web applications, and its official documentation supports the App Router approach; React's documentation supports first\-class TypeScript usage\. citeturn169935search0turn424934search6

## 8\.2 Frontend structure

frontend/  
  app/  
    authority/  
      overview/  
      incidents/  
      fire\-spread/  
      affected\-impact/  
      multi\-hazard/  
      nodes/  
      telemetry/  
      sos/  
      alerts/  
      history/  
      response/  
      audit/  
      system/  
    citizen/  
      page\.tsx  
    api/  
  components/  
    map/  
    command/  
    incidents/  
    alerts/  
    sos/  
    charts/  
    glass/  
  lib/  
    api/  
    websocket/  
    geo/  
    formatting/  
    auth/  
    event\-verification/  
  styles/  
    tokens\.css  
    glass\.css  
  types/  
  tests/  


## 8\.3 Rendering rule

- Server\-side/data\-fetching approaches MAY be used where appropriate, but interactive maps and live operational components are client\-side components\.
- The frontend MUST receive canonical domain outputs from the backend\.
- The frontend may format, filter and animate but must not recalculate hazard state, risk, fire spread, exposure or response priority\.
- Keep raw technical values in an optional advanced view rather than the primary citizen experience\.

# 9\. Geospatial Frontend Stack

## 9\.1 MapLibre

MapLibre GL JS is the locked web mapping engine\. It supports interactive maps, GeoJSON sources/layers, raster visualization, realtime feature updates and browser rendering\. citeturn169935search1turn169935search3

## 9\.2 Map architecture

Backend geospatial output  
  ├── GeoJSON current footprint  
  ├── GeoJSON warning zone  
  ├── GeoJSON projection  
  ├── GeoJSON operational buffer  
  ├── GeoJSON safe route  
  ├── node/incident/SOS points  
  └── raster/derived risk source  
        ↓  
MapLibre sources  
        ↓  
named layers  
        ↓  
layer controls  
        ↓  
click / hover / drill\-down  


## 9\.3 Map layer ownership

__Layer__

__Backend source__

__UI semantics__

Physical footprint

Arrival\-time\-derived geometry

Physical modeled area

Operational buffer

Policy\-derived buffer

Operational caution; not physics

Warning zone

Arrival\-time threshold

Projected near\-term reach

Projection

Arrival\-time threshold

Longer\-horizon modeled reach; assumption\-labeled

Risk heatmap

Hazard Risk Surface

Continuous operational index

Nodes

Node registry

Sensor/network status

Incidents

Incident store

State \+ severity cues

SOS

SOS store

Categorical priority

Population

Exposure source

Context/exposure

Infrastructure

OSM/other sourced data

Impact context

## 9\.4 Visual safety rule

Do not render the footprint, operational buffer, warning zone, projection and heatmap with equally opaque fills\. Use layer hierarchy, transparency, labels and toggles so that the map remains interpretable\.

# 10\. Database & Storage Architecture

## 10\.1 PostgreSQL \+ PostGIS

PostgreSQL is the canonical relational store\. PostGIS provides spatial types/indexes/functions needed for nodes, incidents, polygons, routes, exposure and map queries\. citeturn169935search5turn169935search6

## 10\.2 Core logical tables

__Table/entity__

__Key contents__

nodes

node\_id, identity, location, firmware, connectivity, status

sensors

sensor\_id, node\_id, type, calibration/configuration

telemetry

telemetry\_id, node\_id, timestamps, measurements, source, auth metadata

sensor\_diagnostics

health inputs, quality inputs, diagnostic timestamps

hazard\_assessments

node/hazard, evidence, confidence, severity, risk, state, information condition

incidents

incident\_id, hazard, state, origin, geometry, contributing nodes, timestamps

incident\_events

immutable lifecycle/event records

spread\_runs

incident, environmental context, grid/domain, run metadata

spread\_outputs

arrival field references, geometry/risk output references

exposure\_snapshots

incident, zone, population, citizens, roads, infrastructure

actions

recommendation, approval, target, status, reason

alerts

canonical emergency event, targeting/delivery state, signature

citizens

NexAlert user identity \+ consent metadata

sos

citizen distress, location, priority, status

safe\_places

candidate destination geometry, availability, accessibility

simulation\_scenarios

scenario configuration and status

simulation\_runs

run metadata and source identifiers

audit\_events

actor, action, target, reason, timestamp

## 10\.3 Raster storage policy

Very large raster assets such as DEMs, population grids and arrival\-time surfaces should not be naïvely stored as large JSON blobs\. Keep metadata and references in PostgreSQL/PostGIS and use a file/object storage layout for immutable raster assets where appropriate\. The specific raster format and storage backend will be selected during the geospatial implementation, but the data contract must remain stable\.

# 11\. Communication & Transport Technology

## 11\.1 Transport abstraction

NexAlert separates the physical transport from the application data contract\. The telemetry record is independent of whether it arrived over Wi\-Fi/IP, an optional LoRa\-class link, or another supported local transport\.

Transport Adapter  
  ├── WiFi/IP adapter  
  ├── Optional LoRa/raw\-radio adapter  
  └── Future adapter  
        ↓  
Canonical Telemetry Envelope  
        ↓  
Authentication / validation  
        ↓  
Ingestion

## 11\.2 V1 practical transport

For the SIH prototype, use IP\-based Wi\-Fi/HTTP\(S\) or local TCP/IP connectivity where available because it simplifies the direct real\-hardware demo, local emergency portal, telemetry API and debugging\. A long\-range radio adapter may coexist when the selected hardware requires it\. No LoRaWAN/NB\-IoT network deployment is required for V1\.

## 11\.3 Application protocols

__Path__

__Protocol__

__Use__

Node → Master

HTTPS/HTTP or MQTT\-over\-IP depending on chosen adapter

Telemetry upload; schema/authenticated payload\.

Master → Cloud

HTTPS REST \+ outbound sync/WebSocket as needed

Synchronization and central services\.

Dashboard ↔ backend

HTTPS REST \+ WebSocket

Queries and live updates\.

Citizen ↔ backend

HTTPS REST \+ WebSocket/SSE

Emergency page and updates\.

Citizen ↔ local node/gateway

HTTP over local Wi\-Fi

Offline emergency page\.

Outbound notification

Web Push / optional FCM/APNs later

Subscribed online citizens\.

## 11\.4 Canonical event independence

The emergency event object is transport\-neutral\. Delivery services adapt the transport envelope, not the hazard semantics\.

# 12\. Deployment Profiles

## 12\.1 Development profile

Developer machine  
  Docker Compose  
    ├── backend  
    ├── worker  
    ├── postgres/postgis  
    ├── frontend  
    └── optional local tile/data helper  
  
ESP32  
  ↕  
Developer LAN / test network  


Docker Compose provides a reproducible way to define and run multiple development/test containers, networks and volumes from a YAML configuration\. citeturn169935search8

## 12\.2 Master/field demo profile

Raspberry Pi  
  ├── backend  
  ├── worker  
  ├── PostgreSQL \+ PostGIS  
  ├── local frontend/static assets or local frontend host  
  └── local emergency gateway services  
  
ESP32 nodes  
  ↓  
local transport  
  ↓  
Raspberry Pi  
  ↓  
local dashboard / citizen portal  
  ↓  
optional cloud sync  


## 12\.3 Cloud profile

Managed/VM Linux environment  
  ├── reverse proxy / TLS  
  ├── backend  
  ├── workers  
  ├── PostgreSQL \+ PostGIS  
  ├── object/raster storage  
  └── optional notification service  


## 12\.4 Single\-machine SIH fallback

A full cloud deployment is not required for the demonstration\. A single Raspberry Pi or developer machine may host the backend, worker, database and frontend for demonstration, provided the interfaces remain separated in code and the local/offline behavior remains testable\.

# 13\. Environment & Configuration Management

## 13\.1 Environments

__Environment__

__Purpose__

local\-dev

Fast development; mock/external services optional; synthetic data\.

integration

Full backend \+ DB \+ frontend \+ simulation \+ selected hardware path\.

master\-demo

Raspberry Pi local deployment with field nodes and local gateway\.

cloud\-demo

Public/remote demo environment with real TLS and restricted access\.

test

Automated unit/integration/system test profile\.

## 13\.2 Required configuration groups

- Database connection and migration settings\.
- API host/port and CORS/origin settings\.
- Node credentials/key references\.
- Telemetry freshness/timeouts\.
- Intelligence parameters and baseline windows\.
- Fire/geospatial grid resolution and projection horizon\.
- Risk/response thresholds\.
- Alert providers\.
- Map style/source configuration\.
- Dataset paths and provenance identifiers\.
- Simulation scenario paths\.
- Logging and audit settings\.

__No secrets in source control  
__HMAC node secrets, signing private keys, database passwords, push credentials and API secrets MUST be injected through environment/secret management\. Frontend bundles must never contain server\-side secrets\.

# 14\. Build, Packaging & Versioning

## 14\.1 Firmware

Use ESP\-IDF's CMake/Ninja\-based build flow and lock the target to the actual ESP32\-S3 board configuration\. Keep sdkconfig defaults under version control\. Use a reproducible toolchain/environment for CI where practical\. Espressif's ESP32\-S3 getting\-started documentation explicitly uses ESP\-IDF, toolchain, CMake and Ninja as the development workflow\. citeturn424934search9

## 14\.2 Python

pyproject\.toml  
  ↓  
locked Python version  
  ↓  
locked dependencies  
  ↓  
unit/integration tests  
  ↓  
container image  


## 14\.3 Frontend

package\.json  
package\-lock\.json / equivalent lockfile  
  ↓  
Node\.js version file  
  ↓  
npm/pnpm/yarn chosen once  
  ↓  
typecheck  
lint  
tests  
build  


## 14\.4 API versioning

All public application APIs start at /api/v1\. Domain schemas carry schema\_version when a persistent/transport\-level version is required\. Backward\-incompatible changes require a deliberate new version\.

# 15\. Performance & Resource Budgeting

## 15\.1 Principle

No performance target should be invented merely to make the product sound fast\. Requirements are measured on the actual ESP32 and Raspberry Pi configuration\.

## 15\.2 ESP32 benchmark

__Metric__

__Measure__

Sensor acquisition latency

Time from sampling trigger to normalized reading\.

Telemetry serialization

Time to construct canonical packet\.

HMAC overhead

Time and CPU cost per packet\.

Local intelligence

Time per evaluation cycle\.

Wi\-Fi AP responsiveness

Connection/HTTP response under load\.

Packet delivery

Loss/latency/jitter under representative load\.

Memory

Free heap and high\-water marks under combined workload\.

CPU

Task utilization under combined workload\.

Power

Relative consumption in idle/active/communication states where measured\.

## 15\.3 Master benchmark

__Workload__

__Measure__

Telemetry ingestion

Packets/sec sustainable without queue growth\.

Intelligence

Observations/sec and processing latency\.

Incident correlation

Reports/sec and query latency\.

Fire spread

Simulation wall time for demo grid/horizon\.

Polygonization

Geometry derivation time\.

Risk surface

Raster computation time\.

Exposure

Population/infrastructure overlay time\.

WebSocket updates

Event\-to\-client latency\.

## 15\.4 Browser benchmark

- Initial page load and map initialization\.
- Time from backend event to visible update\.
- Map layer update/render responsiveness for the demo geometry\.
- Memory behavior during fire\-spread replay\.
- Degraded behavior on slow network or low\-end device\.

# 16\. Security Architecture by Technology Boundary

__Boundary__

__Mechanism__

__Required behavior__

Node → Master

Per\-node secret \+ HMAC

Reject unauthenticated/tampered telemetry\.

Master → cloud

TLS \+ authenticated client/service path

Protected synchronization\.

Backend API

Application authentication/authorization

Protect authority actions and data\.

Emergency event

Digital signature / trusted public key

Local verification of authenticity\.

Replay

Sequence \+ timestamp \+ event ID/nonce

Reject duplicates/stale replay\.

Database

Credentials \+ least\-privileged service user

No public DB exposure\.

Frontend

No embedded private secrets

Use server\-side secure APIs\.

Logs

Structured \+ access\-controlled

Do not log raw secrets or unnecessary citizen data\.

## 16\.1 Key storage

Node credentials are provisioned per device\. Private signing keys remain server\-side/local\-gateway protected and are never shipped to ordinary browser clients\. Public verification keys may be distributed to citizen clients for event verification\.

## 16\.2 Threat assumptions

- A malicious device can attempt to inject telemetry\.
- A malicious Wi\-Fi network can imitate an SSID\.
- A network attacker can replay captured messages\.
- A browser can be offline or compromised; the backend remains authoritative\.
- Physical node compromise is possible; V1 focuses on protocol\-level identity and integrity\.

# 17\. Logging, Monitoring & Debugging

## 17\.1 Structured logging

All server\-side modules MUST emit structured logs with timestamp, service/module, event type, correlation/incident ID where applicable, severity and useful diagnostic context\.

## 17\.2 Debug view

A simple internal developer/operator debug view is required for demo reliability\. It should expose the raw\-to\-decision chain without making it the normal authority UX:

Telemetry  
 ↓  
Health H\_i  
 ↓  
Quality Q\_i  
 ↓  
Reliability R\_i  
 ↓  
Baseline state  
 ↓  
Anomaly A\_i  
 ↓  
Hazard evidence E\_h  
 ↓  
Confidence C\_h  
 ↓  
Severity S\_h  
 ↓  
Operational risk R\_h  
 ↓  
Hazard state  
 ↓  
Incident  
 ↓  
Spread / Exposure / Response

## 17\.3 Correlation identifiers

A single incident should be traceable across telemetry processing, incident events, spread runs, exposure snapshots, response actions and alerts through incident\_id and linked event/action/alert IDs\.

# 18\. External Data & Dataset Runtime Handling

## 18\.1 Data is a dependency, not a hardcoded asset

Geospatial and environmental datasets must be loaded through configuration and recorded with provenance\. Demo datasets should be pre\-cached for repeatability\.

## 18\.2 Categories

__Data__

__Examples / purpose__

__Runtime treatment__

DEM

Terrain slope/aspect

Preprocessed/cached region; versioned\.

Fuel

Simplified demo fuel classes

Preprocessed raster/config; clearly labeled\.

Weather

Wind/environment context

Live adapter or controlled demo input; source labeled\.

Rainfall

Flood and moisture context

Live/history adapter or scenario input\.

Population

WorldPop/GHSL\-class source

Precached raster with provenance\.

Infrastructure

OSM\-class source

Preprocessed/cached vectors\.

Fire observation

Satellite/other external context

Validation/context, not unquestioned ground truth\.

## 18\.3 Source provenance record

dataset\_id  
source\_name  
source\_url\_or\_identifier  
version/date  
download\_timestamp  
spatial\_extent  
CRS  
processing\_version  
license/usage\_note  
checksum \(where practical\)  


# 19\. Simulation Runtime Architecture

## 19\.1 Simulator as telemetry producer

The simulator runs as a Python process or worker\. It generates canonical telemetry and submits it to POST /api/v1/telemetry or the equivalent internal ingestion interface\. It MUST NOT call the incident manager, risk engine or dashboard state directly\.

## 19\.2 Scenario engine

Scenario  
  ├── source = SIMULATION  
  ├── start/end  
  ├── node set  
  ├── baseline conditions  
  ├── hazard progression  
  ├── sensor correlations  
  ├── faults  
  ├── environmental context  
  └── private evaluation ground truth \(never sent to intelligence\)  
        ↓  
Telemetry generator  
        ↓  
Canonical telemetry  
        ↓  
REAL INGESTION PIPELINE

## 19\.3 LIVE/SIMULATION parity

The only permitted semantic difference is source metadata/scenario controls\. Domain calculations are shared\. Any simulation\-only shortcut is an architecture violation unless explicitly classified as a presentation\-only test harness\.

# 20\. Detailed Network & Deployment Topology

                          ┌─────────────────────┐  
                          │   CLOUD BACKEND      │  
                          │ FastAPI \+ Workers    │  
                          │ PostgreSQL/PostGIS   │  
                          └──────────▲──────────┘  
                                     │  
                               HTTPS / Sync  
                                     │  
                     ┌───────────────┴───────────────┐  
                     │                               │  
             ┌───────┴────────┐             ┌────────┴─────────┐  
             │  MASTER / EDGE │             │ Authority        │  
             │ Raspberry Pi   │             │ Browser          │  
             │ Python \+ DB    │             │ Next\.js/React    │  
             │ Geospatial     │             └──────────────────┘  
             └───────▲────────┘  
                     │  
               Local transport  
                     │  
          ┌──────────┴───────────┐  
          │                      │  
   ┌──────┴──────┐        ┌──────┴──────┐  
   │ ESP32 Node  │  \.\.\.   │ ESP32 Node  │  
   │ Sensors     │        │ Sensors     │  
   │ Edge AI     │        │ Edge AI     │  
   │ HMAC        │        │ HMAC        │  
   └──────▲──────┘        └──────▲──────┘  
          │                      │  
          └──── local environment ┘  
  
Citizen online → Cloud/Web Push \+ Web UI  
Citizen offline → Node/local gateway Wi\-Fi → local emergency UI  


## 20\.1 Local traffic

Keep local sensor\-to\-Master traffic inside the local network/transport and do not require a public cloud round\-trip for basic edge intelligence\.

## 20\.2 Cloud traffic

Cloud connectivity is used for central persistence, broad\-area coordination, subscribed online citizen delivery, remote authority access and synchronization—not as a prerequisite for edge hazard reasoning\.

# 21\. Technology Failure Behavior

__Failure__

__Technology behavior__

__System behavior__

ESP32 reboot

Watchdog/reboot, persistent config restored

Node returns with status; missing intervals visible\.

Node storage full

Bounded ring buffer/eviction policy or backpressure

Oldest buffered data handled by policy; no memory blow\-up\.

Wi\-Fi link lost

Reconnect; buffer

Store\-and\-forward\.

Internet lost

Master remains local

Cloud state delayed; local functions continue\.

Master dead

Local node/gateway path remains available

Citizen local page and buffering survive to the degree designed\.

Cloud down

Retries bounded

Master/local operation continues\.

Postgres unavailable

Queue/retry critical writes

No silent state loss; service degrades\.

Worker crash

Supervisor/restart

Core API remains alive where possible\.

Frontend map fails

Render text/status and cached data

Emergency action remains visible\.

Invalid event

Reject/flag

No trusted UI rendering\.

Simulation process dies

Scenario stops cleanly

Existing live system unaffected\.

## 21\.1 Bound the blast radius

A failure in one module must not cascade into a total system crash\. For example, failure of population data must not stop fire detection; failure of the map renderer must not stop the emergency action message; failure of cloud sync must not stop local edge intelligence\.

# 22\. Technology Invariants

__🔒 __ESP32 V1 firmware uses ESP\-IDF \+ C/C\+\+ as the default embedded environment\.

__🔒 __Python is the reference implementation for shared intelligence mathematics\.

__🔒 __C/C\+\+ embedded intelligence is verified with golden vectors against Python\.

__🔒 __Fire\-spread geospatial simulation does not run on the ESP32\.

__🔒 __Population/infrastructure overlay does not run on the ESP32\.

__🔒 __Raspberry Pi Master and cloud backend share domain concepts and canonical contracts\.

__🔒 __V1 backend is a modular monolith plus background workers, not microservices\.

__🔒 __PostgreSQL \+ PostGIS is the canonical spatial datastore\.

__🔒 __Next\.js \+ React \+ TypeScript is the web frontend baseline\.

__🔒 __MapLibre GL JS is the map engine\.

__🔒 __Frontend does not own canonical hazard, risk, spread, exposure or response calculations\.

__🔒 __Simulation uses the same telemetry ingestion interface as real data\.

__🔒 __Docker Compose is used for reproducible local/demo service orchestration where useful\.

__🔒 __Exact dependency versions are pinned; unreviewed major\-version upgrades are prohibited during implementation\.

__🔒 __Secrets never live in source code or browser bundles\.

__🔒 __No cloud dependency is allowed inside the essential local intelligence path\.

__🔒 __No new infrastructure technology is added merely for perceived sophistication\.

__🔒 __If an implementation change alters a technology boundary, update this document and the Master Architecture before proceeding\.

# 23\. Technology Decision Matrix — What We Deliberately Did Not Choose

__Candidate__

__Decision__

__Reason__

MicroPython on ESP32

NOT DEFAULT

Technically possible, but V1 requires predictable embedded concurrency and low\-level control; use C/C\+\+ under ESP\-IDF\.

C\+\+ fire\-spread engine on ESP32

NO

Wrong compute target; heavy geospatial/raster workload belongs on Master/cloud\.

C\+\+ backend

NO

Python is materially better for the selected scientific/geospatial/backend stack and rapid iteration\.

Microservices

NO

Operational complexity is unjustified for a six\-person SIH team\.

Kafka\-class streaming

NO

No V1 scale requirement justifies it\.

Kubernetes

NO

No need for cluster orchestration in prototype\.

3D/WebGL terrain engine

NO

Explicitly deferred; 2D geospatial command view is the required product\.

Vector\-tile backend

DEFERRED

Use GeoJSON/appropriate raster sources for demo\-scale data; optimize later if datasets require\.

Native app

DEFERRED

Web/local citizen path is the V1 product\.

Satellite live dependency

DEFERRED

External evidence remains additive, not required for local decisions\.

Advanced ML for fire

NO V1

Real data volume does not justify a trained classifier; deterministic/calibrated reasoning is locked\.

## 23\.1 Technology choices can change only for evidence

A technology may be reconsidered only when it fails a measurable requirement, introduces an unacceptable security/reliability problem, or becomes unavailable\. Popularity, novelty, or a desire for more buzzwords is not sufficient justification\.

# 24\. Implementation Order Driven by Technology Dependencies

__Phase__

__Build__

__Exit condition__

1

Repo \+ Python environment \+ frontend scaffold \+ firmware scaffold

All projects build cleanly\.

2

Postgres/PostGIS \+ migrations \+ canonical schemas

Database initializes reproducibly\.

3

ESP32 telemetry \+ heartbeat \+ HMAC \+ buffering

Real packet reaches ingestion reliably\.

4

Python ingestion \+ validation \+ idempotency

Hardware \+ simulation packet path works\.

5

Intelligence reference implementation

TRD intelligence tests pass\.

6

ESP32 intelligence subset \+ golden vectors

Embedded parity verified\.

7

Incident manager

Merge/split and lifecycle tests pass\.

8

Fire geospatial engine

Core spread tests pass\.

9

Exposure \+ risk

Sourced demo data produces reproducible outputs\.

10

Response/alerts/SOS

Human approval and citizen workflows pass\.

11

Authority dashboard

Live command center consumes canonical APIs\.

12

Citizen UI/local gateway

Online/offline emergency experience works\.

13

Simulation/replay

Same pipeline verified\.

14

Resilience/security/benchmarks

Mandatory pre\-freeze gates pass\.

15

Polish

Glassmorphism/UI polish, animation, demo instrumentation\.

## 24\.1 Rule for parallelization

Frontend can begin against mocked canonical response fixtures before the backend is complete, but mocks must conform to the final schemas\. Geospatial UI can use frozen fixture GeoJSON while the engine is being implemented\. No mock may silently evolve into a second undocumented schema\.

# 25\. Vibe\-Coding Instructions for Agents

## 25\.1 Agent operating procedure

- Read Document 01 and this document before editing architecture\-sensitive code\.
- Read the domain\-specific document before implementing that domain\.
- Use requirement IDs from Document 02 in issue/commit/test references where practical\.
- Implement the smallest conformant module; do not introduce unrelated frameworks\.
- Keep computation server/edge\-side according to the compute allocation matrix\.
- Use typed interfaces at module boundaries\.
- Write tests before changing shared formulas where practical\.
- For Python/C\+\+ parity, add/update a golden\-vector fixture whenever the reference math changes\.
- Do not hard\-code configurable thresholds in application logic\.
- Log enough context to diagnose a demo failure without logging secrets or unnecessary citizen data\.
- After implementation, run unit, integration and relevant system tests before declaring a requirement complete\.

## 25\.2 Prohibited agent behavior

- Do not add a new database, message broker, ML framework or frontend framework without explicit approval\.
- Do not migrate the architecture to microservices\.
- Do not move fire spread into the ESP32 because it seems convenient\.
- Do not replace PostGIS with ad hoc JSON geometry storage\.
- Do not add a second simulation path that bypasses telemetry ingestion\.
- Do not auto\-dispatch responders\.
- Do not silently replace missing datasets with fabricated values\.
- Do not change the visual design language from the locked dark grey/black glassmorphism system without UI/UX spec approval\.

# 26\. Final Stack Summary — Implementation Card

__Component__

__Final V1 choice__

__Execution target__

Field firmware

ESP\-IDF \+ C/C\+\+

ESP32\-S3

Field scheduler

FreeRTOS via ESP\-IDF

ESP32\-S3

Embedded crypto

HMAC \+ secure key handling

ESP32\-S3

Reference intelligence

Python

Developer/Master/Cloud

Embedded intelligence

C/C\+\+ equivalent subset

ESP32\-S3

Master application

Python \+ FastAPI\-style backend

Raspberry Pi/Linux

Geospatial compute

Python \+ geospatial libraries \+ PostGIS

Raspberry Pi/Linux or cloud

Database

PostgreSQL \+ PostGIS

Master/cloud

Background workers

Python worker profile

Master/cloud

Web frontend

Next\.js \+ React \+ TypeScript

Browser/Node build

Visual system

Tailwind \+ CSS custom properties

Browser

Maps

MapLibre GL JS

Browser

Real\-time

WebSocket/SSE

Backend/browser

Simulation

Python

Master/developer/cloud

Containers

Docker \+ Compose for reproducible environments

Dev/demo

Testing

pytest \+ frontend tests \+ firmware tests

CI/dev

Native app

Android/iOS, optional

Deferred

__The core architecture in one line  
__ESP32\-S3 senses and reasons locally → Raspberry Pi aggregates and performs heavy geospatial/operational computation → backend persists and coordinates → TypeScript web clients render the same canonical truth\.

# 27\. Technology Baseline Acceptance Checklist

__☐ 01  __ESP\-IDF firmware builds for the exact selected ESP32\-S3 target\.

__☐ 02  __C/C\+\+ firmware has a documented task/concurrency model\.

__☐ 03  __ESP32 can perform sensing \+ Wi\-Fi/AP/transport \+ HMAC \+ local intelligence under benchmarked load\.

__☐ 04  __Python reference intelligence is implemented and testable independent of the API\.

__☐ 05  __Golden\-vector tests exist for Python vs embedded C/C\+\+ shared functions\.

__☐ 06  __Raspberry Pi can run the local backend and database profile\.

__☐ 07  __PostGIS spatial operations are validated on the chosen deployment\.

__☐ 08  __Frontend builds with Next\.js/React/TypeScript and consumes typed API fixtures\.

__☐ 09  __MapLibre renders fixture current/warning/projection geometries and live node/incident markers\.

__☐ 10  __Local citizen emergency page can operate without cloud\.

__☐ 11  __Cloud synchronization is optional to the essential local loop\.

__☐ 12  __Simulation publishes canonical telemetry through the same endpoint\.

__☐ 13  __Secrets/keys are supplied through configuration/secret handling, not committed\.

__☐ 14  __Dependency versions are pinned and reproducible\.

__☐ 15  __Docker Compose can bring up the local software stack reproducibly\.

__☐ 16  __Structured logs and an internal debug path exist\.

__☐ 17  __No implementation has introduced an unauthorized framework or infrastructure dependency\.

# 28\. Technology Reference Notes

The stack choices above were cross\-checked against current official documentation where relevant\. Exact dependency versions must still be pinned and tested as part of implementation\.

__Technology__

__Reference note__

ESP\-IDF / ESP32\-S3 C\+\+

Espressif documents C\+\+ application support for ESP32\-S3 and provides the ESP\-IDF framework/toolchain workflow\. citeturn424934search0turn424934search8turn424934search9

Python

Python 3\.14 is a current stable release; project implementation should pin an exact compatible patch version rather than track 'latest'\. citeturn424934search4

FastAPI

Official deployment documentation describes deployment as serving the API through an appropriate production/runtime setup\. citeturn424934search2

Next\.js / React / TypeScript

Next\.js is a React framework; official React documentation supports TypeScript with React\. citeturn169935search0turn424934search6turn424934search1

MapLibre GL JS

Official docs support interactive maps, GeoJSON, raster sources and realtime updates; it is suitable for NexAlert's operational mapping layer\. citeturn169935search1turn169935search3

PostGIS

PostGIS extends PostgreSQL with spatial storage, spatial indexes and spatial analysis functions including distance, area, intersection and buffering\. citeturn169935search5turn169935search6

Docker Compose

Official Docker documentation describes Compose as the mechanism for defining/running multi\-container environments with networks and volumes\. citeturn169935search8

