__NEXALERT__

__Native Mobile App Architecture & Functioning Specification__

__FINAL IMPLEMENTATION SPECIFICATION  •  V1 / SIH 2026__

__ROLE OF THE APP__  The mobile app is a citizen endpoint and continuity surface\. It does not become the source of truth, does not invent hazard decisions, and does not replace the offline NexAlert emergency portal\.

__DOCUMENT PURPOSE__

Define the optional native Android/iOS application that consumes the same canonical NexAlert events, alerts, safe\-location decisions, SOS workflow, identity model, maps and freshness semantics used by the web/PWA citizen experience\.

__Document__

__Status__

__Authority__

20 Native Mobile App

FINAL / OPTIONAL V1

Master Architecture \+ Citizen UI \+ Communication/Resilience \+ Security \+ Validation \+ Configuration

Primary audience

Software, AI, frontend/mobile, backend, SIH judges

Implementation reference

Normative rule

App is an endpoint, not a source of truth

All critical decisions remain backend/Master controlled

__Core principle: one hazard/event model, one trust model, one alert model, multiple citizen endpoints\.__

__DOCUMENT MAP__

- 1\. Product Boundary & Non\-Negotiables
- 2\. Platform Strategy: Android / iOS
- 3\. App Architecture & Runtime Modules
- 4\. Navigation & Information Architecture
- 5\. Emergency UX & Alert Lifecycle
- 6\. Identity, Contacts & Privacy
- 7\. Maps, Location & Safe\-Place Experience
- 8\. SOS & Citizen\-to\-Citizen Communication
- 9\. Notifications, Deep Links & Background Behavior
- 10\. Offline / Degraded / Recovery Behavior
- 11\. Security & Trust Model
- 12\. Backend/API Contracts & Caching
- 13\. Accessibility, Localization & Performance
- 14\. Telemetry, Diagnostics & Observability
- 15\. Development & Vibe\-Coding Workflow
- 16\. Validation & Acceptance Tests
- 17\. Release, Feature Flags & Rollback
- 18\. SIH Demonstration Flow
- 19\. Final Implementation Checklist

__RELATIONSHIP TO DOC 14__  This document implements the citizen surface defined in the Citizen Safety UI specification\. It does not create a second UX or second decision engine\.

__REFERENCE DOCUMENTS THAT GOVERN THIS DOC__

__Source__

__Use__

01 Master System Architecture & Invariants

Source\-of\-truth boundaries, state semantics, architecture invariants

04 Mathematical Intelligence & Hazard Reasoning

Hazard/event meaning; app must not reimplement scoring

11 Communication / Distributed Resilience

Offline, store\-forward, local emergency behavior

12 UI/UX Design System

Visual language, state semantics, accessibility

14 Citizen Safety UI & Functioning

Canonical citizen flow and content priorities

16 Security / Threat Model

Identity, signing, replay, local storage, trust

17 Validation / Acceptance

App evidence and test gates

19 Configuration Registry

Feature flags, thresholds, environment profiles

__1\. PRODUCT BOUNDARY & NON\-NEGOTIABLES__

__1\.1 What the native app is__

A native citizen application that provides push notifications, emergency viewing, live hazard context, location\-aware guidance, SOS, trusted\-contact messaging, cached incident state, account/contact management, and optional richer map/device integration\. The app is an endpoint to NexAlert services and may continue operating with cached information during partial outages\.

__1\.2 What the native app is not__

- Not the hazard reasoning engine\.
- Not the fire\-spread engine\.
- Not the authority command system\.
- Not an autonomous dispatch system\.
- Not a replacement for local offline Wi\-Fi emergency access\.
- Not a mechanism for waking a fully powered\-off phone\.
- Not a place to silently reinterpret severity, confidence or risk\.

__1\.3 Non\-negotiable invariants__

__Invariant__

__Required behavior__

Canonical event

Every notification, banner, emergency screen and history item points to one canonical event\_id\.

Truth hierarchy

Latest valid signed/authorized event \+ freshness metadata outrank stale local cache\.

Unknown stays unknown

The app never replaces missing/uncertain source data with fabricated precision\.

Backend decisions remain authoritative

