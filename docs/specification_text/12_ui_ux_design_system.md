__NEXALERT__

UI/UX Design System & Visual Language

Authority Dashboard \+ Citizen Safety UI \+ Offline Emergency Experience

*Implementation\-ready design contract for SIH 2026 prototype and scalable product architecture*

__Document__

12 — UI/UX Design System & Visual Language

__Status__

FINAL / LOCKED BASELINE

__Primary products__

Authority Dashboard, Citizen Safety UI, Offline Emergency Portal

__Design priorities__

Clarity, urgency, trust, accessibility, resilience, operational speed

__Source of truth__

Master Architecture \+ finalized subsystem specifications 01–11

__NON\-NEGOTIABLE UX RULE__

__The interface must make the system’s certainty, uncertainty, current state, and next action obvious\. It must never manufacture confidence through visual polish\.__

# 1\. Purpose and Design Contract

This document defines the visual language, information hierarchy, interaction model, component vocabulary, accessibility requirements, responsive behavior, offline behavior, and implementation mapping for NexAlert\. It is a design\-system contract rather than a mood board\. Frontend work must implement these rules consistently across authority and citizen surfaces\.

__Principle__

__Required behavior__

__Anti\-pattern__

Operational clarity

Show what is happening, how fresh it is, how trustworthy the evidence is, and what action is available\.

Decorative dashboards that hide decision\-critical information\.

Honest uncertainty

Use Information Condition GOOD / DEGRADED / UNKNOWN and confidence explanations where appropriate\.

Turning weak evidence into green/red certainty\.

Emergency first

Hazard, severity/state, distance/direction, freshness, and primary action lead the citizen emergency viewport\.

Making users scroll through analytics before seeing the action\.

Human authority

NexAlert recommends; authorized humans approve operational dispatch\.

UI that implies autonomous dispatch is already authorized\.

Resilience visible

Offline/local mode and stale data are explicit to the user\.

Pretending disconnected systems are live\.

Consistency

Same states, labels, icons, spacing, and semantics across pages\.

Each page inventing its own terminology\.

## 1\.1 Design hierarchy

- Level 1 — Immediate safety/decision: emergency state, critical alert, primary action, affected location\.
- Level 2 — Situation awareness: map, zone geometry, current/warning/projection, incidents, nodes, citizen SOS\.
- Level 3 — Evidence and diagnostics: telemetry, quality, reliability, contributing evidence, timestamps\.
- Level 4 — Investigation and history: simulation, historical comparisons, audit trail, detailed diagnostics\.

# 2\. Design Tokens

Tokens are the implementation vocabulary shared by both frontend applications\. Store tokens centrally and consume them through CSS variables/theme objects rather than hard\-coding values in individual pages\.

__Token family__

__Baseline__

__Usage__

Font family

UI: Aptos/Inter/system sans; monospace: platform monospace

Readable authority UI and data values\.

Base spacing

4 px unit; common steps 4/8/12/16/24/32/48

Layout, card padding, grid rhythm\.

Radius

6 px controls; 10 px cards; 14 px emergency surfaces

Avoid excessive pill\-shaped UI\.

Border

1 px neutral border

Separators and input boundaries; do not over\-box every element\.

Body text

14–16 px

Authority dense enough for operations but legible\.

Small/meta text

12 px minimum; 11 px only for secondary map labels

Timestamp, source, status metadata\.

Heading scale

28 / 22 / 17 / 14 px

Page title through section title\.

Touch target

44×44 px minimum

Citizen actions, SOS, map controls, navigation\.

Focus ring

2 px visible outline \+ offset

Keyboard and assistive navigation\.

Motion

150–220 ms micro; 300–450 ms mode transitions

No motion that delays emergency comprehension\.

## 2\.1 Color semantics

Color communicates state but is never the only carrier\. Every semantic color must have a label, icon, shape, texture, or text counterpart\. Avoid red\-versus\-green\-only meaning because of color\-vision deficiency and low\-contrast field conditions\.

