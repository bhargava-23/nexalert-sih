NEXALERT

MULTI\-HAZARD & SYNTHETIC TELEMETRY SPECIFICATION

Final V1 Engineering Baseline — Hazard Scenario Modeling, Synthetic Telemetry, Replay, Multi\-Node Correlation & Ground\-Truth Separation

# Document Control & Authority

__Field__

__Value__

Document ID

NexAlert FINAL 09

Status

Final V1 Engineering Baseline

Scope

Multi\-hazard representation, synthetic scenario generation, telemetry\-only simulation, replay and evaluation controls

Authority

Master System Architecture \+ final intelligence, hardware and data baselines

Primary Consumers

Backend, AI/ML, simulation, frontend, QA, SIH demo engineering

Implementation Priority

Mandatory for a trustworthy simulation/evaluation loop; hazard models remain independently configurable

Key Invariant

The simulator produces telemetry; the reasoning pipeline must infer the hazard state exactly as it would for hardware data\.

Historical Architecture Rule

Legacy STM32 split, Meshtastic\-first designs and other superseded concepts are not implementation targets unless explicitly re\-approved\.

# 1\. Purpose and System Role

NexAlert must demonstrate more than isolated sensor thresholding\. The system must show that the same distributed telemetry pipeline can observe, assess, correlate and communicate several environmental hazards while remaining honest about uncertainty, sensor quality, communication gaps and model limitations\. This document defines the scenario and telemetry layer that makes that possible\.

## 1\.1 Objectives

- Generate reproducible telemetry streams for normal conditions, gradual change, rapid onset, recovery and multi\-hazard conditions\.
- Exercise the exact live ingestion, authentication, validation, quality, baseline, anomaly, evidence, confidence, severity, risk and state pipeline\.
- Model correlated multi\-node observations rather than producing independent random sensor streams\.
- Inject realistic missingness, stale data, drift, noise, spikes, contradictions, communication loss and recovery\.
- Keep simulator\-only truth and labels separate from telemetry so the reasoning layer cannot accidentally read the answer\.
- Enable deterministic replay for debugging, visual demonstration, regression testing and algorithm comparison\.
- Support fire as the hero hazard and flood, pollution, landslide and extreme heat as reusable hazard paths under the same framework\.

## 1\.2 Non\-objectives for V1

- Do not build a universal learned classifier that claims to recognize every hazard from arbitrary sensor combinations\.
- Do not fabricate scientific ground truth where no real\-world reference exists\.
- Do not feed labels, future state, simulator hazard IDs or hidden scenario parameters into live\-like inference payloads\.
- Do not collapse independent hazards into one combined probability or scalar risk score\.
- Do not require heavy geospatial or fire\-spread computation on ESP32 edge nodes\.

# 2\. Multi\-Hazard Representation

Every hazard is represented as an independent reasoning vector\. Shared infrastructure is allowed; shared truth is not\. A node can simultaneously carry evidence for more than one hazard, and the regional system can maintain multiple incident hypotheses at once\.

__Hazard__

__Primary signals__

__Supporting signals__

__Core evidence concept__

__V1 reasoning posture__

Fire

temperature, smoke/PM, calibrated gas if available

humidity, wind/environment context

coherent rapid thermal \+ particulate/gas change across trusted nodes

deterministic evidence \+ geospatial spread engine; classifier optional

Flood

water level, rainfall

pressure, soil moisture, upstream context

level rise \+ rainfall/level trend \+ spatial corroboration

trend/threshold evidence with persistence

Pollution

PM2\.5/PM10, gas

temperature, humidity, wind/context

sustained concentration elevation with spatial/temporal coherence

configuration\-driven evidence

Landslide

vibration, soil moisture

rainfall, tilt/displacement when available

unusual vibration/displacement/soil response linked to triggering conditions

evidence groups; optional future geotechnical model

Extreme Heat

temperature

humidity, pressure/context

persistent elevated heat index / temperature pattern

duration\-aware evidence

Unknown

any subset