Safe\-place ranking, hazard state, severity and operational risk are server/Master decisions\.

Offline is explicit

Cached or local content is labeled with age/freshness and information condition\.

SOS is additive

No hazard match is required to send SOS; duplicate taps are consolidated, not silently discarded\.

__2\. PLATFORM STRATEGY: ANDROID / IOS__

__2\.1 Recommended implementation approach__

Use one shared mobile codebase where practical, with a thin native capability layer for notifications, secure storage, background execution, location permissions, network status and platform\-specific system UI\. The app should preserve a high degree of visual and behavioral parity across Android and iOS\.

__Layer__

__Responsibility__

__Shared?__

UI

Emergency\-first screens, maps, status cards, navigation

Mostly shared

Domain

Event/state models, freshness, trust, SOS state machine

Yes

Data

API client, cache, sync, outbox, versioning

Yes

Secure storage

Keys/tokens/contact authorization

Native adapter

Notifications

Push token, actions, notification routing

Native adapter

Location

Permission flow, background policy, geofencing hooks

Native adapter

Maps

Provider SDK \+ rendering adapter

Native adapter where required

__2\.2 Platform differences must be treated as constraints, not hidden behavior__

- Push delivery is best\-effort; the app must fetch canonical event state after opening\.
- Background execution is constrained; do not depend on arbitrary periodic execution for life\-safety behavior\.
- Permission denial must degrade gracefully rather than blocking the rest of the app\.
- Notification actions must never be interpreted as proof that the citizen saw or acknowledged the alert unless the canonical backend event records that action\.

__V1 DECISION__  Favor robust foreground \+ push \+ cached emergency UX over ambitious background automation\. The emergency path must also remain available outside the native app through the web/PWA and local NexAlert portal\.

__3\. APP ARCHITECTURE & RUNTIME MODULES__

__Module__

__Key responsibilities__

__Critical states__

App Shell

Startup, session restore, route resolution, theme/localization

BOOTING / READY / DEGRADED

Emergency Center

Current hazard, freshness, action, safe place, map

NORMAL / WATCH / SUSPECTED / CONFIRMED / CRITICAL / RESOLVED

Alert Inbox

List/detail of alerts and acknowledgement actions

NEW / OPENED / ACKED / EXPIRED

Map Module

Hazard geometry, user location, safe places, SOS

LIVE / STALE / NO\-LOCATION

Safety Guidance

Safe place / shelter in place / route context

ROUTEABLE / NO\_SAFE\_ROUTE

SOS Module

Press\-and\-hold trigger, outbox, status, updates

DRAFT / QUEUED / SENT / DELIVERED / FAILED

Contacts

Authorized relationships and notifications

PENDING / VERIFIED / BLOCKED

Identity

User ID, phone verification, session state

SIGNED\_OUT / SIGNED\_IN / VERIFIED

Sync Engine

Fetch, cache, outbox, retry, dedup

ONLINE / OFFLINE / RETRYING

Trust Layer

Signature/event authenticity and replay checks

VERIFIED / INVALID / STALE

Settings

Notification, privacy, language, accessibility

CONFIGURED

Diagnostics

App version, sync age, notification token status

HEALTHY / DEGRADED

__3\.1 State ownership__

Server/Master owns hazard and incident truth\. The mobile app owns presentation state, local draft state, local cache metadata, delivery retries, and user preferences\. The app never mutates authoritative incident state merely because a screen was viewed locally\.

__4\. NAVIGATION & INFORMATION ARCHITECTURE__

__4\.1 Primary navigation__

__Destination__

__Purpose__

__Emergency priority__

Home / Emergency Center

Current hazard, action, status, map, safe place

Highest

Alerts

Recent and active alerts

Highest during active event

Map

Spatial context and hazard layers

High

SOS

Trigger, track, history

Always available

Contacts

Authorized people / organizations

Medium

History

Past incidents and alert outcomes

Low during emergencies

Settings

Notification, privacy, accessibility, language

Low during emergencies

__4\.2 Emergency routing rules__

- Open from push: resolve event\_id → fetch canonical event → render emergency detail, not a stale notification payload\-only screen\.
- Open from home during CRITICAL: route directly to Emergency Center first viewport\.
- Open while offline: show latest cached event with cache age and explicit stale/degraded badge\.
- Deep link without valid event: resolve to safe Home state and display a non\-blocking “information unavailable” status\.

