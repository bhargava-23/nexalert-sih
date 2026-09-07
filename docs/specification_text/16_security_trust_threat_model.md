__NEXALERT__

__Security, Trust & Threat Model__

__FINAL IMPLEMENTATION SPECIFICATION  •  V1 / SIH 2026__

__Core principle  __Security must preserve truthful hazard information, not merely protect a login\. NexAlert must authenticate who produced data, prove which event is being presented, reject stale or replayed messages, limit authority, and remain honest under attack or partition\.

__Document ID:__

NEX\-16\-SEC\-TRUST

__Status:__

FINAL / Implementation\-ready

__Authority:__

Master Architecture \+ TRD \+ Mathematical Intelligence \+ Hardware \+ Communication/Resilience \+ Incident Operations \+ UI specifications

__Security posture:__

Defense in depth; fail closed for privileged actions, fail honest for safety information

__Supersedes:__

Any legacy design that assumes unauthenticated node traffic, trusted local networks, permanent cloud access, or UI\-only access control

# DOCUMENT MAP

__Section__

__Scope__

1\. Security goals & invariants

Trust properties and non\-negotiable security rules

2\. Assets & trust boundaries

What must be protected and where trust changes

3\. Threat model

Adversaries, assumptions, attack surfaces and risk ranking

4\. Identity & provisioning

Node, Master, authority and citizen identities

5\. Cryptographic architecture

HMAC, Ed25519, TLS, key hierarchy, nonce/sequence rules

6\. Node security

ESP32 runtime, firmware, storage, local AP and physical attack posture

7\. Master/backend security

API, database, secrets, sessions, commands and service boundaries

8\. Authority access control

RBAC, least privilege, approval gates and session security

9\. Citizen security & event authenticity

Signed events, offline portal, SOS abuse resistance and privacy

10\. Data integrity & anti\-tamper

Telemetry provenance, immutable audit trail, replay and deduplication

11\. Attack scenarios & controls

Spoofing, MITM, replay, injection, DoS, poisoning and insider cases

12\. Logging, monitoring & incident response

Security telemetry and operator procedures

13\. Secrets, rotation & lifecycle

Provisioning, rotation, revocation and decommissioning

14\. Security testing & acceptance

Red\-team tests, fault injection and release gates

15\. Configuration & implementation checklist

Concrete parameters, flags and ownership

16\. Locked security invariants

Final non\-negotiable constraints

# 1\. Security Goals & Design Invariants

NexAlert is a safety\-relevant distributed system\. Security failures can become operational failures: a forged node can create a false incident, a replayed event can keep an old hazard visible, unauthorized control can change behavior, or a compromised local endpoint can mislead citizens\. Security therefore has to be coupled to provenance, freshness, uncertainty and human authority\.

__Property__

__Required behavior__

Authenticity

Telemetry, node events, commands and authority\-issued alert state must be attributable to an enrolled identity\.

Integrity

Payload changes are detectable; invalid signatures/MACs are rejected before the message affects state\.

Freshness

Sequence number \+ timestamp \+ nonce/event ID rules prevent stale/replayed packets from being treated as current\.

Authorization

Authentication alone never grants operational privilege\. Every privileged action is role\-checked and audited\.

Availability with honesty

DoS or partition may reduce freshness/capability, but must not create false NORMAL or silently fabricate certainty\.

Provenance

Hardware\-originated, simulated, derived and human\-authored data remain distinguishable throughout the pipeline\.

Auditability

Safety\-relevant changes produce durable audit records with actor, object, old/new state and reason when applicable\.

Privacy minimization

Citizen identity/contact data is collected only for declared safety workflows and not exposed to unauthorized parties\.

Fail\-safe control

Automated code may recommend; authorized humans approve operational dispatch/response actions\.

Defense in depth

Application authentication does not depend on LAN trust, SSID visibility, browser behavior or firewall placement alone\.

