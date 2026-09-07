__NEXALERT__

__DATA, DATASET, PROVENANCE & SYNTHETIC TELEMETRY SPECIFICATION__

*Final V1 Engineering Baseline — Data Trust, Scenario Generation, Ground Truth Separation & Reproducible Evaluation*

__Field__

__Value__

Document ID

NEXALERT\-FINAL\-08

Status

Final V1 Engineering Baseline

Primary scope

Environmental telemetry, public data, synthetic data, geospatial context, provenance, scenario control and evaluation datasets

Authority

Master System Architecture \+ TRD \+ Mathematical Intelligence \+ Fire/Geospatial \+ Hardware/Edge specifications

Implementation posture

Simulation and real hardware use the same telemetry ingestion contract; synthetic generators produce telemetry, not hidden answers\.

Last updated

September 2026

__Core principle — __Data is an input to a trustworthy decision system, not a substitute for one\. NexAlert must distinguish observed measurements, derived features, external context, simulator state and private evaluation ground truth\.

# Document Control & Authority

__Authority layer__

__Rule__

1\. Master System Architecture & Invariants

Defines system boundaries, trust model, resilience rules and non\-negotiable invariants\.

2\. Technical Requirements Document

Defines required behaviors, interfaces and acceptance criteria\.

3\. Mathematical Intelligence & Hazard Reasoning

Defines health, quality, reliability, anomaly, evidence, confidence, severity, risk and state logic\.

4\. Fire Spread \+ Geospatial Specification

Defines DEM/fuel/moisture/wind inputs, spread computation, arrival times, geometry, operational buffers and hazard risk surfaces\.

5\. Hardware / Edge Node Specification

Defines sensor classes, telemetry envelope, diagnostics, timestamps, authentication, buffering and edge responsibilities\.

6\. This Data Specification

Defines data classes, provenance, validation, synthetic telemetry, labels/ground truth separation, lineage and dataset release rules\.

Legacy documents

Historical reference only\. They must not silently override the current architecture \(for example old STM32\+ESP32 split, old transport assumptions or old storage choices\)\.

# 1\. Data System Purpose

The NexAlert data system exists to make every important input traceable, quality\-aware, reproducible and safe to use across live hardware, simulation, replay, analytics and evaluation\. The same canonical telemetry contract must flow through the system regardless of whether a packet originated from a physical node or a simulator\.

## 1\.1 Data objectives

- Capture environmental observations without losing timestamp, node identity, provenance or diagnostic context\.
- Distinguish measurement truth from derived intelligence such as anomaly scores, evidence, confidence, severity and risk\.
- Preserve enough lineage to answer: what was observed, by which node, when, with what quality, from which source and after which transformations?
- Enable deterministic replay of incidents and synthetic scenarios using the same ingestion path as live telemetry\.
- Prevent synthetic labels, future knowledge or simulator internals from leaking into live\-like reasoning paths\.
- Support controlled public\-data enrichment without allowing stale or unsupported external data to be treated as direct sensor truth\.
- Enable dataset versioning, parameter versioning and evaluation reproducibility\.

## 1\.2 Data trust classes

__Class__

__Meaning__

__Examples__

__Can directly drive live decisions?__

Observed

Measurement originating from a physical sensor/node\.

temperature, PM2\.5, water level, rainfall, battery voltage

Yes, subject to health/quality/reliability gating\.

Derived

Computed from observed data by a versioned transformation\.

MAD scale, anomaly score, trend, local aggregation

Yes, when produced by approved logic\.

External context

Imported environmental/geospatial/context data\.

DEM, weather fields, population, roads, satellite fire context

Yes, only through explicitly approved context interfaces\.

Synthetic observation

Simulator\-generated telemetry that mimics node packets\.

normal telemetry, drift, correlated fire onset

Yes for simulation/testing only; never presented as field observation\.

Simulation state / private truth

Hidden simulator internals used to evaluate whether outputs are correct\.

true ignition cell, true arrival time, fault injection truth

No\. Must be inaccessible to the reasoning service during the run\.

Human annotation

Review or operator assessment attached after observation\.

confirmed incident, calibration note, false positive review

Only where the workflow explicitly permits human confirmation\.

Presentation

Frontend\-only transformation\.

map tiles, rounded values, chart bins

No\.

# 2\. Canonical Data Architecture

Physical / Synthetic Source \-> Ingestion \-> Schema \+ Auth Validation \-> Time/Sequence Checks  
                     \-> Diagnostic \+ Quality Context \-> Normalized Telemetry Store  
                     \-> Intelligence Pipeline \-> Incident / Hazard State \-> Alerts / Dashboard / Citizen UI  
                     \-> Audit \+ Evaluation Lineage

