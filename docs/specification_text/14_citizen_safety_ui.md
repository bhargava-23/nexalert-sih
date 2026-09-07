NEXALERT

Citizen Safety UI & Functioning

Online Web Push \+ Local Wi\-Fi Captive Portal \+ PWA/Browser Experience

Implementation\-ready citizen experience contract for the SIH 2026 prototype and scalable disaster\-response architecture

__NON\-NEGOTIABLE CITIZEN UX RULE  
__When a person may be in danger, the interface must answer five questions before anything else: What is happening? Where is it? How serious is it? How fresh is this information? What should I do now?

Authority: NexAlert Master System Architecture, Technical Requirements, Communication/Resilience, UI/UX Design System, Incident/Response operations, and Fire/Geospatial specifications\.

Document status: FINAL implementation baseline\. UI labels may be localized, but the information hierarchy, safety semantics, and state transitions are normative\.

# 1\. Purpose and Citizen Product Contract

The Citizen UI is the public\-facing safety endpoint of NexAlert\. It is intentionally simpler than the authority dashboard: it exposes verified, actionable emergency information without requiring the citizen to understand anomaly scores, evidence weights, sensor reliability, or operational indexes\.

## 1\.1 Primary goals

- Provide the fastest useful answer during an emergency, especially on a stressed mobile network or low\-end phone\.
- Work online when cloud delivery is available and locally when a citizen joins the NexAlert Wi\-Fi network\.
- Use one canonical emergency event so online and offline experiences never disagree on the core message\.
- Clearly communicate freshness, uncertainty, and stand\-down/resolution rather than implying certainty the system does not have\.
- Provide a path to safety, a persistent SOS action, and clear contact/communication options without turning the product into a social network\.

## 1\.2 Out of scope for the citizen surface

- Raw telemetry charts, per\-sensor health calculations, model internals, evidence equations, or unexplained confidence numbers\.
- Autonomous emergency dispatch claims\. NexAlert recommends actions; authorized human response workflows remain distinct\.
- Promises that a phone can receive an alert while fully powered off or without any local/online connectivity path\.
- Automatic exposure to another citizen's private relationship data, contact graph, or identity details\.

# 2\. User Modes and Delivery Paths

__Mode__

__Trigger__

__Source of truth__

__Expected behavior__

NORMAL

No active emergency for user location

Current public system state

Calm status view; hazards/history may be visible but do not dominate\.

EMERGENCY

Active hazard intersects or is relevant to permitted user location

Canonical alert event

Emergency first viewport; immediate action and safety context appear before navigation\.

DEGRADED

Connectivity or backend freshness is impaired

Last trusted event \+ local cache

Show stale/freshness state explicitly; avoid presenting old data as live\.

OFFLINE LOCAL

Citizen joins NexAlert Wi\-Fi/captive portal

Local Master/node cache

Serve same canonical safety UI locally, with clear local\-data freshness\.

RESOLVED

Incident stand\-down/resolution received

Canonical incident state

Show resolution clearly; retain useful post\-incident guidance and timestamp\.

## 2\.1 Delivery channels

__Channel__

__Role__

__Prototype requirement__

Web Push

Fast online attention for previously permitted/subscribed users

Implement where browser/platform support exists; event links open one\-page emergency UI\.

Mobile web / PWA

Primary experience

Responsive web app; installation optional except where browser platform requires it for push\.

NexAlert Wi\-Fi AP

Offline/local emergency access

Captive portal or local landing page; no internet dependency for core emergency view\.

Native mobile app

Optional future endpoint

Same event contract, same UI semantics; not a separate source of truth\.

Cell Broadcast / SACHET / satellite

Future authorized integrations

Not required for V1 prototype; must converge on canonical event IDs where integrated\.

# 3\. Emergency First Viewport

The first screen is designed for stress and glance reading\. It should remain useful when the user has poor attention, low bandwidth, or limited time\.

## 3\.1 Required information order

1. Hazard name and plain\-language summary\.
2. Severity and state \(for example WATCH, SUSPECTED, CONFIRMED, CRITICAL\)\.
3. Current relevance: distance, direction, and affected/at\-risk relation where available\.
4. Freshness: measured or updated time plus explicit LIVE / RECENT / STALE / UNKNOWN semantics\.
5. Primary action: EVACUATE, MOVE TO SAFE AREA, SHELTER IN PLACE, AVOID AREA, or MONITOR for lower urgency\.
6. Secondary actions: View live map, Safe places, SOS, Communication, Details\.