__Semantic__

__Visual role__

__Required label/icon companion__

Neutral / baseline

Normal structure and stable information

Text label; no state implied\.

Blue

Network, infrastructure, informational field nodes, non\-threatening system status

Icon or explicit category label\.

Yellow / amber

WATCH, degraded/attention\-needed, projected/awareness contexts where applicable

State label such as WATCH / DEGRADED\.

Orange

SUSPECTED / elevated operational attention

State label and caution icon\.

Red

CRITICAL / immediate hazard

CRITICAL label \+ hazard icon \+ action\.

Green

Resolved/safe operational confirmation only when appropriate

RESOLVED / SAFE label; never used alone to imply low risk\.

Purple / accent

Simulation or analytical mode separation

SIMULATION badge / mode label\.

## 2\.2 Typography rules

- Use sentence case for labels and buttons\. Reserve ALL CAPS for compact state chips only\.
- Use tabular numerals for sensor values, times, and counters so columns visually align\.
- Do not use light font weights for decision\-critical text\. Keep essential labels at regular/medium weight\.
- Do not communicate meaning through color text alone on map overlays; pair with labels or patterns\.

# 3\. Core Component System

__Component__

__Purpose__

__Required states__

State chip

Compact incident/node/condition state

NORMAL, WATCH, SUSPECTED, CONFIRMED, CRITICAL, RESOLVED; plus GOOD/DEGRADED/UNKNOWN where relevant\.

Severity badge

Express severity independently from incident state

Low / Moderate / High / Extreme \(configured vocabulary only\)\.

Information Condition badge

Express evidence availability, not danger

GOOD / DEGRADED / UNKNOWN\.

Timestamp line

Make freshness visible

measurement time, received time, age, source\.

Evidence group

Explain why an incident state exists

Supporting sensors, core evidence coverage, agreement, temporal support, baseline readiness\.

Command card

Operational decision surface

State, condition, recommendation, approval control, timestamps, assigned actions\.

Incident row/card

Scanable incident summary

Hazard, state, severity, location, age, condition, last transition\.

Node card

Network and sensor health

Health, quality, reliability, link, battery/power, heartbeat, recent telemetry\.

Metric tile

Single analytical value

Value, unit, timestamp, trend only when meaningful\.

Action button

Primary operational action

Primary/secondary/destructive variants; explicit consequences\.

Map legend

Decode overlays

Zone type, state, time horizon, node class, uncertainty/context\.

Toast/banner

Transient or persistent system message

Success, warning, degraded, failure; emergency states use persistent banners or panels\.

Confirmation dialog

Protect high\-impact actions

Required for cancel/stand\-down/reset/delete and other irreversible actions; never block urgent alert acknowledgement unnecessarily\.

## 3\.1 Buttons and actions

__Action class__

__Examples__

__Interaction rule__

Primary

Acknowledge alert; Open incident; Get safe route

One visually dominant action per surface\.

Secondary

Explain; View details; Open telemetry

Must never visually compete with life\-safety action\.

Destructive

Cancel alert; Stand down; Delete simulation

Require explicit confirmation and show scope\.

Emergency

SOS; Shelter in place; Get help

Large target, persistent, accessible, available even when map/data fail\.

Mode switch

LIVE / SIMULATION

Prominent, mutually exclusive; always show current mode\.

# 4\. Layout and Navigation Architecture

The authority application uses a persistent navigation shell\. The citizen experience deliberately removes administrative complexity and uses a task\-first flow\. Both products share terminology and state semantics\.

__Authority shell area__

__Behavior__

Top bar

System identity, current mode, global freshness/connection status, operator identity, alerts/critical state indicator\.

Primary navigation

Overview, Incidents, Fire Spread, Affected Area & Impact, Multi\-Hazard & Simulation, Nodes & Network, Telemetry & Intelligence, Citizen SOS, Alert Management, Historical Analysis, Response & Actions, Audit Trail, System\.

Main workspace