The data layer must not create a second hidden telemetry path for simulations\. A synthetic node should serialize into the same canonical envelope and enter the same receiver, validator, authentication \(or simulation\-trust equivalent\), deduplication and normalization logic as a physical node\. The simulator may additionally write private ground truth to an isolated evaluation channel that is never made available to the live reasoning path\.

## 2\.1 Primary data stores

__Store / logical dataset__

__Purpose__

__Key properties__

telemetry\_raw

Original accepted packet payload for traceability\.

Immutable append; authenticated envelope retained; raw timestamps preserved\.

telemetry\_normalized

Canonical measurement records used by downstream services\.

Typed units; normalized fields; quality metadata; schema version\.

diagnostics

Node/transport/power and sensor diagnostic observations\.

Separate from sensor measurement values; fast internal updates allowed\.

intelligence\_events

Derived anomaly/evidence/confidence/severity/risk/state outputs\.

Versioned logic \+ configuration; never overwrites raw telemetry\.

external\_context

Imported weather, DEM, population, maps and similar context\.

Source identifier, acquisition time, coverage, version, license/usage note\.

scenario\_definitions

Human\-authored reproducible simulation scenarios\.

Seed, topology, node config, event timeline, fault schedule\.

simulation\_runs

Execution metadata for a scenario\.

Scenario version, code version, data versions, config versions, timestamps\.

simulation\_truth

Private ground\-truth labels/state for evaluation\.

Access\-restricted; excluded from operational query interfaces\.

annotations

Human review, calibration, field trial notes and adjudications\.

Author, timestamp, reason, evidence references\.

dataset\_releases

Frozen bundles used for benchmarks/demo/reproduction\.

Manifest \+ checksums \+ lineage \+ release tag\.

# 3\. Canonical Telemetry Record

The following fields form the V1 logical contract\. Physical serialization may use JSON, MessagePack, CBOR or another approved compact format, but semantics must remain identical\.

__Field__

__Type__

__Required__

__Semantics__

telemetry\_id

UUID/string

Yes

Globally unique record identifier; generated at source where practical and retained end\-to\-end\.

node\_id

string

Yes

Stable logical identity of the field node\.

sequence

uint64

Yes

Monotonic sequence per node for ordering and replay detection\.

measurement\_timestamp

UTC timestamp

Yes

Time at which the measurement was captured\.

device\_monotonic\_time

duration/int

Optional

Monotonic device clock value useful for interval timing; not a wall\-clock substitute\.

receive\_timestamp

UTC timestamp

Receiver

Time the receiving component accepted the packet; never substitute for measurement\_timestamp\.

location

lat/lon \+ optional altitude

Yes/conditional

Location associated with the node or measurement source; exactness depends on deployment/privacy policy\.

measurements

map/object

Yes

One or more named sensor values with canonical units or declared sensor\-native units\.

diagnostics

object

Yes

Sensor status, communication status, watchdog state, firmware and relevant health metrics\.

power

object

Yes

Battery/power measurements and charging state where available\.

source

enum

Yes

LIVE\_HARDWARE or SIMULATION\.

schema\_version

string

Yes

Contract version used to decode the record\.

auth\_context

object

Yes for live

Authentication outcome, key identity/reference and verification metadata; never store raw secrets\.

metadata

object

Optional

Calibration profile, sensor model, deployment profile and other non\-measurement context\.

__Missing data rule — __Missing, stale, invalid and zero are different states\. A missing value MUST NOT be encoded as numeric zero unless zero is the actual measured value\.

## 3\.1 Measurement subrecord

measurement = \{  
  value: number,  
  unit: string,  
  valid: boolean,  
  quality\_flags: \[string\],  
  sensor\_state: string,  
  captured\_at: timestamp  
\}

The measurement subrecord is designed so a downstream service can reject or down\-weight a value without deleting the original packet\. Quality flags should be composable rather than encoded as a single opaque status\.

## 3\.2 Canonical sensor classes

__Measurement__

__Preferred V1 unit__

__Notes__

temperature

degC

Environmental temperature\.

humidity

%RH

Relative humidity\.

pressure

hPa

Optional context sensor\.

PM2\.5

ug/m3

Core fire/pollution signal when available\.

PM10

ug/m3

Useful for dust/pollution context\.

gas

ppm or calibrated engineering unit

Only use ppm when the actual gas species and calibration justify it; otherwise retain sensor\-native unit\.

water\_level

m

