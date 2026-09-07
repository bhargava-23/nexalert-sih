__NEXALERT__

__Configuration, Parameter & Feature\-Flag Registry__

FINAL IMPLEMENTATION SPECIFICATION  •  V1 / SIH 2026

__Field__

__Value__

Document ID

NEX\-19\-CONFIG\-FLAGS

Status

FINAL / Implementation\-ready

Authority

Master Architecture \+ TRD \+ Mathematical Intelligence \+ Geospatial \+ Hardware \+ Backend \+ Data \+ Multi\-Hazard \+ Operations \+ Communication/Resilience \+ UI \+ Simulation \+ Security \+ Validation \+ Implementation

Purpose

Single controlled registry for tunable constants, thresholds, policy values, hardware limits, feature flags, and environment settings across Edge, Master, Backend, Simulation, and UI\.

Core rule

Code reads configuration; code does not silently invent production thresholds\.

Safety posture

Conservative defaults; unsafe or ambiguous values fail closed or become UNKNOWN/DEGRADED rather than fabricating certainty\.

# DOCUMENT MAP

1\. Registry Governance & Rules

2\. Configuration Namespaces

3\. Edge Node & Sensor Parameters

4\. Intelligence & Baseline Parameters

5\. Hazard Reasoning Parameters

6\. Fire / Geospatial Parameters

7\. Incident / Alert / Response Parameters

8\. Communication & Resilience Parameters

9\. Security Parameters

10\. Simulation / Replay / Scenario Parameters

11\. UI / UX & Presentation Parameters

12\. Environment Profiles & Deployment Overrides

13\. Feature\-Flag Registry

14\. Validation Gates & Change Control

15\. SIH Demo Profile

16\. Implementation Checklist

# 1\. Registry Governance & Rules

This registry is the authoritative catalog of named configuration\. Every tunable value must have a stable key, unit/type, default, allowed range or enumerated values, owner, scope, and validation rule\. Values affecting safety, incident state, alert issuance, geospatial propagation, authentication, or citizen communication require an explicit change record and corresponding validation tests\.

## 1\.1 Configuration classes

__Class__

__Meaning__

__Examples__

__Change policy__

CONST

Mathematical constant or fixed protocol value

MAD scale 1\.4826; Earth radius

Code review; rare change

TUNABLE

Operational model parameter

anomaly lambda; persistence window

Config change \+ tests

POLICY

Authority/operator policy

operational buffer; alert cooldown

Named owner \+ audit

LIMIT

Hard safety/resource ceiling

payload size; queue depth

Must pass load/failure tests

ENUM

Controlled state/mode value

NORMAL/WATCH/\.\.\.

Code\+contract change if altered

FLAG

Feature gate

fire\.engine\_v1

Default OFF for experimental features

SECRET

Credential/key material

node HMAC secret

Never stored in source/config repo

PROFILE

Environment bundle

DEV/SIM/STAGE/SIH/PROD

Versioned snapshot

## 1\.2 Naming convention

Use lower\_snake\_case keys with domain prefix: edge\.\*, intelligence\.\*, hazard\.\*, fire\.\*, incident\.\*, comm\.\*, security\.\*, sim\.\*, ui\.\*, deploy\.\*, flag\.\*\. Units belong in the registry description and schema, not in key names, except where ambiguity is operationally dangerous\.

## 1\.3 Runtime precedence

1. Built\-in safe default\.
2. Versioned application configuration file/profile\.
3. Environment\-specific override\.
4. Secret manager / provisioning store for secrets\.
5. Runtime operator controls only for explicitly whitelisted POLICY keys; never for core security primitives or immutable protocol semantics\.

The effective configuration must be queryable and exposed in the Authority System/Audit surfaces as a version/hash, not as secret values\.

# 2\. Configuration Namespaces

__Namespace__

__Scope__

__Primary consumers__

__Typical risk__

edge\.\*

ESP32 field node

firmware

High

sensor\.\*

Sensor drivers/calibration

ESP32 \+ ingestion

High

intelligence\.\*

Health/quality/baseline/anomaly

Edge \+ Master

High

hazard\.\*

Hazard evidence/state

Edge \+ Master

Critical

fire\.\*

Fire spread/geospatial

Master

Critical