## 3\.2 Example emergency card

__Element__

__Example__

__Implementation rule__

Headline

FOREST FIRE ALERT

Use plain language; no internal incident ID\.

State

CRITICAL \- CONFIRMED

State chip \+ icon \+ text; never color alone\.

Context

Fire detected ~2\.4 km SW

Distance uses Haversine; direction uses bearing/cardinal bucket\.

Freshness

Updated 14:22:10 IST \- 18 s ago

Show elapsed time when active, absolute timestamp in details\.

Action

EVACUATE TOWARD NORTH

Action comes from current safe\-direction/routing result when available\.

Fallback

SHELTER IN PLACE

Use when no viable safe route/destination is available\.

Trust

Verified NexAlert alert

Signature verification/replay protection may surface as a trust badge\.

__Safety rule  
__Do not hide an emergency behind a splash screen, onboarding flow, login requirement, or multi\-step navigation\. A public emergency page must render useful content before secondary assets finish loading\.

# 4\. Hazard State Semantics

__State__

__Citizen meaning__

__Permitted tone__

__Required behavior__

NORMAL

No active hazard relevant to the user

Calm

No emergency banner\.

WATCH

Conditions merit attention but emergency is not established

Caution

Explain what changed and what to monitor\.

SUSPECTED

Evidence suggests a possible event; confirmation is pending

Caution \+ uncertainty

Do not present as confirmed\. Show why attention is recommended\.

CONFIRMED

Hazard declaration meets configured evidence requirements

Urgent

Show action and current affected area\.

CRITICAL

Immediate or severe operational consequence

Emergency

Prioritize action, safe destination, SOS, and freshness\.

RESOLVED

Incident is no longer active under current event state

Stand\-down

Explicitly tell user that the prior warning is resolved; retain time/context\.

## 4\.1 Unknown / insufficient\-information state

When the system cannot establish adequate evidence or freshness, the citizen UI must not fabricate a confidence percentage\. It should say that information is limited, show the last trusted timestamp, and provide the safest applicable instruction such as avoiding the area or sheltering until further information is available\.

# 5\. Freshness, Uncertainty and Trust Language

Citizen\-facing trust is based on honest communication\. The UI distinguishes event certainty from data freshness and from operational severity\. These are different concepts\.

__Condition__

__UI label__

__Example microcopy__

Fresh and current

LIVE

Updated 14:22:10 \- data current\.

Recent but not streaming

RECENT

Last trusted update 45 s ago\.

Stale

STALE

Information may no longer reflect current conditions\.

Unknown freshness

UNKNOWN

Current conditions could not be verified\.

Verified event authenticity

VERIFIED

This alert passed NexAlert integrity checks\.

Limited evidence

INFORMATION DEGRADED

NexAlert has limited sensor/network evidence right now\.

# 6\. Citizen Navigation Structure

Navigation remains shallow\. During an emergency, the primary route is a single safety page with secondary panels rather than a deep app tree\.

__Surface__

__Purpose__

__Emergency priority__

Home / Safety

Current state and most important action

P0

Live Map

Current, warning, projection and user context

P0

Safe Places

Ranked destinations / shelter options

P0

Alerts

Current \+ recent alert history for the user

P1

SOS

Emergency request and status

P0

Communications

Authorized contacts / status information

P1

Details

Expanded evidence, timestamps, methodology summary

P2

Settings

Location permission, notifications, language, accessibility

P2

## 6\.1 Persistent actions

- SOS remains visibly accessible in emergency mode and is never auto\-rejected solely because no known hazard currently covers the user\.
- Language and accessibility controls remain reachable without closing an active alert\.
- Back navigation never discards an active safety state; emergency banners persist until resolved/expired by canonical event policy\.

# 7\. Live Map Experience

The citizen map is a safety map, not an engineering map\. It displays only the information needed for orientation and action\.

## 7\.1 Required layers

