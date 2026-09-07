NEXALERT

INCIDENT, RESPONSE & ALERT OPERATIONS SPECIFICATION

Final V1 Engineering Baseline — Incident Correlation, Human\-in\-the\-Loop Response, Alert Lifecycle, Citizen Safety & Auditability

__Field__

__Value__

Document ID

NEX\-10

Status

Final V1 Engineering Baseline

Primary owners

Backend / Intelligence / Response / UI

Authority hierarchy

Master System Architecture > TRD > this document > implementation details

Scope

Incidents, response workflow, alert operations, SOS triage, escalation, stand\-down, audit

Non\-goal

Autonomous emergency dispatch or unreviewed authority action

Implementation rule: NexAlert recommends, records and communicates; a human authority approves consequential response actions unless an explicitly configured life\-safety local action is already part of the approved edge policy\.

# Document Control & Authority

__Item__

__Decision__

System source of truth

The incident/event model is the canonical operational representation\. Dashboard views, citizen views and notifications are projections of it\.

Incident identity

A deterministic incident\_id is created/merged using hazard type, spatial proximity, temporal window and corroborating context\.

Correlation baseline

Default merge example: same hazard, within 50 m, within 30 s\. A 5 km spatial separation is treated as distinct unless an explicit configured regional\-correlation rule says otherwise\.

Action authority

NexAlert may recommend\. Authorized human operators approve, assign, cancel, escalate or stand down operational actions\.

Trust semantics

Information Condition is reported separately from incident state\. No confidence score is presented as a probability\.

Auditability

Every material state, decision, alert and acknowledgement is immutable/auditable with actor, timestamp, source and reason\.

# 1\. Purpose & Operating Model

This document defines how NexAlert converts hazard observations into operational incidents, recommended response actions, alerts, acknowledgements, assignments and resolution records\. The design is intentionally operational: it must behave coherently when connectivity is degraded, evidence is incomplete, sensors disagree, multiple hazards overlap and an operator must understand why an alert exists\.

## 1\.1 Core operating loop

- Observe: telemetry, node health, external context and citizen SOS enter the system with provenance\.
- Assess: quality, reliability, baseline readiness, anomaly, hazard evidence, confidence, severity and operational risk are calculated according to the locked intelligence architecture\.
- Correlate: observations are grouped into incident entities using deterministic spatial\-temporal rules and hazard context\.
- Decide: NexAlert assigns a state and proposes response actions; it does not silently convert recommendation into authority action\.
- Communicate: one canonical alert event fans out to configured authority/citizen channels\.
- Act: an authorized operator acknowledges and assigns response actions; progress is tracked explicitly\.
- Recover: stand\-down, resolution and post\-incident review close the operational loop while preserving history\.

## 1\.2 Non\-negotiable invariants

- No raw sensor threshold directly creates a public emergency alert\.
- No single stale/broken sensor can silently dominate a multi\-sensor incident decision unless the configured hazard policy explicitly allows a single critical core signal to do so\.
- No operator action is inferred from a recommendation that was never acknowledged/approved\.
- No historical incident state is rewritten because a later model revision differs\. Use a new assessment/version\.
- No “no hazard” conclusion is inferred merely because external nodes or internet services disagree with a valid local event\.
- A citizen SOS is never auto\-rejected solely because no known hazard exists\.
- A no\-route situation resolves to SHELTER\_IN\_PLACE rather than inventing a safe route\.

# 2\. Incident Domain Model

## 2\.1 Canonical incident entity

__Field__

__Type / example__

__Purpose__

incident\_id

UUID

Stable operational identity\.

hazard\_type

FIRE / FLOOD / POLLUTION / LANDSLIDE / EXTREME\_HEAT / UNKNOWN

Independent hazard vector\.

state

NORMAL / WATCH / SUSPECTED / CONFIRMED / CRITICAL / RESOLVED

Operational lifecycle state\.

information\_condition

GOOD / DEGRADED / UNKNOWN