all available context

anomaly or cross\-node inconsistency not assignable to supported hazard rules

must remain UNKNOWN rather than forced into a known class

## 2\.1 Independent hazard vectors

For node n and hazard h:  E\_h\(n,t\) \-> C\_h\(n,t\) \-> S\_h\(n,t\) \-> R\_h\(n,t\) \-> State\_h\(n,t\)

The system stores and displays hazard\-specific state independently\. A fire event must not overwrite flood state, and an active pollution episode must not be hidden because the fire state is NORMAL\.

## 2\.2 Hazard state machine

__State__

__Meaning__

__Transition intent__

NORMAL

No sufficient evidence of the hazard

Remain normal while evidence stays below activation criteria

WATCH

Weak but actionable precursor or elevated environmental condition

Enter after configured persistence or supporting context

SUSPECTED

Meaningful evidence exists but confirmation criteria are not met

Escalate with persistence, corroboration or stronger evidence

CONFIRMED

Evidence passes configured confirmation logic

Issue/maintain incident state subject to authority workflow

CRITICAL

Confirmed hazard with high operational urgency

Fast escalation; safety\-first handling

RESOLVED

Hazard no longer operationally active and stand\-down criteria are met

Remain resolved; reactivation starts a new episode/version where appropriate

# 3\. Scenario Model

A scenario is a versioned, deterministic description of environment, nodes, hazard drivers, communication conditions, sensor faults and evaluation truth\. It is not itself a telemetry message\.

__Scenario component__

__Required fields / intent__

Scenario identity

scenario\_id, version, seed, description, author, created\_at

Spatial setup

node coordinates, grid/region definition, terrain/fuel references when used, hazard source locations

Temporal setup

start\_time, duration, sampling cadence\(s\), event timeline, replay speed

Environmental baseline

temperature, humidity, rainfall, wind, PM/gas background, water level, soil moisture, etc\.

Hazard drivers

fire ignition/source and environmental drivers; flood rainfall/upstream pulse; pollution source; landslide trigger; heat wave profile

Sensor behavior

noise, drift, calibration error, missingness, stale values, dropout, hard failure, contradiction

Network behavior

packet loss, latency, partitions, node isolation, recovery, receiver availability

Ground truth

private expected hazard extent/state/timing; never sent through live telemetry path

Expected evaluation

event windows, target behaviors, acceptance criteria, known corner cases

# 4\. Synthetic Telemetry Architecture

Scenario Definition \-> Environment Generator \-> Hazard Driver \-> Node Observation Model

Node Observation \-> Sensor Fault/Quality Model \-> Telemetry Serializer \-> Real Ingestion Endpoint

                    \(private truth branch \-> evaluator / replay oracle only\)

The telemetry branch must be indistinguishable, at schema level, from hardware telemetry\. The only permitted simulator\-specific metadata is transport\-safe metadata that does not disclose the hidden hazard answer to reasoning services\.

## 4\.1 Same\-path requirement

- Synthetic telemetry uses the same authentication/validation contract as hardware telemetry, with simulator credentials or a clearly segregated trusted simulation identity\.
- The same receive timestamp, sequence checking, quality evaluation, baseline logic and anomaly/evidence engine are exercised\.
- Frontend simulation mode must change data source selection only; it must not replace the reasoning pipeline with precomputed visual states\.
- For fire spread, LIVE and SIMULATION invoke the same geospatial spread engine; simulation supplies inputs, not a pre\-drawn answer\.

# 5\. Synthetic Sensor Observation Model

Synthetic values should be generated from a latent environmental trajectory and then transformed by sensor characteristics\. This avoids visually plausible but statistically meaningless random streams\.

x\_observed\(t\) = x\_environment\(t\) \+ bias\(t\) \+ noise\(t\) \+ event\_response\(t\)

x\_final\(t\) = apply\_missingness\_stale\_drift\_failure\(x\_observed\(t\)\)

