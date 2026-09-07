__NEXALERT__

__MATHEMATICAL INTELLIGENCE & HAZARD REASONING__

Final V1 Engineering Specification — Implementation Baseline

__Document role  
__This is the definitive implementation reference for how NexAlert converts canonical telemetry into trustworthy, hazard\-specific intelligence\. It supersedes older intelligence drafts where they conflict with this document, the Master Architecture, the V2\.3 baseline, or the final adversarial review\. It defines mathematical structure, state semantics, hazard reasoning boundaries, edge\-versus\-Master responsibilities, and validation requirements\.

__Field__

__Value__

Product

NexAlert

SIH problem

SIH26178 — resilient AI\-powered environmental monitoring and early warning

Document

04 — Mathematical Intelligence & Hazard Reasoning

Status

FINAL V1 IMPLEMENTATION BASELINE

Primary target

ESP32\-S3\-class field node \+ Raspberry Pi Master

Hero hazard

Forest fire — real controlled sensing \+ deterministic/manual calibration

Second path

Flood — same framework; synthetic/physically grounded telemetry

Core principle

Local intelligence remains functional without Master/cloud/internet/satellite

__Critical coding\-agent scope lock  
__Do not invent a new mathematical layer during implementation\. Do not introduce a mandatory fire classifier\. Implement the structure first, keep parameters configurable, and let empirical trials determine tunable values\. A learned model is optional only when real data demonstrates that it materially improves the locked deterministic architecture\.

# Document Control & Authority

__Status__

__Meaning__

LOCKED

Architectural or mathematical structure that implementation must preserve unless validation reveals a genuine failure\.

PARAMETER

Value that must be measured, tuned, calibrated, benchmarked or selected from evidence\.

DEFERRED

Supported by architecture but intentionally not required by the first physical prototype\.

ROADMAP

Potential future enhancement; not required for V1\.

REJECTED

An earlier candidate approach that is intentionally not part of V1\.

## Authority hierarchy

__Priority__

__Source__

1

Document 01 — Master System Architecture & Invariants

2

This document — final intelligence mathematical baseline

3

Document 02 — TRD requirements

4

Document 03 — Technology/compute allocation

5

Domain\-specific data/hardware/geospatial specifications

6

Earlier V2\.2/V2\.3 drafts only where consistent with the frozen baseline

__Important historical distinction  
__The uploaded V2\.3 intelligence document is the active mathematical source\. Earlier V2\.2 material included superseded candidates, including an earlier learned\-model direction\. The final architecture keeps deterministic/configuration\-driven hazard reasoning for V1, especially fire, and does not require a trained classifier\. The V2\.3 source explicitly states this implementation direction and the simulator must provide telemetry without the answer\. fileciteturn16file3 fileciteturn17file2

# 1\. Intelligence Layer Objective

The intelligence layer exists to make a field node more than a sensor relay\. It evaluates whether observations are valid, whether the sensing source is healthy and trustworthy, whether signals are unusual relative to local normal behavior, whether the observed pattern supports a specific hazard, how trustworthy that hazard assessment is, how severe the condition is, and what operational state follows\.

OBSERVATIONS  
   ↓  
VALIDATION / MISSINGNESS  
   ↓  
SENSOR HEALTH H\_i  
   ↓  
SIGNAL QUALITY Q\_i  
   ↓  
EVIDENCE RELIABILITY R\_i  
   ↓  
BASELINE READINESS B\_i  
   ↓  
FEATURES / TEMPORAL SIGNALS  
   ↓  
ANOMALY A\_i / A\_node / A\_h  
   ↓  
HAZARD EVIDENCE E\_h  
   ↓  
EVIDENCE CONFIDENCE C\_h  
   ↓  
SEVERITY S\_h  
   ↓  
OPERATIONAL RISK R\_h  
   ↓  
STATE\_h \+ INFORMATION CONDITION  
   ↓  
COMPACT INTELLIGENCE RESULT  
   ↓  
LOCAL ACTION/ALERT \+ MASTER FUSION  


## 1\.1 Core conceptual question

Every intelligence cycle should move toward answering: What is happening? What could it be? How trustworthy is that assessment? How dangerous is it? What should happen next?

## 1\.2 Fundamental separations

__Concept__

__Definition__

__Not equivalent to__

Sensor Health

Longer\-term operational condition of the sensing component\.

Battery, current anomaly, hazard\.

Signal Quality

Current integrity/stability of an observation\.

Long\-term sensor health\.

Evidence Reliability

Trust weight given to a current observation\.

Hazard confidence or operational risk\.

Anomaly

Magnitude of deviation from an appropriate baseline\.

Hazard declaration\.

Hazard Evidence

Support for hazard h from the observed pattern\.

Probability unless separately calibrated\.

Evidence Confidence

Trustworthiness of the current hazard assessment\.

Severity\.

Severity

Intensity/danger of the condition if the hazard is real/continues\.

Probability or evidence confidence\.

Operational Risk

Linear operational index for urgency/context\.

Probability of disaster\.

Information Condition

Completeness/freshness/quality of available information\.

Hazard severity\.

Hazard State

Lifecycle state of the hazard hypothesis\.

Response execution\.

__Foundational invariant  
__Missing evidence is not evidence of absence\. UNKNOWN is not NORMAL\. A system that lacks sufficient information must be able to say so explicitly\.

# 2\. Deployment & Responsibility Boundary

## 2\.1 Prototype

__Component__

__Prototype__

__Scalable interpretation__

Edge nodes

1 ESP32\-S3\-class node

N distributed field nodes

Master

1 Raspberry Pi

Regional local control/compute center

Cloud

Optional for central services

Centralized coordination/persistence

