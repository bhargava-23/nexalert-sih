__NEXALERT__

__HARDWARE, EDGE NODE, SENSOR & TELEMETRY SPECIFICATION__

Final V1 Engineering Baseline — Field Hardware, Embedded Runtime, Diagnostics & Data Contract

__Document role  
__This is the definitive V1 hardware/edge specification for the field node\. It defines the physical sensing boundary, ESP32\-S3 firmware responsibilities, sensor interfaces, timing, diagnostics, telemetry, authentication, buffering, local emergency service, embedded intelligence boundary, and the exact contract presented to the Master\.

__Field__

__Value__

Product

NexAlert

Problem

SIH26178 — resilient AI\-powered environmental monitoring and early warning

Document

06 — Hardware, Edge Node, Sensor & Telemetry Specification

Status

FINAL V1 ENGINEERING BASELINE

Primary field compute

ESP32\-S3\-class MCU

Primary field firmware

ESP\-IDF \+ C/C\+\+

Master

Raspberry Pi\-class Linux compute

Primary purpose

Measure → validate → diagnose → reason locally → authenticate → communicate → buffer

Heavy geospatial compute

NOT on ESP32

__Historical architecture warning  
__Earlier NexAlert project drafts used a dual\-MCU STM32 \+ ESP32 slave\-node architecture, Meshtastic forks and a different responsibility split\. That is NOT the current V1 architecture\. This document follows the frozen architecture: ESP32\-S3\-class field node \+ Raspberry Pi Master, with local intelligence on the node and heavy geospatial/operational computation on the Master/cloud\. The older STM32\-centric proposal is reference history only\. fileciteturn20file13 fileciteturn20file14

# Document Control & Authority

__Status__

__Meaning__

LOCKED

Must be preserved unless hardware validation reveals a genuine incompatibility\.

PARAMETER

To be selected/measured/calibrated\.

CANDIDATE

A proposed hardware component/implementation that is not yet final\.

DEFERRED

Architecturally supported but not required for V1\.

ROADMAP

Future enhancement\.

## Authority order

__Topic__

__Authority__

Overall responsibility split

01 — Master Architecture

Technical requirements

02 — TRD

Runtime/compute allocation

03 — Technology Stack

Intelligence math

04 — Mathematical Intelligence

Fire/geospatial calculations

05 — Fire/Geospatial

This document

06 — Hardware/Edge

__Component\-selection status  
__The architecture requires final selection of specific gas/PM and other sensor components\. Existing NexAlert material mentions a Bosch BME688 for temperature/humidity/pressure/IAQ, but that component choice is not treated as a universal locked sensor assignment here\. Final hardware selection must satisfy the signal contract, calibration requirements, power budget and availability\. The previous slide deck listed BME688, ESP32\-S3, SX1262/SX1276, LiFePO4 and solar hardware as a prior stack, but several of those choices are now treated as candidates unless explicitly revalidated\. fileciteturn20file4

# 1\. Field Node Purpose

The NexAlert field node is a distributed environmental sensing and edge\-intelligence device\. It is deliberately not just a sensor relay\. It must be able to determine whether its own measurements are usable, whether they are unusual, whether the pattern provides hazard evidence, and whether the local hazard state warrants local action/notification—even when the Master, cloud or internet is unavailable\.

## 1\.1 Primary responsibilities

- Acquire environmental measurements\.
- Normalize/validate sensor readings at the earliest practical point\.
- Track sensor diagnostic state and availability\.
- Monitor battery/power state separately from sensor health\.
- Maintain a heartbeat\.
- Compute local sensor health, signal quality and evidence reliability\.
- Maintain baseline readiness and controlled baseline updates\.
- Compute bounded anomaly measures\.
- Evaluate configured lightweight hazard reasoning locally\.
- Produce confidence, severity, operational\-risk and hazard\-state outputs\.
- Authenticate telemetry using a per\-node credential/HMAC\.
- Maintain sequence numbers and timestamps\.
- Buffer telemetry/events while communications are unavailable\.
- Provide the local NexAlert emergency network/service path assigned to the selected hardware design\.
- Recover cleanly after reset/reconnection\.

## 1\.2 Explicit non\-responsibilities

- Large\-scale fire\-spread raster simulation\.
- DEM preprocessing and slope/aspect raster generation\.
- Population/infrastructure intersection\.
- Route optimization\.
- Authority dispatch decisions\.
- Cloud\-only functionality\.
- A mandatory learned fire classifier\.
- Full operational GIS\.

# 2\. Hardware Platform

## 2\.1 MCU baseline

The V1 field node uses an ESP32\-S3\-class MCU as the embedded compute target\. Exact board/flash/PSRAM configuration must be recorded once the physical board is finalized\.

__Item__

__V1 requirement__

MCU family

ESP32\-S3\-class

Firmware environment

ESP\-IDF \+ C/C\+\+

Runtime

FreeRTOS through ESP\-IDF

Nonvolatile storage

On\-board flash and/or configured external storage as required for buffering/configuration\.

Connectivity