Centimetres are acceptable only if schema is kept consistent end\-to\-end\.

rainfall\_rate

mm/h

Instantaneous or interval\-derived rainfall rate; interval semantics must be explicit\.

rainfall\_cumulative

mm

Accumulated rain over a defined reset/lifetime interval\.

soil\_moisture

%VWC or calibrated native unit

Must declare calibration profile if converted to volumetric water content\.

vibration

m/s2 or calibrated native unit

Raw or feature representation depends on hardware capability\.

# 4\. Data Quality Lifecycle

Quality controls should progressively reduce uncertainty without pretending to repair a value that cannot be trusted\. The original measurement remains available; derived quality state determines how it participates in intelligence\.

capture \-> structural validation \-> range/plausibility checks \-> timestamp/sequence checks  
       \-> sensor diagnostic checks \-> stability/continuity checks \-> quality score Q\_i  
       \-> reliability R\_i \-> anomaly/evidence participation

## 4\.1 Quality dimensions

- Integrity: packet structure, parsing, authentication, schema and sequence validity\.
- Stability: impossible jumps, saturation, excessive jitter, stuck values and implausible rate\-of\-change\.
- Freshness: age since measurement versus the hazard\-specific maximum useful age\.
- Continuity: expected cadence versus observed cadence and missing intervals\.
- Calibration context: whether the sensor has an applicable calibration profile and field validation status\.
- Cross\-sensor coherence: whether independent signals support or contradict one another\.
- Cross\-node coherence: whether neighboring nodes provide corroborating evidence without assuming they are independent\.

__No silent imputation — __Do not silently fill missing environmental measurements with a mean, last value or simulator truth and then present the result as observed\. Any imputation for analytics must be explicitly marked as derived and must not erase missingness\.

# 5\. Dataset Taxonomy

__Dataset family__

__Purpose__

__Minimum contents__

D1 — Hardware Field Trials

Validate real sensing, calibration, latency and edge behavior\.

Raw packets, node config, sensor model, calibration notes, environmental conditions, trial event timeline\.

D2 — Public Environmental Context

Provide geospatial/environmental context and bootstrap historical analysis\.

Source, acquisition time, spatial/temporal resolution, coverage, CRS/units, license/usage note\.

D3 — Synthetic Telemetry

Stress the complete pipeline across hazards and failure modes\.

Scenario ID, seed, node topology, generated telemetry packets, injection schedule\.

D4 — Simulation Ground Truth

Measure correctness of simulation/inference\.

True hazard state, true spread/arrival state, injected faults, expected state transitions\.

D5 — Incident Review

Measure operational outcomes and false positives/negatives\.

Incident timeline, operator actions, evidence, alert outcome, adjudication and references\.

D6 — Calibration / Characterization

Understand sensor transfer behavior and limitations\.

Reference instrument, sensor response, environment, repeated trials, calibration model/profile\.

D7 — Evaluation Release

Frozen benchmark for repeatable comparisons\.

Manifest, all referenced versions, checksums, split definition and metrics contract\.

# 6\. Real Hardware Trial Data

Real hardware trials are the highest\-value early evidence because they expose sensor\-specific behavior, installation effects, communication loss, power constraints and environmental confounders that synthetic telemetry cannot reproduce perfectly\.

## 6\.1 Required field\-trial metadata

- Trial ID and human\-readable objective\.
- Node IDs and firmware build IDs\.
- Sensor make/model and calibration profile\.
- Physical placement, height/depth and orientation where relevant\.
- Exact trial location at the privacy level permitted by the project\.
- Start/end timestamps and timezone normalization\.
- Reference instrument or manual observation when used\.
- Environmental conditions and intentionally introduced events\.
- Operator notes, anomalies, failures and corrective actions\.
- Whether the trial is representative, controlled, exploratory or destructive\.

## 6\.2 Fire trial data rule

Fire sensing validation must use controlled, authorized trials with recorded safety conditions and reference observations\. The point of the trial is to characterize the actual node response and the evidence pipeline, not to manufacture a large synthetic claim of field accuracy\.

# 7\. Public Environmental & Geospatial Data

Public data is useful for environmental context, bootstrapping, historical analysis, geospatial modeling and scenario realism\. It is not automatically ground truth for a NexAlert incident\.

__Candidate source class__

__Typical use in NexAlert__

__Trust / usage rule__

Satellite active\-fire products \(e\.g\. NASA FIRMS\-class data\)

External fire context, historical event discovery, scenario seeding, verification support\.

Treat as contextual evidence; do not automatically equate a satellite detection with ground\-truth node detection\.