incident\.\*

Correlation/state

Backend \+ Master

Critical

alert\.\*

Notification policy

Backend

Critical

comm\.\*

Transport/store\-forward/offline

Edge \+ Master

High

security\.\*

Authentication/signing/replay

All

Critical

sim\.\*

Simulation/replay

Simulation

Medium

ui\.\*

Presentation behavior

Frontend

Medium

deploy\.\*

Deployment/runtime

All

High

flag\.\*

Feature exposure

All

High

# 3\. Edge Node & Sensor Parameters

__Key__

__Type / Unit__

__Default__

__Allowed / Notes__

__Owner__

edge\.telemetry\_interval\_s

int / s

5

>=1; normal telemetry cadence

Firmware

edge\.heartbeat\_interval\_s

int / s

30

>=5; lightweight liveness

Firmware

edge\.health\_report\_interval\_s

int / s

300

~5 min detailed health

Firmware

edge\.max\_buffer\_records

int / records

2000

bounded ring buffer; hardware\-memory dependent

Firmware

edge\.critical\_queue\_priority

enum

CRITICAL

critical before normal when transport constrained

Firmware

edge\.local\_service\_enabled

bool

true

required for local emergency path on supported node/gateway

Firmware

edge\.local\_ap\_ssid\_prefix

string

NEXALERT\-

must not contain secrets/PII

Firmware

edge\.local\_ap\_max\_clients

int

8

benchmark\-dependent; must not starve sensing

Firmware

edge\.sequence\_counter\_persist\_every

int / records

100

persistent checkpoint cadence; replay risk trade\-off

Firmware

sensor\.temp\.min\_c

float / °C

\-40

validate against actual sensor

Hardware

sensor\.temp\.max\_c

float / °C

85

validate against actual sensor

Hardware

sensor\.humidity\.min\_rh

float / %RH

0

sensor\-specific

Hardware

sensor\.humidity\.max\_rh

float / %RH

100

sensor\-specific

Hardware

sensor\.water\_level\.min\_m

float / m

0

negative only if sensor semantics permit

Hardware

sensor\.pm\.max\_ugm3

float / µg/m³

1000

display/quality ceiling; calibrated sensor dependent

Hardware

sensor\.gas\.max\_engineering

float

TBD

must be calibration\-defined; no fake ppm

Hardware

sensor\.stale\_after\_s

int / s

30

measurement freshness threshold; override per sensor

Firmware

sensor\.failure\_after\_s

int / s

120

no valid reading/heartbeat window

Firmware

Calibration constants \(offset, gain, response curve, gas species mapping, sensor\-native units\) are node\-specific assets, not universal globals\. A calibrated sensor profile must identify hardware revision, calibration date, method, and validity interval\.

# 4\. Intelligence & Baseline Parameters

__Key__

__Type / Unit__

__Default__

__Allowed / Notes__

__Owner__

intelligence\.health\_weight\_sum\_tol

float

0\.0001

weights must sum to 1 within tolerance

ML/Platform

intelligence\.quality\_floor

float 0\-1

0\.2

below floor may suppress inference

ML

intelligence\.reliability\_floor

float 0\-1

0\.2

node/signal below floor treated weak evidence

ML

intelligence\.mad\_scale

float

1\.4826

robust\-normal consistency constant

ML

intelligence\.mad\_epsilon

float

1e\-6

prevents divide\-by\-zero

ML

intelligence\.z\_cap

float

8

bounds anomaly transform

ML

intelligence\.anomaly\_lambda

float

3

positive; controls saturation of A\_i

ML

intelligence\.baseline\_min\_samples

int

120

readiness gate; hazard/sensor specific overrides allowed

ML

intelligence\.baseline\_learning\_timeout\_s

int / s

1800

after timeout state may remain LEARNING/DEGRADED

ML

intelligence\.baseline\_freeze\_on\_confirmed

bool

true

prevent contaminated learning

ML

intelligence\.recovery\_min\_good\_samples

int

30

before returning to LEARNING/READY

ML

intelligence\.trend\_window\_s

int / s

300

trend\-relative water/soil context

ML

intelligence\.drift\_window\_s

int / s

3600

longer quality/drift assessment

ML

## 4\.1 Sensor health / reliability weighting