Hero hazard

Fire

Additional hazard configurations

Second hazard

Flood

Additional validated hazards

## 2\.2 Local edge responsibilities

- Sensor diagnostics and health\.
- Current signal quality\.
- Evidence reliability\.
- Baseline readiness and controlled baseline updates\.
- Robust anomaly detection\.
- Hazard evidence model for configured lightweight hazards\.
- Evidence confidence\.
- Edge severity\.
- Edge operational\-risk index\.
- Hazard state and local safe behavior\.

## 2\.3 Master responsibilities

- Cross\-node evidence aggregation\.
- Freshness weighting and node trust\.
- Regional hazard assessment and incident correlation\.
- Spatial risk mapping and geospatial services\.
- Population/infrastructure exposure\.
- External evidence integration where enabled\.
- Regional forecasting/long\-term analysis\.
- Authority dashboard and operational workflow\.

__Master non\-override rule  
__The Master must not erase a valid local hazard declaration merely because neighboring nodes or external evidence disagree\. Local state and regional state are separate quantities\. The Master may add corroboration, change regional confidence/severity, or flag uncertainty, but the local node retains the ability to act autonomously\. fileciteturn18file4

# 3\. Diagnostic Layer

Diagnostics occur before hazard reasoning\. Their purpose is to prevent a dead sensor, corrupted measurement, poor signal, or invalid operating condition from masquerading as environmental evidence\.

## 3\.1 Sensor Health H\_i

H\_i answers: Is this sensing component operationally healthy enough to contribute useful measurements over the longer term?

__H\_i^soft\(t\) = Σ\_j w\_ij · D\_ij\(t\),     Σ\_j w\_ij = 1__

__H\_i\(t\) = 0, if F\_i\(t\) = 1; otherwise H\_i\(t\) = H\_i^soft\(t\)__

__Symbol__

__Meaning__

D\_ij

Normalized diagnostic dimension j for sensor i\.

w\_ij

Diagnostic weight; configurable/validated parameter\.

F\_i

Hard\-failure indicator\.

H\_i^soft

Soft weighted health score before hard failure gating\.

H\_i

Final sensor health contribution\.

### Diagnostic dimensions

- Self\-test result\.
- Communication integrity\.
- Calibration validity\.
- Long\-term stability\.
- Drift condition\.
- Sensor\-specific fault indicators\.

### Hard\-failure rule

A definitive self\-test failure, sensor disconnection, sustained communication timeout, impossible electrical state, or sensor\-specific fatal fault may set F\_i=1\. Soft indications of deterioration should remain in H\_i^soft unless the hardware specification defines a true hard failure\.

### Battery separation

Battery and solar state are independent operational signals\. Low battery does not automatically mean poor sensor health\. Sensor availability/health is affected only when the power condition actually degrades the sensor\.

## 3\.2 Signal Quality Q\_i

__Q\_i\(t\) = q\_integrity,i\(t\) × q\_stability,i\(t\)__

__Component__

__What it measures__

q\_integrity

Missing samples, invalid values, saturation, packet/communication errors and basic integrity\.

q\_stability

Short\-window noise, erratic behavior, abnormal variance and observation stability\.

The deliberately small quality model prevents parameter explosion\. More detailed diagnostics remain available as metadata rather than creating dozens of independently tuned scores\.

## 3\.3 Evidence Reliability R\_i

__R\_i\(t\) = H\_i\(t\) × Q\_i\(t\) × K\_i\(t\)__

K\_i represents current calibration/operating validity\. Multiplication acts as a strict trust gate: a fundamentally unhealthy or unusable observation should not regain full influence simply because another dimension is healthy\.

__No double counting  
__R\_i participates in the evidence pathway\. It must not be independently added again as a duplicate confidence penalty later\. Reliability has already affected how much the underlying evidence contributes\.

# 4\. Baseline, Temporal & Feature Layer

## 4\.1 Baseline readiness

__B\_i\(t\) ∈ \[0,1\]__

__State__

__Meaning__

INITIALIZING

Insufficient observations for a stable baseline\.

LEARNING

Baseline is adapting under controlled rules\.

READY

Baseline is sufficiently mature for normal anomaly interpretation\.

FROZEN

Baseline adaptation is stopped because a hazard is confirmed/critical\.

RECOVERING

Post\-event baseline is being cautiously relearned\.

A new node must not claim that its first few observations constitute a trustworthy anomaly baseline\.

## 4\.2 Robust median/MAD baseline

__m\_i = median\(x\_i\)__

__MAD\_i = median\(|x\_i − m\_i|\)__

__s\_i = 1\.4826 × MAD\_i \+ ε__

__z\_i = \(x\_i − m\_i\) / s\_i__

The median/MAD form is the default robust approach for environmental signals such as temperature, humidity, pressure and suitable gas measurements\. It should not be blindly applied to every modality\.

## 4\.3 Sensor\-specific baseline methods

__Signal__

__Preferred treatment__

Temperature/humidity/pressure

Robust median/MAD where behavior is locally appropriate\.

Gas response

Robust baseline subject to sensor calibration/cross\-sensitivity behavior\.

Water level

Trend\-relative or expected\-rate logic; avoid treating legitimate monotonic rise as mere baseline drift\.

Soil moisture

Trend\-relative/hazard\-specific expectation where slow drift is normal\.

Vibration

Amplitude anomaly plus frequency\-domain features when appropriate\.

## 4\.4 Controlled baseline update

__m\_i\(t\+1\) = \(1 − η\_i\)m\_i\(t\) \+ η\_i x\_i\(t\)__

__State__

__Baseline behavior__

NORMAL/WATCH

