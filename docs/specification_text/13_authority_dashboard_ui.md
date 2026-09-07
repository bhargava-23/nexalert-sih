__NEXALERT__

__FINAL SPECIFICATION 13__

__Authority Dashboard  
UI & FUNCTIONING__

*Operational interface for incident command, live hazards, distributed nodes, citizen safety, alerts, response, simulation and audit\.*

__Status: LOCKED FOR IMPLEMENTATION__

Authority / Operations Surface

Document family: NexAlert Final Architecture Set | Predecessors: 01–12

# 1\. Purpose and Product Contract

This document defines the production behavior of the NexAlert authority dashboard\. It is not a visual mock\-up only: every screen, control, map layer, state transition, data dependency and operator action specified here must map to a real backend/API capability or an explicitly marked unavailable/degraded state\.

The dashboard is the command surface for a system whose core promise is trustworthy operation under uncertainty and partial failure\. It must therefore expose what the system knows, what it does not know, what changed, and what action remains available without turning internal mathematical scores into fake certainty\.

__Contract__

__Required behavior__

Source of truth

Backend incident/state models and geospatial products; UI never invents hazard state\.

Human authority

NexAlert recommends and surfaces evidence; authorized humans approve operational actions and dispatch\.

Resilience

Internet loss, Master loss, node isolation and stale data are represented explicitly\.

Hazard separation

Fire, flood, pollution, landslide, heat and unknown hazard states remain separate vectors\.

Evidence honesty

Confidence is presented only when evidence is sufficient; it is not shown as probability\.

Map truth

Physical footprint, warning/projection zones and operational buffers are distinct layers\.

Auditability

Every material operator action and automated state transition has an audit record\.

# 2\. Information Architecture

Top\-level navigation is intentionally operational rather than feature\-marketing oriented\. The operator should move from situational awareness to incident action without hunting through unrelated menus\.

__Primary page__

__Mission__

Overview

Live command picture: nodes, incidents, SOS, hazard zones, network status and command card\.

Incidents

Incident queue, filtering, merge/split, detail, evidence and state control\.

Fire Spread

Real LIVE/SIMULATION geospatial spread, time control, geometry and projections\.

Affected Area & Impact

Current/warning/awareness/projection zones with exposure and impact\.

Multi\-Hazard & Simulation

Separate hazard vectors, scenario control, replay and cross\-hazard context\.

Nodes & Network

Node health, topology, heartbeat, telemetry quality and communications\.

Telemetry & Intelligence

Raw → quality → anomaly → evidence → confidence → severity → risk → state\.

Citizen SOS

Incoming SOS map, queue, contact context and operator handling\.

Alert Management

Alert issuance lifecycle, targeting, delivery and acknowledgement\.

Historical Analysis

Incidents, hazard trends, hotspots, reliability, outcomes and response times\.

Response & Actions

Recommendations, approvals, assignments, status and resolution\.

Audit Trail

Immutable operator/system event history with filters and export controls\.

System

Health, configuration, feature flags, integrations and service status\.

# 3\. Overview: Command Surface

Overview is the default landing page\. It should answer in under one screen: Where is the problem? What is affected? What is changing? How reliable is the information? What needs an operator decision?

## 3\.1 Layout

__Region__

__Function__

Header

Agency/system identity, current time, environment, connectivity, operator identity, global emergency indicator\.

Status strip

Last alert issued, last citizen contact/SOS, active incidents, nodes online/degraded/offline\.

Primary map

Nodes, incident markers, current/warning/projection zones, risk heatmap and relevant context layers\.

Incident Command Card

Selected/most urgent incident: hazard, state, information condition, severity, affected area, freshness, next recommended action\.

Right rail / queue

Urgent alerts, SOS, incidents needing review, node failures and stale\-data warnings\.

Footer / utility

Map legend, layer controls, timestamp, backend/source freshness and operator shortcuts\.

## 3\.2 Map conventions

__Element__

__Visual rule__

__Interaction__

Field/slave node

Blue node marker

Click → node side panel

Master