__Security interpretation  __“Trusted” means cryptographically and operationally justified, not merely “inside the same Wi\-Fi network\.” A local attacker is part of the threat model\.

# 2\. Assets & Trust Boundaries

The system contains several trust zones\. Crossing a boundary requires explicit authentication or signature verification, and data must retain source/provenance metadata after crossing\.

__Asset / zone__

__Examples__

__Protection objective__

__Security owner__

Field\-node identity

Node secret, node signing key, node ID

Prevent impersonation and key extraction

Firmware \+ provisioning

Telemetry

Raw measurements, diagnostics, heartbeat

Integrity, authenticity, freshness

Node \+ Master

Hazard events

Local candidate, incident state, signed alert

Authenticity, provenance, versioning

Node/Master

Master state

Incidents, GIS results, operational state

Integrity, availability, auditability

Backend

Authority identity

User account, role, session token

Strong authentication and least privilege

Auth service

Citizen records

User ID, permitted contact/location metadata, SOS

Minimization, authorization, controlled retention

Citizen service

Cryptographic material

HMAC secrets, signing/private keys, key\-encryption material

Confidentiality, rotation, revocation

Secrets manager / provisioning

Audit trail

Security and operational actions

Tamper evidence, durable retention

Backend/security

Simulation ground truth

Hidden scenario state / labels

Prevent leakage into inference

Simulation service only

## 2\.1 Trust boundary map

__Boundary__

__Threat__

__Required control__

ESP32 \-> Master

Forged/spoofed node, modified packet, replay

Per\-node HMAC, sequence/timestamp validation, identity enrollment

ESP32 \-> citizen browser

Rogue AP, forged local event

Signed event payload, event ID/version/freshness, UI trust badge

Browser \-> Master API

Session theft, CSRF, privilege misuse

TLS where available, secure session/token controls, RBAC, CSRF protection for cookie\-authenticated mutations

Master \-> cloud

Credential compromise, MITM, replay

TLS, scoped credentials, signed event model, outbound allow\-list

Simulation \-> ingestion

Fake “ground truth” or malformed telemetry

Simulator limited to telemetry interface; provenance=SIM; schema validation; no labels in inference path

Authority \-> operations

Insider misuse or compromised account

RBAC, approval gates, audit logs, session expiry, re\-auth for sensitive actions

Physical enclosure \-> device

USB/JTAG/UART/flash attack

Production lock\-down, debug disable where supported, secure boot/flash encryption when hardware capability is validated

# 3\. Threat Model

The V1 threat model assumes realistic local and network attackers but does not require nation\-state capabilities\. The strongest safety assumption is that cryptographic keys remain protected; if a device is fully compromised and its keys extracted, it must be revocable and replaceable rather than implicitly trusted forever\.

__Adversary__

__Capability__

__Goal__

__Priority__

Rogue local user

Access to Wi\-Fi/AP area or physical proximity

Inject telemetry, forge alerts, steal citizen data

CRITICAL

Network attacker

Observe/modify/drop IP traffic

MITM, replay, packet manipulation, DoS

HIGH

Compromised citizen endpoint

Valid browser/user context

Spam SOS, scrape data, attempt privileged API use

HIGH

Compromised authority account

Valid credentials, role\-limited access

Abuse operational controls or exfiltrate data

CRITICAL

Compromised node

Full software execution on one field node

Forge local measurements/events; pivot laterally

CRITICAL

Malicious simulator/user

Can create SIM telemetry or scenarios

Pollute evaluation, create false test incidents

MEDIUM

Physical attacker

Access to enclosure/storage/debug pads

Extract secrets or alter firmware

HIGH

Insider with DB access

Direct database credentials

Tamper with state/audit records

CRITICAL

## 3\.1 Security risk ranking

__Threat__

__Impact__

__Likelihood \(V1\)__

__Treatment__

Unauthorized hazard injection

False emergency / alert fatigue

Medium

HMAC/signature \+ provenance \+ incident correlation \+ operator approval