Use η\_normal; rate\-limited adaptation\.

SUSPECTED

Use slower η\_slow\.

CONFIRMED/CRITICAL

η\_i = 0; freeze\.

RESOLVED

Enter RECOVERING and relearn under bounded adaptation\.

The baseline must not learn a disaster as the new normal\. Rate\-limiting before confirmation is also required so a slowly developing hazard cannot silently contaminate the baseline\.

## 4\.5 Temporal features

__T\_y\(t\) = \[y\(t\) − y\(t−Δt\)\] / Δt__

__G\_y\(t\) = \[T\_y\(t\) − T\_y\(t−Δt\)\] / Δt__

__P\_h\(t\) = \(1/W\) Σ\_\{k=0\}^\{W−1\} 1\[E\_h\(t−k\) > θ\_p\]__

__Feature__

__Meaning__

T\_y

Rate of change/trend\.

G\_y

Acceleration/change in trend\.

P\_h

Fraction of recent samples supporting persistent hazard evidence\.

# 5\. Anomaly Quantities

## 5\.1 Individual anomaly

__A\_i\(t\) = 1 − exp\(−min\(|z\_i|, z\_cap\) / λ\)__

A\_i is bounded and monotonic\. The cap prevents a single extreme observation from dominating without limit\.

## 5\.2 Local aggregate anomaly

__A\_node\(t\) = \[Σ\_i R\_i A\_i\] / \[Σ\_i R\_i \+ ε\]__

A\_node indicates whether the overall local environment is behaving unusually, with unreliable observations contributing less\.

## 5\.3 Hazard\-specific anomaly

__A\_h\(t\) = \[Σ\_i w\_ih R\_i A\_i\] / \[Σ\_i w\_ih R\_i \+ ε\]__

A\_h restricts anomaly aggregation to signals relevant to hazard h\.

## 5\.4 Interpretation

__Value concept__

__Interpretation__

Low A\_i

Measurement is near its baseline\.

High A\_i

Measurement strongly deviates from baseline\.

Low A\_node

No strong local aggregate abnormality\.

High A\_node

Local environment is collectively abnormal\.

High A\_h

Abnormality is concentrated in evidence relevant to hazard h\.

__Important  
__A high anomaly score is not itself a disaster declaration\. The next layer must determine whether the abnormality maps coherently to a known hazard\.

# 6\. Hazard Evidence Engine

## 6\.1 Common interface

__E\_h = HazardReasoning\_h\(A\_i, R\_i, T\_y, G\_y, P\_h, context, availability\)__

Hazard evidence is produced by a reusable hazard\-specific reasoning component\. The implementation can be deterministic/configuration\-driven and does not require a learned classifier\.

## 6\.2 Configuration\-driven architecture

hazard\_config/  
  fire/  
    core\_evidence  
    supporting\_evidence  
    evidence\_groups  
    feature\_mapping  
    thresholds  
    temporal\_requirements  
    state\_rules  
  flood/  
    \.\.\.  
  pollution/  
    \.\.\.  
  landslide/  
    \.\.\.  
  extreme\_heat/  
    \.\.\.  


Adding a hazard should primarily require a hazard configuration and validation scenarios rather than rewriting the common anomaly, confidence, severity, risk, state, or transport pipeline\.

## 6\.3 Evidence source classes

__Class__

__Meaning__

Core evidence

Signals required to support credible confirmation\.

Supporting evidence

Useful corroboration but not sufficient alone for confirmation\.

Temporal evidence

Persistence, rise rate, acceleration or duration\.

Context

Optional environmental/terrain/external context\.

Availability

Explicit indication of what evidence exists or is missing\.

## 6\.4 Hazard guidance

__Hazard__

__Core conceptual signals__

__Supporting/context__

__Temporal evidence__

Fire

Smoke/PM \+ temperature/thermal evidence

Gas, humidity, pressure, wind context

Rise rate, persistence, acceleration

Flood

Water level \+ rainfall

Soil moisture, pressure/weather context

Level trend, rate of rise, cumulative rain

Landslide

Soil moisture and/or vibration/displacement depending hardware

Rainfall, terrain context

Saturation trend, rain accumulation, vibration change

Pollution

PM2\.5/PM10 \+ relevant gas channels

Temperature/humidity, external station data

Spike size, duration, persistence

Extreme heat

Temperature \+ local context

Humidity/pressure

Heat persistence and escalation

__Hardware dependency  
__This table is conceptual hazard guidance, not a final sensor assignment\. The exact core/supporting mapping depends on the locked hardware specification, calibration results and available data\.

# 7\. Evidence Confidence

## 7\.1 Coverage

__C\_cov,h = \[Σ\_i w\_ih u\_i\] / \[Σ\_i w\_ih\]__

u\_i=1 when the relevant evidence is usable and 0 when unavailable\. Missingness must be represented explicitly, never silently converted to a zero sensor value\.

## 7\.2 Core evidence floor

Each hazard declares core and supporting evidence\. If required core evidence is unavailable, confirmation capability is capped according to a validated hazard\-specific rule\. The cap is a parameter and must not be invented during coding\.

## 7\.3 Group\-level agreement

__ē = \[Σ\_g v\_g e\_g\] / \[Σ\_g v\_g\]__

__V\_e = \[Σ\_g v\_g\(e\_g − ē\)^2\] / \[Σ\_g v\_g\]__

__C\_agree = exp\(−k\_v V\_e\)__

Agreement is evaluated over evidence groups rather than treating every individual correlated sensor as an independent vote\. For example, temperature and humidity may be correlated in fire conditions; grouping prevents their co\-movement from masquerading as independent corroboration\. fileciteturn18file12

## 7\.4 Temporal confidence