Yellow marker

Click → compute/network panel

Logical links

Dotted lines

Toggle to reduce clutter

Incident

Distinct incident marker by hazard

Click → incident detail

SOS

Human\-priority marker with tier icon

Click → SOS panel

Current physical hazard

High\-salience translucent geometry

Click → analytical context

Warning / projection

Progressively lower visual dominance

Time/context controls

Operational buffer

Patterned/outlined distinct from physical footprint

Click → policy/source detail

Continuous risk

Heatmap overlay

Legend \+ threshold controls

# 4\. Incident Command Card

The Incident Command Card is the highest\-value non\-map component\. It is the operator’s compact truth surface\. It must never display a green badge simply because the dashboard is connected; the card status reflects incident information condition\.

__Field__

__Required content__

Hazard

Fire, flood, pollution, landslide, extreme heat or unknown\.

State

NORMAL, WATCH, SUSPECTED, CONFIRMED, CRITICAL or RESOLVED\.

Information Condition

GOOD, DEGRADED or UNKNOWN\.

Severity

Operational severity index presented according to configured bands; no probability language\.

Freshness

Age of newest material evidence and evidence groups\.

Footprint

Physical/current affected area with units\.

Projection

Time horizon \+ projected geometry when available\.

Evidence summary

Core evidence groups, corroboration and missing evidence\.

Recommendation

Recommended operational next action\.

Authority action

Approve, acknowledge, assign, issue alert, stand down, or hold for review as permitted by role\.

## 4\.1 Explain affordance

“Explain” expands from the operational conclusion into the evidence chain\. It exposes supporting sensors/groups, reliability, signal quality, baseline readiness, anomaly magnitude, temporal persistence and relevant external context\. It should hide implementation\-only details by default and expand progressively\.

## 4\.2 No\-evidence behavior

When evidence is insufficient for a valid assessment, confidence is shown as N/A or “insufficient evidence”, not as 0%\. A stale or isolated node can remain visible while the command card states DEGRADED or UNKNOWN\.

# 5\. Incidents UI

## 5\.1 Incident queue

__Column__

__Meaning__

Priority

Operational urgency derived from state/severity and configured escalation policy\.

Hazard

Independent hazard type\.

State

Current incident lifecycle state\.

Info condition

GOOD / DEGRADED / UNKNOWN\.

Location

Incident center/front/zone reference\.

Freshness

Newest evidence age\.

Impact

Affected population/infrastructure summary\.

Last action

Latest human/system operation\.

## 5\.2 Deterministic incident correlation

New detections are correlated into an existing incident only through deterministic policy using hazard type plus spatial radius plus temporal window and configured context\. Example policy values may use 50 m / 30 s for closely related detections while materially separated events remain separate\. Values are configuration, not hard\-coded UI assumptions\.

The UI must provide a visible “correlated because” explanation and permit authorized review of merge/split decisions\. Splitting or merging creates an audit event and does not rewrite raw telemetry\.

## 5\.3 Incident detail

- Header: incident identity, hazard, state, information condition, severity, timestamps, incident source\.
- Map: current geometry, warning/projection, nodes, SOS, critical infrastructure and relevant environmental context\.
- Evidence drawer: evidence groups, core coverage, agreement, temporal persistence, baseline readiness, freshness\.
- Action drawer: acknowledge, request review, issue/cancel/stand down alert, assign response action, add note, escalate\.
- Timeline: state transitions, alerts, acknowledgements, response actions, telemetry milestones and audit\-linked events\.

# 6\. Fire Spread Hero Page

Fire Spread is a real analytical surface, not a decorative animation\. It must use the same fire\-spread engine described in the geospatial specification for LIVE and SIMULATION modes\.

__Control__

__Required behavior__

LIVE / SIMULATION

Switches data source; both invoke the same engine and rendering contract\.

Play / Pause

Advances projection time using stored or simulated arrival\-time surface\.

Time slider

Controls evaluation time; shows current footprint and future bands\.

Reset

Returns to incident reference time or simulation initial state\.

Layer toggles

