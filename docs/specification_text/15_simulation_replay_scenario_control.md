Simulation, Replay & Scenario Control

NexAlert SIH26178 | Final Implementation Specification | Document 15

Purpose: define the deterministic simulation, replay, scenario\-control, time\-travel, fault\-injection, and evaluation system used to test the same NexAlert intelligence pipeline that receives live hardware telemetry\.

Authority: this specification derives from the locked Master Architecture, Mathematical Intelligence, Fire/Geospatial, Data, Multi\-Hazard, Incident/Response, Communication/Resilience, and UI specifications\. Simulation is a validation and demonstration system, not a hidden oracle for live inference\.

# 1\. Purpose and Core Contract

The simulation subsystem must make NexAlert testable under normal conditions, evolving hazards, sensor faults, network partitions, multi\-node corroboration, and multi\-hazard conflict\. Every simulated observation enters the same telemetry ingestion, validation, health/quality, baseline, anomaly, evidence, confidence, severity, risk, incident, alert, and UI paths used by hardware\-originated observations\.

__Principle__

__Requirement__

Same pipeline

Simulator emits telemetry/events only; it does not call downstream decision functions directly\.

Deterministic

Given scenario version, seed, initial state, configuration version, and code build, the same run is reproducible\.

Ground truth private

Hazard truth, injected faults, and expected outcomes are stored as evaluation metadata and are never sent into the reasoning path\.

Time controlled

Clock can run slower, equal to, faster than real time, pause, seek to checkpoints, and replay exact event order\.

Live\-safe

Simulation mode cannot accidentally publish production citizen alerts or alter live node state without an explicit environment boundary\.

Explainable

Every derived decision can be traced to telemetry, configuration, event history, and simulation step\.

Replayable

Any run can be archived and replayed from its immutable input bundle\.

# 2\. Simulation Environments

## 2\.1 Required environment separation

__Environment__

__Purpose__

__External Effects__

SIMULATION

Development, testing, SIH demonstration

No citizen notifications, no real node writes

STAGING

Integration with near\-production services

Sandbox\-only notification adapters and synthetic identities

LIVE

Real hardware and approved operations

Production controls and human\-approved alerts/actions

Environment identity is mandatory in every run, event envelope, database record, API response, log line, and UI header\. A SIMULATION run must not be able to authenticate as a LIVE event producer\.

# 3\. Simulation Architecture

The simulator is an event\-producing subsystem around the canonical NexAlert pipeline\. It contains a scenario engine, virtual node fleet, hazard/world model, fault injector, clock controller, transport emulator, ground\-truth recorder, checkpoint manager, and run evaluator\.

__Component__

__Responsibility__

__Must Not Do__

Scenario Engine

Loads versioned scenario definitions and schedules state changes

Bypass telemetry ingestion or write final alarm states

Virtual Node Fleet

Emulates sensors, diagnostics, battery/comm behavior, and node timing

Pretend to be actual ESP32 hardware

Hazard/World Model

Produces environmental evolution and hidden truth layers

Publish truth labels to intelligence services

Fault Injector

Applies missing/stale/noisy/drift/failure/contradiction/communication faults

Silently alter recorded ground truth

Transport Emulator

Models latency, loss, duplication, reordering, partitions, recovery

Hide packet loss from metrics

Clock Controller

Controls simulation time and event ordering

Move LIVE clock

Ground Truth Store

Persists truth and injected conditions for evaluation

Serve truth to production inference endpoints

Evaluator

Compares system outputs against ground truth and scenario expectations

Rewrite system outputs to make a test pass

# 4\. Canonical Simulation Data Flow

The mandatory path is: scenario definition \-> virtual environment \-> virtual node telemetry \-> authentication/envelope validation \-> ingestion \-> health/quality \-> reliability \-> baseline/anomaly \-> hazard evidence \-> confidence/severity/risk \-> incident correlation \-> alert/response \-> dashboard/citizen surfaces\. Ground truth is written in parallel to a private evaluator store\.

For fire scenarios, environmental/geospatial inputs drive the same fire\-spread engine used by LIVE/SIMULATION UI\. The frontend must never draw a decorative hazard shape independently of simulation state\.

# 5\. Scenario Model

__Field__

__Required Meaning__

scenario\_id

Stable human\-readable identifier

version

Semantic or monotonically increasing scenario version

hazards

One or more independent hazard tracks

region

Geospatial extent, coordinate reference, and node placement

duration

Simulation horizon and optional warm\-up period

clock