__C\_temp,h = P\_h__

## 7\.5 Baseline confidence

__C\_base,h = f\(B\_i\)__

The exact mapping from baseline readiness to confidence is hazard/configuration\-specific and must not double count information already used elsewhere\.

## 7\.6 Final evidence confidence

__C\_h = w\_c C\_cov,h \+ w\_a C\_agree,h \+ w\_t C\_temp,h \+ w\_b C\_base,h__

__w\_c \+ w\_a \+ w\_t \+ w\_b = 1__

Confidence is an arithmetic weighted combination\. Reliability is not added a second time here because it has already affected the upstream evidence\.

## 7\.7 Confidence applicability

When E\_h < θ\_assess, confidence should generally be represented as N/A because there is not materially active evidence to characterize\. This avoids presenting an arbitrary confidence value for a non\-active hypothesis\.

__Confidence is not probability  
__C\_h expresses trustworthiness of the evidence assessment under the defined information conditions\. It is not a calibrated probability that the hazard exists\.

# 8\. Severity

## 8\.1 Edge severity

__S\_h^edge = w\_I I\_h \+ w\_T T\_h \+ w\_D D\_h__

__w\_I \+ w\_T \+ w\_D = 1__

__Component__

__Meaning__

I\_h

Hazard\-specific normalized intensity\.

T\_h

Temporal escalation/trend contribution\.

D\_h

Duration/persistence or other hazard\-specific danger dimension\.

Severity deliberately excludes E\_h\. The system should not create a circular construct where 'we believe it is a fire' directly makes the fire more severe\.

## 8\.2 Hazard\-specific normalization

Intensity mapping must be hazard\-specific\. A water\-level rise rate cannot be treated as numerically equivalent to a gas\-response magnitude\. Each mapping is defined in the hazard configuration and validated against relevant trials/scenarios\.

## 8\.3 Regional enrichment

The Master may enrich edge severity using spatial context, cross\-node evidence, exposure and other authorized information\. This produces regional assessment context while preserving the distinction between edge and regional state\.

# 9\. Operational Risk Index

__R\_h^edge = w\_E E\_h \+ w\_S S\_h \+ w\_T T\_h__

__w\_E \+ w\_S \+ w\_T = 1__

R\_h is explicitly an Operational Risk Index, not a probability of disaster\. It combines evidence, consequence\-related severity and temporal escalation into an operational urgency measure\.

## 9\.1 Confidence handling

Confidence is handled by the state/decision engine rather than multiplying R\_h by C\_h\. This allows severe\-but\-uncertain conditions to trigger urgent verification without pretending they have high confirmation confidence\.

## 9\.2 Regional context

At the Master, regional risk may incorporate node trust, freshness, spatial corroboration, exposure and regional context\. The result remains an operational index and must be labeled accordingly\.

__Never do this  
__Do not introduce R = E × C × S as a replacement for the locked architecture\. Do not interpret the linear operational\-risk index as a probability\.

# 10\. Decision & Hazard State Engine

## 10\.1 Hazard states

__State__

__Meaning__

__General condition__

NORMAL

No meaningful active hazard hypothesis\.

Evidence/risk below watch criteria\.

WATCH

Something meaningful is changing\.

Anomaly or risk crosses watch criteria\.

SUSPECTED

A hazard explanation is plausible but confirmation is incomplete\.

Evidence meaningful; confidence/persistence/core coverage incomplete\.

CONFIRMED

Evidence supports credible hazard declaration\.

Evidence \+ confidence \+ temporal/core requirements satisfied\.

CRITICAL

Urgent/severe or rapidly escalating condition\.

Very high severity/evidence or fast\-escalation pathway\.

RESOLVED

Hazard condition has subsided and remained below exit conditions\.

Recovery/hysteresis criteria satisfied\.

## 10\.2 Information Condition

__Condition__

__Meaning__

GOOD

Sufficient relevant observations and diagnostics are available\.

DEGRADED

Important sensing/quality limitations exist, but useful reasoning remains possible\.

UNKNOWN

The system cannot responsibly characterize the situation or applicability of a known hazard is insufficient\.

Environmental state and information condition are independent\. CONFIRMED FIRE \+ DEGRADED information is valid if one supporting sensor is unavailable\. SUSPECTED FIRE \+ GOOD information is also valid if the data are clean but evidence has not yet crossed the confirmation requirements\.

## 10\.3 Hysteresis

__θ\_enter > θ\_exit__

Separate entry and exit thresholds reduce state flapping caused by normal measurement noise\.

## 10\.4 Persistence

Persistence is used to distinguish transient spikes from sustained hazard evidence\. The required window W and evidence threshold θ\_p are configuration parameters\.

## 10\.5 Fast escalation

A rapidly escalating severe event must not be forced to wait through a long fixed persistence period\. The V1 approach is a simple policy path: weaker evidence requires more persistence; stronger evidence requires less; extreme severity plus rapid escalation may reach urgent action quickly\.

## 10\.6 Unknown fallback

__If A\_node > θ\_A AND max\_h\(E\_h\) < θ\_known → UNKNOWN / INVESTIGATE__

This is a conservative fallback, not a claim of rigorous out\-of\-distribution detection\.

# 11\. Multi\-Hazard Intelligence

## 11\.1 Independent hazard evaluation

Every configured hazard evaluates the same observation frame through its own evidence mapping\. The framework is common; the evidence relationships are hazard\-specific\.

same telemetry  
    ↓  
common diagnostics / baseline / anomaly  
    ↓  