Wi\-Fi/local IP plus the selected field\-network transport where applicable\.

Power

Solar/battery subsystem according to hardware team's final design\.

Time source

RTC/NTP/GPS or other configured time source; domain semantics must survive intermittent connectivity\.

## 2\.2 Why ESP32\-S3

The architecture uses the ESP32\-S3 as the field compute target because the required local intelligence operations are primarily bounded arithmetic, rolling statistics, comparisons, small buffers, and configuration\-driven reasoning\. The principal engineering challenge is concurrent execution of sensing, communications, local service, buffering, authentication and intelligence, which must be benchmarked rather than assumed safe\.

## 2\.3 Board selection record

__Field__

__Must be recorded before hardware freeze__

Exact board/module

Manufacturer \+ module/board identifier\.

Flash

Capacity and allocation\.

PSRAM

Present/absent and capacity\.

GPIO map

Per sensor/peripheral\.

ADC/DAC

Channels/resolution used\.

I2C

Bus address map\.

SPI

Bus/device map\.

UART

Device/console map\.

Wi\-Fi role

AP/client/concurrent mode configuration\.

Power input

Voltage/current range\.

Enclosure

Weatherproofing/rating and thermal assumptions\.

# 3\. Sensor Architecture

## 3\.1 Canonical sensor classes

__Signal__

__Canonical unit__

__Primary hazard relevance__

__Status__

Temperature

°C

Fire, extreme heat, contextual pollution

REQUIRED class

Relative humidity

%RH

Fire/context, heat

REQUIRED class

Pressure

hPa

Context/weather; optional

OPTIONAL

PM2\.5

µg/m³

Fire/smoke, pollution

RECOMMENDED; exact sensor pending

PM10

µg/m³

Fire/smoke, pollution

RECOMMENDED

Gas

ppm only if calibrated; otherwise sensor\-native engineering unit

Fire/pollution

REQUIRED capability; exact sensor pending

Water level

m \(cm acceptable if schema is normalized\)

Flood

REQUIRED for physical/synthetic flood path

Rainfall rate

mm/h

Flood

REQUIRED capability for flood path where hardware supports it

Cumulative rainfall

mm

Flood

RECOMMENDED

Soil moisture

%VWC or calibrated native unit

Flood/landslide

RECOMMENDED

Vibration

m/s² or calibrated native unit

Landslide/structural context

RECOMMENDED

## 3\.2 Fire minimum

A fire\-capable node must have a combination of temperature, smoke/PM and gas capabilities subject to final sensor calibration\. Humidity is supporting evidence\. A single sensor is never the entire fire decision\.

## 3\.3 Flood minimum

A flood\-capable hardware configuration requires a water\-level signal and rainfall/context input; soil moisture is useful supporting evidence\. The exact hardware arrangement may use a dedicated node configuration or the same multi\-sensor node\.

## 3\.4 Gas sensor rule

__Gas sensor must not be a name\-only decision  
__A specific gas sensor must be selected based on the actual gas species or response quantity, calibration process, cross\-sensitivity, response time, operating voltage, temperature dependence, and available driver/library support\. If it cannot honestly be expressed in calibrated ppm, the telemetry must use the sensor's declared native engineering unit rather than a fabricated ppm conversion\.

# 4\. Electrical & Software Sensor Interfaces

## 4\.1 Interface conventions

__Interface__

__Expected use__

I²C

Temperature/humidity/pressure/air\-quality class sensors where supported\.

SPI

High\-rate sensors, radios, displays or storage where applicable\.

UART

Smart sensors, GNSS or external co\-processors where required\.

ADC

Analog gas/water/vibration/level inputs where final sensor requires it; must include calibration\.

GPIO/interrupt

Rain gauge pulses, threshold interrupts, sensor\-ready signals where applicable\.

## 4\.2 Per\-sensor configuration record

sensor\_id  
node\_id  
sensor\_type  
manufacturer  
model  
interface  
bus/channel/address  
unit  
sampling\_interval  
calibration\_status  
calibration\_version  
valid\_range  
warmup\_time  
saturation\_range  
diagnostic\_rules  
driver\_version  
enabled  
hazard\_roles\[\]  


## 4\.3 Electrical assumptions

The final hardware document must record actual logic levels, supply voltage, pull\-ups, ADC reference behavior, sensor warm\-up, current draw and interface timing for every selected part\. The software specification must never invent a sensor value that the electrical design cannot physically measure\.

# 5\. Sampling, Timing & Time Semantics

## 5\.1 Observation cadence

Each sensor class gets a configured sampling interval based on its dynamics, power cost, driver limitations and hazard role\. There is no requirement that every sensor sample at the same rate\.

__Signal class__

__Typical V1 cadence direction__

__Reason__

Fast smoke/PM changes

Seconds to tens of seconds

Fire/pollution events can change quickly\.

Temperature/humidity

Seconds to minutes

Environmental dynamics slower than PM\.

Water level

Seconds to minutes

Flood rate\-of\-rise requires temporal resolution\.

Rainfall

Event/pulse\-based or short interval

Cumulative and rate calculations\.