Reanalysis / meteorological products \(e\.g\. ERA5\-Land\-class data\)

Wind, temperature, humidity and other environmental context for replay/simulation\.

Record acquisition/version/time grid and interpolation method; mark as external context\.

Precipitation products \(e\.g\. GPM IMERG\-class data\)

Rainfall context, flood scenario construction and historical analysis\.

Record temporal/spatial aggregation; do not silently replace node rainfall observations\.

Flood / hazard public products

Historical/reference context and scenario design\.

Use as contextual evidence unless a specific product is explicitly adopted as an authoritative external source\.

Population datasets \(e\.g\. WorldPop/GHSL\-class\)

Exposure analysis for affected\-area reporting\.

Keep distinct from physical hazard risk surface; version and year must be recorded\.

OpenStreetMap\-class vector data

Roads, buildings, hospitals, schools and infrastructure context\.

Record extract date/region and tag filters; data completeness is not guaranteed\.

DEM datasets

Terrain slope/aspect for fire spread and geospatial analysis\.

Use a declared DEM version, resolution, CRS and preprocessing chain\.

__Source\-selection policy — __The exact provider, version, license and access method must be frozen in the Data Release Manifest before a benchmark or SIH demo uses external data as a reproducible dependency\.

## 7\.1 Public data provenance record

__Field__

__Example semantics__

source\_id

Human\-readable provider/source identifier\.

dataset\_name

Specific published dataset/product name\.

provider\_version

Provider release/version/date\.

acquired\_at

When NexAlert retrieved or materialized the data\.

coverage

Spatial/temporal extent used\.

native\_crs

Native coordinate reference system\.

processing\_crs

Projected CRS used for metric geospatial operations, when applicable\.

resolution

Native and/or resampled resolution\.

processing\_steps

Clip, reproject, resample, interpolate, aggregate, filter, etc\.

license\_note

Internal reference to applicable usage/license terms\.

checksum

File/object checksum for the materialized artifact\.

lineage\_parent

Input asset\(s\) from which derived artifact was created\.

# 8\. Synthetic Telemetry Architecture

Synthetic telemetry exists to exercise the system across normal conditions, hazards, sensor faults, node failures, communication disruption, corroboration and contradiction\. It must produce plausible packets, not hidden answers embedded in the telemetry\.

## 8\.1 Simulator boundaries

- The simulator owns scenario state and private ground truth\.
- The simulator emits only telemetry and explicitly approved external\-context\-like inputs to the operational pipeline\.
- Ground\-truth labels, exact future arrival times and injected\-fault truth remain in an isolated evaluation store\.
- The simulator uses the same packet schema, units, timestamps, node IDs, sequence semantics and ingestion endpoint as hardware\.
- The simulator must support deterministic seeds so the same scenario can be replayed exactly when software/config/data versions are unchanged\.

## 8\.2 Scenario dimensions

__Dimension__

__Required cases__

Baseline

Stable normal environment; realistic noise; periodic telemetry\.

Hazard onset

Slow onset and abrupt onset for fire, flood and pollution paths\.

Correlated signals

Expected relationships such as temperature \+ PM \+ gas changes or rainfall \+ water\-level changes\.

Single\-sensor anomaly

One sensor drifts, spikes, sticks or becomes unavailable while others remain healthy\.

Multi\-sensor anomaly

Multiple signals move coherently and incoherently\.

Node failure

Hard failure, stale telemetry, watchdog reboot, power loss, intermittent recovery\.

Communication failure

Packet loss, burst loss, high latency, partition, store\-and\-forward recovery\.

Contradiction

One node reports strong evidence while a neighboring node disagrees\.

Multi\-node corroboration

Spatially coherent evidence across multiple independent nodes\.

Multi\-hazard

Fire and pollution; flood and pollution; unrelated hazards in separate regions\.

Environmental shift

Wind or humidity changes mid\-run; future spread must be recomputed from current state rather than rewriting history\.

Recovery

Hazard declines/ends, evidence decays and system reaches RESOLVED only after configured stand\-down rules\.

Adversarial / malformed

Invalid schema, out\-of\-order sequence, duplicate packet, replay, impossible value, auth failure\.

# 9\. Synthetic Fire Telemetry

The fire telemetry generator must reflect the same conceptual path as the fire intelligence model: environmental context \-> sensor response \-> quality/reliability \-> evidence \-> state\. It must not simply generate a hazard label and then generate matching values\.

## 9\.1 Fire signal generation model