__4\.3 Information hierarchy__

First viewport during emergency: hazard → severity/state → distance/direction → freshness → immediate action\. Secondary content: map → safe place → SOS/comms → active hazards → system status → collapsed technical details\.

__5\. EMERGENCY UX & ALERT LIFECYCLE__

__5\.1 Canonical event\-to\-screen flow__

__Stage__

__Backend/Master__

__Mobile app__

Detection

Incident candidate / evidence / confidence

No direct decision

Authorization

Alert issued under human\-approved policy

Receives signed/canonical event

Delivery

Push/Web/other channel

Displays notification if delivered

Open

Event fetched

Verifies freshness/trust; renders canonical state

Action

Citizen action may be recorded

Shows primary action \+ safe guidance

Resolution

Incident state becomes RESOLVED/stand\-down

Replaces emergency screen state; preserves audit history

__5\.2 Emergency detail screen contract__

__UI region__

__Required data__

Header

Hazard type, state, severity, freshness

Status card

Information Condition: GOOD / DEGRADED / UNKNOWN

Location context

Distance \+ compass direction \+ affected\-area context

Action

Explicit action phrase from authoritative guidance

Map

Current/warning/projection zones as applicable

Safe place

Ranked destination or SHELTER\_IN\_PLACE

SOS

Persistent press\-and\-hold control

Trust

Verified event badge / stale / unavailable indicator

__DO NOT__  Expose internal confidence/risk formulas as if they were probabilities\. Technical details can be available in an expandable “Why this alert?” panel only when useful\.

__6\. IDENTITY, CONTACTS & PRIVACY__

__6\.1 Identity model__

__Element__

__V1 behavior__

NexAlert User ID

Primary application identity\. Stable across sessions\.

Phone verification

Optional/required only for flows that need a verified phone contact\. OTP is handled by backend/identity service\.

Email / social sign\-in

Optional extension; must map back to NexAlert User ID\.

Device registration

One or more app installations linked to the user; each has push\-token lifecycle\.

Contact relationships

Private labels such as FAMILY / FRIEND / CAREGIVER; never used as public profile metadata\.

__6\.2 Consent and privacy rules__

- Location is requested only when a feature needs it; approximate/local context is acceptable when precise location is unnecessary\.
- Background location, contacts and notification permissions are separately consented\.
- Citizen location history is minimized and retained according to backend policy; UI should expose meaningful privacy controls\.
- SOS location may be transmitted as part of the emergency flow, with clear user feedback\.
- A citizen must never be able to browse another citizen’s location merely because they share an alert region\.

__6\.3 Contact authorization flow__

Request → pending → recipient accepts → relationship authorized → selected notification/SOS permissions enabled\. Revocation immediately stops future relationship\-based sharing; historical records remain subject to audit/retention policy\.

__7\. MAPS, LOCATION & SAFE\-PLACE EXPERIENCE__

__7\.1 Map layers__

__Layer__

__Mobile behavior__

User location

Show only with permission; accuracy indicator and stale\-location state\.

Hazard geometry

Current / warning / projection where supplied by authoritative event\.

Operational buffer

Visually distinct from physical hazard footprint\.

Safe locations

Ranked results with route context and capacity/availability metadata where available\.

SOS markers

Only authorized/appropriate visibility; never public\-by\-default\.

Offline cache

Last available map/hazard context; timestamp displayed prominently\.

__7\.2 Safe\-location rules__

The app requests a backend/Master\-ranked recommendation\. It does not independently choose the nearest facility\. Ranking may consider hazard exposure on route, travel time, destination exposure, capacity, accessibility and multi\-hazard conflicts\.

__Result__

__UI__

Viable safe place

“Go to \[place\]” with route and ETA context

Multiple options

Ranked cards with reason summary

Conflicting hazards

Warn that route/destination has another active hazard

No viable safe route

SHELTER\_IN\_PLACE with explicit safety guidance

Unknown destination data

Do not label as safe; mark availability/verification uncertainty

__8\. SOS & CITIZEN\-TO\-CITIZEN COMMUNICATION__