┌──────────────┬──────────────┬──────────────┐  
│ FIRE         │ FLOOD        │ POLLUTION    │  
│ E,C,S,R,state│ E,C,S,R,state│ E,C,S,R,state│  
└──────────────┴──────────────┴──────────────┘  
                 ↓  
          independent outputs

## 11\.2 Simultaneous hazards

A node or region may simultaneously report different states for different hazards\. One hazard must never overwrite another\.

## 11\.3 No universal combined hazard risk

__Permanent rule  
__Fire risk, flood risk, pollution risk, landslide risk and other hazard risk surfaces/assessments remain separate\. The system may show that several hazards are active simultaneously, but V1 never algebraically blends unrelated hazard risks into one universal 'disaster probability'\.

# 12\. Distributed Intelligence & Regional Fusion

## 12\.1 Why fusion exists

One node provides local evidence\. Multiple nodes can corroborate or contradict one another\. The Master combines node\-level information to build a regional picture\.

## 12\.2 Conceptual fusion

__RegionalEvidence\_h = weighted aggregation of node evidence using trust × confidence × freshness/context__

The exact production fusion formula is intentionally kept configurable\. The architectural invariant is that stale, untrusted or low\-confidence evidence must not carry the same influence as current, trustworthy observations\.

## 12\.3 Node trust

Node trust T\_n is a slow\-changing reliability/context quantity influenced by long\-term behavior and network observations\. It is distinct from momentary sensor reliability R\_i\.

## 12\.4 Freshness

__Age\_i = t\_now − t\_measurement__

Freshness weighting λ\_f or equivalent decay is a parameter to validate under realistic network latency/partition conditions\.

## 12\.5 Correlated regional evidence

Multiple nearby sensors may observe the same environmental phenomenon\. The fusion layer should not treat spatially redundant or causally correlated measurements as fully independent proof\.

## 12\.6 Local vs regional state

Local node state remains locally actionable\. Regional state is a separate assessment used for broader mapping, incident management, exposure and authority operations\.

# 13\. Hazard\-Specific V1 Strategy

## 13\.1 Fire — hero hazard

__Fire strategy is locked  
__Fire is manually configured/calibrated\. Do not build a mandatory supervised fire classifier for V1\. Use repeated controlled real fire/smoke trials to calibrate evidence mappings, thresholds and safety behavior\.

__Aspect__

__Fire V1__

Core evidence

Smoke/PM \+ temperature/thermal evidence, subject to final hardware\.

Supporting

Gas, humidity, pressure and other contextual evidence where valid\.

Temporal

Rise rate, persistence, acceleration\.

Reasoning

Deterministic/configuration\-driven\.

Calibration

Real controlled hardware trials\.

Geospatial follow\-on

Fire spread engine defined in Document 05\.

ML requirement

None\.

The intelligence layer's fire output triggers/conditions downstream geospatial services\. Fire spread itself is not part of the anomaly/evidence mathematics in this document; it has its own specification\.

## 13\.2 Flood — second validation path

Flood reuses the same common pipeline but changes the hazard\-specific feature mapping\. Water level, rainfall, soil moisture and context are interpreted using flood\-specific relationships, including level trend, rate of rise and cumulative rainfall\.

Synthetic flood scenarios are allowed to demonstrate the end\-to\-end system when real controlled flood data are unavailable\. The simulator must send telemetry only; it must not send the expected label into the intelligence engine\.

## 13\.3 Other hazards

Pollution, landslide and extreme heat remain framework\-supported where configured evidence and hardware/data exist\. They are not automatically claimed to have the same validation strength as fire\.

# 14\. Data & Learning Strategy

## 14\.1 Three data classes

__Data class__

__Purpose__

Real hardware data

Calibration, repeatability, sensor characterization, fire validation\.

External environmental/geospatial data

Context, exposure, validation and geospatial computation\.

Synthetic telemetry

Scenario testing, failure injection, software validation and multi\-hazard demonstration\.

## 14\.2 Bootstrap principle

NexAlert does not require a massive labeled ML dataset to begin operating\. The V1 architecture is explicitly designed to bootstrap with deterministic reasoning, measured real trials, real environmental/context datasets, and synthetic scenarios\.

## 14\.3 Ground\-truth isolation

A simulator may keep ground\-truth hazard labels privately for evaluation\. Those labels MUST NOT be included in the telemetry or context presented to the reasoning engine\. This ensures the simulator tests the system's ability to infer the hazard rather than merely replaying the answer\.

## 14\.4 Learned model introduction

A learned classifier/model becomes eligible only when real data show a meaningful failure of the current reasoning and the learned model demonstrates measurable improvement on held\-out data\. It must then be introduced as a documented model component rather than silently replacing deterministic safety logic\.

# 15\. Intelligence Failure & Degraded Behavior

__Condition__

__Intelligence behavior__

Missing sensor value

Mark unavailable; do not substitute zero\.

Sensor hard failure

H\_i=0 for that sensor contribution\.

Poor signal integrity

Lower Q\_i; exclude invalid observations as appropriate\.

Calibration invalid

Lower/gate K\_i; reduce R\_i\.

Baseline not ready

Limit anomaly/confidence interpretation\.

Confirmed/critical event

Freeze baseline\.

Post\-event

Controlled RECOVERING state\.

Conflicting evidence

Reduce agreement/confidence; do not force certainty\.

Core evidence missing

Apply hazard\-specific confirmation cap\.

Stale observation

Reduce freshness/trust and potentially information condition\.

Unknown hazard mapping

UNKNOWN / INVESTIGATE when abnormality lacks sufficient known\-hazard support\.

Master unavailable

Local intelligence continues on node\.

Internet unavailable

Local intelligence continues; upstream synchronization delayed\.

## 15\.1 Diagnostic output vs hazard output