- User location when permission is granted and location confidence is acceptable\.
- Current affected/physical footprint where available\.
- Warning and projection zones with distinct labels/styles\.
- Operational buffer shown separately from the physical hazard geometry\.
- Safe places and relevant infrastructure where exposure/availability data exists\.
- Active incident marker and directional indicator relative to the user\.

## 7\.2 Map semantics

__Layer__

__Meaning__

__Citizen treatment__

Current / affected

Area already impacted or inside current footprint

Highest visual priority; label clearly\.

Warning

Expected near\-term arrival zone

Use distinct pattern/opacity from current footprint\.

Projection

Longer\-horizon potential spread

Do not imply certainty; pair with time window\.

Operational buffer

Policy safety margin around physical footprint

Label as operational safety buffer, not physical hazard\.

Safe place

Candidate destination

Show availability/capacity status when known\.

SOS markers

Reported citizen requests

Only show aggregate/privacy\-safe information to other citizens\.

# 8\. Distance, Direction and Geospatial Context

The UI derives distance from the citizen location and hazard geometry/incident point using geodesic distance appropriate to the product\. Direction is expressed as human\-readable sectors such as N, NE, E, SE, S, SW, W, NW rather than raw bearing degrees\.

- For irregular hazard polygons, distance is based on the nearest relevant geometry rather than only the incident centroid\.
- When location permission is absent, remove misleading personalized distance/direction text and present the affected area on the map\.
- If GPS accuracy is poor, say so\. Do not display false precision such as "2\.37 km" when the location uncertainty is large\.
- Projected spread must display its forecast horizon/time context\. A projection is not the same as the current footprint\.

# 9\. Safe\-Location Recommendation UI

Safe\-location ranking is performed by the backend/Master, not by the frontend\. The citizen UI explains a ranked destination without pretending that the nearest location is automatically the safest\.

## 9\.1 Candidate card fields

__Field__

__Purpose__

Place name/type

Identify destination: shelter, school, public building, etc\.

Status

Open / limited / full / unknown

Distance \+ travel estimate

Orientation; route\-aware when possible

Hazard exposure

Whether route or destination intersects current/warning/projected hazards

Accessibility

Accessible entrance/route where known

Reason

Plain\-language explanation of why it is recommended

Last updated

Freshness of capacity/location information

Primary action

NAVIGATE / VIEW DETAILS / CALL AUTHORITY

## 9\.2 Fallback behavior

__No viable safe route  
__Show SHELTER IN PLACE prominently\. Do not force the user toward a destination merely because it is geographically close\. Explain that safe\-route information is unavailable or conflicted and provide the safest configured immediate instruction\.

# 10\. SOS Experience

SOS is an emergency request channel, not an AI hazard detector\. A citizen may need help even when NexAlert has no confirmed hazard\.

## 10\.1 Interaction

1. User presses and holds SOS for approximately 3 seconds to reduce accidental activation\.
2. UI shows confirmation countdown and clear cancellation affordance\.
3. Upon activation, create a unique SOS event with user/session identifier, timestamp, and last known location when permitted\.
4. Route the SOS through the strongest available channel and show delivery state: QUEUED, SENT, ACKNOWLEDGED, UNREACHABLE, or RESOLVED\.
5. Consolidate repeated taps/presses into the active request while retaining event history; never silently discard a legitimate SOS\.
6. Provide a clear emergency\-contact or authority escalation path when configured\.

## 10\.2 Privacy behavior

- Display only the user's own SOS status to the citizen unless explicit sharing is configured\.
- Citizen\-to\-citizen contact requires explicit contact authorization; relationship labels are private metadata\.
- Location history is not exposed merely because a user sent an SOS\.

# 11\. Offline Local Emergency Portal

The local portal is the citizen\-facing resilience path when internet/cloud delivery is unavailable\. A citizen joins the distinctive NexAlert Wi\-Fi network and reaches the same emergency information model through a captive portal/local URL\.

## 11\.1 Offline flow

1. Citizen sees NexAlert SSID in available Wi\-Fi networks\.
2. Citizen joins the network; device receives local connectivity parameters\.
3. Captive portal or local landing route opens the Emergency Safety page\.
4. UI loads the latest locally verified canonical event/cache\.
5. Freshness banner identifies that the page is operating through a local/offline path\.
6. SOS and local communication actions use the channels available in that deployment; unavailable cloud actions are explicitly labeled\.