__8\.1 SOS interaction__

__Rule__

__Implementation__

Trigger

Press\-and\-hold or deliberate 3\-second action; avoid accidental activation\.

Duplicate taps

Consolidate rapid repeats; never silently erase a legitimate attempt\.

Hazard relation

No active hazard is required to submit SOS\.

Offline

Queue locally with timestamp and location if available; transmit on recovery\.

Status

QUEUED → SENT → RECEIVED/ACKNOWLEDGED where backend supports those states\.

Failure

Show explicit failed/unreachable state and preserve retry path\.

__8\.2 Citizen messaging__

Messaging remains opt\-in and authorization\-based\. Relationship\-scoped conversations may use cloud delivery online and a local emergency communication path when provisioned by NexAlert\. The mobile app must distinguish “sent to server,” “delivered,” and “seen” states; never infer delivery merely from local enqueue\.

__8\.3 Emergency contact escalation__

- User selects or preconfigures authorized contacts\.
- Emergency event/SOS creates a canonical action record\.
- Notification fan\-out uses backend rules, not mobile\-side guesses\.
- Contact privacy permissions are checked server\-side\.
- The app shows the current delivery status without exposing private routing internals\.

__9\. NOTIFICATIONS, DEEP LINKS & BACKGROUND BEHAVIOR__

__9\.1 Notification classes__

__Class__

__Purpose__

__Behavior__

CRITICAL hazard

Immediate action needed

High\-priority notification where platform policy permits; opening must resolve canonical event

WATCH / SUSPECTED

Attention / prepare

Standard alert; may deep\-link into event detail

UPDATE

Meaningful incident change

Replace/update prior alert where possible

STAND\-DOWN

Hazard resolved / no longer active

Explicit resolution notification

SYSTEM

Device/app issue

Never presented as hazard state

__9\.2 Payload rules__

Notification payload should be minimal: event\_id, event revision/version, hazard/state, severity presentation token, title/body summary, issued\_at, expiry and signature reference\. The app then fetches canonical details\. Sensitive location/contact information should not be embedded in a generic push payload\.

__9\.3 Deep\-link contract__

__Input__

__Result__

nexalert://event/\{event\_id\}

Resolve event, verify, open detail

nexalert://sos

Open SOS screen

nexalert://safe\-place/\{id\}

Resolve destination against current valid data

Expired/deleted event

Show event unavailable \+ route to current active alerts

Tampered/invalid link token

Reject action and log security diagnostic

__PLATFORM SAFETY__  Do not claim that notification delivery is guaranteed\. The authoritative record is the event state on the service; the app’s delivery state is observational\.

__10\. OFFLINE / DEGRADED / RECOVERY BEHAVIOR__

__10\.1 Three continuity surfaces__

__Condition__

__Primary citizen path__

Internet \+ app reachable

Native app \+ push \+ backend APIs

Internet degraded / backend reachable intermittently

Cached app \+ retry/outbox \+ explicit freshness

Internet unavailable but local NexAlert Wi\-Fi exists

Browser/PWA captive portal / local emergency page

App unavailable / not installed

Browser/PWA or local portal

Master unavailable but node\-local emergency path available

Local path remains available; app may be disconnected from authoritative cloud state

__10\.2 Local cache policy__

- Persist latest valid active event set, safe\-place snapshot, recent alerts, user profile essentials and app configuration needed for emergency viewing\.
- Store event revision and source timestamp with every cache entry\.
- Never silently present stale data as live\.
- Cache invalidation is version\-based; older revisions cannot overwrite newer ones\.
- Sensitive caches are encrypted using platform\-secure storage facilities where practical\.

__10\.3 Sync/recovery state machine__

OFFLINE → CONNECTING → AUTHENTICATING → SYNCING → RECONCILED → ONLINE\. On failure: backoff, retain outbox, preserve user\-visible cached state, and show Information Condition appropriately\. Replay protection and idempotency prevent duplicate SOS or action records\.

__11\. SECURITY & TRUST MODEL__

__11\.1 Threats__

__Threat__

__Mitigation__

Fake notification

Canonical event fetch \+ signature/trust verification

Replay of old alert