Start timestamp and simulation step/event rules

seed

Deterministic seed used by stochastic generators

initial\_conditions

Environmental, node, network, and incident state

environmental\_drivers

Rainfall, wind, temperature, humidity, terrain/fuel inputs as applicable

node\_profiles

Sensor inventory, baseline status, health, battery/power, communications

faults

Timed or conditional telemetry/network faults

ground\_truth

Private hidden hazard state for evaluation only

expected\_outcomes

Acceptance assertions and measurable targets

safety\_policy

Rules controlling external\-effect adapters

# 6\. Scenario Families

__Family__

__Example Objective__

Baseline / Normal

Verify stable telemetry, no false incidents, healthy baseline learning

Slow Fire Onset

Verify gradual evidence accumulation and persistence/hysteresis

Rapid Fire Escalation

Verify fast escalation and current/warning/projection surfaces

Flood Rising

Verify trend\-relative water anomaly and multi\-node corroboration

Pollution Event

Verify PM/gas/temperature evidence and degraded sensing behavior

Landslide/Vibration

Verify vibration\-feature path and missing\-data degradation

Extreme Heat

Verify temperature/humidity evidence without forcing unrelated hazards

Multi\-Hazard

Fire \+ flood, pollution \+ heat, or independent simultaneous incidents

Contradictory Sensors

One strong signal vs\. neighboring disagreement / bad probe

Network Partition

Node\-to\-Master loss, Master isolation, recovery and replay

Master Failure

Master unavailable while local node emergency path remains possible

Sensor Drift/Failure

Progressive drift, hard failure, stale values, correlated bias

Alert Lifecycle

Watch \-> suspected \-> confirmed \-> critical \-> resolved \-> stand\-down

Replay Regression

Re\-run frozen scenario after code/config change and compare outputs

# 7\. Hazard Simulation Models

## 7\.1 Fire simulation

Fire simulation uses the locked geospatial chain: DEM \+ fuel \+ moisture \+ wind \-> directional rate of spread \-> arrival\-time propagation \-> current/warning/projection geometry \-> operational buffer \-> hazard risk surface \-> exposure\. Wind is treated as FROM meteorological input and converted to propagation direction before directional spread calculation\. Terrain slope/aspect is computed in metric projected coordinates\. Non\-burnable cells have zero ROS; the front routes around them\. Arrival time is propagated through orthogonal and diagonal neighbors with metric distances\.

When environmental drivers change, historical truth is frozen\. The current frontier is extracted, future arrival times are reset from that frontier, and future propagation is recomputed\. The new projection is versioned so the UI can distinguish a revised forecast from a rewritten past\.

## 7\.2 Flood / pollution / heat / landslide

These scenario generators focus on sensor\-observable evolution rather than pretending to be high\-fidelity national disaster physics\. The generator may synthesize water\-level trends, rainfall, PM spikes, gas response, temperature/humidity shifts, soil moisture changes, and vibration features using configurable functions and spatial correlation\. The intelligence pipeline remains responsible for deciding what these observations mean\.

# 8\. Multi\-Hazard Orchestration

Each hazard is simulated as an independent truth track and intelligence vector\. The system must not collapse fire, flood, pollution, landslide, heat, or unknown\-hazard risk into a universal scalar\. A node may contribute evidence to more than one hazard vector when its sensor class is relevant\.

__Rule__

__Behavior__

Independent state

Each hazard maintains its own evidence/confidence/severity/risk/state

Shared observations

A telemetry observation may be mapped to multiple hazard\-specific evidence groups

Shared incident?

Only when deterministic incident\-correlation rules say observations belong to the same event

Conflicting hazards

Citizen/authority UI shows hazard\-specific conflicts and safe\-direction implications

Safe location

Ranking evaluates destination against all active hazards; nearest is not automatically safest

# 9\. Virtual Node and Telemetry Generator

A virtual node mirrors the canonical telemetry contract: node\_id, sequence, measurement\_timestamp, device monotonic time if applicable, location, measurements, diagnostics, power/battery, source, schema\_version, and HMAC/auth envelope\. Missing means absent/stale, never numeric zero unless the sensor truth is actually zero\.

__Generator Control__

__Examples__

Sampling

1 s, 5 s, 30 s, 60 s or configured node rate

Noise

Gaussian, bounded, asymmetric, burst noise

Drift

Linear, piecewise, step, random walk

Missingness

Random, contiguous outage, sensor\-specific outage

Staleness

Freeze value while timestamps advance or stop

Bias