Replay of old emergency

Persistent false/stale warning

Medium

Sequence/timestamp/nonce \+ event version \+ freshness gate

Node impersonation

Fabricated sensor network state

Medium

Per\-node enrollment \+ secret/key identity \+ revocation

Authority privilege abuse

Unauthorized operational change

Low\-Medium

RBAC \+ approval \+ audit \+ session controls

Database tampering

Corrupted incident history / audit

Low\-Medium

Least privilege \+ backups \+ append\-only audit \+ integrity checks

Citizen privacy exposure

Personal safety/privacy harm

Medium

Data minimization \+ field\-level authorization \+ retention policy

Local AP spoofing

Citizen misinformation

High

Signed payload verification \+ explicit verified\-event UI \+ no secret actions via local page

Denial of service

Reduced availability

High

Rate limits \+ bounded queues \+ degradation modes \+ local autonomy

# 4\. Identity & Provisioning

Every persistent security principal has a stable identifier separate from any display name or network address\. IP addresses, SSIDs and browser sessions are not identities\.

__Principal__

__Identifier__

__Credential__

__Lifecycle__

Field node

node\_id / UUID

Per\-node HMAC secret; optional Ed25519 key pair for signed event candidates

Provision \-> active \-> rotate \-> revoke \-> decommission

Master

master\_id

Protected service secret / host credentials; signing key for published events

Provision \-> active \-> rotate \-> revoke

Authority user

user\_id

Password \+ TOTP/WebAuthn where deployed; session credential

Invite \-> verify \-> role assign \-> suspend/revoke

Citizen

NexAlert User ID

Optional verified contact identifier; session credential

Register/verify \-> active \-> revoke/delete per policy

Simulator

sim\_id

Scoped API credential / local\-only token

Create \-> scoped \-> revoke

## 4\.1 Node enrollment

__1\. __Create node\_id in the provisioning registry; never derive identity from MAC address alone\.

__2\. __Provision unique per\-node secret material\. Where signed events are enabled, provision or generate an Ed25519 key pair and register the public key\.

__3\. __Store credentials in protected device storage supported by the chosen ESP32 platform\. Do not hard\-code production secrets in source control\.

__4\. __Record hardware revision, firmware baseline, calibration/config version and provisioning timestamp in the registry\.

__5\. __Return only the minimum configuration required for normal operation\. Provisioning credentials are not reused for telemetry authentication\.

__6\. __Test authentication immediately with a known\-good packet and a known\-bad MAC/signature\.

__Prototype rule  __A copied firmware binary must not give an attacker a universal fleet credential\. Every provisioned node has unique authentication material\.

# 5\. Cryptographic Architecture

Use established cryptographic primitives through mature libraries\. The application does not invent encryption, hashing or signature schemes\. Exact library/API choice is implementation\-specific, but semantics are locked\.

__Primitive / mechanism__

__Purpose__

__V1 rule__

HMAC\-SHA\-256

Node \-> Master message authentication

Per\-node secret; verify before state mutation

Ed25519

Signed hazard/event authenticity for downstream verification

Use public\-key verification by Master/browser\-facing trust layer where practical

TLS 1\.2\+ / preferably TLS 1\.3

Transport confidentiality and server authentication

Required for remote/cloud links; preferred for LAN Master API; local captive portal may be HTTP but payload authenticity remains cryptographic

CSPRNG

Nonce/session/key generation

OS/hardware\-backed RNG only; never predictable PRNG

Argon2id / scrypt / equivalent

Authority password hashing

Store salted password verifiers; never plaintext passwords

SHA\-256 / SHA\-3 hash

Content addressing / integrity digest

Digest is not authentication by itself

## 5\.1 Node telemetry authentication

canonical\_message = schema\_version | node\_id | telemetry\_id | sequence | measurement\_timestamp | payload\_hash  
mac = HMAC\_SHA256\(node\_secret, canonical\_message\)  
accept iff: node enrolled AND schema valid AND MAC valid AND sequence/freshness checks pass