A failed sensor is not itself an environmental hazard\. The diagnostic layer can cause the hazard engine to lower evidence availability/confidence, while the underlying environmental state remains independently determined\.

## 15\.2 Contradictions

When one sensor indicates danger and another reliable core sensor strongly contradicts it, the system must preserve the contradiction through group\-level agreement and information condition\. It must not silently select whichever sensor produces a preferred hazard state\.

# 16\. Intelligence Packet

## 16\.1 Purpose

The intelligence packet is the compact edge result transmitted to the Master or resilient network\. It carries the decision\-relevant state, trust context and enough provenance to explain the decision without retransmitting the entire raw time series\.

## 16\.2 Canonical conceptual structure

\{  
  "node\_id": "NODE\-001",  
  "timestamp": "\.\.\.",  
  "sequence": 1842,  
  
  "information\_condition": "GOOD",  
  
  "hazards": \{  
    "fire": \{  
      "evidence": 0\.89,  
      "confidence": 0\.88,  
      "severity": 0\.81,  
      "operational\_risk": 0\.84,  
      "state": "CONFIRMED"  
    \},  
    "flood": \{  
      "evidence": 0\.03,  
      "confidence": "N/A",  
      "severity": 0\.04,  
      "operational\_risk": 0\.03,  
      "state": "NORMAL"  
    \}  
  \},  
  
  "diagnostics": \{  
    "health\_summary": "\.\.\.",  
    "baseline\_readiness": "\.\.\.",  
    "core\_evidence\_coverage": "\.\.\."  
  \}  
\}

This is conceptual; the exact transport schema is defined in the final backend/telemetry specification\. Raw variable names and encoding may change for implementation, but the semantics must remain\.

## 16\.3 Explainability fields

- Contributing evidence groups\.
- Core\-evidence availability\.
- Agreement quality\.
- Persistence status\.
- Baseline readiness\.
- Key trend/escalation signals\.
- Information condition\.

# 17\. Health Reporting & Timing

Fast diagnostics operate internally at the observation cadence; slower health summaries are reported periodically for system visibility\.

__Quantity__

__Typical behavior__

Sensor Health H\_i

Slow\-changing; longer\-term diagnostic view\.

Signal Quality Q\_i

Fast; seconds/minutes scale depending sensor\.

Evidence Reliability R\_i

Fast; per observation/decision\.

Baseline readiness B\_i

Slowly increasing during learning\.

Node Trust T\_n

Slow\-changing long\-term quantity\.

Battery/power

Continuously monitored and reported separately\.

## 17\.1 Periodic health report

The existing heartbeat mechanism may be extended with a component\-level health report at approximately five\-minute intervals, while faster diagnostics continue internally\. The dashboard can show an aggregate health summary only when it has underlying diagnostic components to justify it\.

__Health category__

__Example fields__

Compute

ESP32 health, attached compute health if present\.

Communication

Wi\-Fi/radio health, packet loss/latency indicators\.

Sensors

Per\-sensor health/availability/calibration/stability\.

Power

Battery, solar state, power mode\.

Storage

Flash/storage availability\.

Node metadata

Uptime, last heartbeat, current state\.

# 18\. ESP32 Implementation Boundary

## 18\.1 Why the intelligence is edge\-capable

The V1 intelligence mathematics is lightweight enough to express in embedded C/C\+\+: arithmetic, comparisons, bounded exponential operations, rolling statistics and configuration\-driven rules\. The dominant implementation risk is concurrency between sensing, networking, buffering, local service and inference, not the mathematical operations themselves\. This boundary and benchmark requirement are carried from the V2\.3 baseline\. fileciteturn17file7

## 18\.2 Likely concurrent workloads

- Sensor sampling\.
- Wi\-Fi AP/local emergency service\.
- Telemetry serialization and HMAC authentication\.
- Telemetry buffering\.
- Diagnostics\.
- Baseline/anomaly computation\.
- Hazard reasoning\.
- Application/network services\.

## 18\.3 Benchmark requirements

__Metric__

__Required measurement__

Sensing\-to\-decision latency

End\-to\-end local time under normal and stressed network load\.

Sampling jitter

Worst\-case timing variation while a phone/client is connected\.

Free heap

Minimum free heap/high\-water behavior under combined workload\.

CPU utilization

Per\-task/overall CPU load\.

Inference frequency

Actual achievable local intelligence cadence\.

Starvation

Verify Wi\-Fi AP/network/buffering cannot starve intelligence\.

__Architecture candidate, not assumption  
__A dual\-core task partition on ESP32\-S3 is a reasonable candidate, but it is not considered validated until measured on the actual firmware stack and sensor set\.

## 18\.4 Python reference vs C/C\+\+ embedded implementation

The same mathematical specification can have two runtime implementations\. Python is the reference for validation/simulation/server execution; C/C\+\+ is the embedded implementation on ESP32 where local computation is required\. Golden\-vector tests must compare the two within documented tolerances\.

# 19\. Intelligence Demo Flows

## 19\.1 Real fire

Controlled physical event  
  ↓  
real sensors  
  ↓  
ESP32 telemetry \+ local intelligence  
  ↓  
FIRE state created locally  
  ↓  
NexAlert transport  
  ↓  
Raspberry Pi / backend  
  ↓  
regional incident  
  ↓  
geospatial fire spread  
  ↓  
risk / affected area / exposure  
  ↓  
response recommendation  
  ↓  
authority \+ citizen views

The decision should exist on the ESP32 before it is visible at the Master, demonstrating genuine edge reasoning\.

## 19\.2 Synthetic multi\-hazard

Scenario generator  
  ↓  
telemetry only  
  ↓  
same telemetry contract  
  ↓  