Constant or time\-varying offset

Correlation

Neighboring nodes move together with spatially decaying correlation

Contradiction

One group disagrees with otherwise correlated neighbors

Sensor failure

Hard failure / invalid flag / saturation

Power

Battery decline, brownout, recovery, sensor duty\-cycle effects

Communication

Loss, duplication, delay, reorder, partition, reconnection

# 10\. Network and Resilience Simulation

__Fault__

__Expected System Observation__

Packet loss

Quality/freshness degrades; no fabricated continuity

Duplicate packet

Idempotency by telemetry identity/sequence prevents duplicate state changes

Reordering

Measurement timestamp and sequence preserve ordering semantics

Partition

Local autonomy continues; Master marks node reachability degraded

Master power loss

Node\-local emergency path remains available for configured local actions

Internet loss

Master/local system continues local operation; cloud delivery is degraded separately

Recovery

Buffered telemetry replays with bounded backoff and deduplication

Auth failure

Message rejected and audited; no state mutation

Replay attack

Old sequence/timestamp/event rejected per security policy

# 11\. Simulation Clock and Event Ordering

Simulation time is independent from wall time\. The clock controller supports REALTIME, FAST\_FORWARD, PAUSED, STEP, SEEK\_TO\_CHECKPOINT, and REPLAY modes\. Every emitted event carries simulation timestamp and deterministic sequence/order metadata\.

When multiple events share a timestamp, ordering is deterministic: configuration changes \-> node health/availability \-> sensor measurements \-> network delivery \-> ingestion/processing \-> incident transitions \-> notification adapters\. The exact internal worker ordering must not change the persisted event sequence for a deterministic build\.

__Mode__

__Behavior__

__Primary Use__

REALTIME

1 simulation second = 1 wall\-clock second

Demo / observation

FAST\_FORWARD

Runs as fast as safe while preserving event ordering

Regression tests

PAUSED

No event advancement

Debugging

STEP

Advance one logical event or fixed step

Root\-cause analysis

SEEK

Restore nearest checkpoint and re\-run forward

What\-if analysis

REPLAY

Play an immutable prior run

Audit / demonstration

# 12\. Checkpoints and Time Travel

Checkpoints are immutable snapshots containing scenario version, code/config identifiers, simulation clock, node state, pending events, transport queues, active incidents, baseline state, hazard\-spread state where applicable, and random\-generator state\. Seeking never mutates the original run; it creates a child run with a parent\_run\_id and branch point\.

# 13\. Fault Injection Framework

Faults are first\-class scenario objects with a start condition, scope, mutation, duration/termination rule, and expected evaluator effect\. Fault definitions are recorded separately from the telemetry they produce so the evaluator can distinguish a system failure from an injected environmental or hardware condition\.

__Fault Class__

__Examples__

__Pass Criterion__

Sensor integrity

CRC/schema/invalid\-value condition

Rejected or degraded safely

Sensor quality

Noise, drift, saturation

Reliability responds; no unjustified confidence

Baseline

Insufficient history / freeze / recovery

Correct readiness/state transitions

Topology

Node isolation / route change

Local and regional state remain distinct

Transport

Delay/loss/reorder/duplicate

Correct freshness and idempotency

Authentication

Wrong HMAC / old sequence

Rejected and audited

Processing

Worker restart / queue pressure

No silent event loss; bounded recovery

Hazard change

Wind/rain/moisture shift

Future projection updates; past stays fixed

Citizen channel

Push unavailable / offline portal

Correct channel fallback behavior

# 14\. Ground Truth and Evaluation Separation

Ground truth is an evaluator\-only representation of what the simulator intentionally created\. For example, a fire cell may have ignition truth, arrival time, physical state, and exposure truth\. The live intelligence path sees only telemetry and approved contextual inputs\. This separation prevents label leakage and makes simulation useful as an adversarial test instead of a scripted demo\.

Evaluation labels may be aligned to system timestamps after a run, but never injected into live inference requests\. Expected outcomes define ranges and invariants rather than requiring an exact internal score when the architecture intentionally uses operational indices rather than probabilities\.

# 15\. Metrics and Evaluation

__Metric__

__Definition / Use__

Detection delay

Time from truth crossing a defined evaluation threshold to first valid alert/incident state

False positive rate

Alerts/incidents produced when scenario truth is below defined hazard condition

False negative rate

Missed or late hazard conditions above evaluator threshold

Spatial overlap

Agreement between predicted/current/warning/projected geometry and truth at matching times