- Temperature response may increase with distance/time relative to the simulated fire front, with configurable lag and noise\.
- PM/smoke response should depend on proximity, wind direction, dispersion assumptions and sensor response profile\.
- Gas response should use a declared sensor response model rather than an arbitrary binary switch\.
- Humidity may move plausibly with environmental/fire conditions but remains supporting evidence\.
- Nodes outside the active influence area should continue to produce realistic background telemetry and may experience occasional unrelated noise\.
- No simulator field named “fire\_detected=true” may enter the operational telemetry stream as a shortcut\.

## 9\.2 Fire ground truth

__Ground\-truth field__

__Use__

true\_ignition\_time

Evaluation of onset detection latency\.

true\_ignition\_geometry

Evaluation of initial footprint\.

true\_arrival\_time\[cell\]

Evaluation of spread/arrival estimation\.

true\_burn\_state\[cell\]

Evaluation of current footprint\.

true\_future\_projection\[cell,t\]

Evaluation of projection horizon\.

injected\_sensor\_faults

Evaluation of diagnostics and resilience\.

injected\_network\_faults

Evaluation of store\-and\-forward and recovery\.

true\_environment\_timeline

Evaluation of mid\-run recomputation logic\.

__Isolation rule — __Ground truth is not a feature\. During operational reasoning, the services may know only the telemetry/context that a real deployment would know at that time\.

# 10\. Synthetic Flood / Pollution / Other Hazard Telemetry

The same scenario framework supports other hazards without forcing every hazard into identical sensor semantics\.

__Hazard__

__Illustrative signals__

__Key synthetic behaviors__

Flood

rainfall, water level, humidity, pressure

rain bursts, cumulative rain, lagged water response, sensor submergence/failure, upstream/downstream timing\.

Pollution

PM2\.5, PM10, gas, wind, temperature, humidity

source onset, directional plume behavior, calm/stable periods, sensor saturation, background variability\.

Landslide

soil moisture, rainfall, vibration, optional tilt/context

progressive wetting, vibration/instability bursts, correlated and contradictory signals\.

Extreme heat

temperature, humidity, pressure

slow sustained rise, nighttime recovery, local spatial gradients, sensor thermal drift\.

Unknown anomaly

any configured sensor set

novel or contradictory patterns designed to test UNKNOWN / DEGRADED behavior\.

# 11\. Scenario Definition Contract

scenario\_id  
scenario\_version  
seed  
description  
region  
start\_time  
duration  
node\_topology  
sensor\_profiles  
base\_environment  
hazard\_events\[\]  
fault\_events\[\]  
transport\_events\[\]  
external\_context\_versions\[\]  
expected\_assertions\[\]

## 11\.1 Example scenario structure

hazard\_events:  
  \- type: FIRE  
    start: T\+300s  
    ignition: \[lat, lon\]  
    intensity\_profile: controlled  
  
fault\_events:  
  \- type: SENSOR\_STUCK  
    node\_id: N03  
    sensor: PM2\.5  
    start: T\+420s  
    duration: 90s  
  
transport\_events:  
  \- type: PARTITION  
    node\_ids: \[N03, N04\]  
    start: T\+450s  
    duration: 60s

# 12\. Dataset Splits & Evaluation Hygiene

Dataset splits must prevent the benchmark from becoming a disguised lookup table\. Random row\-level splitting is insufficient for time\-series and spatially correlated environmental data\.

__Split strategy__

__Use__

Temporal holdout

Train/tune on earlier periods; evaluate on later periods\.

Spatial holdout

Hold out nodes/regions to test geographic generalization\.

Scenario holdout

Hold out complete synthetic scenarios/fault combinations\.

Node holdout

Evaluate on sensor nodes unseen during model fitting when feasible\.

Event holdout

Keep entire incident windows together so adjacent rows do not leak context across train/test\.

Cross\-domain holdout

Where data supports it, evaluate on public\-context or hardware\-trial domains not used for development\.

__Leakage rule — __Do not split one physical incident into both training and validation/test sets unless the metric is explicitly intended to measure within\-incident interpolation\. For operational generalization, hold out the complete incident or scenario\.

# 13\. Labels, Ground Truth & Adjudication

NexAlert does not assume that every telemetry record has a perfect label\. Labels exist at multiple levels and must declare their provenance and confidence\.

__Label level__

__Example__

__Authority__

Measurement quality

valid / stale / failed / drift suspected

Automated diagnostics \+ calibration review\.

Hazard evidence

supporting / contradictory / unavailable

Deterministic evidence logic \+ source state\.

Incident state

suspected / confirmed / resolved

System state machine; confirmation may require multi\-evidence or operator action depending on hazard\.