Quality/coverage of available information\.

severity\_index

0\.\.1

Operational severity index; not probability\.

risk\_index

0\.\.1

Operational risk index; not probability\.

geometry

Point/Polygon/MultiPolygon

Affected or projected hazard geometry as applicable\.

centroid

lat/lon

Convenient display/query anchor\.

first\_observed\_at

UTC timestamp

Earliest trusted observation linked to incident\.

last\_observed\_at

UTC timestamp

Most recent linked evidence\.

current\_version

integer

Assessment/version counter\.

source\_summary

node IDs / external sources / citizen reports

Traceability\.

created\_by

SYSTEM / OPERATOR / CITIZEN\_SOS

Initiating pathway\.

resolution\_reason

Controlled vocabulary

Why incident was resolved\.

## 2\.2 Observation, evidence and incident distinction

- Observation = one telemetry or external/citizen input at a specific time\.
- Evidence = a normalized hazard\-specific interpretation of observations and contextual inputs\.
- Assessment = the current aggregate of evidence, confidence, severity and risk for an incident\.
- Incident = the operational object that carries state, communications, response actions and audit history\.

This separation prevents a dashboard alert from becoming the accidental source of truth\. The source of truth is the persisted incident plus its evidence/assessment lineage\.

## 2\.3 Incident creation and deterministic correlation

New evidence first attempts to match an active incident of the same hazard family\. The baseline implementation uses a deterministic spatial\-temporal correlation gate; hazard\-specific policy may narrow or expand it only through configuration\.

same\_hazard AND distance\(observation, incident\_context\) <= correlation\_radius  
AND time\_gap <= correlation\_window  
=> candidate for same incident  
else => distinct incident candidate

__Default__

__Value__

__Rationale__

Merge radius

50 m

Prototype baseline for local node cluster correlation\.

Merge window

30 s

Prevents separated events from collapsing into one event\.

Clearly separate example

5 km

Treat as distinct incidents unless explicit regional correlation is configured\.

Corroboration

Core evidence \+ supporting sensors

Raises confidence without pretending correlation is proof\.

Manual merge/split

Operator action, audited

Required for unusual geography/events\.

## 2\.4 Incident split / merge rules

- Split when an event develops into geographically distinct active fronts, clearly separate ignition points or independent hazard mechanisms\.
- Merge only when correlation rules are met or an operator explicitly merges incidents with a reason\.
- Never delete the source histories of merged incidents; preserve parent/child lineage\.
- A split creates new incident IDs with references to the source incident and preserves pre\-split state\.

# 3\. Incident State Machine

## 3\.1 States

__State__

__Operational meaning__

__Typical entry__

__Typical exit__

NORMAL

No actionable hazard evidence\.

No active event\.

WATCH when weak/early evidence appears\.

WATCH

Change warrants attention but not emergency action\.

Persistent anomaly, weak evidence, low\-to\-moderate risk\.

SUSPECTED, NORMAL\.

SUSPECTED

Hazard is plausible with meaningful evidence but insufficient confirmation\.

Core anomaly \+ supporting evidence\.

CONFIRMED, WATCH, RESOLVED\.

CONFIRMED

Evidence crosses configured confirmation criteria\.

Corroborated core evidence \+ persistence/coverage\.

CRITICAL, RESOLVED\.

CRITICAL

Confirmed incident with immediate or severe operational consequence\.

Rapid escalation, extreme severity/risk, dangerous projection\.

RESOLVED, downgrade only by explicit policy/operator workflow\.

RESOLVED

No longer operationally active\.

Hazard ended/contained/expired/false positive declared\.

Reopen only through a new incident or explicit audited reopen policy\.

## 3\.2 Transition guardrails

- Persistence/hysteresis applies to upward and downward transitions so noise does not flap incident state\.
- Rapid escalation may bypass normal dwell time when severity/risk or core evidence crosses a configured emergency threshold\.
- State transitions carry from\_state, to\_state, trigger, evidence\_ids, actor, timestamp and incident\_version\.
- Information Condition does not itself force a hazard state\. Poor information may cap confidence or produce UNKNOWN rather than “safe”\.