event revision \+ issued\_at/expiry \+ nonce/replay policy

Token theft

Short\-lived access token \+ secure storage \+ refresh/revocation policy

Local data extraction

Encrypted local storage; minimize cached sensitive data

Fake safe\-place link

Destination revalidated against trusted backend state

Account takeover

Strong authentication / OTP controls / session revocation

Notification spoofing

Do not treat notification body as source of truth

Rooted/jailbroken device

Degrade trust\-sensitive actions as configured; never rely on device state alone

__11\.2 Trust indicators__

__Indicator__

__Meaning__

Verified

Canonical event passed authenticity/freshness checks

Stale

Known event is older than freshness policy

Degraded

Some dependencies unavailable; displayed content may be partial

Unknown

The app cannot establish enough evidence to present a trustworthy current state

Unverified

Content cannot be authenticated; do not present as an official emergency instruction

__11\.3 Never hide security degradation__

A signed event is about authenticity, not probability or certainty\. The user interface must not convert “verified” into “guaranteed true in the physical world”; it indicates that the message came through the expected trust path and passed configured validation\.

__12\. BACKEND/API CONTRACTS & CACHING__

__12\.1 Required mobile\-facing resource families__

__Resource__

__Purpose__

GET /me

Identity \+ profile essentials

GET /events/active

Current canonical events

GET /events/\{id\}

Full event detail \+ revisions

GET /events/\{id\}/map

Hazard geometry \+ presentation metadata

GET /events/\{id\}/safe\-places

Ranked safe destinations / fallback

POST /sos

Create idempotent SOS

GET /sos/\{id\}

SOS status

GET /alerts

Alert inbox/history

POST /alerts/\{id\}/ack

Record acknowledgement

GET /contacts

Authorized contacts

POST /contacts/requests

Create relationship request

GET /sync?cursor=\.\.\.

Incremental reconciliation

POST /devices/register

Push/device registration

__12\.2 Idempotency__

All write actions that can be retried must accept a client\-generated idempotency key or equivalent deterministic request identity\. The mobile app stores pending operations in an outbox and marks them complete only after authoritative acknowledgement\.

__12\.3 Cache keys__

__Cache key__

__Version rule__

event:\{id\}

Keep latest event revision

events:active

Replace transactionally

safe\-places:\{event\_id\}

Replace with event revision

user:\{id\}

ETag/version based

alerts:\{cursor\}

Append/deduplicate by alert\_id

sos:\{id\}

Monotonic status transitions only

__13\. ACCESSIBILITY, LOCALIZATION & PERFORMANCE__

__13\.1 Accessibility__

- All critical actions are reachable without color alone\.
- Tap targets and spacing follow platform accessibility guidance and are tested on small screens\.
- Dynamic text sizing must not break the Emergency First Viewport\.
- Icons have text labels or semantic descriptions; maps have text alternatives for critical guidance\.
- Emergency alerts use concise, high\-contrast text and a distinct visual hierarchy\.

__13\.2 Localization__

__Concern__

__Rule__

Text

All user\-visible strings externalized; no hard\-coded emergency copy

Hazard names

Canonical hazard vocabulary translated from server\-provided codes

Directions

Locale\-aware units and compass words

Time

Localized format plus relative freshness when useful

Voice

Optional text\-to\-speech uses localized strings, never raw technical formulas

Fallback

If translation missing, use approved default language and log metric

__13\.3 Performance targets__

__Metric__

__Target__

Cold start to usable shell

<= 2\.5 s on representative supported device

Cached emergency screen

<= 1\.0 s after app process available

Push tap to emergency detail

<= 3 s when backend responds normally

Map first usable frame

<= 2\.5 s with cached tiles/data

SOS local enqueue

<= 500 ms

UI frame stability

No persistent jank during emergency scrolling/maps

Battery

No unnecessary high\-frequency background polling

__14\. TELEMETRY, DIAGNOSTICS & OBSERVABILITY__

__14\.1 App telemetry__

__Event__

__Purpose__

__Privacy rule__

app\_open

Usage baseline

No precise location

alert\_received

Delivery observation

Event\_id only

alert\_opened

UX confirmation

Event\_id \+ timestamp