Soil moisture

Minutes

Slow\-changing\.

Vibration

Windowed high\-rate acquisition then features

Frequency content may be more informative than raw samples\.

These are cadence classes, not locked numerical sampling frequencies\. Exact intervals are parameters validated against real hardware/power budgets\.

## 5\.2 Timestamps

Each observation must retain a measurement timestamp\. Node\-generated timestamps should use a synchronized or monotonic time basis where possible\. The backend records a separate receive timestamp\.

## 5\.3 Sequence numbers

Every telemetry packet must carry a per\-node sequence number or equivalent monotonic identifier\. Sequence values support duplicate detection, missing\-packet diagnosis and store\-and\-forward reconciliation\.

# 6\. Diagnostics & Sensor Health

## 6\.1 Diagnostic signals

__Diagnostic__

__Examples__

Self\-test

Sensor internal self\-test/pass/fail\.

Availability

Present/absent/responding\.

Communication integrity

I²C/SPI/UART errors, retries/timeouts\.

Calibration

Valid/expired/invalid/calibration version\.

Stability

Short\-window noise/variance\.

Drift

Longer\-term deviation from expected behavior\.

Saturation

ADC/sensor max/min or declared saturation\.

Electrical

Impossible voltage/current/state when available\.

Warm\-up

Sensor still in startup/warm\-up\.

## 6\.2 Sensor health

__H\_i^soft = Σ\_j w\_ij D\_ij,   Σ\_j w\_ij = 1__

__H\_i = 0  if F\_i=1;  otherwise H\_i = H\_i^soft__

The weighted diagnostic score and hard\-failure gate are defined in Document 04\. The embedded firmware must expose the component diagnostics that justify the scalar\.

## 6\.3 Battery is separate

Battery percentage, solar activity and power mode are operational quantities\. They are not copied into H\_i\. Only an actual power\-induced sensor degradation may reduce sensor health/availability\.

## 6\.4 Hard failure examples

- Definitive self\-test failure\.
- Sensor physically disconnected\.
- Sustained bus communication failure\.
- Impossible electrical state\.
- Sensor\-specific fatal error\.

# 7\. Signal Quality & Reliability on the Node

## 7\.1 Signal quality

__Q\_i\(t\) = q\_integrity,i\(t\) × q\_stability,i\(t\)__

q\_integrity represents current data validity; q\_stability represents short\-window consistency/noise\. The embedded implementation must compute/approximate these using bounded, resource\-appropriate algorithms\.

## 7\.2 Evidence reliability

__R\_i\(t\) = H\_i\(t\) × Q\_i\(t\) × K\_i\(t\)__

K\_i captures current calibration/operating validity\. The node uses R\_i to weight hazard evidence\. It does not add R\_i again as a separate confidence factor\.

## 7\.3 Example

A healthy sensor with low current quality can legitimately have high H\_i but low Q\_i and therefore lower R\_i\. This distinction is useful during transient communication/noise problems\.

# 8\. Edge Baseline & Anomaly

## 8\.1 Baseline states

__State__

__Node behavior__

INITIALIZING

Collect initial observations\.

LEARNING

Adapt under controlled rate\.

READY

Normal anomaly interpretation available\.

FROZEN

No baseline learning during confirmed/critical hazard\.

RECOVERING

Controlled post\-event relearning\.

## 8\.2 Default robust baseline

__m\_i = median\(x\_i\)__

__MAD\_i = median\(|x\_i − m\_i|\)__

__s\_i = 1\.4826 × MAD\_i \+ ε__

__z\_i = \(x\_i − m\_i\) / s\_i__

## 8\.3 Anomaly

__A\_i\(t\) = 1 − exp\(−min\(|z\_i|, z\_cap\)/λ\)__

__A\_node\(t\) = \[Σ\_i R\_i A\_i\] / \[Σ\_i R\_i \+ ε\]__

__A\_h\(t\) = \[Σ\_i w\_ih R\_i A\_i\] / \[Σ\_i w\_ih R\_i \+ ε\]__

## 8\.4 Modality\-specific behavior

Water level and soil moisture may use trend\-relative methods; vibration may use frequency\-domain features\. The common pipeline stays unchanged\.

## 8\.5 Edge resource rule

Do not maintain unbounded time series on the ESP32\. Use ring buffers/windows sized to the exact feature/baseline configuration\. Raw history should be persisted upstream or in bounded chunks when required\.

# 9\. Local Hazard Reasoning Boundary

## 9\.1 Configuration\-driven reasoning

The node evaluates each configured hazard independently\. Fire reasoning is deterministic/manual\-calibration driven in V1\. Flood follows the same common framework with hazard\-specific evidence rules\.

ObservationFrame  
  ↓  
Diagnostics  
  ↓  
Baseline / features  
  ↓  
Anomaly  
  ↓  
Fire reasoning ──→ Fire assessment  
Flood reasoning ─→ Flood assessment  
Pollution ───────→ Pollution assessment  
Landslide ───────→ Landslide assessment  
Heat ────────────→ Heat assessment  
  ↓  
