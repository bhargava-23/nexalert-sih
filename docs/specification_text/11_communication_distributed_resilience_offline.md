__NEXALERT__

__Communication, Distributed Resilience & Offline Operation__

__FINAL IMPLEMENTATION SPECIFICATION  •  V1 / SIH 2026__

__Core principle  __NexAlert must continue to communicate the truth it already knows when upstream infrastructure is unavailable\. A network partition is a degraded information condition, not permission to fabricate certainty\.

__Document ID:__

NEX\-11\-COMM\-RES

__Status:__

FINAL / Implementation\-ready

__Authority:__

Master System Architecture \+ Technical Requirements \+ Mathematical Intelligence \+ Hardware \+ Incident Operations

__Supersedes:__

Any legacy communication design that assumes STM32\+ESP32 split, mandatory Meshtastic, or Master/cloud availability

# DOCUMENT MAP

__Section__

__Scope__

1\. Purpose & invariants

What resilience means and what must never change

2\. Communication architecture

Node, Master, local and cloud paths

3\. Protocol and transport strategy

Wi\-Fi, LoRaWAN/NB\-IoT, IP services and selection rules

4\. Message classes

Telemetry, heartbeat, event, command, citizen and audit traffic

5\. Integrity, ordering and replay protection

HMAC, sequence, timestamps, deduplication

6\. Store\-and\-forward

Offline queues, prioritization, retry and persistence

7\. Master failure vs internet failure

Independent degraded modes and recovery

8\. Local emergency operation

Node\-hosted emergency UI and captive portal

9\. Distributed fusion and authority

What happens during partition and disagreement

10\. Citizen communications

Online notification, offline access, SOS and acknowledgements

11\. Failure modes & operational states

Connectivity, power, clock and node isolation cases

12\. Resilience testing

Fault injection, soak, recovery and acceptance tests

13\. Configuration & implementation

Parameters, feature flags and code boundaries

14\. Acceptance criteria

Definition of done for the communication layer

15\. Locked invariants

Non\-negotiable implementation constraints

# 1\. Purpose & Design Invariants

This document specifies how NexAlert moves telemetry, health state, hazard evidence, alerts, acknowledgements and citizen safety information across a distributed environment where links may be slow, intermittent, partitioned or completely unavailable\. The communication layer is part of the safety architecture: it must preserve freshness, provenance and uncertainty rather than merely maximize delivery rate\.

__Resilience definition  __A component may be disconnected and still remain useful\. The system degrades from regional intelligence \-> local intelligence \-> cached emergency information, rather than collapsing from “online” to “dead”\.

__Invariant__

__Implementation rule__

Local autonomy

ESP32 performs acquisition, diagnostics, local health/quality/reliability and configured local hazard reasoning without requiring cloud access\.

Master autonomy

Raspberry Pi\-class Master can ingest, fuse, serve authority UI and run geospatial hazard computation without internet\.

Internet independence

Loss of internet must not erase node<\->Master communication or local citizen emergency access\.

Master\-failure independence

Loss of Master must not erase the last known valid local emergency state from nodes that cached it\.

Information honesty

Every consumer\-visible state carries freshness / information\-condition semantics; unknown is never converted to normal\.

Canonical events

A single incident/alert event ID drives all delivery channels; channels do not invent separate truths\.

Human authority

NexAlert recommends; an authorized human approves operational dispatch or response actions\.

Replay safety

Authenticated sequence/timestamp/event identifiers prevent stale packets from being accepted as new state\.

Store\-forward

Critical and safety\-relevant messages persist through bounded local queues and retransmit after recovery\.

Telemetry/label separation

Synthetic telemetry may exercise the pipeline, but hidden scenario ground truth never enters inference inputs\.

# 2\. Communication Architecture

NexAlert uses a layered communication model\. The prototype can operate primarily over IP/Wi\-Fi, while the architecture keeps lower\-bandwidth transports available for field deployment\. Transport choice is an implementation detail; event semantics and integrity rules remain transport\-independent\.

__Layer__

__Primary role__

__Minimum capability__

L0 — Sensor/MCU

Sensor acquisition and local state

ESP32 firmware, monotonic sequencing, diagnostics

L1 — Field node

Local buffering, health, edge reasoning, local emergency service

Wi\-Fi AP/local HTTP service, secure uplink, store\-forward

L2 — Master