## 11\.2 Offline trust

- Offline UI must not invent internet connectivity\. Show LOCAL / OFFLINE status plainly\.
- Cached event data must retain timestamps and validity/expiry rules\.
- Only locally stored, verified event content may be presented as canonical emergency data\.
- Spoofed SSIDs cannot be prevented purely by the UI; authenticity is established through signed event/content verification where supported\.

# 12\. Online Web Push Experience

Web Push is an attention mechanism, not the full emergency interface\. Notification text is concise and links into the canonical emergency page\.

__Stage__

__UI behavior__

Permission

Explain why notifications matter before the browser permission prompt; never repeatedly nag\.

Delivery

Use hazard \+ state \+ action in concise notification text\.

Open

Deep\-link to the emergency event page, preserving event ID\.

Offline/open failure

Show last cached event when possible and make freshness explicit\.

Stand\-down

Send resolution/stand\-down where supported so users do not retain obsolete alarm state\.

## 12\.1 Notification examples

- FOREST FIRE \- CRITICAL: Evacuate away from the affected area\. Updated 14:22\.
- FLOOD WATCH: Water levels rising near your area\. Check safe locations and updates\.
- ALERT RESOLVED: The earlier fire warning is no longer active as of 15:07\.

# 13\. Accessibility and Stress\-Resilient Interaction

- Use large touch targets, readable typography, strong contrast, and generous spacing on emergency actions\.
- Never rely on red/green alone: pair state colors with labels, icons, shape, and text\.
- Support screen readers with semantic landmarks, live\-region announcements for state changes, and descriptive map alternatives\.
- Provide a text\-only safety summary when map tiles fail or bandwidth is poor\.
- Keep critical actions accessible with one hand on common mobile viewports\.
- Use plain language and avoid abbreviations unless they are widely understood or expanded on first use\.
- Localization must preserve action meaning and urgency ordering; translated text must not push the primary action below the fold where avoidable\.

# 14\. Network Failure and Degraded\-State UX

__Failure__

__What user sees__

__Allowed actions__

Cloud unavailable

LOCAL/OFFLINE or CONNECTION DEGRADED banner

View last trusted local event; join NexAlert Wi\-Fi if available\.

Push unavailable

No silent claim that alert was delivered

Open web app manually; cached event remains available if present\.

Map tiles unavailable

Text safety summary \+ simplified local geometry

Read action/distance/freshness; retry map\.

Location unavailable

Generic affected\-area view

Choose safe place manually; show no fake personalized distance\.

Safe\-place data stale

STORAGE/DESTINATION DATA STALE

Avoid strong availability claims; use fallback instruction\.

Backend uncertainty

INFORMATION DEGRADED / UNKNOWN

Follow conservative configured safety instruction; await update\.

# 15\. Security, Authenticity and Session Rules

The citizen application consumes canonical alert events and must treat event identity, signature status, freshness, and authorization as first\-class fields\.

## 15\.1 Event contract expectations

__Field__

__Use__

event\_id

Deduplication and deep\-linking

incident\_id

Connect the alert to the authoritative incident

hazard\_type

Fire/flood/pollution/etc\.

state

NORMAL/WATCH/SUSPECTED/CONFIRMED/CRITICAL/RESOLVED

issued\_at / updated\_at

Freshness and ordering

target\_geometry / target\_rule

Determine relevance

action

Primary citizen instruction

severity\_label

Human\-readable urgency

information\_condition

GOOD/DEGRADED/UNKNOWN

signature\_status

Verified/unverified/rejected

expiry / standdown

Prevent obsolete emergency state

schema\_version

Client compatibility

## 15\.2 Client rules

- Reject or clearly quarantine malformed/invalid events; never silently render them as trusted emergency content\.
- Protect against replay using event ID, timestamp/expiry, and deployment\-appropriate verification\.
- Keep the app idempotent: opening the same event repeatedly must not create duplicate citizen\-side emergency state\.
- Never expose internal authentication secrets, per\-node credentials, or privileged operator endpoints to the browser\.

# 16\. Citizen Information Architecture by Screen

__Screen__

__Primary content__

__Secondary content__

__Key action__

Emergency Home

Hazard, severity/state, freshness, action, distance/direction

Map preview, safe place preview, SOS