confidence / severity / risk / state  
  ↓  
Intelligence packet

## 9\.2 Local state

The node may produce a local hazard state that can drive local safety behavior\. The Master may build a separate regional state later\. The Master must not erase a valid local state merely because other nodes disagree\.

## 9\.3 Local response

A local node may trigger configured local alert behavior \(e\.g\., local emergency page state\) according to policy\. It must never autonomously dispatch external responders\.

# 10\. Local Emergency Network / Citizen Access

## 10\.1 Purpose

The field node/local gateway must be capable of exposing the NexAlert emergency experience through the local network path when configured for V1\. The exact web\-serving architecture depends on the final memory/flash budget and network topology\.

## 10\.2 Minimal local service

Node enters CRITICAL/local alert condition  
  ↓  
Local emergency service becomes available  
  ↓  
Distinctive NexAlert Wi\-Fi presence  
  ↓  
Citizen associates with network  
  ↓  
Local emergency page served  
  ↓  
Verified event rendered  


## 10\.3 Important limitation

The system cannot forcibly open a webpage on an arbitrary nearby phone that has never associated with the NexAlert network\. The citizen must participate through a supported local connection path\. This is a platform/operating\-system constraint, not a software bug\.

## 10\.4 Master independence

__Master\-death requirement  
__The local citizen path must not depend exclusively on the Raspberry Pi Master being alive\. The final hardware design must therefore reserve enough node/gateway capability to serve the emergency experience and retain a minimal emergency state when the Master is unavailable\.

# 11\. Canonical Telemetry Packet

## 11\.1 Packet requirements

\{  
  "schema\_version": "1\.0",  
  "telemetry\_id": "TEL\-01JXYZ",  
  "node\_id": "NODE\-001",  
  "sequence": 1842,  
  
  "measurement\_timestamp": "\.\.\.",  
  "device\_monotonic\_ms": 12345678,  
  
  "location": \{  
    "lat": 13\.1542,  
    "lon": 77\.5881  
  \},  
  
  "measurements": \{  
    "temperature\_c": 42\.4,  
    "humidity\_pct": 31\.2,  
    "pressure\_hpa": 1007\.4,  
    "pm25\_ug\_m3": 186\.0,  
    "pm10\_ug\_m3": 271\.0,  
    "gas\_value": 14\.2,  
    "gas\_unit": "ppm",  
    "water\_level\_m": null,  
    "rainfall\_mm\_h": 0\.0,  
    "rainfall\_cumulative\_mm": 2\.1,  
    "soil\_moisture\_pct\_vwc": null,  
    "vibration\_m\_s2": 0\.04  
  \},  
  
  "diagnostics": \{  
    "self\_test": "PASS",  
    "communication\_integrity": "GOOD",  
    "calibration\_status": "VALID",  
    "stability": "GOOD",  
    "availability": "GOOD",  
    "saturation": false  
  \},  
  
  "power": \{  
    "battery\_pct": 87,  
    "solar": "ACTIVE"  
  \},  
  
  "source": "HARDWARE",  
  "auth": \{  
    "algorithm": "HMAC\-SHA256",  
    "signature": "\.\.\."  
  \}  
\}

## 11\.2 Missing vs zero

__Value__

__Meaning__

null / explicit missing status

No usable measurement is available\.

0\.0

Sensor actually reports a measured zero\.

__Never  
__Do not serialize an unavailable water\-level/gas/rain/sensor field as 0\.0\. Missingness is semantically meaningful to the intelligence layer\.

# 12\. Measurement Semantics & Validation

__Field class__

__Validation examples__

Temperature

Finite numeric; sensor\-specific range; reject NaN/Inf\.

Humidity

0–100 %RH unless sensor declares another valid representation\.

Pressure

Finite; configurable plausible bounds\.

PM2\.5/PM10

Finite non\-negative; saturation explicitly flagged\.

Gas

Valid native/calibrated unit; no fake ppm conversion\.

Water level

Finite non\-negative or explicitly signed if sensor requires datum convention\.

Rainfall rate

Finite non\-negative mm/h\.

Cumulative rain

Non\-decreasing except explicit reset/re\-baseline event\.

Soil moisture

Declared unit/range\.

Vibration

Finite; preserve unit/calibration\.

Timestamp

Must pass sanity checks; future/too\-old values flagged\.

## 12\.1 Validation outcomes

__Outcome__

__Meaning__

ACCEPT

Usable observation\.

ACCEPT\_WITH\_FLAGS

Usable but has a non\-fatal diagnostic condition\.

REJECT

Malformed, unauthenticated or invalid observation\.

BUFFER

Valid packet that cannot currently be forwarded\.

## 12\.2 Validation order

receive  
→ authenticate  
→ parse  
→ schema validate  
→ timestamp/sequence validate  
→ range/unit validate  
→ attach diagnostics  
→ persist/buffer  
→ intelligence

# 13\. Node Authentication & Integrity

## 13\.1 V1 node\-to\-Master authentication

Each node receives a unique provisioned secret\. Telemetry packets are authenticated with HMAC\-SHA256 or the final approved HMAC construction\. The Master verifies the packet before accepting it into canonical ingestion\.