Ingestion, cross\-node fusion, incident management, GIS and local authority UI

Linux compute, database, message broker/API, geospatial engine

L3 — Cloud / remote

Remote notification, archival, remote access and future integrations

Internet connection; optional for core local operation

L4 — Citizen endpoint

Emergency information, acknowledgements and SOS

Browser/PWA online or local captive portal offline

__Reference topology  __ESP32 field nodes <\-> local link <\-> Raspberry Pi Master <\-> optional internet/cloud\. A node may additionally host a minimal local emergency page and cached event state so it remains useful during Master failure\.

__2\.1 Logical paths__

__Path__

__Preferred path__

__Fallback / degraded path__

Telemetry

Node \-> Master ingestion API / message transport

Node buffer \-> retry when link returns

Master \-> node command

Authenticated command channel

Command queued until link restores; safety\-critical commands require explicit expiry

Master \-> cloud

HTTPS/WebSocket/push integration

No dependency for local authority operation

Citizen online

Cloud notification \-> emergency web UI

Retry / recent cached notification

Citizen offline

Node Wi\-Fi AP \-> captive portal \-> local emergency UI

No network access outside radio/AP reach

SOS

Citizen endpoint \-> available local/online receiver

Persist locally and transmit when a permitted path returns

# 3\. Protocol & Transport Strategy

The prototype should prefer the transport that is simplest to validate end\-to\-end on the current hardware\. Wi\-Fi/IP is therefore the primary prototype path\. LoRaWAN, NB\-IoT, 4G/5G or other long\-range transports remain supported as deployment adapters, not as hidden assumptions in business logic\.

__Transport__

__Best use__

__Constraints__

__V1 status__

Wi\-Fi / TCP\-IP

Node <\-> Master; local AP/captive portal

Range, interference, power use

PRIMARY

Ethernet

Fixed Master / gateway backhaul

Wiring required

OPTIONAL

LoRaWAN

Low\-rate long\-range telemetry

Small payloads, downlink constraints, gateway dependence

ADAPTER

NB\-IoT / LTE\-M

Wide\-area field connectivity

Modem, SIM/network coverage, power

ADAPTER

4G/5G IP

High\-rate remote backhaul

Coverage, power and cost

ADAPTER

BLE

Provisioning / local maintenance

Short range; not primary event transport

OPTIONAL

__Transport abstraction  __The application layer sends typed NexAlert messages\. Each transport adapter is responsible for framing, connection lifecycle, retry and MTU constraints; it must not reimplement incident or hazard logic\.

__3\.1 Network service boundaries__

__Service__

__Transport__

__Purpose__

Node telemetry ingress

HTTPS or authenticated TCP/WebSocket

Receive telemetry, diagnostics and events

Node status/health

HTTPS or lightweight authenticated request

Heartbeat and on\-demand diagnostics

Local citizen UI

HTTP over node AP

Emergency read\-mostly local experience

Master authority UI

HTTPS/HTTP on LAN

Operational dashboard and incident control

Cloud sync

HTTPS/WebSocket

Remote notifications, backup and external integrations

# 4\. Message Classes & Canonical Envelope

All communication objects use a shared envelope so the backend, simulator, hardware and test harness can reason about message identity uniformly\. Payload schemas vary by type, but identity, timing, provenance and authentication are common\.

__Field__

__Requirement__

message\_id

Globally unique identifier for the message instance\.

message\_type

telemetry | heartbeat | health | event | alert | command | ack | sos | audit\.

node\_id / sender\_id

Stable authenticated origin identifier\.

sequence

Monotonic sender sequence for ordering/deduplication\.

measurement\_timestamp

Sensor\-side event/measurement time; never overwritten by receive time\.

received\_timestamp

Assigned by receiver; used for transport freshness and delay analysis\.

schema\_version

Versioned payload contract\.

priority

NORMAL | HIGH | CRITICAL; affects local queue scheduling\.

ttl / expires\_at

Optional explicit expiry for commands and transient alerts\.

payload

Typed content for the message class\.

auth

HMAC or final approved authenticated envelope\.

\{  
  "message\_id": "evt\_01H\.\.\.",  
  "message\_type": "event",  
  "sender\_id": "NODE\_001",  
  "sequence": 18422,  
  "measurement\_timestamp": "2026\-09\-07T01:10:15Z",  
  "received\_timestamp": "2026\-09\-07T01:10:16Z",  
  "schema\_version": "1\.0",  
  "priority": "CRITICAL",  
  "payload": \{ \.\.\. \},  
  "auth": \{"alg":"HMAC\-SHA256","value":"\.\.\."\}  
\}