The production pipeline remains H\_i \-> Q\_i \-> R\_i = H\_i Q\_i \-> baseline/anomaly\. Battery is intentionally excluded from R\_i and is surfaced as a power/health dimension\. Hard failure gates H\_i to zero\. Missing data is never interpreted as numeric zero\.

# 5\. Hazard Reasoning Parameters

__Key__

__Type__

__Default__

__Notes__

__Owner__

hazard\.min\_core\_coverage

float 0\-1

0\.67

minimum core\-evidence coverage before confidence assessment

Safety

hazard\.coverage\_weight

float

0\.30

C\_cov contribution

Safety

hazard\.agreement\_weight

float

0\.30

C\_agree contribution

Safety

hazard\.temporal\_weight

float

0\.20

C\_temp contribution

Safety

hazard\.baseline\_weight

float

0\.20

C\_base contribution

Safety

hazard\.confidence\_assess\_floor

float 0\-1

0\.30

below => confidence N/A

Safety

hazard\.confirm\_persistence\_s

int / s

30

hazard\-specific overrides permitted

Safety

hazard\.critical\_persistence\_s

int / s

10

fast escalation window; cannot bypass safety evidence

Safety

hazard\.resolve\_clear\_s

int / s

120

clear window before RESOLVED

Safety

hazard\.watch\_decay\_s

int / s

300

hysteresis decay where applicable

Safety

hazard\.state\_merge\_radius\_m

float / m

50

incident correlation starting point

Operations

hazard\.state\_merge\_window\_s

int / s

30

incident correlation starting point

Operations

hazard\.info\_condition\_min\_reliability

float 0\-1

0\.40

maps to GOOD/DEGRADED/UNKNOWN policy

Safety

The numerical defaults above are implementation starting points and must be calibrated/validated against actual field trials and golden scenarios before production use\. They are not probabilities or evidence that a hazard exists\.

# 6\. Fire / Geospatial Parameters

__Key__

__Type / Unit__

__Default__

__Notes__

__Owner__

fire\.grid\_cell\_size\_m

float / m

25

metric projected grid; benchmark on target area

Geo

fire\.max\_runtime\_area\_km2

float / km²

25

simulation guardrail for demo runtime; scale tested separately

Geo

fire\.neighbor\_connectivity

enum

8

8\-neighbor arrival propagation in V1

Geo

fire\.meteorological\_wind\_is\_from

bool

true

convert FROM to TO before propagation

Geo

fire\.wind\_midflame\_factor

float 0\-1

0\.4

WAF starting point; fuel/context dependent

Geo

fire\.nonburnable\_ros

float / m/s

0

barrier state

Geo

fire\.warning\_horizon\_s

int / s

1800

warning zone horizon

Operations

fire\.projection\_horizon\_s

int / s

3600

must be > warning horizon

Operations

fire\.recompute\_on\_environment\_change

bool

true

freeze history, reseed frontier, recompute future

Geo

fire\.operational\_buffer\_m

float / m

100

policy buffer; distinct from physical footprint

Authority

fire\.risk\_time\_decay\_lambda

float

0\.001

U\_c exp\(\-lambda\*tau\); calibrate for UI use

Safety

fire\.use\_directional\_vectors

bool

true

wind\+slope directional vectors; never arbitrary scalar sum

Geo

fire\.simplify\_display\_geometry

bool

true

display only; raw raster/geometry remains source of truth

Geo

Fire engine must use a projected metric CRS\. Meteorological wind direction is interpreted as FROM and converted to propagation direction\. Physical footprint, warning/projected zones, and operational buffer are separate layers\.

# 7\. Incident / Alert / Response Parameters

__Key__

__Type__

__Default__

__Notes__

__Owner__

incident\.correlation\_radius\_m

float / m

50

same hazard \+ within radius \+ temporal window => candidate same incident

Ops

incident\.correlation\_window\_s

int / s

30

same incident temporal window

Ops

incident\.reopen\_window\_s

int / s

300

post\-resolve recurrence behavior

Ops

incident\.alert\_cooldown\_s

int / s

300

fatigue guardrail; critical escalation may override

Ops

alert\.require\_human\_approval

bool

true

NexAlert recommends; human approves

Authority

alert\.max\_retry\_count

int

8