node secret  
   \+  
canonical serialized packet  
   ↓  
HMAC\-SHA256  
   ↓  
signature  
   ↓  
Master verification  


## 13\.2 Replay protection

HMAC alone does not prevent replay\. Use telemetry\_id \+ sequence \+ measurement timestamp \(and/or explicit nonce where required\) so duplicate/stale packets can be rejected\.

## 13\.3 Key storage

- Do not hard\-code production secrets in public source\.
- Store per\-node secret in protected nonvolatile storage appropriate to the board and threat model\.
- Provision a unique credential per node\.
- Support credential rotation/revocation at the backend level where practical\.

## 13\.4 Invalid packet

HMAC invalid  
→ reject  
→ security/audit event  
→ no intelligence processing  
→ no incident side effect

# 14\. Local Buffering & Store\-and\-Forward

## 14\.1 Why buffering exists

Disaster networks can be intermittent\. A node should not lose every measurement simply because its communication path is temporarily down\.

## 14\.2 Buffer record

buffer\_id  
telemetry\_id  
node\_id  
sequence  
measurement\_timestamp  
payload  
auth\_metadata  
stored\_at  
retry\_count  
priority  
status  


## 14\.3 Buffer policy

__Rule__

__V1 behavior__

Ordering

Prefer per\-node sequence order\.

Deduplication

Same telemetry\_id/sequence must not be ingested twice\.

Retry

Bounded retry with backoff\.

Full buffer

Apply explicit ring\-buffer/retention policy; never unlimited memory growth\.

Critical event

Higher transmission priority than routine telemetry where transport supports priority\.

Recovery

Sync buffered data then resume normal flow\.

## 14\.4 Synchronization

link restored  
→ authenticate  
→ send oldest eligible buffered records  
→ receive ACK  
→ mark synchronized  
→ continue  
→ deduplicate at receiver as a second defense

# 15\. Heartbeat & Node Health Reporting

## 15\.1 Heartbeat

The node must emit a lightweight heartbeat on the configured cadence\. Existing NexAlert design uses a heartbeat mechanism; the intelligence layer extends this into component\-level health reporting while fast diagnostics remain internal\. The exact cadence remains a parameter\.

__Heartbeat field__

__Purpose__

node\_id

Device identity\.

sequence/heartbeat\_seq

Ordering\.

uptime

Node runtime health\.

firmware\_version

Compatibility\.

last\_sensor\_sample\_age

Sampling health\.

battery\_pct

Power state\.

solar\_state

Power state\.

communications

Link state/quality summary\.

storage\_available

Buffer capacity\.

sensor\_health\_summary

Aggregate plus per\-sensor diagnostics reference\.

current\_local\_state

Local hazard state summary\.

## 15\.2 Approximate five\-minute detailed health report

A component\-level health report may be transmitted approximately every five minutes, while faster diagnostics continue internally\. The final interval is configurable and must be benchmarked for bandwidth/power impact\.

## 15\.3 Staleness

__Age = t\_now − t\_last\_heartbeat__

A heartbeat becomes stale after the configured timeout\. Staleness changes node/network state; it does not automatically mean every sensor is physically dead\.

# 16\. Firmware Architecture

firmware/  
  main/  
  components/  
    sensors/  
    diagnostics/  
    intelligence/  
    telemetry/  
    security/  
    network/  
    storage/  
    local\_gateway/  
    system/  
  test/  


## 16\.1 Logical task set

__Task/module__

__Purpose__

Sensor acquisition

Sample sensors on schedule\.

Diagnostics

Self\-test, quality, availability, calibration\.

Intelligence

Baseline, anomaly, hazard reasoning, state\.

Telemetry

Serialize, sequence, metadata\.

Security

HMAC, key access, replay protection\.

Network

Transmit/reconnect/local network\.

Storage

Ring buffer and persistence\.

Local gateway

Emergency web/portal service where enabled\.

System

Watchdog, time sync, configuration, logging\.

## 16\.2 Concurrency principle

Do not create one FreeRTOS task per sensor by default\. Start with a small bounded task architecture and use queues/event groups/timers\. Increase concurrency only after measurement shows a bottleneck\.

## 16\.3 Watchdog/restart

- Enable a watchdog appropriate to the final task model\.
- A blocked sensor driver must not indefinitely block telemetry/network tasks\.
- A network reconnect loop must have bounded delays\.
- After reboot, buffered valid data and configuration must be recovered safely\.

# 17\. Edge Intelligence Implementation

## 17\.1 What may run locally

__Function__

__Embedded status__

Sensor health H\_i

MUST

Signal quality Q\_i

MUST

Reliability R\_i

MUST

Baseline readiness

MUST

Anomaly A\_i

MUST for configured sensors

Hazard evidence

MUST for configured lightweight hazards

Confidence

MUST

Severity

MUST

Operational risk

MUST

Hazard state

MUST

Fire spread

MUST NOT run on ESP32

Population exposure

MUST NOT run on ESP32