# 5\. Integrity, Ordering, Freshness & Replay Protection

A packet that arrives is not automatically a packet that should be trusted\. NexAlert validates origin, integrity, freshness and sequence semantics before the payload can affect operational state\.

__1\. __Authenticate the sender using its provisioned per\-node secret and the configured HMAC algorithm\.

__2\. __Verify the message body and canonical serialization before parsing it into domain state\.

__3\. __Reject malformed, expired or otherwise invalid messages before they reach hazard reasoning\.

__4\. __Deduplicate using message\_id and sender sequence\.

__5\. __Track receive time separately from measurement time; large transport delay lowers freshness but does not rewrite history\.

__6\. __Apply bounded clock\-skew rules\. A bad wall clock must not create false historical ordering when the sender sequence remains valid\.

__7\. __Persist the last accepted sequence window across reboot where practical; use a bounded replay cache for event IDs\.

__Golden rule  __Freshness answers “how recent is the information?” Integrity answers “did an authenticated sender produce it?” Neither one alone proves that the sensor value is correct\.

__Condition__

__System action__

Valid auth \+ new sequence \+ fresh timestamp

Accept and process normally\.

Valid auth \+ delayed timestamp

Accept if within configured lateness window; mark transport delay/freshness accordingly\.

Valid auth \+ duplicate sequence/event

Ignore as duplicate; do not create a second operational action\.

Valid auth \+ sequence gap

Accept if policy permits, record missing range and request recovery/backfill if available\.

Invalid HMAC

Reject; record security event; do not update hazard state\.

Expired command

Reject; record expired command for audit\.

Unknown sender

Reject and record unauthorized\-source event\.

# 6\. Store\-and\-Forward Architecture

Every node maintains a bounded persistent outbound queue for telemetry and event messages that could not be delivered\. The queue is a ring\-buffered safety mechanism, not an unbounded database\.

__Queue class__

__Examples__

__Policy__

Q0 — CRITICAL

Emergency event, node\-local hazard declaration

Highest priority; durable; retry aggressively with backoff; retain until delivered or explicitly expired\.

Q1 — HIGH

Health degradation, escalation, critical diagnostics

Durable; retransmit after recovery\.

Q2 — NORMAL

Telemetry samples, routine status

Bounded; oldest low\-value samples may be compacted or dropped under pressure according to policy\.

Q3 — BULK

Historical backfill / debug traces

Lowest priority; suspend under constrained links\.

__6\.1 Retry algorithm__

delay = min\(base\_delay \* 2\*\*attempt, max\_delay\)  
delay = jitter\(delay\)  
retry until delivered, expired, or policy\_drop  
while CRITICAL queue non\-empty: transmit Q0 before Q2/Q3

__Rule__

__Implementation__

Backoff

Exponential backoff with bounded jitter; avoid synchronized node storms\.

Compaction

Prefer compacting routine telemetry before dropping critical events\.

Drain order

CRITICAL \-> HIGH \-> NORMAL \-> BULK\.

Recovery burst control

Limit packets/sec during reconnection so Master/network is not flooded\.

Durability

Use crash\-safe local storage or append\-only journal plus bounded ring index\.

Observability

Expose queue depth, oldest message age, retry count and drop count\.

# 7\. Master Failure vs Internet Failure

These are separate failure domains and must produce separate information conditions\. The system must never display “offline” as a single vague state when the actual fault is known\.

__Mode__

__Master__

__Internet__

__Node<\->Master__

__Required behavior__

A — Fully connected

UP

UP

UP

Full authority, cloud and citizen channels available\.

B — Internet lost

UP

DOWN

UP

Local authority dashboard and distributed fusion continue; cloud delivery pauses; nodes buffer outward traffic if needed\.

C — Master lost

DOWN

Any

DOWN

Nodes continue local sensing/edge reasoning; cached emergency state and node\-hosted local emergency page remain available; central fusion unavailable\.

D — Master \+ internet lost

DOWN

DOWN

DOWN

Field nodes operate independently; local emergency pages and local hazard states remain usable; no false regional claims\.

E — Node isolated

UP

UP or DOWN

Single node isolated

Node continues local state and buffering; authority records node as unreachable/stale\.