Arrival\-time error

Prediction vs\. truth for fire\-cell arrival where truth supports timing

Confidence calibration review

Check whether evidence/coverage language behaves as documented; C\_h is not treated as probability

Alert delivery latency

Event issue \-> channel acceptance/open where observable

Recovery time

Fault injection \-> restored valid operation

Data loss

Expected vs\. persisted telemetry/events across failures

Determinism

Same bundle rerun produces equivalent persisted outputs within defined tolerance

Resource behavior

CPU, memory, queue depth, latency under accelerated simulation

# 16\. Golden Scenario Suite

__Scenario ID__

__Mandatory Assertion__

G01\-NORMAL\-001

Healthy nodes remain NORMAL with no spurious incident

G02\-FIRE\-SLOW\-001

Slow fire reaches WATCH/SUSPECTED before CONFIRMED according to configured persistence

G03\-FIRE\-FAST\-001

Rapid evidence can escalate without waiting through normal persistence

G04\-FIRE\-WIND\-001

Wind directionality matches FROM\-to\-TO conversion and directional ROS behavior

G05\-FIRE\-CHANGE\-001

Environmental change revises future projection without rewriting history

G06\-FLOOD\-TREND\-001

Water\-level trend anomaly is evaluated relative to local baseline

G07\-POLLUTION\-001

PM/gas evidence can trigger pollution path without falsely creating fire

G08\-MULTI\-001

Two simultaneous hazards maintain independent states and risk surfaces

G09\-CONTRADICTION\-001

One faulty sensor cannot erase corroborated valid evidence

G10\-PARTITION\-001

Node partition triggers degraded information state and local continuity

G11\-MASTER\-OFF\-001

Master loss does not imply node\-local emergency path loss

G12\-SECURITY\-001

Bad HMAC/sequence is rejected and audited

G13\-REPLAY\-001

Recorded run replays deterministically

G14\-SOS\-001

SOS remains available even without a known hazard; no automatic rejection

G15\-SHELTER\-001

No viable safe route produces SHELTER\_IN\_PLACE guidance

# 17\. Scenario Control Interface

Authority\-only simulation controls expose scenario selection, environment, run ID, seed, clock mode, start/pause/step/reset, checkpoint seek, speed multiplier, injected faults, hazard\-driver controls, node health overrides, transport controls, ground\-truth visibility \(simulator/evaluator role only\), and export\.

The public citizen surface never exposes ground truth, evaluator labels, hidden seeds, internal score formulas, or scenario\-control endpoints\.

__Control__

__Validation__

Load scenario

Schema validated before any event can emit

Start

Environment and permissions verified; safety policy shown

Pause/step

No new event except explicit step action

Inject fault

Logged with actor, time, scope, old/new state

Seek

Creates child run; parent immutable

Reset

Creates new run or restores explicit baseline; does not truncate audit history

Export

Bundles scenario, config hashes, event manifest, outputs, metrics, evaluator results

# 18\. API and Run Lifecycle

Minimal backend surface: create scenario run, validate scenario, start/pause/resume/stop, advance step, create checkpoint, seek/branch, inject fault, set simulation parameter, query run state, query event stream, query ground truth for evaluator role, compute metrics, and export replay bundle\.

Every mutating request is idempotent where practical and authenticated\. Run status states are CREATED \-> VALIDATED \-> RUNNING \-> PAUSED \-> COMPLETED or STOPPED; FAILED is terminal for infrastructure failure and retains partial artifacts\.

# 19\. Replay Bundle Specification

__Artifact__

__Purpose__

scenario\.yaml/json

Exact scenario definition and version

config snapshot

Parameter registry values actually used

build metadata

Application/model/engine commit or image identifiers

seed \+ clock policy

Deterministic execution context

node manifests

Virtual node inventory and sensor configuration

event manifest

Ordered event stream or immutable event references

truth bundle

Private evaluator truth

output bundle

Observed system outputs and state transitions

metrics report

Computed performance results

hash manifest

Integrity check for all bundle parts

# 20\. Security and Safety Boundaries

• SIMULATION credentials cannot authenticate to LIVE ingestion or notification adapters\.

• Ground\-truth endpoints require evaluator/admin role and must be disabled on citizen\-facing routes\.

• Simulation alerts are visibly labeled in authority UI and cannot be presented as live emergency instructions\.

• Notification adapters default to sink/console delivery in SIMULATION; real channels require explicit environment configuration and approval\.

• Run creation, fault injection, parameter changes, seek/branch, and exports are audited\.