Routing

MUST NOT run on ESP32

## 17\.2 Numerical constraints

Embedded mathematics must use bounded numeric ranges, preallocated buffers and validated floating\-point or fixed\-point representations appropriate to the final firmware\. Do not use dynamic allocation inside high\-frequency sensor loops unless measured safe\.

## 17\.3 Golden vector

Every shared formula that exists both in Python and on the ESP32 must have reference vectors\. The Python implementation is the reference for numerical intent; the C/C\+\+ result must stay within declared tolerance\.

# 18\. Field Communication Interface

## 18\.1 Transport abstraction

The node software must isolate application telemetry from physical transport\. This prevents replacing Wi\-Fi with a long\-range radio from changing the intelligence schema\.

Application telemetry  
      ↓  
Transport\-independent envelope  
      ↓  
HMAC/authentication  
      ↓  
Transport adapter  
  ├─ Wi\-Fi/IP  
  ├─ optional long\-range/radio adapter  
  └─ future adapter  


## 18\.2 V1 practical transport

The current prototype may use Wi\-Fi/IP for the simplest real\-hardware path\. Long\-range radio may be added through an adapter where hardware availability and time justify it\. A full LoRaWAN/mesh deployment is not required to satisfy the V1 software architecture\.

## 18\.3 Legacy note

Earlier project materials described SX1262/SX1276 radios, Meshtastic forks and an STM32 routing controller\. Those belong to an earlier hardware architecture and must not be copied into the V1 firmware simply because they appear in legacy presentations\. fileciteturn20file4

# 19\. Calibration & Sensor Characterization

## 19\.1 Calibration layers

__Layer__

__Examples__

Factory calibration

Sensor manufacturer baseline\.

Node\-level calibration

Known reference comparison before deployment\.

Environmental compensation

Temperature/humidity dependence if documented\.

Operational validity

Calibration freshness/quality status\.

Software conversion

Unit/offset/scaling conversion with version\.

## 19\.2 Calibration record

calibration\_id  
sensor\_id  
performed\_at  
performed\_by  
reference\_method  
reference\_values  
raw\_values  
calibration\_parameters  
uncertainty/notes  
valid\_from  
valid\_until \(if applicable\)  
firmware/driver\_version  


## 19\.3 Fire trial

Controlled fire trials should measure sensor response repeatability, time\-to\-detection, cross\-sensor agreement, baseline contamination risk, recovery behavior and false\-alarm behavior\. Do not turn a single trial into a claimed accuracy number\.

# 20\. Hardware Verification & Benchmarks

__Test__

__Required evidence__

Sensor read test

Every selected sensor produces expected valid values\.

Sensor disconnect

Firmware detects unavailable sensor\.

Sensor saturation

Saturation flag/quality behavior is correct\.

Noise test

Quality decreases under injected/observed noise\.

Warm\-up

No false hazard during declared warm\-up\.

Calibration invalid

Reliability/availability changes correctly\.

Heartbeat

Periodic report visible at Master\.

Duplicate packet

Receiver deduplicates\.

HMAC invalid

Packet rejected\.

Offline buffer

Data retained while link is down\.

Reconnect

Buffered packets sync without duplication\.

Wi\-Fi AP stress

Local portal remains responsive during sensing/telemetry\.

Concurrent intelligence

Local inference does not starve sensor/network tasks\.

Master failure

Local citizen emergency page remains available\.

## 20\.1 Mandatory ESP32 concurrency benchmark

__Metric__

__Measure under combined workload__

Sensing latency

Time from scheduled acquisition to usable sample\.

Sampling jitter

Worst\-case deviation from intended sample time\.

Inference latency

Time for local intelligence cycle\.

Wi\-Fi response

Request/connection responsiveness\.

Telemetry latency

Packet creation/HMAC/send time\.

Packet loss

Loss during representative load\.

Free heap

Minimum free heap/high\-water behavior\.

CPU usage

Per\-task/overall utilization\.

Queue depth

Peak queue occupancy\.

Storage usage

Buffer growth during outage\.

Power

Relative energy draw where instrumentation permits\.

__Benchmark gate  
__The firmware architecture is not considered validated merely because it compiles\. The combined workload—sensor acquisition \+ Wi\-Fi/local service \+ telemetry \+ HMAC \+ buffering \+ local intelligence—must be measured on the actual ESP32\-S3 hardware\.

# 21\. Power & Thermal Requirements

## 21\.1 Power domains

__Domain__

__Requirement__

MCU

Power budget measured in active/idle/network states\.

Sensors

Measure continuous vs duty\-cycled draw\.

Radio/network

Measure transmit/connect duty\.

Display/local portal

Treat as a separate power budget if present\.

Solar

Record charge behavior and operating assumptions\.

Battery

Record chemistry, capacity, BMS/protection\.

## 21\.2 Low\-power behavior

Low\-power operation may reduce sampling cadence or disable nonessential functions when configured, but must not silently disable critical safety sensing without updating node health/information condition\.

## 21\.3 Thermal