__Check__

__Rule__

__Failure action__

Identity

node\_id must exist and be active

Reject; security event

MAC

Constant\-time compare on expected MAC

Reject; rate\-limit repeated failures

Sequence

Strictly increasing within configured replay window; allow bounded recovery state after reconnect

Reject duplicate/old packet; record gap or replay condition

Timestamp

Within configured skew window unless monotonic device\-time policy permits otherwise

Mark stale/reject depending message class

Payload schema

Validate types, ranges, units, provenance

Reject malformed; never coerce invalid values into safe values

Freshness

Receive time distinct from measurement time

Preserve both; do not overwrite measurement time

## 5\.2 Signed event model

A safety\-relevant event has an immutable event\_id plus versioned mutable state\. A producer may sign a candidate event; the Master may issue a new authoritative state/version\. Consumers verify signature, issuer identity, event timestamp, nonce/version and expiration/freshness metadata before presenting a trust badge\.

signed\_event = event\_id | incident\_id | hazard\_type | state | severity | issued\_at | expires\_at | nonce | issuer\_id | payload  
signature = Ed25519\_Sign\(issuer\_private\_key, canonical\_bytes\(signed\_event\)\)

# 6\. Field\-Node / ESP32 Security

The edge node is both a sensor computer and a safety endpoint\. The security design protects its credentials and keeps its failure domain local: one compromised node must not become a fleet\-wide trusted root\.

__Control__

__Requirement__

__Verification__

Debug interfaces

Disable or restrict JTAG/UART boot/debug features in production configuration where supported

Production image test \+ physical inspection

Secure boot

Use hardware\-supported secure boot when validated on selected MCU/bootloader

Boot tamper test

Flash encryption

Enable when supported and validated; store secrets in protected NVS/secure storage

Flash extraction test

Firmware identity

Firmware build/version and schema version included in device metadata

Inventory check

Firmware update

Signed/verified firmware artifacts; reject unsigned downgrade where feasible

Bad\-signature and rollback test

Credential isolation

Node secret not exposed through telemetry, debug logs or local UI

String scan \+ protocol test

Local AP

Distinctive SSID but no implication of trust; sensitive admin endpoints unavailable

Connect as untrusted client

Rate limits

Authentication failures and expensive local endpoints are bounded

Flood test

Watchdog/recovery

Security fault must recover to known\-safe firmware state without fabricating telemetry

Fault injection

## 6\.1 Local emergency page security

- Expose read\-only emergency status and safe\-action content without requiring citizen login\.
- Do not expose node secrets, diagnostics requiring operator privilege, configuration write APIs or arbitrary shell/command execution through the citizen portal\.
- Every event displayed locally must carry a verified/unverified badge based on signature validation and freshness, not merely on coming from the local AP\.
- Use a deliberately constrained local web surface; disable arbitrary uploads, script execution hooks, debugging endpoints and open proxies\.
- Offline portal availability must survive cloud loss and Master loss, but absence of a current signed event must be represented as stale/unknown rather than NORMAL\.

# 7\. Master / Backend Security

The Raspberry Pi\-class Master is the highest\-value local compute target because it aggregates multiple nodes, computes geospatial hazard state and serves operator interfaces\. The architecture stays modular\-monolith for V1 but security boundaries remain explicit in code\.

__Surface__

__Control__

Telemetry ingress

Schema validation \-> identity verification \-> HMAC \-> replay/freshness \-> provenance \-> persistence

Command endpoint

Role/target authorization \-> command expiry \-> authenticated node channel \-> audit record \-> acknowledgement

Authority API

Authenticated session \+ RBAC \+ object\-level authorization \+ CSRF protection if cookie\-based

Simulation API

Separate scope; may submit telemetry/scenario controls but cannot write production incident state unless explicit simulation context is selected

Database

Least\-privilege DB user; parameterized SQL/ORM; no direct public exposure; backups protected separately