Take action

Full Map

Current/warning/projection, user, safe places

Legend, freshness, incident details

Navigate / view area

Safe Places

Ranked destinations \+ status

Route context, reason, accessibility

Navigate

SOS

Activation, status, timestamp, location

Contact/escalation details

Send / update SOS

Alerts

Active \+ recent user\-relevant alerts

Resolution history, details

Open alert

Details

Plain\-language evidence summary, timestamps, methodology note

Raw\-ish detail only where appropriate

Close / return to action

Offline Portal

Local emergency event \+ freshness

Network state, retry instructions

Follow local action

# 17\. Frontend State Machine

The frontend must derive view state from the canonical event and connectivity state, not from ad hoc component\-level flags\.

__State__

__Entry__

__Exit__

__UI effect__

IDLE

No relevant event

Relevant event arrives

Normal Home

ALERT\_PRESENT

Relevant event accepted

Stand\-down/expiry

Emergency banner/card

ACTION\_REQUIRED

Event severity/action policy requires response

User views action or event resolves

Primary action pinned

DEGRADED

Freshness/connectivity below threshold

Fresh trusted data arrives

Degraded banner \+ stale labeling

OFFLINE\_LOCAL

Local network detected

Connectivity returns / user leaves

Local data \+ offline banner

RESOLVED

Canonical event resolved

New relevant event

Stand\-down confirmation

## 17\.1 Ordering rules

1. Latest valid canonical event wins within the same incident/event lineage\.
2. A newer lower\-severity update must not hide a still\-active higher\-severity event unless canonical incident policy explicitly resolves/downgrades it\.
3. Network status never silently overwrites hazard state\.
4. Stale data changes presentation trust/freshness; it does not automatically change the underlying hazard state\.

# 18\. API / Event Integration Surface

The frontend should consume narrow read models rather than direct database tables\. The contract below is conceptual and must map to Document 07 backend/API specification\.

__Endpoint/read model__

__Purpose__

__Minimum fields__

GET /citizen/alerts/current

Current relevant citizen events

event\_id, incident\_id, hazard, state, severity, action, freshness, geometry summary

GET /citizen/alerts/\{event\_id\}

Detailed emergency page

canonical event \+ evidence summary \+ safe context

GET /citizen/map

Citizen\-safe geospatial layers

current/warning/projection/buffer, safe places, user context

GET /citizen/safe\-places

Ranked destinations

place, rank, status, distance, route safety, reason, updated\_at

POST /citizen/sos

Create/update SOS

sos\_id, received\_at, delivery\_state

GET /citizen/sos/\{sos\_id\}

SOS status

state, timestamps, acknowledgment, escalation

GET /citizen/config

UI/configuration

language, branding, feature flags, deployment mode

# 19\. Performance and Reliability Targets

__Metric__

__Prototype target__

__Notes__

Emergency first content

< 2 s on local network / cached path

Do not wait for map tiles to show hazard/action\.

Local portal bootstrap

< 3 s on Raspberry Pi\-class local gateway

Depends on Wi\-Fi association and client device\.

UI event application

< 250 ms after event receipt

Avoid full page reloads for updates\.

Offline page availability

Independent of internet

Core event/action content must remain locally servable\.

Notification deep\-link

< 2 taps to emergency content

Notification itself is not the entire safety message\.

Low\-bandwidth mode

Text\-first rendering

Map/image assets may load later or be omitted\.

# 20\. Testing and Acceptance Matrix

__ID__

__Scenario__

__Expected result__

CIT\-01

Confirmed fire intersects user area

Emergency first viewport shows fire, CRITICAL/CONFIRMED state, freshness, action, map\.

CIT\-02

Suspected fire with limited evidence

UI says SUSPECTED / INFORMATION DEGRADED; no fake probability\.

CIT\-03

Active warning but user outside affected zone

Shows relevance/distance and warning context without claiming user is inside current footprint\.

CIT\-04

Projected fire approaches in 30 min

Projection labeled with horizon; no claim that projection is current impact\.

CIT\-05

Operational buffer surrounds physical footprint

Both are distinguishable in legend and text\.

CIT\-06

No viable safe route

SHELTER IN PLACE shown as primary fallback\.

CIT\-07

User sends SOS with no known hazard