same intelligence engine  
  ↓  
independent FIRE/FLOOD/etc evaluation  
  ↓  
same incident/state path

## 19\.3 Kill\-network

CONNECTED  
  ↓  
event detected  
  ↓  
network/Internet failure  
  ↓  
local intelligence continues  
  ↓  
buffer  
  ↓  
reconnect  
  ↓  
authenticate/deduplicate  
  ↓  
synchronize

## 19\.4 UNKNOWN

Strong abnormality  
\+  
weak mapping to every configured known hazard  
        ↓  
UNKNOWN / INVESTIGATE

# 20\. Intelligence Architectural Invariants

__🔒 01  __Battery ≠ Sensor Health\.

__🔒 02  __Health ≠ Signal Quality\.

__🔒 03  __Anomaly ≠ Hazard\.

__🔒 04  __Evidence ≠ Probability\.

__🔒 05  __Confidence ≠ Severity\.

__🔒 06  __Severity ≠ Probability\.

__🔒 07  __Operational Risk ≠ Probability\.

__🔒 08  __Missing ≠ Zero\.

__🔒 09  __UNKNOWN ≠ NORMAL\.

__🔒 10  __Local state ≠ regional state\.

__🔒 11  __Reliability must not be double\-counted in confidence\.

__🔒 12  __Correlated sensors must be grouped for agreement\.

__🔒 13  __Required core evidence must constrain confirmation capability\.

__🔒 14  __Confirmed/critical events must freeze the baseline\.

__🔒 15  __Hazard states are independent across hazards\.

__🔒 16  __Simulation must provide telemetry, not the expected answer\.

__🔒 17  __Fire V1 does not require a trained classifier\.

__🔒 18  __Local intelligence must not depend on Master/cloud/internet/satellite\.

__🔒 19  __The Master must not erase a valid local hazard declaration\.

__🔒 20  __Frontend clients do not calculate intelligence truth\.

__🔒 21  __NexAlert recommends downstream response; human approval is required before operational action\.

# 21\. Parameters Requiring Validation

__Parameter__

__Purpose__

__Validation method__

w\_ij

Sensor\-health diagnostic weights

Sensor behavior/engineering validation\.

λ, z\_cap

Anomaly sensitivity and cap

Controlled baseline/outlier experiments\.

w\_ih

Hazard relevance mapping

Domain reasoning \+ scenario ablation\.

Hazard reasoning configuration

Evidence mappings, thresholds, temporal rules

Manual calibration \+ controlled scenarios\.

w\_c,w\_a,w\_t,w\_b

Confidence weights

Scenario validation/tuning\.

w\_I,w\_T,w\_D

Severity weights

Hazard\-specific validation\.

w\_E,w\_S,w\_T

Operational\-risk weights

Decision\-policy validation\.

θ\_assess, θ\_known

Assessment/known\-hazard thresholds

Adversarial scenario sweep\.

State thresholds

Enter/exit transitions

Noise/hysteresis testing\.

W, θ\_p

Persistence window/threshold

Controlled event timing\.

η\_normal, η\_slow

Baseline learning rates

Drift/contamination experiments\.

C\_cap/core limits

Missing\-core behavior

Hazard\-specific missingness tests\.

λ\_f

Freshness decay

Network latency/partition experiments\.

T\_n update rate

Long\-term node trust adaptation

Long\-term node simulations\.

ESP32 scheduling

Concurrency safety

Measured firmware benchmark\.

__Parameter rule  
__These values are not to be copied from a paper, internet example, or arbitrary guess and then treated as scientifically optimal\. The structure is locked; the numerical values are evidence\-driven configuration\.

# 22\. Intelligence Validation Plan

__Test__

__Pass condition__

Health hard gate

Definitively failed sensor contributes H\_i=0\.

Health/battery separation

Low battery does not automatically reduce H\_i when sensor remains operational\.

Signal\-quality degradation

Noise/saturation/missingness lowers Q\_i appropriately\.

Reliability weighting

Low R\_i reduces evidence influence\.

Baseline learning

Fresh node stays in initialization/learning behavior\.

Baseline freeze

Confirmed/critical event stops baseline adaptation\.

Recovery

Resolved event enters controlled relearning\.

Anomaly monotonicity

Increasing |z| does not decrease A\_i\.

Correlated evidence

Correlated group behavior does not create false independent agreement\.

Core evidence floor

Removing a required core sensor limits confirmation\.

Temporal persistence

Transient spike does not behave like sustained evidence under fixed policy\.

Hysteresis

Small oscillations around threshold do not flap states\.

Fast escalation

Strong rapidly increasing event can escalate without arbitrary long delay\.

UNKNOWN

Strong anomaly with weak hazard mapping produces UNKNOWN/INVESTIGATE\.

Multi\-hazard independence

Fire/Flood can hold different simultaneous states\.

Node vs regional

One node cannot silently overwrite regional state, and Master cannot erase local state\.

Simulation blindness

Removing private ground truth from engine inputs does not break inference\.

Golden vectors

C/C\+\+ and Python shared calculations agree within tolerance\.

Offline edge

Local decision continues without Master/cloud\.

## 22\.1 Real fire validation

Fire must be evaluated through repeated controlled real\-hardware trials\. The final evidence set should report actual outcomes \(including false positives/false negatives where applicable\) rather than inventing an accuracy target\.

## 22\.2 Flood validation

Where real controlled flood data are insufficient, synthetic scenarios can validate software logic and state transitions\. Such tests are not equivalent to field\-validation of flood prediction accuracy\.

# 23\. Implementation Rules for the Coding Agent

## 23\.1 Required implementation pattern

telemetry  
  ↓  