Admin/maintenance

LAN restriction \+ strong auth \+ explicit enable flag; disabled by default

Secrets/config

Environment/secret file with filesystem permissions or secret manager; never browser\-visible

OS

Dedicated service user, patched base image, firewall/default\-deny inbound services, minimal packages

## 7\.1 Command authorization

authorized\(command, actor, target\) =  
  actor\.active AND role\_allows\(actor\.role, command\.type\)  
  AND target\.enrolled AND target\.active  
  AND command\.expires\_at > now  
  AND command\.scope matches actor\.permissions  
  AND audit\_record\_created

__Human authority  __NexAlert never silently converts a model recommendation into autonomous dispatch\. Commands that change operational response require an authorized human action and an auditable record\.

# 8\. Authority Access Control

__Role__

__Read__

__Analyze__

__Acknowledge / respond__

__Admin / security__

Viewer

Assigned dashboards

No

No

No

Analyst

Assigned dashboards \+ telemetry

Yes

No

No

Operator

Operational incidents \+ citizen SOS

Yes

Yes, scoped

No

Incident Commander

All incident context

Yes

Yes \+ approval actions

Limited

System Admin

System state/config

Yes

Only where operational role separately granted

Yes

Security Admin

Security/audit configuration

Limited

No dispatch authority by default

Yes

__Least privilege  __Roles are permissions, not labels\. UI hiding is insufficient: the backend must enforce every object and action boundary\.

## 8\.1 Session controls

- Prefer passkeys/WebAuthn or TOTP\-backed strong authentication for authority users in production; password\-only is allowed only for isolated prototype evaluation with explicit restriction\.
- Use short\-lived access sessions and rotating refresh/session identifiers\. Invalidate sessions on account disable, credential reset and security incident\.
- Protect cookies with Secure, HttpOnly and SameSite attributes when cookies are used\.
- Require re\-authentication or step\-up authentication for security\-sensitive actions such as role changes, credential rotation, deleting users or altering trust configuration\.
- Log authentication success/failure, session issuance/revocation and privilege changes without logging secrets\.

# 9\. Citizen Security, Privacy & Event Authenticity

Citizen safety UX is intentionally low\-friction, but security\-sensitive actions remain bounded\. The emergency experience must communicate authentic event content without requiring citizens to understand cryptography\.

__Area__

__Rule__

Identity

NexAlert User ID is primary; verified phone/contact may be secondary contact identifier\.

Location

Use only permitted/recent location signals needed for geofencing or safe\-location ranking; retain no more precision than required by policy\.

Relationships

Contact/relationship labels are private and never exposed to arbitrary users\.

Emergency event

Display issuer, state, freshness and verification status; never infer trust solely from network origin\.

SOS

Never auto\-reject solely because no known hazard exists\. Apply abuse controls without blocking a potentially real emergency\.

Offline portal

No citizen credential is required to read emergency information\. No account\-management or privileged command surface is exposed\.

Messaging

Citizen\-to\-citizen communication requires explicit contact authorization; no implicit directory exposure\.

Retention

Define retention by data class; minimize long\-term storage of personal data and raw location history\.

## 9\.1 Local SSID spoofing

A distinctive public SSID cannot itself prove that the nearby network is genuine\. NexAlert therefore treats SSID names as a discovery aid only\. Authenticity comes from signed event content and, where available, an authenticated server path\. The UI must make “Verified NexAlert event” a cryptographically\-derived state, not a branding decision\.

# 10\. Data Integrity, Provenance & Anti\-Tamper

__Data class__

__Integrity mechanism__

__Tamper response__

Telemetry packet

HMAC \+ schema \+ sequence/timestamp

Reject before anomaly/evidence pipeline

Node event candidate

Ed25519 signature \+ event metadata

Reject unverified event; keep audit/security record

Derived intelligence

Provenance links to source telemetry and model/config version

Do not silently overwrite; create new computation/version