Map/table/chart \+ side panel where context requires simultaneous situational awareness\.

Context side panel

Opens on node/incident/SOS selection without destroying map state; can pin for comparison\.

Bottom/utility region

Legend, time controls, scale, map status, data source/freshness\.

## 4\.1 Responsive behavior

__Viewport__

__Authority__

__Citizen__

Desktop

Full navigation, multi\-panel analytical layout\.

Single\-column emergency page or 2\-column safe\-place/map view\.

Tablet

Collapsible nav, prioritized map \+ command card; panels stack when necessary\.

Large touch controls; map/action card alternation\.

Mobile

Operational priority only; secondary analytics collapse\.

Emergency\-first; persistent SOS; cached local mode; no dense tables\.

Offline local AP

Minimal authority diagnostics only if exposed; prioritize local node state\.

Same emergency information architecture, served locally, no cloud dependency\.

# 5\. Map and Geospatial Visual Language

Maps are a primary operational canvas, not decoration\. The frontend renders authoritative geometries and layers generated by the backend/geospatial engine\. The frontend must not independently invent fire spread or risk geometry\.

__Layer__

__Visual treatment__

__Interaction__

Node

Blue field/slave nodes; yellow Master; icon identifies type\.

Click opens node side panel\.

Logical link

Dotted relationship line where useful\.

Toggleable; not confused with physical radio path\.

Current affected

Solid/filled hazard footprint with strong label\.

Click for incident context\.

Warning / awareness

Distinct lighter/hatched or contour treatment\.

Legend must explain time horizon\.

Projection

Clear future\-horizon overlay; never indistinguishable from current state\.

Time slider updates label/time horizon\.

Operational buffer

Separate visual treatment from physical hazard geometry\.

Legend explicitly says OPERATIONAL BUFFER\.

Continuous risk surface

Transparent heat/gradient overlay\.

Shows analytical risk index, not probability\.

SOS marker

High\-visibility person/help icon; category/tier on selection\.

Click opens SOS queue/profile/contact\.

Uncertainty/context

Pattern, opacity, or outline rather than color\-only\.

Explain source and meaning in legend\.

Population/exposure

Secondary overlay, only when relevant\.

Filterable to avoid map overload\.

## 5\.1 Fire Spread page

1. Place LIVE / SIMULATION toggle at the top of the page and repeat the mode in the map header\.
2. Show current footprint, projected spread, time slider, play/pause, reset, and environment context in one coherent control group\.
3. Expose wind direction and source/context as readable metadata, not as unexplained arrows\.
4. Separate affected population/infrastructure from physical hazard geometry\.
5. When environmental conditions change mid\-run, show a projection\-version or recalculation indicator rather than silently rewriting history\.

# 6\. Authority Dashboard Interaction Patterns

## 6\.1 Incident Command Card

Every active incident has a command card with a stable decision structure: hazard, state, severity, Information Condition, affected/current zone, evidence summary, latest transition, recommended action, human approval state, and freshness\.

__Card section__

__Required content__

Identity

Incident ID, hazard type, location/zone, created time, last state transition\.

State

Current state chip \+ severity badge; explicit INFORMATION CONDITION\.

Evidence

Core sensor/evidence groups, data freshness, baseline readiness, agreement summary\.

Recommendation

What NexAlert recommends and why; distinguish recommendation from authorization\.

Actions

Acknowledge, escalate, approve/issue alert, assign, stand down, open response plan according to permission\.

Audit context

Who approved/changed state, when, and from which source/version\.

## 6\.2 Explain affordance

The user\-facing label is “Explain” rather than “AI reasoning”\. The expansion is concise and operational: supporting evidence, counter\-evidence, missing/invalid inputs, stale sensors, core\-evidence coverage, and current confidence\. Do not expose raw equations to routine operators unless the diagnostic view explicitly requests them\.

## 6\.3 Alert\-fatigue awareness