Event ground truth

actual ignition / flood onset / pollution release

Controlled trial record, authoritative event source or isolated simulator truth\.

Operational outcome

alert useful / late / false / unreachable / stand\-down

Post\-incident human review and system logs\.

## 13\.1 Label provenance fields

- label\_id
- subject\_id
- label\_type
- label\_value
- source\_type
- source\_reference
- created\_at
- annotator/operator
- review\_status
- confidence\_or\_certainty\_note
- supersedes
- reason\_for\_change

# 14\. Data Versioning & Lineage

A reproducible NexAlert run is defined by more than source data\. Code, configuration, model/ruleset versions, schemas, geospatial assets and scenario seeds all affect the output\.

RUN\_REPRODUCIBILITY = \{  
  code\_commit,  
  schema\_versions,  
  config\_version,  
  intelligence\_ruleset\_version,  
  fire\_model\_version,  
  external\_context\_manifest,  
  scenario\_version,  
  random\_seed,  
  hardware\_firmware\_builds,  
  dataset\_release  
\}

## 14\.1 Immutable release manifest

__Manifest field__

__Requirement__

release\_id

Unique immutable identifier\.

created\_at

Release creation timestamp\.

purpose

Benchmark, demo, field trial, regression, research, etc\.

artifacts

List of included datasets/files/objects\.

checksums

Checksum per artifact\.

schemas

Exact schema versions\.

config

Exact configuration registry version\.

code

Commit/build identifier\.

source\_provenance

External source lineage\.

known\_limitations

Documented caveats\.

license\_notes

Usage constraints for included external data\.

approval

Owner/reviewer and status\.

# 15\. Data Retention & Lifecycle

__Data class__

__V1 retention posture__

__Notes__

Raw hardware telemetry

Keep for the active project evaluation window and preserve frozen benchmark subsets\.

Raw data is high\-value for debugging and audit\.

Normalized telemetry

Retain as long as required for operations, analytics and replay\.

May be compacted while preserving raw lineage\.

Diagnostics / heartbeat

Retain enough history for reliability and outage analysis\.

Detailed rapid diagnostics can use a shorter horizon than event records\.

Intelligence events

Retain incident\-relevant and audit\-relevant outputs\.

Must preserve logic/config versions\.

Simulation runs

Retain benchmark/demo runs and scenario manifests\.

Delete/rebuildable runs may be pruned only when not part of a release\.

Simulation ground truth

Retain for evaluation releases\.

Access restricted and never surfaced in operational UI\.

External data assets

Retain exact artifacts for frozen releases when licensing permits\.

Otherwise retain reproducible source/version metadata and acquisition instructions\.

Personal / citizen operational data

Apply minimal\-retention policy consistent with the security/communications design\.

Do not duplicate unnecessary PII into environmental datasets\.

# 16\. Privacy & Data Minimization

Environmental telemetry should remain environmental telemetry\. Citizen identity, precise personal location and emergency communications data must not be copied into broad analytics datasets unless there is an explicit operational purpose and access control\.

- Prefer node IDs and coarse operational locations where exact coordinates are not needed\.
- Separate citizen/contact identity records from environmental sensor records\.
- Aggregate population/exposure outputs rather than exporting unnecessary individual\-level details\.
- Use access\-controlled views for operational versus research/evaluation datasets\.
- Never place secrets, raw HMAC keys or authentication credentials inside dataset exports\.
- When creating demo datasets, strip or synthesize personal identifiers\.

# 17\. Data Quality & Integrity Invariants

1. Every accepted live telemetry record has node identity, sequence, measurement timestamp and schema version\.
2. Receive time and measurement time remain distinct\.
3. Missing is not zero\.
4. Raw telemetry is immutable after acceptance; corrections are represented as derived records or annotations\.
5. Synthetic records are explicitly marked source=SIMULATION\.
6. Simulation ground truth never enters the live reasoning path\.
7. Every derived intelligence artifact records the versions needed to reproduce its calculation\.
8. External data is labeled as external context and retains provenance\.
9. Location units and CRS semantics are explicit; metric geospatial calculations use an appropriate projected CRS\.
10. No public\-data source is silently treated as authoritative incident ground truth unless explicitly approved\.
11. Dataset splits prevent avoidable spatial, temporal and incident\-level leakage\.
12. All benchmark/demo releases are immutable and checksum\-addressable\.

# 18\. Data Quality Metrics

__Metric__

__Definition / example__

Telemetry completeness

Received expected records / expected records\.

Freshness

Age distribution from measurement\_timestamp to processing time\.