• No simulation feature may mutate live node firmware, configuration, relay outputs, or citizen profiles\.

# 21\. Performance and Determinism Requirements

__Target__

__Requirement__

Event throughput

Support at least 10x prototype telemetry rate during accelerated regression with bounded queue growth

Clock fidelity

No duplicate or missing logical steps caused solely by acceleration

Replay

Golden scenario produces same state transitions and event IDs under same build/config/seed

Checkpoint

Create/restore without corrupting incident or transport state

UI responsiveness

Simulation controls remain responsive while background workers process events

Backpressure

Simulator slows or buffers when ingestion capacity is exceeded rather than silently dropping truthless data

Resource visibility

CPU/memory/queue/latency counters available to operator during accelerated runs

# 22\. Testing and Acceptance Matrix

__Test__

__Pass Condition__

Scenario schema

Invalid scenarios fail before execution with actionable validation errors

Pipeline parity

Simulation and hardware\-originated telemetry reach the same ingestion contracts

Determinism

Rerun yields equivalent outputs and identical truth under pinned build/config/seed

Fault isolation

Injected fault appears in telemetry/diagnostics and does not contaminate evaluator truth

Fire geometry

Current/warning/projection are derived from arrival\-time state and actual geometry

Multi\-hazard

Independent hazard vectors persist; no universal combined score appears

Master outage

Local emergency capability survives Master loss in supported prototype path

Network recovery

Buffered events recover without duplicate incident transitions

Security

Simulation cannot cross environment boundary

Replay export

Bundle can reconstruct run provenance and metrics

# 23\. SIH Demonstration Scenarios

## 23\.1 Hero demo: Fire detection \-> spread \-> alert

Start in SIMULATION with a healthy virtual node cluster\. Gradually introduce correlated temperature/PM/gas evidence, show health/quality/reliability, transition to WATCH/SUSPECTED/CONFIRMED as configured, then visualize actual current/warning/projected fire geometry from the same spread engine\. Change wind and demonstrate future projection revision while historical affected area remains stable\. Issue an alert through the sandbox adapter and show acknowledgement/response lifecycle\.

## 23\.2 Resilience demo: connectivity loss

Partition a node or disconnect the Master from upstream services\. Show stale/freshness changes, preserved local state, buffered telemetry, local emergency access path, and recovery/replay after reconnection\. The dashboard must distinguish Master failure from internet/cloud failure\.

## 23\.3 Multi\-hazard demo

Run a pollution event near one cluster while a separate flood/fire track evolves elsewhere\. Show independent incident cards, independent risk surfaces, and a safe\-location ranking that accounts for destination exposure rather than simply selecting the nearest shelter\.

# 24\. Implementation Rules for Vibe\-Coding / Agents

• Build one vertical simulation slice first: scenario \-> telemetry \-> ingestion \-> intelligence \-> incident \-> UI\.

• Use the canonical telemetry schema; do not invent a simulation\-only payload that bypasses production validation\.

• Keep scenario generators, fault injectors, evaluators, and ground truth outside the live decision modules\.

• Every new simulator parameter must be registered in the configuration/feature\-flag registry with a default, unit, range, owner, and rationale\.

• Write golden\-vector tests for mathematical functions and deterministic replay tests for end\-to\-end event streams\.

• Do not add autonomous actions merely because simulation makes them easy to script; NexAlert recommends and humans approve operational dispatch\.

• When changing fire or geospatial logic, rerun geometry, environmental\-change, non\-burnable\-cell, CRS, and arrival\-time regression suites\.

• When changing transport/security logic, rerun loss/reorder/duplicate/HMAC/replay/master\-loss scenarios\.

• Keep the simulator honest: it creates observations and conditions; it must not secretly answer the hazard question for the intelligence engine\.

# 25\. Final Simulation Invariants

• Simulation uses the same ingestion and reasoning path as hardware telemetry\.

• Ground truth is private evaluation data, never an inference input\.

• Multi\-hazard truth and system state are independent by hazard\.

• Fire simulation is geospatial and arrival\-time based, not a decorative radius animation\.

• Environmental changes revise future projection without rewriting the past\.

• Faults are explicit, timestamped, auditable, and separable from truth\.

• Replay is deterministic under a pinned scenario, seed, configuration, and build\.

• Branching creates child runs; original runs remain immutable\.

• Simulation cannot cross into LIVE control or citizen\-notification paths without explicit safety gates\.

• Every demo claim must be reproducible from an archived run bundle\.