Outdoor enclosure design must ensure sensor readings are not materially biased by MCU/PMIC heating\. The final physical design must document ventilation/thermal\-isolation strategy where relevant\.

# 22\. Field Deployment & Ruggedization

__Aspect__

__V1 requirement__

Outdoor exposure

Enclosure and connectors suitable for intended demo conditions\.

Water ingress

Physical design prevents direct exposure of electronics to rain/spray\.

Dust

Protect sensing electronics while preserving measurement validity\.

Mounting

Stable orientation for sensors that require it\.

Cable management

Strain relief and secure connectors\.

Serviceability

Sensors replaceable without destroying the whole node\.

Labeling

Node ID and hazard\-facing status physically identifiable\.

Recovery

Power\-cycle and firmware recovery procedure documented\.

## 22\.1 Sensor placement

Placement affects measurements\. Temperature/PM/gas sensors must not be placed where the node's own heat, enclosure, solar panel or battery exhaust produces a systematic false signal\. Water\-level and rain sensors require physically appropriate installation relative to the environment\.

## 22\.2 Fire safety

Controlled fire demonstrations must use a controlled environment, safe distance, suitable supervision and non\-hazardous test procedures\. The hardware specification does not authorize unsafe open\-flame deployment\.

# 23\. Schema Versioning & Backward Compatibility

## 23\.1 Schema version

Every telemetry packet carries schema\_version\. A Master should reject incompatible schema versions explicitly rather than guessing field meaning\.

## 23\.2 Firmware/backend compatibility

__Change__

__Behavior__

Added optional field

Older receiver may ignore if forward\-compatible\.

Changed unit

Requires schema/version or explicit conversion contract; never silently reinterpret\.

Renamed field

Versioned contract\.

Changed semantics

Must increment schema version and update all consumers\.

Firmware driver update

Telemetry carries driver/calibration version where relevant\.

# 24\. Edge Error & Recovery State Machine

BOOT  
 ↓  
SELF\_TEST  
 ├─ FAIL → DEGRADED / SENSOR\_UNAVAILABLE  
 └─ PASS  
      ↓  
SYNC\_TIME \(if possible\)  
      ↓  
LOAD\_CONFIG  
      ↓  
INITIALIZING  
      ↓  
LEARNING  
      ↓  
READY  
      ↓  
RUNNING  
 ├─ communication loss → BUFFERING  
 │                         ↓ reconnect  
 │                      SYNCING  
 │                         ↓  
 │                      RUNNING  
 ├─ sensor fault → DEGRADED  
 │                   ↓ recovery/self\-test  
 │                 RUNNING  
 └─ fatal system condition → SAFE\_RESTART  
                              ↓  
                              BOOT

## 24\.1 Rule

A sensor fault must not crash the entire node\. A network outage must not stop sensing\. A temporary storage error must not create undefined memory behavior\.

# 25\. Intelligence Packet vs Raw Telemetry

## 25\.1 Why both exist

Raw telemetry is required for audit, replay, debugging and downstream validation\. The intelligence packet is a compact decision\-oriented summary that can travel through constrained links\.

__Packet__

__Use__

Raw telemetry

Measurements, diagnostics, provenance, replay\.

Intelligence packet

Current local hazard states, confidence/severity/risk, information condition and key explanatory metadata\.

Heartbeat

Node/system liveness and health summary\.

SOS/local event

Urgent event requiring higher transmission priority where transport supports it\.

## 25\.2 Intelligence packet conceptual shape

\{  
  "node\_id": "NODE\-001",  
  "sequence": 1842,  
  "timestamp": "\.\.\.",  
  "information\_condition": "GOOD",  
  "hazards": \{  
    "fire": \{  
      "evidence": "\.\.\.",  
      "confidence": "\.\.\.",  
      "severity": "\.\.\.",  
      "operational\_risk": "\.\.\.",  
      "state": "CONFIRMED"  
    \}  
  \},  
  "diagnostics\_summary": \{\},  
  "auth": \{\}  
\}

Exact schema is maintained jointly with the backend specification\. The important invariant is that the compact packet is derived from the same intelligence implementation that can be inspected through the raw evidence path\.

# 26\. Security & Privacy on the Node

__Concern__

__V1 requirement__

Telemetry integrity

HMAC\.

Replay

Sequence \+ timestamp \+ event identity/nonce\.

Secret storage

Protected device storage; no public source secret\.

Firmware integrity

Use signed/reproducible firmware workflow where practical\.

Debug access

Disable/remove production debug paths not required for demo\.

Citizen data

Minimize local retention\.

Logs

No secrets; bounded storage\.

## 26\.1 Privacy rule

The field node should not collect citizen identity/location data unless the local architecture explicitly requires it for the emergency portal\. Hazard telemetry is the primary node responsibility; citizen identity is handled at the citizen/backend layer\.

# 27\. Hardware Implementation Order