Terrain, fuel, moisture, wind, physical footprint, warning, projection, buffer, risk, exposure\.

Context panel

Wind FROM direction, propagation TO direction, wind speed, slope/terrain, fuel/moisture inputs, model version\.

Impact panel

Affected population/infrastructure derived downstream from geometry\.

Version banner

Displays projection version and recompute timestamp after environmental changes\.

## 6\.1 Geometry truth

The UI renders actual raster\-derived connected components/polygons from the spread engine\. Polygon and MultiPolygon are supported\. Display simplification is allowed only for presentation; the underlying raster/geometry remains the source of truth\.

## 6\.2 Environmental change

When wind/fuel/moisture or another material input changes, the UI must show a recomputation/version event\. Historical truth remains fixed; future propagation is reseeded from the current frontier and recomputed\. The operator must be able to see “projection updated at T because inputs changed,” rather than silently seeing historical geometry mutate\.

# 7\. Affected Area & Impact

This page translates hazard geometry into operational impact without contaminating the physical hazard model with exposure data\.

__Layer / panel__

__Function__

Current

Cells/polygons already affected at evaluation time\.

Warning

Near\-future exposure band\.

Awareness / planning

Configured planning envelope where policy requires it\.

Projection

Longer future envelope based on model horizon\.

Operational buffer

Policy buffer around physical hazard geometry; visually distinct\.

Population

Population intersecting relevant geometry, with source/freshness\.

Infrastructure

Roads, schools, hospitals, utilities and configured critical assets\.

SOS

Citizen requests inside/near affected areas\.

Conflict view

Flags safe\-direction or multi\-hazard conflicts without creating a fake combined risk scalar\.

Population/infrastructure are downstream impact layers\. They are not substituted into the fire physical propagation equation and are not silently added into the hazard probability model\.

# 8\. Multi\-Hazard & Simulation

The UI presents hazards as parallel analytical vectors\. It never sums fire \+ flood \+ pollution into a universal “combined risk” number\.

__Hazard__

__Primary UI evidence__

Fire

Temperature, smoke/PM, gas where calibrated, fire evidence, spread geometry, wind/terrain/fuel context\.

Flood

Water level, rainfall, trend/persistence, corroborating nodes and inundation context\.

Pollution

PM/gas/meteorology patterns, spatial corroboration, quality and baseline readiness\.

Landslide

Vibration/soil/moisture/rain context and localized corroboration\.

Extreme heat

Temperature/humidity/derived heat context, duration and spatial persistence\.

Unknown

Anomaly/evidence groups without a configured hazard declaration; preserves uncertainty\.

## 8\.1 Simulation controls

- Scenario selector with versioned scenario ID\.
- Start / pause / reset / step controls\.
- Injected failures: missing, stale, drift, contradictory sensors, communication loss/recovery\.
- Network replay: exact telemetry stream through the same ingestion path as hardware\.
- Ground truth: visible only to evaluator/replay tools; never injected into production reasoning APIs\.
- Compare mode: scenario truth vs system output after the run, not during inference\.

# 9\. Nodes & Network UI

__Panel__

__Must show__

Node overview

Node ID, location, role, connectivity, last heartbeat, telemetry freshness, battery/power, firmware\.

Sensor health

Per sensor component health and hard\-failure gate where applicable\.

Signal quality

Integrity/stability indicators, stale/missing/invalid counts\.

Reliability

R = H × Q × K displayed as an internal trust metric with explanation\.

Baseline

INITIALIZING / LEARNING / READY / FROZEN / RECOVERING\.

Diagnostics

Reset count, queue depth, packet loss, error counters, local service status\.

Topology

Master/field relationships and logical links; partition/isolation visible\.

Telemetry drill\-down

Raw measurement, receive timestamp, measurement timestamp, sequence, schema/auth state\.

Battery is a power status signal and is not silently multiplied into sensor health\. A node may be operationally degraded because of power risk while its sensing\-health metrics remain independently interpretable\.

## 9\.1 Master vs internet failure