The interface should expose alert frequency and repeated\-event context\. Repeated alerts for the same incident are grouped rather than presented as unrelated notifications\. Escalation history remains available\. Never suppress a critical alert merely because frequency is high\.

# 7\. Citizen Safety Experience

The citizen experience has two operating conditions: online and offline local Wi\-Fi/captive portal\. The information architecture stays the same so users do not need to relearn emergency semantics during network failure\.

## 7\.1 Emergency first viewport

__Priority__

__Element__

__Behavior__

1

Hazard \+ state \+ severity

Largest block; plain language; no ambiguous color\-only encoding\.

2

Distance \+ direction

Readable distance and cardinal/ordinal direction; geometry\-aware when relevant\.

3

Freshness

“Updated X ago” plus local/online source indicator\.

4

Primary action

Get to safety / view safe place / shelter in place / follow authority instruction\.

5

Map

Live or cached map with current/warning/projected zone distinction\.

6

SOS

Persistent, press\-and\-hold or 3\-second action depending implementation; available regardless of known hazard classification\.

7

Details

Expandable hazard explanation, affected areas, instructions, communication status\.

## 7\.2 Safe\-location presentation

- Show recommended destination and why it is recommended: estimated travel time, route hazard exposure, capacity/accessibility constraints when known\.
- Nearest is not automatically safest\. The UI should not label a location “safe” if the route or destination conflicts with active hazards\.
- When no viable route/destination is available, present SHELTER IN PLACE prominently\.
- Never fabricate route, capacity, or shelter status when information is stale or unavailable\.

## 7\.3 Citizen communication

Online notifications deep\-link to the one\-page emergency UI\. Offline users who join the NexAlert Wi\-Fi network receive the same emergency information from the local path\. The page must state whether content is live, cached, or stale\.

# 8\. Offline and Degraded UI States

__System condition__

__UI behavior__

LIVE \+ GOOD

Normal map/telemetry freshness; actions enabled according to permissions\.

LIVE \+ DEGRADED

Persistent DEGRADED badge; show stale sources and which capabilities are affected; do not silently hide missing telemetry\.

UNKNOWN information condition

Use UNKNOWN explicitly where assessment evidence is insufficient; do not convert to safe/normal\.

Internet unavailable, Master online locally

Authority/citizen local functions remain available according to architecture; show OFFLINE / LOCAL MODE\.

Master unavailable, field node local gateway available

Citizen emergency page remains available; show LOCAL NODE / LIMITED CONTEXT and timestamp\.

No current connection

Show cached data age; disable actions requiring unavailable backend capabilities; keep SOS/local safety action available\.

Recovery

Show synchronization/reconnection banner and refreshed timestamp; do not jump the screen unexpectedly\.

# 9\. Accessibility and Field Usability

__Requirement__

__Specification__

Color contrast

Meet accessible contrast targets for normal text, icons, and controls; never rely on red/green alone\.

Keyboard

Every interactive element reachable in logical order; visible focus state; map actions have non\-map alternatives\.

Screen reader

State, severity, freshness, and action order must be understandable without visual map interpretation\.

Motion

Respect reduced\-motion preference\. No flashing or rapid transitions for emergency cues\.

Touch

44×44 px minimum for citizen actions and compact authority controls where practical\.

Language

Text must be translatable; do not bake critical text into images or canvas layers\.

Field conditions

Support low bandwidth, glare, low battery, intermittent connectivity, and noisy outdoor environments\.

Map alternatives

Provide list/panel alternatives for nodes, incidents, safe places, and SOS results\.

## 9\.1 Emergency content writing

- Lead with the action, not the algorithm\.
- Use “Updated 35 seconds ago” instead of technical timestamps in the citizen layer unless details are expanded\.
- Use “Information is limited” or “Some sensors are stale” rather than hiding uncertainty\.
- Avoid “100% safe”, “guaranteed”, or probability\-like language for confidence/risk indices\.

# 10\. Interaction States, Loading, Errors and Empty States

__State__

__Visual pattern__

__Copy rule__

Loading