## 3\.3 Example transition record

\{  
  "incident\_id": "INC\-\.\.\.",  
  "from\_state": "SUSPECTED",  
  "to\_state": "CONFIRMED",  
  "trigger": "core\_evidence\_persisted",  
  "assessment\_version": 12,  
  "information\_condition": "GOOD",  
  "actor": "SYSTEM",  
  "timestamp": "\.\.\.",  
  "reason": "fire\_core\_evidence\_met\_confirmation\_policy"  
\}

# 4\. Assessment, Risk & Information Condition in Operations

## 4\.1 Operational interpretation

- Confidence C\_h describes confidence in the quality/consistency/coverage of the assessment, not probability that the hazard is real\.
- Severity S\_h describes how serious the hazard condition is operationally\.
- Risk R\_h combines hazard evidence, severity and operational context; it is an index, not a probability\.
- Information Condition reports whether operators have enough current, trustworthy information to rely on the assessment\.

__Condition__

__Meaning__

__UI/alert behavior__

GOOD

Core evidence sufficiently covered and fresh; inputs reasonably agree\.

Normal assessment visibility; eligible for configured alerting\.

DEGRADED

Some important data missing/stale/conflicting\.

Alert may proceed when policy allows, but message includes uncertainty and freshness\.

UNKNOWN

Evidence insufficient to support a defensible assessment\.

Do not manufacture a numeric confidence; use explicit UNKNOWN and request verification\.

# 5\. Response Recommendation Engine

## 5\.1 Principle: recommend, then approve

The response engine maps incident state, hazard type, severity, risk, geometry, affected assets, freshness, available resources and known constraints to a ranked set of recommended actions\. The output is advisory until an authorized operator approves it\.

__Recommendation__

__When useful__

__Approval__

EVACUATE\_ZONE

Current/projected exposure threatens people in defined zone\.

Human authority required\.

SHELTER\_IN\_PLACE

No viable safe route/destination or travel exposure is worse than sheltering\.

Human authority required\.

FIELD\_VERIFY

Evidence is meaningful but confirmation is incomplete\.

Can be auto\-recommended; dispatch remains human\-controlled\.

MONITOR\_CLOSELY

Watch/suspected with moderate consequence\.

Operator may acknowledge without external dispatch\.

PROTECT\_CRITICAL\_ASSET

Infrastructure/site likely exposed\.

Human approval\.

MOBILIZE\_RESOURCE

Response team/equipment may be needed\.

Human approval and assignment\.

STAND\_DOWN

Evidence no longer supports active operational response\.

Human approval except configured automatic alert expiry where explicitly allowed\.

## 5\.2 Recommendation payload

__Field__

__Meaning__

action\_id

Stable action identifier\.

incident\_id

Parent incident\.

action\_type

Controlled action vocabulary\.

priority

IMMEDIATE / HIGH / STANDARD / VERIFY\.

reason\_codes

Structured explanation tied to evidence\.

target\_zone

Geometry or named operational zone\.

constraints

Route, capacity, hazard conflicts, access limitations\.

expires\_at

Action freshness boundary\.

approval\_required

Boolean; true for consequential actions\.

status

PROPOSED / APPROVED / REJECTED / ASSIGNED / EN\_ROUTE / COMPLETED / CANCELLED\.

## 5\.3 No autonomous dispatch

- A recommendation cannot directly page a field team unless a policy\-specific integration explicitly treats the action as a non\-dispatch informational event\.
- Authority approval must be recorded before external operational assignments are issued\.
- Local edge actions already approved as safety policy \(for example, local buzzer/LED or a cached emergency page\) are separate from authority dispatch and remain within the edge policy envelope\.

# 6\. Alert Lifecycle

## 6\.1 One canonical alert event