transport\-specific retry cap

Backend

alert\.exponential\_backoff\_base\_s

float / s

2

retry base

Backend

alert\.max\_backoff\_s

int / s

300

cap retry delay

Backend

alert\.ttl\_s

int / s

3600

alert expiration; emergency flow may differ

Backend

alert\.resolution\_requires\_explicit\_standdown

bool

true

no silent disappearance

Authority

sos\.hold\_seconds

int / s

3

press\-and\-hold UX; not auto reject outside hazards

Citizen

sos\.priority\_tiers

enum set

IMMEDIATE,HIGH,STANDARD,VERIFY

categorical; no fake numeric score

Authority

response\.no\_safe\_route\_action

enum

SHELTER\_IN\_PLACE

fallback when route/destination unavailable

Authority

# 8\. Communication & Resilience Parameters

__Key__

__Type__

__Default__

__Notes__

__Owner__

comm\.hmac\_algorithm

enum

HMAC\-SHA256

per\-node transport/authentication

Security

comm\.replay\_window\_s

int / s

120

timestamp freshness window; sequence is primary dedup primitive

Security

comm\.max\_clock\_skew\_s

int / s

60

adjust with time source quality

Security

comm\.store\_forward\_enabled

bool

true

bounded ring buffer

Firmware

comm\.critical\_first\_queue

bool

true

critical data before routine telemetry where transport constrained

Firmware

comm\.retry\_jitter\_s

float / s

1

prevents synchronized retries

Firmware/Backend

comm\.offline\_portal\_cache\_s

int / s

900

local emergency state cache lifetime

Citizen

comm\.local\_gateway\_health\_interval\_s

int / s

15

Master/gateway health heartbeat

Resilience

comm\.master\_failure\_timeout\_s

int / s

45

distinguish Master failure from internet failure

Resilience

comm\.internet\_failure\_timeout\_s

int / s

60

cloud reachability classification

Resilience

comm\.partition\_reconciliation\_window\_s

int / s

600

history reconciliation window

Backend

comm\.max\_offline\_event\_age\_s

int / s

86400

stale event handling; still retain audit lineage

Backend

# 9\. Security Parameters

__Key__

__Type__

__Default__

__Notes__

__Owner__

security\.signature\_algorithm

enum

Ed25519

signed emergency/event candidate where enabled

Security

security\.hmac\_secret\_source

enum

secure\_provisioning

never hard\-code in repo

Security

security\.nonce\_bytes

int

16

cryptographic nonce size

Security

security\.event\_id\_entropy\_bits

int

128

unique event identifiers

Security

security\.max\_auth\_failures\_per\_min

int

30

rate\-limit; tune to deployment

Security

security\.key\_rotation\_days

int

90

deployment policy; emergency rotation can be earlier

Security

security\.revocation\_cache\_s

int / s

3600

bounded offline cache

Security

security\.admin\_session\_ttl\_s

int / s

1800

authority dashboard

Security

security\.audit\_retention\_days

int / days

365

deployment/legal policy dependent

Security

# 10\. Simulation / Replay / Scenario Parameters

__Key__

__Type__

__Default__

__Notes__

__Owner__

sim\.mode

enum

SIMULATION

SIMULATION/LIVE; explicit separation

Simulation

sim\.random\_seed

int

20260907

must be recorded in run metadata

Simulation

sim\.tick\_interval\_s

float / s

1

scenario clock step

Simulation

sim\.telemetry\_jitter\_s

float / s

0\.2

synthetic transport timing variability

Simulation

sim\.packet\_loss\_rate

float 0\-1

0\.00

scenario override

Simulation

sim\.duplicate\_rate

float 0\-1

0\.00

replay/dedup test

Simulation

sim\.missing\_rate

float 0\-1

0\.00

missing \!= zero

Simulation

sim\.stale\_rate

float 0\-1

0\.00

freshness/quality testing

Simulation

sim\.bias\_drift\_rate

float

0\.00

sensor drift scenario

Simulation

sim\.contradiction\_rate

float 0\-1

0\.00

cross\-sensor disagreement scenario

Simulation

sim\.freeze\_ground\_truth\_output

bool

true

ground truth never enters inference path

Safety

sim\.replay\_deterministic

bool

true