__Mandatory distinction  __Master failure is an application/compute failure\. Internet failure is an upstream connectivity failure\. Their UI states, recovery procedures and audit records must remain distinct\.

__7\.1 Local emergency continuity requirement__

- Each field node caches the latest signed canonical emergency state relevant to its local area, including event ID, hazard, severity, state, issue/update time and freshness condition\.
- The node exposes a minimal read\-mostly HTTP emergency page through its own Wi\-Fi AP/local network service when configured and powered\.
- The local page must not require the Master, cloud, external DNS or internet access\.
- When the Master returns, the node and Master reconcile using event ID, version/update timestamp and authenticated source rules rather than blindly overwriting local state\.
- Local emergency content is explicitly labeled “LOCAL / LAST KNOWN” when the regional command view is unavailable\.

# 8\. Offline Citizen Emergency Operation

Offline access is not a separate product\. It is the same canonical emergency information model served locally when the citizen cannot reach cloud infrastructure\.

__Step__

__Behavior__

1\. Discover

Citizen sees distinctive NexAlert Wi\-Fi SSID in the local service area\.

2\. Join

Citizen connects to the node/gateway AP; no internet assumption\.

3\. Captive portal

DNS/HTTP redirect or explicit local landing page opens the emergency UI\.

4\. Read

UI shows hazard, state, severity, distance/direction when computable, freshness and immediate safety action\.

5\. Act

Citizen can view safe\-location guidance where locally cached/calculable, and can use SOS/contact functionality supported by the local path\.

6\. Recover

Once an uplink returns, queued citizen and node events synchronize to the canonical backend\.

__Offline honesty  __The UI must state when content is cached/local and how old it is\. It must never show a live regional map as though it were current when only a last\-known local snapshot exists\.

__Offline page block__

__Required behavior__

Emergency status

Hazard \+ severity \+ state \+ issued/updated age\.

Immediate action

Clear instruction or SHELTER\_IN\_PLACE when no viable safe route is known\.

Map

Local cached geometry or last\-known local footprint; freshness clearly visible\.

Communication

Available local instructions; no fake “message sent” confirmation without a receiver/queue acknowledgement\.

SOS

Accept locally where supported; show “queued / sent / delivered” as distinct states\.

System status

LOCAL MODE / MASTER UNAVAILABLE / LAST KNOWN as appropriate\.

# 9\. Distributed Fusion, Partition & Authority

Nodes may disagree with one another or with the Master’s broader picture\. Distributed resilience means preserving valid local evidence while explicitly modeling uncertainty and source scope\.

__Situation__

__Rule__

Same hazard \+ close spatial/temporal evidence

Master may deterministically correlate into one incident using configured merge radius/time window\.

Different hazards at same location

Keep independent hazard vectors; do not collapse them into one universal score\.

Neighbor disagrees with node

Retain both authenticated observations; recompute confidence/evidence according to the mathematical intelligence specification\.

Node declares local hazard while Master lacks external context

Do not erase the node’s valid local declaration solely because external evidence is absent\.

Cloud disagrees with local Master state

Local operational state remains available; cloud disagreement becomes a reconciliation/audit event\.

Partition split\-brain

Do not allow two independently issued operational commands to silently overwrite each other; use event/version/authority metadata and human reconciliation where required\.

__9\.1 Source scope metadata__

__Scope__

__Meaning__

LOCAL\_NODE

Evidence/state produced at one field node\.

LOCAL\_MASTER

State fused by the local Master from connected nodes\.

REGIONAL\_CLOUD

Broader context obtained through cloud/external systems\.

CACHED

Previously valid state available while current authority path is unavailable\.

UNKNOWN

Required information is missing or stale enough that a stronger claim is not supported\.

# 10\. Citizen Notifications, Delivery & SOS

Citizen communication follows one canonical event with channel\-specific delivery receipts\. The communication system distinguishes issued, delivered, opened, acknowledged and unreachable outcomes\.

__Stage__

__Definition__

ISSUED

Authorized alert exists in the canonical alert store\.

DISPATCHED

A delivery worker handed the alert to a configured channel/provider\.

DELIVERED

Endpoint/provider confirms receipt where such confirmation exists\.

OPENED

Citizen endpoint indicates that the emergency page/content was accessed\.

ACKNOWLEDGED

Citizen explicitly confirms receipt where the workflow supports acknowledgement\.