ObservationFrame  
  ↓  
DiagnosticResult  
  ↓  
BaselineState  
  ↓  
FeatureVector  
  ↓  
AnomalyResult  
  ↓  
HazardAssessment\[\]  
  ↓  
DecisionState  
  ↓  
IntelligencePacket

## 23\.2 Recommended module boundaries

__Module__

__Responsibility__

diagnostics

H\_i, Q\_i, validation flags, hard\-failure logic\.

baseline

B\_i, baseline storage/update/freeze/recovery\.

features

Trend, acceleration, persistence and hazard features\.

anomaly

z\-score/MAD, A\_i, A\_node, A\_h\.

hazards

Hazard\-specific E\_h configurations and reasoning\.

confidence

Coverage, core floor, grouped agreement, temporal/baseline confidence\.

severity

Hazard\-specific intensity normalization and common severity structure\.

risk

Operational risk index\.

state\_machine

Hysteresis, persistence, escalation, resolution\.

fusion

Master regional aggregation, freshness/node trust\.

packet

Compact serialization and provenance\.

## 23\.3 Prohibited implementation shortcuts

- Do not calculate hazard state directly from one raw sensor threshold without going through the configured evidence pathway\.
- Do not turn missing values into zero\.
- Do not let the baseline learn confirmed/critical hazards\.
- Do not calculate confidence from a single sensor reliability scalar\.
- Do not count correlated sensors as independent votes\.
- Do not multiply confidence into operational risk just to obtain a smaller number\.
- Do not introduce an opaque ML classifier in the fire pathway\.
- Do not pass simulation ground truth into hazard reasoning\.
- Do not put heavy geospatial fire\-spread computation on the ESP32\.

# 24\. Worked Conceptual Examples

## 24\.1 Healthy sensor, unusual observation

A temperature sensor may have H\_i=0\.98 and Q\_i=0\.95 while its measurement is strongly above baseline\. The result can be high A\_i and high R\_i\. This means 'the sensor is trustworthy and the value is unusual,' not 'a fire exists\.' Hazard reasoning must still evaluate cross\-sensor evidence\.

## 24\.2 Dead sensor during otherwise strong event

Suppose PM and temperature are strongly abnormal but the gas sensor hard\-fails\. Gas receives H\_i=0 and contributes no usable evidence\. The fire evidence may remain meaningful, but core\-evidence coverage and confidence follow the fire configuration\.

## 24\.3 Strong severity, incomplete confidence

A condition may be severe and rapidly escalating while confidence remains moderate because a key sensor is unavailable\. The state engine can produce urgent verification/action behavior without falsely calling the evidence fully confirmed\.

## 24\.4 Unknown anomaly

Suppose several sensors behave abnormally but no configured hazard receives enough coherent evidence\. A\_node may be high while max\_h\(E\_h\) remains below the known\-hazard threshold\. The system returns UNKNOWN/INVESTIGATE rather than forcing fire/flood/pollution\.

## 24\.5 Multi\-hazard

Rainfall and water level indicate flood evidence while PM also spikes\. Flood can be CONFIRMED and pollution WATCH simultaneously\. Neither state overwrites the other, and the system retains separate hazard risk surfaces downstream\.

# 25\. Final Implementation Summary

__Layer__

__Locked implementation concept__

Diagnostics

H\_i weighted health \+ hard gate; Q\_i integrity × stability; battery separate\.

Reliability

R\_i = H\_i × Q\_i × K\_i\.

Baseline

Readiness state \+ robust median/MAD where suitable \+ controlled adaptation\.

Temporal

Trend, acceleration, persistence\.

Anomaly

Bounded A\_i plus reliability\-weighted local/hazard aggregate\.

Hazard evidence

Configuration\-driven deterministic reasoning\.

Confidence

Coverage \+ grouped agreement \+ temporal persistence \+ baseline readiness\.

Severity

Hazard\-specific intensity \+ temporal \+ duration/context\.

Operational risk

Linear operational index; not probability\.

State

NORMAL/WATCH/SUSPECTED/CONFIRMED/CRITICAL/RESOLVED\.

Information

GOOD/DEGRADED/UNKNOWN independent of state\.

Multi\-hazard

Independent hazard evaluations and states\.

Regional fusion

Freshness \+ node trust \+ confidence/context\.

Edge

Local autonomous intelligence\.

Master

Regional fusion/enrichment/geospatial/operations\.

ML

Optional only when real data demonstrates measurable benefit; not mandatory for fire V1\.

__Final rule  
__The intelligence layer is intentionally sophisticated in its discipline rather than in the number of mathematical layers\. Every quantity exists for a distinct reason, every uncertainty state remains visible, and every tunable value is separated from the architectural structure\. Implementation should now focus on coding, calibration, benchmark and validation rather than adding new intelligence layers\.

# Appendix A — Source Basis

This document was rebuilt from the uploaded NexAlert Environmental Intelligence V2\.3 baseline and reconciled with the final architecture decisions established after adversarial review\. The V2\.3 source explicitly defines the edge\-first pipeline, H\_i/Q\_i/R\_i diagnostic quantities, baseline/MAD behavior, anomaly aggregation, configuration\-driven hazard reasoning, evidence confidence, severity, operational risk, state engine, distributed fusion, fire/flood strategies, health reporting, edge boundary, demo flows and parameter\-validation list\. fileciteturn16file0 fileciteturn18file8

The final review corrections incorporated here include correlation\-aware evidence grouping, a core\-evidence floor, explicit UNKNOWN behavior, preservation of local state under Master disagreement, and the prohibition on introducing a mandatory fire classifier\. fileciteturn18file3 fileciteturn18file5