seed \+ scenario manifest \+ config hash

Simulation

sim\.allow\_live\_transport

bool

false

must remain false for simulation environment

Safety

# 11\. UI / UX & Presentation Parameters

__Key__

__Type__

__Default__

__Notes__

__Owner__

ui\.map\.refresh\_s

float / s

2

Authority map target; adaptive under load

Frontend

ui\.citizen\.emergency\_first\_view

bool

true

hazard/severity/state/distance/direction/freshness first

Citizen

ui\.show\_internal\_scores\_by\_default

bool

false

C\_h/S\_h/R\_h hidden from default citizen UX

Product

ui\.show\_information\_condition

bool

true

GOOD/DEGRADED/UNKNOWN explicit

Product

ui\.show\_physical\_vs\_operational\_zone

bool

true

distinct layers/labels

Safety

ui\.colorblind\_safe\_palette

bool

true

mandatory design rule

UX

ui\.sos\_hold\_seconds

int / s

3

must match sos\.hold\_seconds

Citizen

ui\.offline\_banner\_enabled

bool

true

source/freshness/degraded status visible

Citizen

ui\.simplify\_fire\_geometry\_for\_display

bool

true

does not modify source geometry

Frontend

# 12\. Environment Profiles & Deployment Overrides

__Profile__

__Purpose__

__Key characteristics__

DEV

local development

safe synthetic data; simulation only; secrets from local vault/env

TEST

automated tests

golden vectors, fault injection, deterministic seed; no external alerts

SIM

operator simulation

full simulator; same ingestion path; LIVE transport disabled

STAGE

integration / field rehearsal

realistic topology; sandbox notifications; full audit

SIH

competition demo

controlled demo scenario; local resilience enabled; external alert side effects disabled

PROD

future deployment

approved calibration \+ policy; real credentials; alert side effects enabled only with authority approval

Profiles are versioned bundles\. A deployment must expose profile name, registry version, effective configuration hash, git commit, firmware build, backend build, model/config asset hashes, and simulation seed when applicable\.

# 13\. Feature\-Flag Registry

__Flag__

__Default__

__Purpose__

__Safety / rollout rule__

flag\.fire\_engine\_v1

true

enable physics\-informed cellular fire engine

mandatory for fire simulation; no decorative frontend\-only spread

flag\.fire\_ml\_classifier

false

optional learned fire classifier

OFF until real data shows improvement over deterministic baseline

flag\.flood\_engine\_v1

true

enable flood hazard path

use validated synthetic \+ real trial evidence

flag\.pollution\_engine\_v1

true

enable pollution reasoning

hazard\-specific evidence rules

flag\.landslide\_engine\_v1

false

experimental landslide path

OFF until validated

flag\.heat\_engine\_v1

true

extreme heat reasoning

validated thresholds only

flag\.distributed\_fusion

true

Master cross\-node fusion

must preserve local truth under disagreement

flag\.local\_offline\_portal

true

offline citizen emergency UI

mandatory resilience path

flag\.web\_push

true

online citizen notifications

requires explicit subscription/permission

flag\.authority\_auto\_dispatch

false

autonomous dispatch

must remain OFF; human approval required

flag\.route\_optimization

false

safe\-route optimization

SHELTER\_IN\_PLACE fallback remains mandatory

flag\.external\_cell\_broadcast

false

future authorized integration

not for prototype

flag\.experimental\_risk\_heatmap

false

new risk algorithm

must be isolated and benchmarked

flag\.telemetry\_raw\_archive

true

retain raw telemetry for audit/replay

bounded/retention policy

flag\.synthetic\_live\_merge

false

mix simulation telemetry with live

must stay OFF in SIH/live unless specifically approved

## 13\.1 Flag safety classes

__Class__

__Examples__

__Default__

__Rule__

SAFE

UI\-only presentation

ON/OFF

may be runtime\-toggled

CONTROLLED

simulation/experimental model

OFF

change requires test evidence

CRITICAL

security, dispatch, source\-of\-truth semantics

fixed/guarded

runtime toggle prohibited or role\-gated

ENVIRONMENT

transport/external integration

profile\-controlled

must match deployment profile

# 14\. Validation Gates & Change Control