Skeleton/placeholder with stable layout; never full\-screen spinner for every interaction\.

Explain what is loading when meaningful\.

No data

Empty state with reason and next step\.

Differentiate “no incidents” from “data unavailable”\.

Stale data

Timestamp \+ stale badge; affected metric remains visible with caveat\.

Say what is stale and by how much\.

Permission denied

Inline explanation \+ request/access path\.

Do not imply system failure\.

Action failure

Persistent enough error \+ retry \+ scope of failure\.

Never report success unless backend confirms\.

Conflict

Explicit data disagreement state\.

Explain which sources disagree or are missing\.

Critical

Persistent high\-visibility panel/banner\.

Keep action visible until acknowledged or resolved by policy\.

# 11\. Data Visualization Rules

__Chart__

__Use__

__Rule__

Time series

Sensor trend, environmental context, baseline comparison\.

Show units, sampling/freshness, gaps, and source\.

Anomaly timeline

A\_i / anomaly events\.

Pair score with underlying signal; do not imply probability\.

Confidence bar/ring

C\_h evidence confidence\.

Label “confidence” and note it is not probability\.

Severity scale

S\_h operational severity\.

Use configured ordinal semantics; not a probability gauge\.

Risk surface

R\_h operational risk index\.

Legend must state operational index, not probability\.

Heatmap

Spatial concentration or hazard risk surface\.

Avoid red\-only gradients; provide legend and numerical ranges when useful\.

Network topology

Node links and partitions\.

Use line style/state to distinguish logical links, offline, stale, and healthy\.

## 11\.1 Numerical formatting

- Always show units beside physical measurements\.
- Use sensible precision: distance in metres/km as context dictates; environmental values use calibrated sensor precision\.
- Use explicit timestamp age and timezone when an exact timestamp is relevant\.
- Never display internal score precision beyond what supports a decision; avoid false precision such as 97\.283% confidence\.

# 12\. Frontend Implementation Contract

__Area__

__Implementation expectation__

Design tokens

Central token file/theme object consumed by dashboard and citizen apps\.

Component library

StateChip, SeverityBadge, InfoConditionBadge, Timestamp, EvidenceGroup, CommandCard, NodeCard, IncidentRow, AlertBanner, SOSButton, MapLegend, DataFreshnessIndicator\.

Map framework

One authoritative map layer stack for LIVE and SIMULATION; no separate decorative fire engine in frontend\.

State model

UI consumes canonical incident/node/alert state enums from backend contracts\.

Permissions

Action visibility and enabled state derived from authorization model; backend remains authority\.

Offline

Service\-worker/PWA cache only for approved assets/data; cache age shown to user; local portal uses same presentation contract\.

Telemetry

UI reads normalized telemetry/quality/anomaly/evidence payloads; no frontend recalculation of system\-of\-record decisions\.

Testing

Visual regression, accessibility tests, responsive tests, offline tests, stale\-data tests, permission tests, and emergency\-flow usability checks\.

## 12\.1 Suggested component tree

AppShell → TopBar → PrimaryNav → Workspace → MapCanvas \+ ContextPanel → CommandCard / IncidentPanel / NodePanel → DetailTabs → DataVisualization\. Citizen: EmergencyShell → StatusBanner → HazardSummary → PrimaryAction → MapCard → SafePlaceCard → SOS → DetailsAccordion\.

# 13\. Canonical User Flows

## 13\.1 Authority flow — new hazard evidence

1. Node/telemetry evidence arrives and freshness is updated\.
2. Backend updates anomaly/evidence/confidence/severity/state\.
3. Incident Command Card changes only through canonical incident state transitions\.
4. Operator opens Explain to review core evidence, counter\-evidence, and Information Condition\.
5. NexAlert presents a recommendation; authorized human approves alert/response action\.
6. Alert Management tracks issued/delivered/acknowledged/unreachable states\.
7. Response & Actions tracks assigned/en route/resolved lifecycle\.
8. Audit Trail records material transitions and approvals\.