Incident state

Application transaction \+ actor authorization \+ audit

Reject unauthorized transition

Alert artifact

Signed canonical payload \+ alert/incident version

Show stale/invalid state instead of silently accepting

Audit entry

Append\-only application semantics \+ restricted DB permissions \+ periodic integrity digest where practical

Detect tampering; preserve forensic context

Simulation ground truth

Separate private store; provenance=GROUND\_TRUTH; never passed to production inference API

Fail test if inference endpoint receives labels

## 10\.1 Idempotency and deduplication

dedupe\_key = \(node\_id, sequence\) for telemetry  
dedupe\_key = \(issuer\_id, event\_id, version\) for signed events  
request\_id = client\-generated UUID for mutating API requests  
accept duplicate only when the resulting state is identical and operation is idempotent

__Never “latest packet wins” blindly  __A later\-arriving packet may have an older measurement timestamp\. The system compares sequence, measurement time, receive time and event version according to message class\.

# 11\. Attack Scenarios & Required Controls

__Attack__

__Expected outcome__

__Primary controls__

Forged node telemetry

No state mutation; security event recorded

Per\-node identity \+ HMAC \+ enrollment

Replay valid telemetry

Old packet rejected or marked duplicate/stale

Sequence \+ timestamp \+ dedupe window

Bit\-flip / packet mutation

Verification failure

HMAC/signature

MITM on cloud link

Connection rejected or privacy protected

TLS certificate validation; no insecure fallback

Rogue local AP

Citizen may connect but cannot cause UI to mark forged event as verified

Signed payload \+ verification badge \+ no privileged endpoints

Citizen API brute force

Account/session protected; service remains available

Rate limit \+ lockout/backoff \+ MFA where enabled

Compromised operator account

Damage limited to role scope and audited

RBAC \+ object authorization \+ step\-up auth \+ audit

Command replay

Old command not executed

Command nonce/id \+ expiry \+ authenticated node channel

Simulator injection into LIVE

Simulation data cannot mutate live state

Separate provenance/context \+ authorization \+ write guard

Sensor poisoning

Model evidence may be degraded but provenance remains visible

Sensor reliability/quality \+ cross\-node corroboration \+ anomaly explainability

DB record tamper

Change is detectable/privileges constrained

Least privilege \+ audit integrity \+ protected backups

DoS flood

Service degrades without unsafe state mutation

Rate limiting \+ queue limits \+ circuit breakers \+ local autonomy

## 11\.1 Credential compromise runbook

__1\. __Mark the principal compromised and revoke its credential/identity immediately\.

__2\. __Stop accepting new messages/commands from the affected principal while preserving valid state already received\.

__3\. __Issue replacement credentials from the provisioning/authentication service\.

__4\. __Search audit/security logs for affected time range, targets and correlated principals\.

__5\. __Reconcile affected incident/alert state from cryptographically valid peer evidence and operator review\.

__6\. __Record the incident, remediation and re\-enrollment in the audit trail\.

# 12\. Security Logging, Monitoring & Incident Response

Security logs are separate from raw telemetry and must not leak secrets\. Logs must answer: who did what, to which object, when, from where, with what authorization decision, and what changed\.

__Event__

__Minimum fields__

__Severity__

Auth success/failure

user\_id, source, timestamp, method, result

INFO/WARN

Node auth failure

node\_id, source, reason, timestamp, count window

WARN

Replay detected

principal, sequence/event\_id, received\_at, reason

WARN

Signature failure

issuer\_id, event\_id, reason

HIGH

Privilege change

actor, subject, old/new role, reason

HIGH

Operational approval

actor, incident, action, old/new state, timestamp

HIGH

Credential rotation

principal, key version, actor/system, result

HIGH

Security config change

actor, config key, old/new, reason

HIGH

DoS/rate\-limit trigger

source, endpoint, rate, threshold

WARN/HIGH

Audit integrity failure

scope, digest/version, detection time