System health must distinguish: “Master unavailable”, “internet/cloud unavailable”, “node unreachable”, and “data stale”\. These are different causes with different recovery options and different citizen\-safety implications\.

# 10\. Telemetry & Intelligence UI

Telemetry & Intelligence provides progressively deeper inspection while keeping the default operator view understandable\.

__Stage__

__UI representation__

Raw telemetry

Measurement, timestamps, sequence, source, schema/auth status\.

Quality

Integrity/stability flags and Q\.

Health

Soft health/hard failure and H\.

Reliability

R plus explanation of K/calibration factor\.

Baseline

State \+ readiness B\.

Anomaly

A\_i / A\_node / A\_h with method and cap/config version\.

Evidence

Hazard evidence groups, core coverage, temporal agreement\.

Confidence

C\_h only when evidence is sufficient; show factors, not probability wording\.

Severity

Operational severity S\_h with component breakdown\.

Risk

Operational risk R\_h with component breakdown\.

State

NORMAL/WATCH/SUSPECTED/CONFIRMED/CRITICAL/RESOLVED and transition reason\.

# 11\. Citizen SOS UI

Citizen SOS is treated as a human safety signal, not as a hazard classifier\. The dashboard must never auto\-reject an SOS solely because no known hazard is active\.

__Element__

__Behavior__

Queue priority

Categorical IMMEDIATE / HIGH / STANDARD / VERIFY\.

Map

SOS marker, location/freshness, nearest incident/hazard context and operator notes\.

Profile

NexAlert User ID, verified contact identifier when available, permitted relationship context\.

Status

Received, acknowledged, assigned, actioned, resolved or unable\-to\-locate\.

Location confidence

Explicitly distinguish fresh GPS, recent permitted location and coarse/unknown location\.

Safety action

Show recommended safe place/route only when supported; otherwise SHELTER\_IN\_PLACE\.

# 12\. Alert Management

Alerts are lifecycle objects, not one\-click notifications\. A single canonical emergency event drives all supported delivery channels\.

__Stage__

__UI state / evidence__

Draft / recommendation

System or operator has a proposed alert payload and target zone\.

Approved

Authorized operator approved issuance\.

Issued

Canonical event accepted for distribution\.

Delivering

Per\-channel delivery counters and errors\.

Delivered

Delivery confirmation where supported\.

Opened

Client open/receipt telemetry where supported\.

Acknowledged

Citizen/operator acknowledgement where supported\.

Unreachable

Target endpoint could not be reached; reason retained\.

Escalated

Policy or human escalation recorded\.

Stand down

Alert withdrawn/resolved with explicit reason and timestamp\.

Online and offline channels remain visibly distinct\. Online delivery relies on the appropriate web/client path; offline access uses the NexAlert local Wi\-Fi/captive portal path\. Future channels such as cell broadcast or satellite are marked integration states until authorized and implemented\.

# 13\. Response & Actions

NexAlert recommends; authorized humans approve and assign\. The UI must not imply autonomous emergency dispatch\.

__Action lifecycle__

__Operator\-facing state__

Recommendation

Suggested action \+ reason \+ supporting evidence\.

Acknowledged

Authority has seen and accepted responsibility\.

Approved

Operational decision approved\.

Notified

Relevant person/team notified\.

Assigned

Owner/team assigned\.

En route

Response resource reports movement\.

On scene

Arrival recorded where applicable\.

Resolved

Action complete\.

Cancelled / superseded

Reason retained in audit\.

# 14\. Historical Analysis

Historical views are for learning and accountability, not retroactive rewriting of incident truth\.

__Analysis__

__Examples__

Incidents

Frequency by hazard, state duration, geography, seasonal/time patterns\.

Hotspots

Repeated detections/SOS clusters using actual stored event data\.

Node reliability

Heartbeat gaps, quality/reliability trends, failure recurrence\.

Response

Alert\-to\-ack, ack\-to\-assignment, assignment\-to\-resolution\.

Alert outcomes

Issued vs delivered/opened/acknowledged/unreachable\.

Model comparison