Where appropriate, event response is hazard\-specific and parameterized by sensor class\. For example, a simulated smoke/PM channel can respond rapidly after ignition, while humidity may respond more slowly and can be used as supporting context rather than direct fire proof\.

## 5\.1 Baseline pattern families

__Pattern__

__Purpose__

__Examples__

Stationary

Normal conditions and false\-positive testing

stable PM, stable temperature, stable water level

Diurnal

Realistic periodic behavior

temperature/humidity day\-night cycle

Trend

Slow environmental movement

rising river level, drying soil

Pulse

Short\-lived event

rain burst, pollution plume passage

Step

Abrupt regime change

sensor exposure to a new environment

Ramp

Rapid onset / escalation

fire temperature rise, water\-level surge

Oscillatory

Periodic perturbation

vibration, machinery\-like interference

Piecewise

Multiple phases

normal \-> precursor \-> event \-> recovery

# 6\. Multi\-Node Spatial Correlation

The simulator must preserve the spatial structure needed to demonstrate distributed intelligence\. Nearby nodes should not all produce identical values, but a common hazard should create correlated changes with distance, delay and local variability\.

impact\_i\(t\) = source\_intensity\(t \- delay\_i\) \* spatial\_attenuation\(distance\_i\)

x\_i\(t\) = background\_i\(t\) \+ impact\_i\(t\) \+ local\_noise\_i\(t\)

Spatial attenuation and delay are configurable\. They are simulation constructs for testing system behavior, not claims of physical truth unless backed by an explicit model or source dataset\.

## 6\.1 Correlation classes

__Class__

__Definition__

__Use__

Independent

Node responds mostly to local noise/background

false\-correlation tests

Locally correlated

Nearby nodes share a common event with different magnitude/timing

single incident corroboration

Regionally correlated

Many nodes experience a broad environmental regime

heat wave, regional pollution

Adversarial contradiction

One node disagrees sharply with a correlated group

sensor fault / spoofing resilience

Communication\-only divergence

Underlying environment agrees but packets arrive late/missing

store\-and\-forward and freshness handling

# 7\. Fire Scenarios

Fire is the hero hazard and therefore receives the richest scenario family\. V1 uses deterministic evidence and the configured fire\-spread engine\. A learned classifier is optional and must not be required for the core demonstration\.

## 7\.1 Fire scenario families

__Scenario__

__Telemetry behavior__

__Expected system response__

F0 Normal dry/ambient

normal diurnal temperature, PM and gas behavior

NORMAL; baseline becomes READY

F1 Small local ignition

rapid local temperature \+ PM/gas change, neighboring nodes delayed/attenuated

WATCH/SUSPECTED \-> CONFIRMED if core evidence passes

F2 Fast escalation

steep temperature/PM rise and expanding corroboration

rapid transition toward CRITICAL

F3 False smoke spike

PM spike on one node without temperature corroboration and no spatial support

anomaly may be high; hazard confidence remains limited

F4 Sensor fault during fire

one critical sensor fails or drifts while peers remain coherent

incident survives; confidence/Information Condition degrade honestly

F5 Communication partition

event continues while some nodes are disconnected

local node state remains; regional picture becomes degraded/incomplete

F6 Multi\-source fire

two spatially separate ignition sources

separate incidents when merge radius/time window not satisfied

F7 Changing wind/environment

future spread driver changes mid\-run

historical truth frozen; future projection version recomputed from current frontier

F8 Receding / resolved

event intensity falls and burned area stabilizes

stand\-down only after configured persistence and operational criteria

## 7\.2 Fire telemetry coupling

- PM/smoke and gas channels should respond according to configured response curves, not identical copies of temperature\.
- Humidity can alter context but should not by itself confirm fire\.
- Wind belongs to environment/context and feeds the geospatial spread model; it is not a direct proof of combustion\.
- Sensor quality and reliability weight all evidence aggregation\. A failed or untrusted channel must not silently become zero\-valued evidence\.

# 8\. Flood Scenarios