UNREACHABLE

No valid delivery path or endpoint confirmation exists within policy\.

__No fake reachability  __A notification request is not proof that a phone received it\. A fully powered\-off phone cannot be awakened by the prototype\. The audit trail must preserve the difference between attempted delivery and confirmed delivery\.

__10\.1 SOS path__

__1\. __Citizen presses\-and\-holds or otherwise confirms SOS according to the configured UX\.

__2\. __Client creates a unique SOS event ID and timestamp\.

__3\. __Client transmits through the best available path: online service first when reachable; local NexAlert path when offline and supported\.

__4\. __Receiver validates identity/signature and deduplicates repeated submissions without outright blocking a user from reattempting an SOS\.

__5\. __Authority dashboard categorizes the request as IMMEDIATE / HIGH / STANDARD / VERIFY rather than using a misleading single numeric “danger score”\.

__6\. __Operational action remains human\-approved\. The system can recommend response priority and location context, but does not autonomously dispatch emergency services\.

# 11\. Failure Modes & Operational States

__Failure__

__Detection__

__Expected state__

__Recovery__

Wi\-Fi link loss

Heartbeat timeout / packet loss

NODE\_ISOLATED

Continue local sensing \+ queue; reconnect/backoff\.

Master process crash

Local health watchdog/API failure

MASTER\_DEGRADED

Restart service; nodes continue local path\.

Master power loss

Node heartbeat absence / gateway loss

MASTER\_UNAVAILABLE

Node\-local emergency service remains available if powered and configured\.

Internet loss

Backhaul health check fails

CLOUD\_UNAVAILABLE

Local Master/authority operation continues\.

Clock drift

Clock sanity check

TIME\_DEGRADED

Use sequence \+ monotonic time; mark wall\-clock confidence low\.

Queue full

Queue depth threshold

BUFFER\_PRESSURE

Drop/compact lowest\-priority bulk data first; preserve critical events\.

Bad HMAC

Auth validation failure

SECURITY\_REJECT

Discard payload; emit security/audit event\.

Sensor stale

Measurement age exceeds threshold

TELEMETRY\_DEGRADED

Lower quality/reliability; do not silently substitute zero\.

Conflicting hazards

Evidence/correlation layer

MULTI\_HAZARD\_ACTIVE

Keep independent hazard states and user\-visible conflict guidance\.

__11\.1 Information\-condition propagation__

- GOOD — required communication inputs are recent enough for the intended decision\.
- DEGRADED — some relevant inputs or channels are missing/stale, but useful local or cached information remains\.
- UNKNOWN — information required to make the requested claim is unavailable or too stale to support it\.

# 12\. Resilience Validation & Fault\-Injection Plan

Communication resilience is demonstrated through deliberate failure, not through a green network icon\. Each test records time to detect, time to degrade, retained state, user\-visible condition, recovery latency and data loss\.

__Test ID__

__Injected fault__

__Expected result__

__Pass condition__

R\-01

Internet unplugged from Master

Local authority operation continues

No loss of local incident control; cloud status becomes unavailable/degraded\.

R\-02

Master process killed

Nodes keep sensing and buffering

Node\-local state persists; cached emergency UI remains reachable where configured\.

R\-03

Master physically powered off

Node local path continues

Emergency page does not depend on Master\.

R\-04

Wi\-Fi link loss 5 min

Node queues data

Critical events retained; no false resolved state\.

R\-05

Reconnect 20 nodes simultaneously

Backpressure occurs

System drains without crash or unacceptable queue storm\.

R\-06

Duplicate replay packet

No duplicate state transition

Exactly\-once operational effect even if network is at\-least\-once\.

R\-07

Invalid HMAC

Security reject

Payload never reaches hazard reasoning\.

R\-08

Clock jump

Temporal logic degrades safely

No future/past corruption; sequence remains usable\.

R\-09

Conflicting node evidence

Fusion recalculates confidence

Local valid hazard not erased solely by disagreement\.

R\-10

Power cycle node

Persistent queue \+ latest emergency state restored

No corruption; recovery observable\.

R\-11

Offline citizen joins AP

Captive portal works

Emergency content loads without internet\.

R\-12

Repeated SOS taps

Events consolidated but not blocked

Single operational SOS case with audit trail of retries\.