Duplicate rate

Duplicate telemetry IDs/sequences / received records\.

Out\-of\-order rate

Records arriving outside expected sequence window\.

Invalid\-value rate

Records rejected for schema/range/plausibility issues\.

Node uptime evidence

Expected heartbeats observed over interval\.

Sensor missingness

Missing values per sensor per node over interval\.

Calibration coverage

Percentage of deployed sensors with current calibration profile\.

Scenario reproducibility

Percentage of deterministic scenario reruns producing identical operational outputs given identical versions/seeds\.

Label coverage

Fraction of evaluation events with adjudicated or simulator ground truth\.

Provenance completeness

Percentage of external/derived artifacts with complete lineage manifests\.

# 19\. Benchmark & Acceptance Dataset

The project must maintain a small, explicit acceptance dataset that can be executed repeatedly before a SIH demo, release or major refactor\. It should be more rigorous than a collection of screenshots\.

__Acceptance pack__

__Must demonstrate__

A — Normal baseline

Stable telemetry, healthy quality, no false incident\.

B — Single sensor failure

Health/quality degradation prevents one bad sensor from dominating the decision\.

C — Correlated fire onset

Multiple signals corroborate; hazard state escalates according to persistence/evidence rules\.

D — Contradiction

Conflicting sensor/node evidence degrades confidence rather than forcing certainty\.

E — Communication partition

Local node/master autonomy and recovery work without data corruption\.

F — Replay

A captured packet stream reproduces the same derived event sequence under the same versions\.

G — Fire spread projection

Real geospatial engine computes current/warning/projection footprints from declared inputs\.

H — Mid\-run environmental change

History remains frozen; future projection is recomputed from current frontier\.

I — Multi\-hazard

Fire and flood/pollution vectors remain separate; no fake combined scalar is emitted\.

J — Ground\-truth isolation

Operational reasoning cannot query simulator truth\.

# 20\. Data APIs / Event Boundaries

The concrete endpoint names are defined in the Backend/API specification, but the data contract already establishes the required boundaries\.

__Boundary__

__Payload class__

__Direction__

Node \-> Master

Canonical telemetry \+ heartbeat \+ diagnostics

Upstream

Simulator \-> Ingestion

Canonical synthetic telemetry

Upstream

Master \-> Intelligence

Normalized observations \+ external context

Internal

Intelligence \-> Incident engine

Evidence/confidence/severity/risk/state outputs

Internal

Incident engine \-> Alert system

Canonical emergency event

Internal

Simulation controller \-> Scenario runner

Scenario/configuration

Control

Scenario runner \-> Evaluation store

Private ground truth

Evaluation only

Replay \-> Ingestion

Recorded canonical telemetry

Test/replay

# 21\. Data Import / Export Rules

- CSV is acceptable for simple offline analysis exports, but not the canonical operational representation\.
- JSON is acceptable for human\-readable APIs and scenario manifests\.
- Columnar formats such as Parquet are preferred for larger offline analytical datasets when the implementation warrants them\.
- Binary telemetry formats may be used on constrained links, provided the canonical logical schema is preserved\.
- Every exported dataset carries schema/version metadata and a release identifier\.
- Exports that contain external data preserve the original source/version metadata\.
- Exports must state whether they contain observed data, synthetic data, derived features, or ground truth\.

# 22\. Operational Data Failure Modes

__Failure__

__Required response__

Bad packet

Reject safely; log reason; do not crash ingestion\.

Duplicate packet

Deduplicate idempotently; preserve audit information\.

Out\-of\-order packet

Accept within configured window or quarantine; never silently reorder destructive updates\.

Stale packet

Store when useful for audit/replay but exclude from fresh\-evidence decisions according to policy\.

Sensor value impossible

Flag invalid; retain raw record; reduce participation in intelligence\.

External context unavailable

Declare degraded/unknown context rather than inventing values\.

Dataset version missing

Block benchmark/replay that claims reproducibility\.

Ground truth accidentally exposed

Fail the evaluation run; log violation; fix isolation before trusting metrics\.

Schema mismatch

Version\-gate the record; migrate explicitly rather than silently guessing fields\.

# 23\. Implementation Guidance

The first implementation should prioritize a small number of trustworthy pathways over a large data platform\. The recommended approach is a modular operational store with explicit schemas and background workers, while keeping the option to scale storage and analytics later\.