Flood scenarios center on water level and temporal change, with rainfall and supporting sensors providing corroboration\. The same anomaly\-to\-evidence\-to\-state framework is reused\.

__Scenario__

__Primary trajectory__

__Expected behavior__

W0 Normal river/channel

stable or slow seasonal oscillation

NORMAL

W1 Gradual rise

persistent positive level trend with rainfall context

WATCH then SUSPECTED if persistence passes

W2 Rapid surge

steep level increase

fast escalation; severity rises with rate and magnitude

W3 Rain\-only false alarm

heavy rain but no corresponding level rise

confidence remains bounded; no forced confirmation

W4 Sensor drift

slow baseline movement in one probe

baseline/reliability logic reduces trust; peers can maintain awareness

W5 Sensor failure

water\-level signal unavailable

Information Condition DEGRADED/UNKNOWN; do not infer zero water level

W6 Recovery

level falls below operational thresholds with stable trend

RESOLVED after persistence / hysteresis

# 9\. Pollution Scenarios

__Scenario__

__Pattern__

__Expected behavior__

P0 Background

stable PM/gas with normal variation

NORMAL

P1 Local plume

rapid rise at one node then delayed nearby response

localized SUSPECTED/CONFIRMED depending on corroboration

P2 Regional episode

moderate correlated elevation across many nodes

higher coverage and confidence

P3 Single\-sensor spike

isolated extreme reading

anomaly without automatic high\-confidence hazard

P4 Sensor poisoning/drift

slowly elevated biased channel

quality/reliability degradation

P5 Wind\-driven movement

source shifts with environmental context

spatial sequence changes while incident remains coherent

# 10\. Landslide Scenarios

Landslide telemetry is especially sensitive to sensor placement and false vibration\. The simulator therefore emphasizes correlated trigger conditions and contradiction cases\.

__Scenario__

__Pattern__

__Expected behavior__

L0 Stable slope

quiet vibration \+ normal soil/rainfall

NORMAL

L1 Rain\-triggered instability

soil moisture/rainfall rising, then vibration anomaly

WATCH \-> SUSPECTED

L2 Rapid movement

sharp vibration/displacement response with corroborating context

fast escalation

L3 Vibration nuisance

short isolated vibration burst without trigger context

anomaly may increase, evidence remains limited

L4 Partial node outage

best\-positioned node unavailable

regional confidence degrades rather than fabricating continuity

# 11\. Extreme Heat Scenarios

__Scenario__

__Pattern__

__Expected behavior__

H0 Normal diurnal

expected daily temperature cycle

NORMAL

H1 Persistent heat

multi\-hour/day elevated temperature

WATCH/SUSPECTED based on configured duration

H2 High temperature \+ humidity

temperature and humidity jointly worsen exposure context

higher severity

H3 Regional heat wave

correlated elevated temperature at multiple nodes

regional event with broad spatial support

H4 Sensor saturation/failure

sensor clips or goes unavailable

confidence/Information Condition degrade

# 12\. Unknown Hazard and Cross\-Hazard Conditions

Unknown is a first\-class state, not an error bucket\. The system must be able to say: something changed materially, but available evidence does not justify assigning it to a supported hazard\.

## 12\.1 Unknown scenario families

- Large anomaly with no configured hazard evidence group satisfied\.
- Conflicting sensors across hazard families with insufficient reliability to resolve the conflict\.
- Novel multi\-signal event deliberately outside current rule coverage\.
- Simulated sensor pattern that looks hazardous but is intentionally generated as instrumentation interference\.

## 12\.2 Multi\-hazard scenarios

Multi\-hazard scenarios activate two or more independent hazard vectors\. Examples include flood \+ pollution, fire \+ extreme heat, or heavy rain \+ landslide precursors\. The system must preserve each hazard state independently and expose cross\-hazard conflict when the same destination, route or response action becomes unsafe\.

__Combination__

__Required test__

Fire \+ extreme heat

heat context must not be mistaken for combustion; fire evidence still needs its own core group

Flood \+ pollution