__Recommended benchmark evidence  __Capture packet loss, telemetry latency, queue depth, CPU/free heap, local page response time, HMAC verification cost, recovery time and number of lost/deduplicated messages\. Include plots/tables in the validation document, not as marketing\-only screenshots\.

# 13\. Configuration & Implementation Boundaries

__Parameter / flag__

__Suggested V1 default__

__Purpose__

heartbeat\_interval\_s

30

Fast node reachability indication\.

health\_report\_interval\_s

300

Detailed periodic diagnostics\.

telemetry\_queue\_capacity

Configured per node storage budget

Bounded store\-forward\.

critical\_retry\_max\_delay\_s

60

Backoff ceiling for high\-priority events\.

normal\_retry\_max\_delay\_s

300

Backoff ceiling for routine data\.

clock\_skew\_limit\_s

Configurable

Timestamp sanity bound\.

event\_dedup\_window\_s

Configurable

Replay/duplicate handling window\.

local\_cache\_max\_age\_s

Configurable by event class

Citizen\-facing freshness guard\.

captive\_portal\_enabled

true for field demo

Local emergency access\.

cloud\_sync\_enabled

true when internet available

Optional remote delivery\.

transport\_primary

wifi\_ip

Prototype transport adapter selection\.

__13\.1 Code ownership boundaries__

__Component__

__Owns__

__Must NOT own__

ESP32 firmware

Sensor reads, diagnostics, local state, HMAC, queue, local emergency service

Regional GIS, population exposure, heavy routing, cross\-node incident fusion

Master communication service

Transport adapters, authentication verification, ingestion, queues, synchronization

Sensor\-driver logic

Incident service

Deterministic correlation, lifecycle, alert objects

Raw radio framing

Citizen delivery worker

Channel dispatch, receipts, retries

Hazard classification

Simulation service

Synthetic telemetry emission through real ingestion path

Injecting hidden labels into reasoning

Frontend

Presentation, user interaction and local\-page rendering

Independent hazard truth or decorative spread simulation

# 14\. Acceptance Criteria

__1\. __A node can continue sensing, performing configured local intelligence and buffering messages when the Master is unreachable\.

__2\. __Loss of internet does not disable the local authority dashboard or local node<\->Master operation\.

__3\. __Loss of Master does not erase the last known emergency state from a field node that has cached it\.

__4\. __A citizen can reach the local emergency page from the NexAlert AP without internet access when the local service is configured and powered\.

__5\. __All accepted node messages are authenticated and deduplicated\.

__6\. __The backend preserves measurement time separately from receive time\.

__7\. __Critical events survive network interruption and are retried after reconnection\.

__8\. __The system makes the distinction between GOOD, DEGRADED and UNKNOWN visible at appropriate authority/citizen surfaces\.

__9\. __Split\-brain or conflicting evidence does not silently erase valid local hazard declarations\.

__10\. __Citizen delivery states distinguish issued, dispatched, delivered, opened, acknowledged and unreachable where each stage is measurable\.

__11\. __SOS is never auto\-rejected solely because the system has no current known hazard\.

__12\. __The communication layer passes replay, invalid\-auth, power\-cycle and partition tests without violating the mathematical or operational invariants in the rest of the NexAlert specification set\.

# 15\. Locked Invariants — Do Not Regress

__LOCKED  __These rules are part of the NexAlert architecture contract\. A future optimization is invalid if it breaks one of them\.

- Node <\-> Master authentication is mandatory for trusted operational traffic\.
- Master failure and internet failure are separate states\.
- Local emergency operation must not require internet or cloud access\.
- Cached emergency information is labeled with scope and freshness; stale data is never presented as live\.
- Store\-and\-forward queues are bounded and priority\-aware\.
- At\-least\-once transport may be used, but operational effects are deduplicated/idempotent\.
- Canonical event IDs are reused across alert delivery channels\.
- Synthetic telemetry follows the same ingestion path as hardware telemetry\.
- No frontend\-only simulated hazard is allowed to become the source of truth\.
- NexAlert recommends; authorized humans approve operational dispatch and response actions\.
- SAFE\_LOCATION / SHELTER\_IN\_PLACE behavior must remain explicit when no viable safe route is known\.
- Multi\-hazard states remain independent; no universal combined hazard score is introduced merely for UI convenience\.
- Every resilience claim is testable with an explicit fault\-injection scenario\.

__END OF SPECIFICATION__

*NexAlert remains useful when the network is not\.*