1. Implement the canonical telemetry schema and validator first\.
2. Implement raw \+ normalized telemetry persistence\.
3. Add diagnostic and quality metadata without modifying raw measurements\.
4. Build the simulator as a packet generator that targets the same ingestion interface\.
5. Build private ground\-truth storage and enforce code\-level access boundaries\.
6. Add scenario manifests, deterministic seeds and replay tooling\.
7. Freeze a small acceptance dataset and run it in CI/regression checks\.
8. Add public\-data importers only behind versioned provenance manifests\.
9. Only then add larger analytical exports, feature pipelines or learned models where evidence justifies them\.

# 24\. V1 Data Deliverables

__Deliverable__

__Definition of done__

Canonical schema

Versioned schema implemented in code with validation tests\.

Telemetry archive

Raw and normalized paths working for both LIVE and SIMULATION\.

Provenance manifest

External data and derived artifacts include source/version/processing/checksum lineage\.

Scenario library

At least one reproducible scenario for each mandatory fault/hazard class\.

Ground\-truth isolation

Reasoning services cannot access private simulator truth during operational execution\.

Replay engine

Recorded telemetry can be replayed through the same ingestion path\.

Acceptance dataset

Frozen scenarios/trials cover normal, failure, contradiction and multi\-hazard cases\.

Release manifest

Demo/benchmark bundle is immutable and reproducible\.

Quality dashboard inputs

Metrics exist for completeness, freshness, duplicates, validity and calibration coverage\.

# 25\. Final Data Invariants

__Invariant 01 — __Observed data, derived intelligence and private evaluation truth are different data classes and must remain distinguishable\.

__Invariant 02 — __Simulation uses the same operational telemetry path as hardware\.

__Invariant 03 — __Synthetic telemetry generates inputs; the reasoning system must generate the decision\.

__Invariant 04 — __Historical truth is never silently rewritten when conditions change; future simulation state is recomputed from the current frontier\.

__Invariant 05 — __External datasets are contextual evidence with provenance, not automatically ground truth\.

__Invariant 06 — __Every benchmark result is reproducible only when data, code, configuration, scenario seed and external context versions are known\.

__Invariant 07 — __Missingness is explicit and never silently converted into zero or fabricated certainty\.

__Invariant 08 — __Data quality affects trust/reliability; it does not delete the underlying observation\.

__Invariant 09 — __Citizen/privacy data is minimized and separated from environmental analytics wherever practical\.

__Invariant 10 — __The smallest trustworthy dataset is better than a large dataset with unclear provenance\.

# Appendix A — Recommended V1 Folder / Artifact Layout

data/  
  schemas/  
    telemetry/v1/  
    diagnostics/v1/  
    intelligence/v1/  
  raw/  
    live/  
    simulation/  
  normalized/  
  external/  
    dem/  
    weather/  
    precipitation/  
    population/  
    osm/  
    fire\_context/  
  scenarios/  
    fire/  
    flood/  
    pollution/  
    resilience/  
  truth/  
    simulation/  
    adjudication/  
  releases/  
    <release\_id>/manifest\.json  
  replay/  
  calibration/

# Appendix B — Minimum Scenario Catalog for SIH Demo

__Scenario ID__

__Story__

__Primary proof__

FIRE\-01

Normal \-> gradual smoke/temperature onset \-> corroboration \-> alert

Evidence, confidence and state escalation\.

FIRE\-02

Fire \+ wind shift \-> projection changes mid\-run

Real geospatial recomputation and versioned projection\.

FIRE\-03

Fire with one failed sensor

Reliability gating / resilience\.

FIRE\-04

Fire with neighboring contradiction

Confidence degradation without arbitrary suppression\.

FLOOD\-01

Rain burst \-> rising water level \-> affected area

Multi\-signal reasoning path\.

NET\-01

Master/network interruption with local autonomy

Store\-forward / local emergency path\.

MULTI\-01

Fire \+ pollution in same region

Independent hazard vectors; no combined fake score\.

SEC\-01

Duplicate/replay/malformed packet

Authentication and ingestion safety\.

REPLAY\-01

Recorded run replayed twice

Deterministic reproducibility\.

# Appendix C — Review Checklist Before Locking Any Dataset

- What exactly is the source of this value?
- Is it observed, derived, external context, synthetic observation or private ground truth?
- Can another engineer reproduce the transformation from its parent artifact?
- Are timestamp, units, CRS and calibration semantics explicit?
- Could this dataset leak future knowledge into a live\-like decision?
- Could spatial/temporal correlation create evaluation leakage?
- What happens when this value is missing, stale or contradictory?
- Is the dataset version/checksum recorded for the benchmark or demo?
- Are privacy and licensing constraints documented?
- Does the dataset exercise a real requirement from the current architecture rather than a legacy feature?