SOS is accepted/queued; no auto\-rejection\.

CIT\-08

Cloud unavailable, Master/local path available

Citizen can join NexAlert Wi\-Fi and see locally cached trusted event\.

CIT\-09

Event data becomes stale

STALE/UNKNOWN state appears; emergency content is not silently presented as live\.

CIT\-10

Duplicate event notification arrives

Client deduplicates by event/incident identity\.

CIT\-11

Stand\-down received

UI clearly marks incident resolved and removes emergency action dominance\.

CIT\-12

Map tiles fail

Text safety summary and primary action remain usable\.

CIT\-13

Location permission denied

No fake personalized distance/direction; general map remains functional\.

CIT\-14

Screen reader enabled

All critical information and actions are announced/read in meaningful order\.

CIT\-15

Spoofed/invalid event signature

Event is rejected/quarantined and not shown as verified emergency content\.

# 21\. Demo\-Critical Citizen Flows

## 21\.1 Online emergency demo

1. Citizen has previously permitted location/notification access\.
2. Fire incident becomes CONFIRMED/CRITICAL for target geography\.
3. Web Push arrives with concise action text\.
4. Citizen opens the deep link\.
5. First viewport shows fire \+ severity \+ freshness \+ direction/distance \+ EVACUATE action\.
6. Live map shows current/warning/projection geometry and operational buffer distinctly\.
7. Safe Places returns a ranked destination with explanation\.
8. Citizen can press\-and\-hold SOS and view queued/sent state\.

## 21\.2 Offline resilience demo

1. Disable internet/cloud path while keeping local NexAlert network available\.
2. Citizen joins NexAlert Wi\-Fi SSID\.
3. Captive portal opens the emergency page\.
4. Local event loads with LOCAL/OFFLINE banner and timestamp\.
5. Core action and map context remain usable without internet\.
6. Cloud connectivity restoration reconciles state without duplicate alerts\.

# 22\. Implementation Rules for Vibe\-Coding / Frontend Agents

- Build the citizen app from typed domain models and the canonical event schema; never scatter hazard state logic across visual components\.
- Create reusable SafetyBanner, EmergencyCard, FreshnessBadge, HazardLegend, SafePlaceCard, SOSControl, ConnectivityBanner, and EvidenceSummary components\.
- Centralize design tokens from Document 12\. Do not invent per\-screen emergency colors or typography\.
- Keep geospatial rendering replaceable: map provider is an implementation detail; domain geometry/state must remain provider\-neutral\.
- Use mocked canonical events in development, but route simulation and hardware telemetry through the same production\-shaped API contracts\.
- Keep online and offline adapters separate from shared rendering components so the same emergency UI can run against cloud or local data sources\.
- Write deterministic UI tests for every citizen acceptance case in Section 20 before visual polish is considered complete\.

# 23\. Final Citizen UX Invariants

1. EMERGENCY FIRST: safety information appears before secondary content\.
2. ONE CANONICAL EVENT: online, offline, simulation, and hardware experiences consume the same event semantics\.
3. HONEST FRESHNESS: every safety\-critical view tells the citizen how current the information is\.
4. NO FAKE CERTAINTY: confidence is never invented or shown as probability unless explicitly justified by an approved model\.
5. CURRENT \!= WARNING \!= PROJECTION: physical/current, near\-term warning, and future projection remain visually and textually distinct\.
6. PHYSICAL \!= OPERATIONAL BUFFER: policy safety margin is clearly labeled separately from hazard physics\.
7. SOS IS NOT HAZARD\-DEPENDENT: a citizen may request help even when NexAlert has not confirmed a hazard\.
8. NO ROUTE, NO FALSE PROMISE: when safe routing cannot establish a viable destination, use SHELTER IN PLACE\.
9. OFFLINE SURVIVAL: core emergency information can be served locally without internet when the local deployment supports it\.
10. HUMAN ACTION REMAINS HUMAN: NexAlert communicates and recommends; it does not claim autonomous emergency dispatch authority\.
11. PRIVACY BY DEFAULT: another citizen cannot see private relationships, detailed identity information, or location history without explicit authorization\.
12. ACCESSIBLE UNDER STRESS: critical meaning is never encoded by color alone and remains usable under poor network, poor vision, or screen\-reader conditions\.