Every outward alert channel references one canonical alert event\. Channel adapters do not create competing alert truths\.

__Stage__

__Description__

DRAFT

Alert content assembled from incident state and current assessment\.

PENDING\_APPROVAL

Used when the configured alert type requires operator approval\.

APPROVED

Authorized operator has approved issuance\.

ISSUED

Canonical alert emitted with event/version identifiers\.

DELIVERING

Channel adapters are attempting delivery\.

DELIVERED

Channel confirms delivery/receipt semantics available to that channel\.

OPENED

Recipient opened the alert where supported\.

ACKNOWLEDGED

Recipient or operator acknowledged it\.

ESCALATED

Alert was upgraded/reissued because conditions worsened or acknowledgement was absent\.

STAND\_DOWN

Active alert superseded by explicit closure/stand\-down\.

EXPIRED

Time\-based validity ended without implying that the incident is resolved\.

CANCELLED

Issued/queued alert withdrawn for a recorded reason\.

## 6\.2 Alert content contract

- Hazard and severity/state first\.
- Where relevant: affected/current/projection zone, distance, direction, time/freshness and required action\.
- Information condition and uncertainty when degraded/unknown\.
- Alert ID, incident ID/version and event timestamp for traceability\.
- Stand\-down/resolution status is explicit; silence is never interpreted as resolution\.

## 6\.3 Delivery accounting

__Status__

__Stored fields__

DELIVERED

channel, provider\_message\_id, delivered\_at, recipient\_scope

OPENED

opened\_at where channel supports it

ACKNOWLEDGED

actor/contact, acknowledged\_at

UNREACHABLE

channel error, retry count, last attempt

RETRYING

next\_attempt\_at, backoff state

FAILED

terminal\_reason, final\_attempt\_at

# 7\. Escalation & Alert\-Fatigue Controls

## 7\.1 Escalation triggers

- State escalates \(for example CONFIRMED → CRITICAL\)\.
- Risk/severity crosses a configured emergency boundary\.
- Projected arrival time becomes materially shorter than the previous assessment\.
- Affected population/infrastructure expands beyond an operational threshold\.
- No responsible operator acknowledges an IMMEDIATE/HIGH alert within the configured response window\.
- Information degrades after issuance and the alert must communicate uncertainty or request verification\.

## 7\.2 Anti\-fatigue rules

- Use event/version semantics instead of repeatedly emitting identical alerts\.
- Apply cooldowns to non\-escalating repeats\.
- Escalations bypass cooldown when operationally necessary\.
- Group related updates into an incident timeline while preserving each canonical alert event\.
- Track alert frequency per zone/channel/operator to expose noisy configurations\.
- Never suppress a genuinely new incident merely because the same area produced an earlier alert\.

# 8\. Citizen SOS Operations

## 8\.1 SOS as an independent operational source

Citizen SOS is a signal into the operational system, not a claim that a hazard exists\. It must remain useful when the sensing network is incomplete\. Each SOS receives a categorical handling tier based on urgency signals and available context; the system does not expose or rely on a fake numeric “SOS score\.”

__Tier__

__Meaning__

__Default handling__

IMMEDIATE

Life\-safety concern or acute danger indicators\.

Fast operator queue priority; location/context surfaced first\.

HIGH

Serious concern requiring prompt review\.

Prioritized queue and acknowledgement expectation\.

STANDARD

Relevant assistance request without immediate danger indicators\.

Normal operational triage\.

VERIFY

Ambiguous, incomplete or potentially duplicated report\.

Verification requested; never auto\-discarded solely because no hazard is known\.

## 8\.2 SOS consolidation

- Repeated SOS from the same user/device within a short interval may be linked to one SOS case while preserving each transmission timestamp\.
- Different citizens in the same location may be correlated as corroborating reports, never silently merged into one identity\.
- Location freshness and reported text/media provenance are stored separately\.

# 9\. Response Action State Machine

__Action state__

__Meaning__