CRITICAL

__No secret logging  __Never log passwords, private keys, HMAC secrets, access tokens, full session cookies or raw credential material\. Hashes of identifiers may still be sensitive and should be used deliberately\.

## 12\.1 Response states

__State__

__Meaning__

__Action__

SECURITY\_OBSERVED

Suspicious but not confirmed compromise

Continue service; rate\-limit; collect evidence

CONTAINMENT

Principal/path isolated or revoked

Stop affected credentials/commands; preserve valid local state

RECOVERY

Replacement credentials / firmware / service restored

Re\-enroll; verify integrity; replay safe data

POST\_INCIDENT

Service normal with investigation complete

Document cause, impact, controls and residual risk

# 13\. Secrets, Key Rotation & Lifecycle

__Secret/key__

__Storage__

__Rotation trigger__

__Revocation__

Node HMAC secret

Protected MCU storage / secure element where available

Periodic policy, suspected compromise, device replacement

Set node inactive; replace secret

Node Ed25519 private key

Protected device storage

Compromise / firmware lifecycle

Revoke public key; enroll replacement

Master signing key

OS protected secret store / HSM when deployed

Planned rotation or compromise

Publish new key version; retire old

Authority auth secret

Password verifier / MFA secret store

Reset, compromise, policy

Disable credential/session

Cloud credentials

Environment secret store

Provider rotation / compromise

Revoke provider token

Session secret

Application secret store

Deployment rotation / incident

Invalidate active sessions

## 13\.1 Key versioning

key\_id = <principal\_id>:<purpose>:<version>  
message carries key\_id when multiple active verification keys exist  
verification policy may accept current \+ previous key during controlled rotation window  
private material is never transmitted in telemetry, config dumps or browser responses

## 13\.2 Decommissioning

- Mark device/principal REVOKED before physical retirement\.
- Remove or rotate its credentials from every trust registry\.
- Invalidate sessions and commands associated with the principal\.
- Wipe protected storage where supported and physically destroy or secure any removable credential\-bearing media\.
- Preserve only the minimum audit metadata required to explain historical events\.

# 14\. Security Testing & Acceptance

Security is a release gate, not a final checklist\. The same simulation/fault\-injection discipline used for resilience testing is used to exercise cryptographic rejection, privilege boundaries and recovery paths\.

__Test ID__

__Test__

__Expected result__

__Release gate__

SEC\-01

Forge telemetry with wrong HMAC

Packet rejected; no anomaly/incident effect

MUST PASS

SEC\-02

Replay previously valid packet

Duplicate/stale rejected; security log generated

MUST PASS

SEC\-03

Modify signed event field

Signature verification fails; event not trusted

MUST PASS

SEC\-04

Use revoked node credential

Rejected immediately after revocation

MUST PASS

SEC\-05

Attempt operator\-only endpoint as viewer

403/denied; no side effect; audit entry

MUST PASS

SEC\-06

Replay operational command

Command rejected after expiry/duplicate

MUST PASS

SEC\-07

Inject simulation ground truth into inference

Guard blocks / test fails loudly

MUST PASS

SEC\-08

Spoof local SSID and present forged event

UI remains unverified; no false “verified” badge

MUST PASS

SEC\-09

Flood telemetry endpoint

Rate limited/bounded; service remains responsive

MUST PASS

SEC\-10

Remove Master/internet

Local emergency path remains; information condition degrades honestly

MUST PASS

SEC\-11

Compromise one node in test environment

Other nodes remain isolated; revoked node cannot rejoin silently

MUST PASS

SEC\-12

Tamper audit record in test DB

Integrity control detects or access control prevents unauthorized edit

MUST PASS

SEC\-13

Invalid firmware image

Device rejects image / enters defined recovery path

MUST PASS where secure update enabled

SEC\-14

Credential rotation

Old credential fails, new credential succeeds, audit complete

MUST PASS

## 14\.1 Security test evidence