water hazard and pollution hazard remain separate; downstream safe\-location logic sees both

Rain \+ landslide

rain is supporting context; landslide confirmation requires appropriate evidence

Two fires

incident correlation must keep spatially/time\-separated sources distinct

Fire \+ communication outage

local edge declaration persists while regional information degrades

# 13\. Sensor Fault and Data Quality Injection

Fault injection is mandatory because a resilient disaster network is defined as much by what it refuses to believe as by what it detects\.

__Fault__

__Simulation rule__

__Expected intelligence effect__

Gaussian\-like noise

increase variance within configured bounds

lower stability / anomaly certainty as appropriate

Spike

one or few extreme samples

high local anomaly possible; evidence depends on corroboration/persistence

Dropout

missing samples

coverage decreases; never substitute zero

Stale

repeat last valid measurement with old measurement timestamp

freshness degrades; new event must not be inferred from repeated old value

Drift

slow bias term changes over time

baseline/reliability logic should detect reduced trust

Bias step

persistent offset after fault event

quality/reliability or calibration checks should reduce trust

Hard failure

no valid reading / diagnostic flag

health gate can force reliability toward zero

Contradiction

one node/channel opposes trusted group

group agreement and sensor reliability expose disagreement

Packet reordering

out\-of\-order sequence arrival

dedup/replay/sequence logic handles safely

Replay packet

duplicate old packet

must not create a fresh event

Clock skew

measurement timestamp offset

freshness/time\-quality logic handles bounded skew

Corruption

invalid schema / signature / range

reject or quarantine before reasoning

# 14\. Communication and Network Scenarios

__Scenario__

__Injected condition__

__Expected behavior__

N0 Healthy network

low loss, bounded latency

normal regional fusion

N1 Intermittent loss

bursty packet loss

store\-forward and freshness behavior visible

N2 Node partition

one node isolated

local autonomy remains; regional coverage degrades

N3 Master unreachable

Master path unavailable

edge local emergency path remains available where designed

N4 Internet outage

cloud unavailable while local Master remains

local dashboard/local alert path continues

N5 Recovery storm

many buffered packets return together

deduplication, sequence ordering and catch\-up must remain stable

N6 Adversarial duplicate

replayed signed telemetry

replay protection prevents double counting

# 15\. Ground Truth Separation

Ground truth is necessary for evaluation but must not contaminate inference\. The scenario runner maintains a private evaluator branch that contains the intended hazard source, onset, footprint, affected cells and expected state windows\. The telemetry branch contains only observations and diagnostics\.

__Artifact__

__Visible to reasoning pipeline?__

__Purpose__

Telemetry observation

YES

what the system is allowed to infer from

Sensor diagnostics

YES

health/quality/reliability context

Receive timestamp / sequence

YES

freshness, ordering, replay protection

Scenario ID

OPTIONAL / controlled

replay identification only if it carries no answer

Hazard label

NO

evaluation oracle only

True hazard footprint

NO

evaluation of geospatial output

True onset/end time

NO

temporal detection evaluation

Simulator source intensity

NO

prevents answer leakage

Expected state transition

NO

tests actual state logic

Evaluation report

POST\-RUN

accuracy / robustness measurement

# 16\. Scenario and Replay Schema

A canonical scenario manifest should be JSON/YAML compatible\. The exact storage backend is an implementation choice; field semantics are normative\.

scenario\_id: FIRE\_F3\_FALSE\_SMOKE

version: 1

seed: 240901

start\_time: 2026\-01\-01T10:00:00Z

duration\_s: 1800

cadence\_s: 5

nodes: \[\.\.\.\]

environment: \{\.\.\.\}

drivers: \{\.\.\.\}

sensor\_faults: \[\.\.\.\]

network\_faults: \[\.\.\.\]

ground\_truth: \{private: true, \.\.\.\}

evaluation: \{\.\.\.\}

## 16\.1 Minimum scenario manifest fields

__Field__

__Type__

__Required__

__Meaning__

scenario\_id

string

yes

stable unique scenario identifier