1. Freeze the exact ESP32\-S3 board/module and record flash/PSRAM/pin budget\.
2. Freeze the sensor set and electrical interfaces\.
3. Build a sensor\-driver bring\-up firmware\.
4. Implement diagnostics and per\-sensor health reporting\.
5. Implement heartbeat/time/sequence\.
6. Implement canonical telemetry serialization\.
7. Implement HMAC authentication\.
8. Implement buffering and reconnect\.
9. Implement local intelligence subset\.
10. Implement local emergency service\.
11. Run the combined concurrency benchmark\.
12. Run calibration/controlled fire trials\.
13. Connect to the Raspberry Pi Master\.
14. Run golden\-vector parity tests\.
15. Only then add field\-enclosure/power polish and broader node replication\.

# 28\. Hardware V1 Freeze Checklist

__☐ 01  __Exact ESP32\-S3 board selected and documented\.

__☐ 02  __GPIO/I2C/SPI/UART/ADC map frozen\.

__☐ 03  __Exact sensor part numbers selected and documented\.

__☐ 04  __Gas sensor calibration method documented\.

__☐ 05  __PM/smoke sensor selected and characterized\.

__☐ 06  __Water/rain/soil/vibration sensor capabilities documented if included\.

__☐ 07  __Sampling intervals configured\.

__☐ 08  __Sensor warm\-up and saturation behavior defined\.

__☐ 09  __Diagnostic fields implemented\.

__☐ 10  __H\_i/Q\_i/R\_i inputs available on node\.

__☐ 11  __Baseline/anomaly logic implemented in C/C\+\+\.

__☐ 12  __Python/C\+\+ golden vectors pass\.

__☐ 13  __Heartbeat implemented\.

__☐ 14  __Sequence \+ measurement timestamp implemented\.

__☐ 15  __Receive timestamp assigned at receiver\.

__☐ 16  __HMAC implemented and invalid packet rejected\.

__☐ 17  __Replay/dedup logic implemented\.

__☐ 18  __Offline buffer and sync implemented\.

__☐ 19  __Local emergency page survives Master failure\.

__☐ 20  __ESP32 concurrency benchmark completed\.

__☐ 21  __Power/thermal measurements collected\.

__☐ 22  __Hardware demo test completed safely\.

# 29\. Hardware / Edge Invariants

__🔒 01  __The field node is ESP32\-S3\-class with ESP\-IDF \+ C/C\+\+ in V1\.

__🔒 02  __Historical STM32 dual\-MCU architecture is not part of the current V1 unless explicitly re\-approved\.

__🔒 03  __Battery state is not sensor health\.

__🔒 04  __Missing measurement is not zero\.

__🔒 05  __Every telemetry packet has node identity, sequence, measurement timestamp and schema version\.

__🔒 06  __Receive timestamp is assigned at the receiving system and is distinct from measurement time\.

__🔒 07  __Node telemetry is authenticated before canonical ingestion\.

__🔒 08  __Invalid HMAC means reject and audit\.

__🔒 09  __Duplicate packets do not create duplicate downstream effects\.

__🔒 10  __Offline buffer is bounded; memory must never grow without limit\.

__🔒 11  __Sensing continues when communication is unavailable\.

__🔒 12  __A sensor fault does not crash the node\.

__🔒 13  __Local intelligence does not require the Master/cloud/internet\.

__🔒 14  __Fire spread does not run on the ESP32\.

__🔒 15  __Population/infrastructure exposure does not run on the ESP32\.

__🔒 16  __Python is the reference implementation for shared intelligence mathematics; C/C\+\+ is the embedded implementation\.

__🔒 17  __Shared Python/C\+\+ functions are tested with golden vectors\.

__🔒 18  __Fire V1 reasoning is deterministic/configuration\-driven; no mandatory fire classifier\.

__🔒 19  __Local hazard state and regional Master state are distinct\.

__🔒 20  __Master disagreement must not erase valid local hazard behavior\.

__🔒 21  __The node may provide local emergency citizen access through a supported local network path\.

__🔒 22  __Master failure and internet failure are distinct conditions\.

__🔒 23  __Every configured sensor has explicit units, validity rules and diagnostics\.

__🔒 24  __Gas is only represented in ppm when a defensible calibration/unit conversion exists\.

__🔒 25  __Exact numeric sampling/power/threshold parameters remain measured/configured rather than guessed\.

# 30\. Source & Reconciliation Notes

The V2\.3 intelligence baseline defines the edge\-first philosophy, local health/quality/reliability/baseline/anomaly/hazard reasoning boundary, Raspberry Pi regional responsibilities and the ESP32 implementation constraint\. fileciteturn20file2

The older V2\.2 document and legacy project proposal contain useful historical details such as heartbeat/health reporting, embedded workload considerations and prior hardware responsibilities, but the current architecture supersedes their STM32\-centric and earlier implementation choices\. fileciteturn20file1 fileciteturn20file13

The legacy deck previously listed BME688, SX1262/SX1276, Meshtastic, SQLite/WAL and STM32\+ESP32\. Those values are intentionally not copied into the current V1 lock without revalidation; the current technology/compute architecture uses ESP32\-S3 \+ C/C\+\+ at the field node and Raspberry Pi \+ Python/PostGIS/backend services at the Master\. fileciteturn20file4