- Every new key requires schema/type/unit/default/range/owner and a test reference\.
- Every threshold used in a safety or state transition requires a golden scenario proving expected NORMAL/WATCH/SUSPECTED/CONFIRMED/CRITICAL/RESOLVED behavior\.
- Every fire parameter change requires geospatial benchmark plus no\-regression test for non\-burnable cells, wind FROM→TO conversion, 8\-neighbor propagation, time horizons, and history\-preserving recomputation\.
- Every communication/security parameter change requires replay, duplication, partition, authentication, and offline\-path tests\.
- Every UI parameter that changes emergency prominence must pass citizen/authority acceptance tests and accessibility checks\.
- Production profile cannot contain TBD values, experimental flags, placeholder secrets, or simulation\-only transport settings\.
- Configuration changes are versioned independently from application builds when possible; the effective configuration hash is stored in audit/event metadata\.
- Rollback means restoring a previously validated profile version, not manually editing individual values during an incident\.

## 14\.1 Registry validation matrix

__Check__

__Requirement__

__Failure action__

Schema

valid type, enum/range, unit

reject registry load

Cross\-key consistency

warning horizon < projection horizon; SOS times match; weights sum

reject load or mark profile invalid

Safety ceilings

no value exceeds documented hard limit

reject profile

Secrets hygiene

no secrets in plain config

reject CI build

Feature compatibility

flag combinations valid

reject deployment

Migration

new/removed keys handled by version

block startup on unknown critical keys

Runtime observability

effective hash/version visible

degrade system if unavailable for authority diagnostics

# 15\. SIH Demo Profile

The SIH profile is a deterministic, low\-risk demonstration configuration\. It keeps the production architecture visible while preventing accidental real\-world side effects\. Simulation telemetry uses the same ingestion path as hardware, but simulation mode is explicit and external notification integrations remain disabled\.

__Key__

__SIH value__

__Why__

deploy\.profile

SIH

explicit competition environment

sim\.mode

SIMULATION

no live side effects

sim\.random\_seed

20260907

deterministic replay

sim\.replay\_deterministic

true

repeatable demo

flag\.authority\_auto\_dispatch

false

human remains in control

flag\.local\_offline\_portal

true

demonstrate resilience

flag\.external\_cell\_broadcast

false

no external broadcast

flag\.synthetic\_live\_merge

false

keep simulation/live isolated

fire\.warning\_horizon\_s

1800

clear warning visual

fire\.projection\_horizon\_s

3600

clear projection visual

alert\.require\_human\_approval

true

demonstrate approval workflow

ui\.show\_information\_condition

true

demonstrate honest uncertainty

# 16\. Implementation Checklist

- Create typed registry schema \(Pydantic/JSON Schema\-equivalent\) shared by backend, simulator, and generated TypeScript types\.
- Generate a machine\-readable config bundle from this registry; keep human\-readable DOCX as governance artifact\.
- Add startup validation for ranges, enums, cross\-key constraints, and forbidden production combinations\.
- Add config hash to telemetry metadata, incident records, alerts, simulation manifests, and audit trail where applicable\.
- Expose non\-secret effective configuration in Authority > System > Configuration\.
- Keep secret material outside the registry: per\-node HMAC secrets, signing keys, database credentials, push credentials, and deployment tokens use secure provisioning/secrets storage\.
- Add golden tests for every critical threshold and feature\-flag branch\.
- Freeze the SIH profile before demo rehearsal; create an immutable snapshot and checksum\.
- Never hot\-edit critical safety parameters during a live incident\. Use a validated profile change and auditable deployment action\.
- When a value is unknown or not calibrated, use TBD/disabled in non\-production profiles rather than inventing a plausible number\.

# FINAL INVARIANTS

- Configuration is data, not hidden logic\.
- No threshold becomes authoritative merely because it is convenient\.
- Confidence is not probability; risk is not probability\.
- Multi\-hazard risk layers remain independent\.
- Local node truth is not erased by distributed disagreement\.
- Physical hazard footprint and operational policy buffers remain distinct\.
- Simulation cannot leak private ground truth into inference\.
- Autonomous dispatch remains disabled; NexAlert recommends and a human approves\.
- Master failure and internet failure are distinct operating conditions\.
- An unknown value leads to honest degradation, not fabricated certainty\.