Confidence/severity/state vs post\-incident outcome where ground truth exists\.

Environmental trends

Temperature, rain, water, PM/gas and context trends\.

Replay

Re\-run a historical or synthetic scenario with pinned configuration/model versions\.

# 15\. Audit Trail

Audit is queryable, append\-oriented and linked to the entity that changed\. Examples: incident state transition, incident merge/split, alert approval/issuance/standdown, response assignment, configuration change, access/role change, feature\-flag change, system failover and replay start/stop\.

__Audit field__

__Requirement__

event\_id

Unique and immutable\.

timestamp

Server\-side timestamp plus original event time where relevant\.

actor

Operator/service identity\.

action

Normalized action name\.

entity

Incident/alert/node/config/etc\.

before / after

Structured values where meaningful\.

reason

Required for sensitive state changes\.

correlation id

Links related workflow events\.

source

UI/API/system/edge/replay\.

# 16\. System & Service Health

__Status__

__Meaning / operator response__

Healthy

Expected services and data freshness within configured thresholds\.

Degraded

Known functionality impaired but safety path remains active\.

Disconnected

Network/cloud unavailable; local capabilities may remain active\.

Master unavailable

Master compute inaccessible; display last\-known state only and surface local fallback status if available\.

Unknown

Cannot establish trusted condition from available evidence\.

The UI should always show the last successful synchronization / data freshness time instead of implying that an empty panel means zero activity\.

# 17\. Interaction Rules & Operator Safety

__Rule__

__Implementation__

Destructive actions

Require confirmation and role authorization; explain consequence\.

Emergency actions

Keep primary emergency controls available; do not bury behind charts\.

Alert issuance

Show target zone, hazard/state, freshness, rationale and approval identity before commit\.

Stand down

Require explicit reason and display who/what remains affected\.

Merge/split incident

Show deterministic correlation basis and create audit event\.

Stale data

Show staleness inline, not only in a global banner\.

Unknown

Do not map UNKNOWN to normal/green\.

Loading

Show skeleton/progress with data timestamp; never show fabricated values\.

No data

State “No trusted data available” rather than “0”\.

Map conflicts

Preserve multiple layers and explain which source owns each geometry\.

# 18\. Role\-Based Access

__Role__

__Typical permissions__

Viewer

Read\-only dashboard, maps and historical analysis\.

Analyst

Evidence inspection, simulation/replay, notes; no alert issuance\.

Incident Operator

Incident acknowledgement, response workflow, alert preparation/authorized operations\.

Supervisor

Escalation, alert approval, standdown, incident merge/split approval\.

System Administrator

Configuration, integrations, feature flags, account/role administration; operational actions remain audited\.

Actual permissions are backend\-enforced\. Hiding a button in the frontend is not a security boundary\.

# 19\. Frontend Data / API Contract

The frontend consumes versioned read models and command endpoints\. It should not recompute authoritative hazard state, incident correlation, exposure or safe\-route rankings in the browser\.

__Frontend need__

__Backend contract__

Overview map

Snapshot endpoint \+ incremental event/stream updates\.

Incident detail

Incident read model \+ evidence \+ geometry \+ timeline\.

Node panel

Node health/readiness/telemetry read model\.

Fire page

Spread snapshot \+ time\-indexed arrival/risk/exposure layers\.

Alert management

Alert lifecycle \+ delivery receipts \+ command endpoint\.

SOS

SOS queue/read model \+ secure command endpoint\.

Historical

Aggregations/read\-only analytics endpoints\.

Audit

Paginated immutable audit query\.

All commands must be idempotent where practical and must return the resulting server\-side state plus correlation/audit identifiers so the UI can reconcile without optimistic fiction\.

# 20\. Responsive & Offline Authority Behavior

__Mode__

__Required authority UI behavior__

Desktop online

Full dashboard, map, multi\-panel analytical workflows\.

Tablet

Prioritize command card, map, incident queue and alerts; secondary detail in drawers\.

Offline / disconnected

Show cached last\-known command state with prominent freshness and connectivity status; do not imply live truth\.