event\_refresh\_failed

Operational quality

Error class; no secrets

sos\_queued/sent/failed

Reliability

SOS id \+ status

location\_permission\_changed

Feature capability

No location value

cache\_stale

Information\-condition UX

Event\_id \+ age bucket

deep\_link\_rejected

Security/diagnostic

Reason code only

__14\.2 Operational dashboards__

- Push\-to\-open latency distribution\.
- Event fetch failure rate by app version\.
- SOS enqueue/send/ack success rate\.
- Offline outbox age and replay/duplicate counts\.
- Map load failures and cache\-hit ratio\.
- Crash\-free sessions and emergency\-screen error rate\.
- Notification permission opt\-in and token invalidation rate\.

__14\.3 Privacy by design__

Diagnostics must be useful without becoming a shadow location\-tracking system\. Use event identifiers, coarse timing/age buckets and reason codes wherever full payloads are not required\.

__15\. DEVELOPMENT & VIBE\-CODING WORKFLOW__

__15\.1 Build vertical slices, not screens in isolation__

__Slice__

__Definition of done__

S1 App shell

Login/session, navigation, theme, localization

S2 Canonical event

Fetch → verify → render → refresh → stale state

S3 Push flow

Receive event\_id → deep\-link → canonical fetch

S4 Emergency map

Geometry \+ location \+ freshness \+ legend

S5 Safe\-place flow

Ranked response \+ route/no\-route fallback

S6 SOS

Outbox \+ idempotency \+ recovery

S7 Offline

Cached emergency state \+ explicit degraded condition

S8 Contacts

Authorization flow \+ privacy checks

S9 Hardening

Security, a11y, performance, crash/error handling

__15\.2 AI / vibe\-coding rules__

- Give the coding agent one bounded vertical slice and the contract it must satisfy\.
- Require tests for state transitions and API behavior before polishing UI\.
- Reject invented backend fields; the agent must use the canonical schema or explicitly mark placeholders\.
- Ask the agent to produce diffs plus a test report, not “trust me” summaries\.
- Use generated UI only after emergency states, offline behavior and accessibility are represented in tests\.
- Keep platform\-specific code behind adapters so generated changes do not leak into the shared domain layer\.

__PROMPT TEMPLATE__  “Implement only the mobile event\-detail slice\. Use canonical event\_id/revision/freshness/state fields\. Do not calculate hazard severity or safe\-place ranking\. Add offline stale\-state tests, accessibility labels, and a minimal diff summary\.”

__16\. VALIDATION & ACCEPTANCE TESTS__

__ID__

__Test__

__Pass condition__

APP\-001

Install \+ first launch

Usable shell within target; no fatal permission blocker

APP\-002

Canonical event rendering

Correct event revision and freshness shown

APP\-003

Tampered event

Rejected / unverified; no emergency instruction presented as trusted

APP\-004

Push deep link

Event opened from canonical fetch, not stale payload\-only content

APP\-005

Offline active alert

Latest valid cached alert shown with age/degraded indicator

APP\-006

Reconnect

Cache reconciles without older revision overwriting newer state

APP\-007

SOS duplicate taps

One logical request or safely consolidated retries

APP\-008

SOS offline

Queued locally; transmitted once on recovery

APP\-009

No safe route

SHELTER\_IN\_PLACE displayed

APP\-010

Permission denied

Core app remains usable with explicit feature degradation

APP\-011

Dynamic text

Emergency action remains readable at supported text sizes

APP\-012

Low bandwidth

Cached emergency path remains responsive

APP\-013

Crash/relaunch

Session \+ pending outbox recover safely

APP\-014

Notification token rotation

Backend device registration updates correctly

APP\-015

Cross\-platform parity

Core event/SOS state behavior matches across Android/iOS

__16\.1 Golden scenario set__

- Fire CONFIRMED → CRITICAL escalation → notification → emergency detail → safe place\.
- Flood WATCH → internet loss → cached state becomes stale → local NexAlert portal remains fallback\.
- Multi\-hazard fire \+ flood → app displays independent hazard cards; no combined fake scalar\.
- Master/backend unavailable → app reports degraded/unknown rather than inventing “all clear\.”
- SOS outside known hazards → request still queues and reaches authority workflow\.