version

integer/string

yes

scenario definition version

seed

integer

yes

deterministic RNG seed

start\_time

timestamp

yes

simulation epoch

duration\_s

number

yes

simulation length

cadence\_s

number/list

yes

telemetry cadence or per\-node schedule

nodes

array

yes

node definitions and locations

environment

object

yes

background and context generators

drivers

object

yes

hazard source/event generators

faults

array

no

sensor/network fault injections

ground\_truth

private object

yes for evaluation scenarios

hidden oracle

evaluation

object

yes for test scenarios

acceptance windows and expected properties

# 17\. Determinism, Replay and Scenario Control

The same scenario manifest \+ software version \+ configuration version \+ seed must reproduce the same synthetic stream, subject to explicitly nondeterministic infrastructure components\.

## 17\.1 Replay controls

- Reset to scenario start\.
- Play/pause and adjustable replay speed\.
- Seek to a timestamp without changing the underlying event sequence\.
- Jump to hazard onset, confirmation, peak, communication outage, recovery or resolution markers\.
- Replay telemetry through ingestion exactly as recorded/generated\.
- Re\-run the same scenario after changing one configuration version to compare outputs\.
- Export an evaluation bundle containing manifest hash, software/config versions, telemetry identifiers and result summary\.

## 17\.2 Event sourcing rule

Historical observations and emitted intelligence should be append\-only/versioned\. Re\-running a model against the same historical telemetry creates a new analysis version rather than rewriting the old result\.

# 18\. Evaluation Metrics

Synthetic telemetry is valuable only if it can reveal whether NexAlert behaves correctly\. Evaluation must measure detection, uncertainty, resilience, localization and operational behavior rather than accuracy alone\.

__Metric family__

__Examples__

Detection

time\-to\-WATCH, time\-to\-SUSPECTED, time\-to\-CONFIRMED, missed\-event rate

False alarm

false confirmation rate, nuisance alert rate, single\-sensor false\-positive resistance

Confidence quality

coverage\-aware confidence degradation, agreement sensitivity, baseline\-readiness behavior

Resilience

behavior under packet loss, stale data, node isolation, Master/internet outage

Correlation

correct merge/separation of incidents by spatial/temporal windows

Geospatial

footprint overlap/error against private simulation truth where a physical model is defined

Operational

severity/state transition stability, hysteresis behavior, stand\-down correctness

Reproducibility

same seed/config produces same event stream and equivalent results

Performance

ingestion rate, inference latency, queue depth, replay throughput

# 19\. Golden Scenarios for V1

__ID__

__Scenario__

__Why it matters__

__Pass criterion__

G01

Normal baseline

proves system does not hunt noise

no false confirmation; baseline reaches READY

G02

Fire with 3\-node corroboration

hero path and distributed evidence

incident confirms with coherent spatial/temporal evidence

G03

False smoke spike

tests conservative confidence

anomaly may rise; no unjustified confirmation

G04

Flood rapid rise

tests trend \+ persistence

rapid escalation without threshold flapping

G05

Pollution regional plume

tests multi\-node correlation

regional state reflects correlated evidence

G06

Landslide precursor

tests multi\-signal evidence

WATCH/SUSPECTED reflects trigger \+ anomaly coherence

G07

Extreme heat wave

tests duration/context

sustained state without sensitivity to single spikes

G08

Multi\-hazard fire \+ heat

tests independent vectors

both states preserved; no scalar collapse

G09

Communication partition during fire

tests resilience

local declaration survives; regional info becomes degraded

G10

Master/internet outage

tests local path separation

local emergency function remains where designed

G11

Sensor drift \+ peer corroboration

tests reliability weighting

bad node influence is reduced, not silently trusted

G12

Two separate fires

tests deterministic incident correlation

separate incidents remain separate

G13

Changing wind mid\-run

tests versioned future projection

past remains frozen; future projection recomputed

G14

Replay exact match

tests determinism

same seed/config reproduces telemetry and expected outputs