__Next states__

PROPOSED

System recommendation waiting for decision\.

APPROVED / REJECTED / EXPIRED

APPROVED

Authorized operator accepted action\.

ASSIGNED / CANCELLED

ASSIGNED

Named responder/team/resource assigned\.

EN\_ROUTE / CANCELLED

EN\_ROUTE

Resource acknowledged movement\.

ON\_SCENE / CANCELLED / FAILED

ON\_SCENE

Responder arrived / started action\.

IN\_PROGRESS / COMPLETED / FAILED

IN\_PROGRESS

Work underway\.

COMPLETED / FAILED / CANCELLED

COMPLETED

Action delivered\.

Terminal

FAILED

Action could not be completed\.

RETRY / REASSIGN / TERMINAL

CANCELLED

Action intentionally stopped\.

Terminal

## 9\.1 Required action log

__Field__

__Purpose__

action\_id

Stable action identity\.

actor

System recommendation or human actor\.

actor\_role

Authority role/permission context\.

timestamp

When transition occurred\.

from/to

State transition\.

reason

Human\-readable rationale\.

reason\_codes

Structured reason taxonomy\.

incident\_version

Assessment version acted upon\.

location

Optional responder/asset location\.

notes

Operational comments\.

# 10\. Safe\-Location & Routing Decision Interface

Safe\-location ranking is a backend/Master responsibility and must not be recreated by the client\. “Nearest” is not equivalent to “safest\.” The decision service evaluates hazard exposure along the route and at the destination, travel time, capacity, accessibility and multi\-hazard conflicts\.

__Outcome__

__System behavior__

VIABLE\_SAFE\_DESTINATION

Return ranked candidates with route\-risk context\.

NO\_VIABLE\_ROUTE

Return SHELTER\_IN\_PLACE recommendation; do not invent a destination\.

DESTINATION\_CONFLICT

Exclude/flag candidate if another active hazard makes it unsafe\.

STALE\_ROUTE\_CONTEXT

Downgrade confidence/freshness and require re\-evaluation before action\.

# 11\. Multi\-Hazard Response

## 11\.1 Independent hazard vectors

Fire, flood, pollution, landslide and extreme heat remain independent hazard states and risk layers\. The response system evaluates each incident separately and then checks for response conflicts, such as an evacuation route threatened by a second hazard\. It does not calculate a universal combined probability or a fake combined risk scalar\.

## 11\.2 Response conflict examples

- Fire evacuation route enters an active flood warning zone → route rejected or reranked\.
- Flood shelter candidate sits inside a pollution plume → candidate rejected/flagged\.
- Extreme heat overlaps evacuation staging area → resource plan must account for exposure and capacity\.
- Network outage reduces information quality during a hazard → communication plan escalates uncertainty rather than lowering the hazard state\.

# 12\. Offline & Distributed Response Behavior

__Condition__

__Required behavior__

Internet unavailable, Master alive

Continue local Master operations; queue cloud synchronization; maintain local authority/citizen interfaces\.

Master service unavailable, internet available

Field nodes retain local edge safety behavior; local emergency path must remain available through the approved lightweight gateway path; incident/alert synchronization resumes when Master returns\.

Master physical power failure

No claim of centralized reasoning availability\. Local nodes continue local monitoring/actions within policy; citizen emergency page may remain available on the node/gateway path\.

Node isolated from network

Node buffers telemetry/events; local hazard state remains valid locally; syncs when connection returns\.

Citizen phone offline

Citizen may reach local NexAlert AP/captive portal if physically/network reachable; otherwise the phone cannot be awakened by NexAlert\.

## 12\.1 Local alert envelope

The local emergency path uses signed, bounded event payloads and cached rendering assets\. It does not require cloud reachability\. The local page must display hazard, state, freshness, action guidance and known uncertainty without pretending that unavailable centralized context exists\.

# 13\. Authority Dashboard Operations

## 13\.1 Incident Command Card