## 13\.2 Citizen flow — online emergency

1. Notification opens emergency page\.
2. Hazard/state/severity/distance/direction/freshness appear immediately\.
3. User follows primary safe action or opens safe\-place details\.
4. Map distinguishes current/warning/projection and physical vs operational buffer\.
5. User can invoke SOS regardless of known hazard state\.
6. Resolved/stand\-down state remains explicit until closed\.

## 13\.3 Citizen flow — offline local portal

1. Citizen joins visible NexAlert Wi\-Fi network\.
2. Captive portal opens local emergency page\.
3. Page identifies LOCAL MODE and content age/source\.
4. User sees cached/current local incident data and safety action\.
5. If no viable route exists, SHELTER IN PLACE is presented\.
6. When connectivity recovers, UI shows synchronization/reconnection state\.

# 14\. UI/UX Acceptance Criteria

- Every critical incident surface shows state, severity, Information Condition, and freshness together\.
- Every map overlay has a legend and is not distinguishable solely by color\.
- LIVE and SIMULATION modes are visually unmistakable and share the same core map interaction model\.
- Fire current/warning/projection zones are visually distinct and linked to authoritative geometry\.
- Physical affected footprint and operational buffer have distinct labels and visual treatments\.
- Citizen emergency first viewport exposes hazard, severity/state, distance/direction, freshness, and primary action without scrolling\.
- SOS remains available even when no known hazard is active and is not auto\-rejected by hazard classification\.
- Offline/local mode is visibly identified; stale/cache age is explicit\.
- No UI text treats confidence or risk as probability\.
- No UI implies autonomous dispatch; operational authorization is visibly human\-controlled\.
- Master failure and internet failure present distinct user\-facing states\.
- No empty state conflates “no incidents” with “data unavailable”\.
- Critical actions are keyboard/touch accessible and have non\-color labels\.
- Visual regression passes at desktop, tablet, mobile, and local captive\-portal dimensions\.
- Accessibility audit and emergency\-flow usability test pass before SIH demo freeze\.

# 15\. Design Token / State Registry Starter

__Key__

__Value / allowed set__

incident\.state

NORMAL | WATCH | SUSPECTED | CONFIRMED | CRITICAL | RESOLVED

information\.condition

GOOD | DEGRADED | UNKNOWN

operation\.mode

LIVE | SIMULATION

ui\.dataFreshness

LIVE | RECENT | STALE | UNKNOWN

hazard\.type

FIRE | FLOOD | POLLUTION | LANDSLIDE | EXTREME\_HEAT | UNKNOWN | future configured types

zone\.kind

CURRENT | WARNING | AWARENESS | PROJECTION | OPERATIONAL\_BUFFER

sos\.priority

IMMEDIATE | HIGH | STANDARD | VERIFY

safePlace\.fallback

SHELTER\_IN\_PLACE

node\.role

MASTER | FIELD\_NODE

visual\.language

Shape \+ label \+ icon \+ color; never color alone

# 16\. Final UX Guardrails

- The visual system is part of the safety architecture: misleading polish is a defect, not a cosmetic issue\.
- Information Condition is the explicit command\-surface answer to “can we trust what we know right now?”
- Confidence, severity, and operational risk are presented as distinct concepts\.
- Fire spread visuals are generated from actual geospatial simulation output; the frontend never animates a fake expanding circle as system truth\.
- Offline UI is not a degraded imitation of the cloud UI; it is the same core emergency contract with an explicit local\-information state\.
- Every high\-impact action exposes who/what approved it and when\.
- For SIH demonstration, the polished UI must show the architecture honestly: real telemetry path, real incident state, real map geometry, real stale/failure behavior, and visible resilience\.

# 17\. Document Closeout

This design\-system specification is the authoritative UI/UX baseline for NexAlert implementation\. Any deviation that changes the meaning of state, confidence, risk, safety action, offline behavior, or operational authorization requires explicit architecture review and must be reflected in the relevant source specification before frontend freeze\.