# 20\. Implementation Structure

The simulator should be modular but not over\-fragmented\. A practical V1 package structure is:

simulation/

  scenarios/          \# manifests, validators, scenario registry

  environment/        \# background temporal/spatial generators

  hazards/             \# fire, flood, pollution, landslide, heat, unknown drivers

  sensors/             \# response functions, noise, drift, faults

  network/             \# latency, loss, partitions, replay behavior

  telemetry/           \# canonical serialization \+ same\-path transport

  oracle/               \# private ground truth; never imported by inference

  replay/               \# seek, pause, checkpoint, deterministic rerun

  evaluation/           \# metrics, event matching, reports

  fixtures/             \# golden scenario manifests and expected properties

The backend owns orchestration; the frontend controls scenario selection/replay but does not become the simulator of record\.

# 21\. Configuration and Parameter Rules

All scenario parameters that influence telemetry generation or hazard reasoning must be versioned and auditable\. No hidden constants may be introduced in simulation code when a behavior affects evaluation or the SIH demo\.

__Parameter class__

__Examples__

Temporal

cadence, persistence windows, event durations, replay speed

Spatial

source location, attenuation radius, node separation, correlation radius

Sensor

noise scale, drift rate, response lag, saturation, dropout probability

Network

latency distribution, packet\-loss model, partition duration, retry behavior

Hazard

source intensity curve, onset profile, evidence thresholds, scenario drivers

Reasoning

hazard weights, z cap/lambda, confidence weights, hysteresis values

Geospatial

grid resolution, CRS, spread coefficients, warning/projection horizons

Evaluation

event matching radius/time window, metric thresholds, expected outcome windows

# 22\. Guardrails and Failure Modes

__Failure mode__

__Guardrail__

Simulator directly tells frontend the answer

frontend renders backend state/geospatial outputs only

Hazard label leaks into telemetry

strict schema validation \+ separate oracle storage

Zero used for missing data

missing/stale must remain explicit in telemetry/quality layer

Independent hazards collapsed

separate hazard vectors, states and risk layers

All nodes behave identically

spatial attenuation \+ delay \+ local variability

False confidence from single bad sensor

reliability and corroboration gates

Replay changes history

versioned analysis; append\-only historical record

Scenario irreproducible

seed \+ manifest \+ config/software version captured

Synthetic model presented as field truth

scenario metadata and documentation clearly identify synthetic nature

Legacy architecture returns by accident

current final baseline and document authority list are explicit

# 23\. V1 Acceptance Checklist

1. At least one deterministic scenario exists for each supported hazard and one Unknown case\.
2. At least one multi\-hazard scenario activates two independent hazard vectors concurrently\.
3. Synthetic telemetry enters the same backend ingestion contract used by hardware telemetry\.
4. Ground truth is inaccessible to production inference code\.
5. Missing, stale, drifted, failed and contradictory sensor cases are represented explicitly\.
6. Multi\-node scenarios contain spatial correlation, delay and attenuation rather than duplicated streams\.
7. Network partition and recovery scenarios exercise store\-forward, freshness and deduplication behavior\.
8. Fire scenarios invoke the same fire\-spread engine as LIVE mode\.
9. Changing environmental conditions create versioned future projections without rewriting historical truth\.
10. Replay can pause, seek, restart and reproduce a scenario deterministically\.
11. Golden scenarios have machine\-checkable acceptance criteria\.
12. Every parameter affecting a test result is versioned and traceable\.
13. SIHDemo mode never depends on decorative or precomputed hazard visuals that bypass backend reasoning\.

# 24\. Final Engineering Position

NexAlert will not be judged by how many synthetic hazards it can make appear on a screen\. The purpose of this layer is to prove that the same architecture can remain useful under normal conditions, uncertain evidence, multiple simultaneous hazards, broken sensors and broken communications\. Synthetic telemetry is therefore a controlled test instrument: it creates difficult situations, preserves the observational boundary, and lets the actual NexAlert intelligence prove what it can and cannot infer\.