- Hazard type \+ incident ID\.
- Current state and severity\.
- Information Condition shown directly and prominently\.
- Time observed / last update / freshness\.
- Current affected area and projection status where applicable\.
- Top recommended action and approval status\.
- Escalation/stand\-down controls with permission gating\.

## 13\.2 Explain affordance

The operator may expand an Explain panel to see evidence groups, core\-evidence coverage, quality/reliability contribution, freshness and state\-transition reasons\. The default view should remain operational rather than mathematical\.

# 14\. Audit Trail & Accountability

Audit is first\-class system data\. Every material operational action must be reconstructable after the fact without relying on UI screenshots or transient logs\.

__Event__

__Minimum audit fields__

Incident transition

incident\_id, version, from/to, trigger, actor, timestamp, evidence refs

Assessment update

assessment version, inputs summary, model/config version, timestamp

Alert issue

alert\_id, incident\_id/version, channel, scope, approval actor, issued\_at

Alert acknowledgement

alert\_id, actor/contact, timestamp, channel

Action approval

action\_id, approver, role, timestamp, reason

Action assignment

action\_id, responder/resource, timestamp

Manual override

object, old value, new value, actor, reason, expiry if applicable

Incident merge/split

source IDs, result IDs, actor, reason, timestamp

## 14\.1 Immutability and correction

- Append new events rather than overwriting historical state\.
- Corrected observations create new records linked to the original\.
- Configuration/model changes record the effective version used for the assessment\.
- Human overrides never erase the original system recommendation; both remain visible in the timeline\.

# 15\. Backend Data Model Summary

__Entity__

__Key relationships__

Incident

has many Assessments, Evidence, Alerts, ResponseActions, SOSLinks, AuditEvents, GeometryVersions

Assessment

belongs to Incident; references model/config versions and evidence set

Alert

belongs to Incident/version; has many DeliveryAttempts / Acknowledgements

ResponseAction

belongs to Incident; optional parent recommendation

SOSCase

belongs to citizen/contact context; may link to zero or more Incidents

IncidentLink

many\-to\-many relation for corroboration / cause / related incident

AuditEvent

append\-only event log across incident/alert/action entities

# 16\. API Contract Expectations

## 16\.1 Core endpoints

__Method__

__Endpoint__

__Purpose__

POST

/incidents/correlate

Create or attach an observation/evidence item to an incident\.

GET

/incidents/\{id\}

Retrieve current operational incident snapshot\.

GET

/incidents/\{id\}/timeline

Return state, evidence, alert and response timeline\.

POST

/incidents/\{id\}/assess

Persist assessment version\.

POST

/incidents/\{id\}/actions/recommend

Generate response recommendations\.

POST

/actions/\{id\}/approve

Approve a response action\.

POST

/actions/\{id\}/transition

Advance action state with validation\.

POST

/alerts/\{id\}/approve

Approve an alert when required\.

POST

/alerts/\{id\}/standdown

Stand down an alert\.

POST

/sos

Create/update citizen SOS case\.

GET

/sos/queue

Return prioritized SOS queue\.

## 16\.2 Idempotency

- Ingestion and alert endpoints accept idempotency keys where retries are expected\.
- Duplicate telemetry or alert issue attempts must not create duplicate incident actions\.
- State transitions must validate current version/ETag or equivalent optimistic concurrency token\.

# 17\. Operational Metrics & SLO\-style Measures

__Metric__

__Definition__

Time to detect

First trusted evidence to first incident candidate\.

Time to confirm

First incident candidate to CONFIRMED/CRITICAL\.

Time to acknowledge

Alert issue to operator acknowledgement\.

Time to act

Approval to responder assignment / action start\.

Alert delivery success

Successful deliveries / attempted deliveries by channel\.

Escalation latency

Trigger to escalation alert\.

False\-alert rate

Operationally reviewed alerts later classified as unsupported/false\.

Missed\-incident rate

Known validation incidents not surfaced to expected state\.