Master unavailable

Preserve local/static emergency pathway where implemented; authority dashboard reports Master outage explicitly\.

Partial node loss

Continue with surviving evidence while marking affected spatial confidence/degraded coverage\.

Recovered

Reconcile buffered telemetry/receipts and show recovery event in timeline/audit\.

# 21\. Visual Semantics Checklist

__Semantic__

__Must remain consistent__

Hazard state

Use state\-specific treatment from Document 12\.

Information condition

GOOD / DEGRADED / UNKNOWN always visible on command surfaces\.

Warning vs projection

Different styles and legends\.

Physical vs policy

Operational buffer never looks identical to physical footprint\.

Confidence

Never presented as probability\.

Risk

Operational index; avoid probability iconography\.

SOS

Human\-priority categorical tier; no fake scalar\.

Stale

Timestamp \+ age \+ explicit stale treatment\.

Offline

Connectivity badge \+ local\-mode explanation\.

# 22\. Acceptance Tests

__Test__

__Pass condition__

Fire LIVE

Actual engine geometry changes over time; no decorative circle layer\.

Fire SIMULATION

Synthetic telemetry uses same ingestion path; spread engine and UI are identical in contract\.

Master failure

Dashboard reports Master failure distinctly from internet outage; local emergency capability remains discoverable where supported\.

Stale node

Node panel and command card show stale/freshness information and degrade information condition appropriately\.

Conflicting sensors

Contradiction is visible in evidence explanation; system does not silently average away the conflict\.

Insufficient evidence

Confidence is N/A/insufficient rather than 0%\.

Incident correlation

Spatial/temporal policy shown for merge; merge/split audited\.

Alert issue

Authorized approval required and canonical event created once; repeats are deduplicated\.

SOS

SOS outside known hazards is still accepted into operator queue\.

No safe route

Citizen/action panel can present SHELTER\_IN\_PLACE when routing is unsafe/unavailable\.

Multi\-hazard

Fire/flood/etc\. remain independent; no combined universal risk scalar appears\.

Audit

Every material operator command can be traced to actor, time, entity and result\.

# 23\. Implementation Blueprint

Recommended frontend structure: a typed React/Next\.js application using the Document 12 design tokens/components and a thin operational\-state layer\. State should be split between server\-authoritative query caches and transient UI state; do not duplicate domain logic in the browser\.

__Module__

__Responsibilities__

app\-shell

Navigation, auth/session, global connectivity/freshness, keyboard shortcuts\.

map\-engine

Map rendering, layer toggles, hit testing, geometry source/version labels\.

incident\-console

Queue, detail, evidence, commands, timeline\.

command\-card

Urgency, state, information condition, evidence summary, action controls\.

fire\-console

LIVE/SIMULATION, time controls, spread/risk/impact layers\.

node\-console

Health, reliability, diagnostics, telemetry drill\-down\.

safety\-console

SOS, alerts, safe\-place/action context\.

history\-console

Analytics, trends, replay links\.

audit\-console

Immutable event browsing and export\.

realtime\-layer

Server events, reconciliation, reconnect/backfill logic\.

permissions

Role/capability checks; server remains authoritative\.

# 24\. Final UI Invariants

- The dashboard never invents a hazard state, risk surface, exposure value, delivery status or system health value\.
- No single global risk score is used to collapse independent hazards\.
- Information Condition is visible at the command level and is not inferred from network connectivity alone\.
- Historical data is immutable from the UI; corrections are new events with audit context\.
- Fire geometry comes from the real spread engine and the same engine serves LIVE and SIMULATION\.
- Physical hazard footprint and operational policy buffer are separate concepts and separate visual layers\.
- Human safety signals such as SOS are handled as human\-priority inputs, not auto\-rejected hazard classifications\.
- NexAlert recommends; authorized humans approve operational actions and alerts\.
- Every critical action is auditable and returns server\-authoritative resulting state\.
- When the system is unsure, the UI must say so clearly and still show the operator what remains actionable\.

__END OF DOCUMENT 13__