- Each test stores test ID, build/version, configuration hash, test inputs, expected result, actual result and timestamp\.
- Negative tests are first\-class artifacts: a secure system must demonstrate that invalid traffic is rejected, not merely that valid traffic works\.
- Acceptance screenshots must show the operator/citizen\-facing result for trust badges, degraded states and denied actions where applicable\.
- Hardware tests record board revision and firmware build so a successful result cannot be misattributed to a different device\.

# 15\. Configuration & Implementation Checklist

__Parameter__

__Recommended V1 value__

__Notes__

HMAC algorithm

HMAC\-SHA\-256

Per\-node secret; application layer

Event signature

Ed25519

For signed event candidates / published event artifacts

Remote transport

TLS 1\.2\+

Prefer TLS 1\.3 when library/runtime permits

Node identity

UUID / opaque node\_id

Never MAC\-as\-identity

Replay window

Bounded by message class

Configure timestamp skew \+ sequence tolerance

Command TTL

Short and class\-specific

Never accept indefinite safety commands

Auth rate limit

Per IP \+ per principal

Backoff on repeated failures

Session idle timeout

Short for authority UI

Exact value is deployment configuration

Audit retention

Policy\-driven

Keep safety/security evidence longer than routine debug logs

Debug mode

OFF in production demo build

Explicit feature flag

Simulation provenance

SIMULATION

Must be non\-transferable to LIVE without deliberate operator action

Security incident flag

Enabled

Used to trigger containment flow

## 15\.1 Code boundaries

__Module__

__Security responsibility__

__Must not do__

edge\_security

HMAC/signature, replay checks, key access

Expose secrets to application/UI

ingest\_gateway

Schema validation, auth verification, rate limiting

Run hazard decisions before auth/provenance

authz

Role \+ object authorization

Trust UI\-hidden controls

event\_signing

Canonical serialization \+ signing/verification

Sign ambiguous/non\-canonical JSON

audit

Append\-only application semantics

Store raw passwords/tokens

security\_policy

Config\-driven thresholds/allow\-lists

Embed scattered hard\-coded bypasses

simulation\_gateway

Simulation scope/provenance isolation

Write hidden ground truth into live telemetry store

# 16\. Locked Security Invariants

__1\. __No node is trusted solely because it is on the local network\.

__2\. __Every active field node has unique authentication material\.

__3\. __HMAC/signature verification happens before telemetry or event data can mutate operational state\.

__4\. __Sequence, timestamp and event version semantics are mandatory anti\-replay controls; receive time never replaces measurement time\.

__5\. __A signed event is not equivalent to a confirmed hazard: authenticity and hazard truth are separate concepts\.

__6\. __Local SSID names are discovery aids, not proof of authenticity\.

__7\. __Citizen emergency pages expose no privileged administration or secret material\.

__8\. __Simulation telemetry remains distinguishable from LIVE telemetry and cannot silently write LIVE incident state\.

__9\. __NexAlert recommends; authorized humans approve operational dispatch/response actions\.

__10\. __RBAC is enforced at the backend/API layer, not only in the UI\.

__11\. __Security logs never contain credentials, private keys or live session secrets\.

__12\. __Revocation must be possible for a compromised node, user or key without redeploying the whole fleet\.

__13\. __Master failure, internet failure and security compromise are modeled as distinct states with explicit degraded behavior\.

__14\. __The system fails honest: when authenticity, freshness or information sufficiency cannot be established, it presents an uncertainty/degraded state rather than false confidence\.

__Definition of secure  __A NexAlert deployment is secure enough for V1 when an attacker cannot silently make untrusted data look trusted, cannot execute privileged operations outside authorized scope, and cannot erase the distinction between current verified information and stale/unknown information — while the system continues to provide the safest information it still possesses during partition or attack\.

__NEXALERT SECURITY POSTURE__

__Authenticate the source\. Verify the event\. Authorize the action\.  
Preserve the evidence\. Degrade honestly\.__