Alert fatigue rate

Repeated non\-escalating alerts per incident/zone/channel\.

Offline continuity

Duration the local emergency path remains usable without cloud connectivity\.

Audit completeness

Material state transitions with required audit fields / total transitions\.

# 18\. Validation & Test Matrix

__Scenario__

__Expected result__

Two nodes detect same fire within 20 m and 10 s

Single incident; evidence corroborated\.

Two similar events 5 km apart

Distinct incidents\.

Same location fire reports separated by >30 s

Do not auto\-merge solely on proximity\.

One stale node \+ fresh core sensors

Stale node contribution reduced by quality/freshness; no silent dominance\.

Master loses internet

Local operations continue; cloud delivery queued/recoverable\.

Master process/power unavailable

Node\-local safety path remains available within approved envelope\.

Incident becomes more severe rapidly

Escalation bypasses normal cooldown/dwell where configured\.

Operator never acknowledges HIGH alert

Escalation workflow fires according to policy\.

No viable safe route

SHELTER\_IN\_PLACE returned\.

Citizen SOS outside known hazard

SOS enters queue; not auto\-rejected\.

Human rejects recommended evacuation

Rejection audited; alert not issued from that recommendation\.

Incident resolved

Stand\-down/resolution recorded; prior timeline preserved\.

Model/config revision after incident

New assessment version, historical version preserved\.

# 19\. Implementation Architecture

backend/  
  incidents/  
    correlation\.py  
    state\_machine\.py  
    assessment\.py  
    models\.py  
    service\.py  
  response/  
    recommend\.py  
    actions\.py  
    routing\.py  
    safe\_locations\.py  
  alerts/  
    policy\.py  
    composer\.py  
    dispatcher\.py  
    delivery\.py  
    escalation\.py  
  sos/  
    intake\.py  
    triage\.py  
    queue\.py  
  audit/  
    events\.py  
  workers/  
    recompute\.py  
    notify\.py  
    escalation\.py  


# 20\. Configuration & Feature Flags

__Parameter__

__Default / baseline__

__Change rule__

incident\.correlation\_radius\_m

50

Configurable, audited

incident\.correlation\_window\_s

30

Configurable, audited

alert\.high\_ack\_timeout\_s

Policy\-defined

Must be environment/config controlled

alert\.cooldown\_s

Policy\-defined

Hazard/channel specific

alert\.max\_repeat\_per\_window

Policy\-defined

Guard against fatigue

incident\.rapid\_escalation\_enabled

true

Safety\-critical; changes audited

response\.autonomous\_dispatch

false

Must remain false for V1

response\.shelter\_in\_place\_fallback

true

Safety invariant unless formally replaced

audit\.require\_reason\_for\_override

true

Safety invariant

# 21\. V1 Acceptance Criteria

- One deterministic incident can be traced from raw evidence through assessment, state transition, alert, response action and resolution\.
- Same\-hazard observations inside the baseline spatial\-temporal window correlate predictably; clearly separated observations remain separate\.
- Operator approvals/rejections are enforced and fully audited\.
- Canonical alerts support issuance, delivery accounting, escalation, acknowledgement and stand\-down\.
- Citizen SOS remains operational even when no hazard is currently known\.
- Offline/local behavior is explicit and does not pretend to have unavailable centralized context\.
- Multi\-hazard conflicts are handled as separate hazard vectors with response coordination, not a universal combined risk scalar\.
- At least the validation scenarios in Section 18 pass in automated and demonstration tests\.

# 22\. Final Operational Principle

NexAlert is not an alarm button with a map\. It is an incident operating system for a distributed environmental network: it preserves the distinction between evidence and action, makes uncertainty visible, keeps local safety behavior alive when the network is degraded, and records who decided what happened and why\.

Lock status: This document is the final V1 incident/response baseline\. Changes to incident correlation, autonomous authority, alert semantics, local failure behavior or auditability require an explicit architecture\-level review\.