__17\. RELEASE, FEATURE FLAGS & ROLLBACK__

__17\.1 Suggested mobile feature flags__

__Flag__

__Default V1__

__Notes__

native\_app\_enabled

true

Global app availability

critical\_push\_enabled

true

Emergency notification pathway

safe\_place\_ui\_enabled

true

Depends on backend ranking availability

citizen\_messaging\_enabled

false unless backend\-ready

Authorization \+ abuse controls required

background\_location\_enabled

false

Enable only after privacy/performance validation

voice\_guidance\_enabled

false

Optional accessibility enhancement

advanced\_map\_layers\_enabled

true

May degrade offline

diagnostics\_upload\_enabled

true

Privacy\-reviewed reason\-code telemetry

__17\.2 Release channels__

__Channel__

__Purpose__

Development

Local/device testing; synthetic endpoints only

Internal QA

Hardware/simulation integration; signed builds

Pilot

Controlled users / demo environment

SIH Demo

Frozen version \+ fixed backend/config snapshot

Production

Approved release after acceptance gates

__17\.3 Rollback__

Mobile releases cannot instantly recall a notification already delivered\. Therefore rollback focuses on preventing new bad behavior: disable feature flag, revoke endpoint/config if necessary, publish corrected app version, and keep canonical event state authoritative\. Never rely on app rollback to invalidate an already\-issued emergency event\.

__18\. SIH DEMONSTRATION FLOW__

__18\.1 Recommended 4–6 minute mobile story__

- 1\. Start with app on normal state and show live status/freshness\.
- 2\. Trigger a controlled fire scenario in Simulation through the same telemetry pipeline\.
- 3\. Master computes incident state; authority approves alert\.
- 4\. Push notification arrives on the phone with event\_id\.
- 5\. App opens canonical emergency detail: state, severity, distance, direction, freshness\.
- 6\. Show actual hazard geometry and safe\-place ranking\.
- 7\. Force internet loss\. App switches to cached/degraded state; show explicit information condition\.
- 8\. Demonstrate local NexAlert Wi\-Fi portal as the independent offline citizen path\.
- 9\. Trigger SOS; show queued/sent/recovery status\.
- 10\. Restore connectivity and show reconciliation with no duplicate actions\.

__18\.2 Judge\-facing proof points__

__Claim__

__Evidence__

Native app is not a second intelligence engine

Shared canonical event/API models \+ no mobile scoring code

Works during partial outage

Offline cache \+ stale indicator \+ recovery test

Trustworthy alerts

Signature/freshness verification test

Actionable guidance

Safe\-place backend contract \+ SHELTER\_IN\_PLACE fallback

Resilient SOS

Idempotent outbox \+ reconnect demo

Accessibility

Dynamic text \+ semantic labels \+ contrast test evidence

__19\. FINAL IMPLEMENTATION CHECKLIST__

- Canonical event/event\_id/revision model implemented and versioned\.
- Hazard state, severity, freshness and Information Condition are rendered exactly as defined by backend contracts\.
- Native app shares the same citizen design system as the PWA/offline portal\.
- Push opens canonical event fetch; notification payload is never the sole source of truth\.
- Offline cache stores source timestamp \+ event revision and exposes staleness\.
- SOS uses idempotent outbox with safe retry and duplicate consolidation\.
- Safe\-place ranking is backend/Master controlled; no “nearest = safest” mobile logic\.
- SHELTER\_IN\_PLACE is supported when no viable safe route is returned\.
- Security verification, replay protection and secure local storage are tested\.
- Permissions degrade gracefully; core emergency view remains accessible\.
- Localization and dynamic text are tested on emergency screens\.
- Crash/relaunch recovery preserves the outbox and latest valid cache\.
- Observability avoids unnecessary precise location collection\.
- Feature flags support controlled rollout and rapid disablement\.
- SIH demo build is frozen against a known backend/config snapshot\.
- Native app remains optional: citizen safety continues through PWA/local portal\.

__FINAL RULE__  The native app increases reach and usability; it must never reduce resilience\. When the app, internet, or cloud path fails, NexAlert still has the independent offline emergency path and must communicate honestly about information quality\.

