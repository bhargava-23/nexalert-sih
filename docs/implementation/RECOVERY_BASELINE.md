# NexAlert Recovery Baseline — SIH Final Build

Status: Recovery baseline v1.0
Date: 2026-09-13
Purpose: Freeze the architecture and define the controlled path from the current repository snapshot to a defensible SIH final system.

## 1. North-star architecture

NexAlert is a resilient distributed environmental monitoring and early-warning decision-support system, not a sensor dashboard.

Product pillars:
- Access
- Resilience
- Intelligence

Canonical flow:

Field sensors → ESP32 Edge Node → authenticated telemetry → Raspberry Pi Master → intelligence/fusion/geospatial/incident logic → Backend persistence/API/audit → Authority/Citizen surfaces

Synthetic telemetry MUST enter the same post-ingestion path as hardware telemetry.

## 2. Responsibility boundaries

### ESP32 Edge Node

Owns:
- sensor acquisition
- local sensor validation/diagnostics
- heartbeat
- health / quality / reliability inputs
- lightweight baseline/anomaly/evidence/state functions appropriate for MCU limits
- local buffering/store-and-forward
- node identity and authentication
- local emergency path required by the architecture

Must NOT own:
- large fire-spread raster propagation
- GIS raster/vector processing
- population exposure computation
- multi-node fusion

### Raspberry Pi Master

Owns:
- local ingestion
- authentication/validation
- normalization and receive timestamps
- deduplication
- node registry/state
- full local intelligence
- multi-node fusion and correlation
- fire geospatial engine
- local persistence/continuity
- local WebSocket/API for UI
- local degraded operation

Master failure is distinct from internet failure.

### Backend / Cloud

Owns:
- canonical persistence
- API boundary
- audit history
- alert lifecycle / human approval workflow
- long-running/background orchestration
- cloud synchronization

### Frontend

Consumes canonical API/event data. It is never an alternate source of hazard truth and never independently computes authoritative severity/risk/safe-place decisions.

## 3. Current repository health

### KEEP / GREEN
- 20 specification documents and extracted Markdown mirrors
- Implementation Constitution
- Repository map / workflow / decision records
- Reference intelligence modules
- Golden-vector test suite
- Existing backend/geospatial modules as starting material
- Database schema/migration foundation

### FIX / YELLOW
- telemetry representations across schema/Python/TypeScript
- configuration precedence and runtime ownership
- MQTT/transport integration
- resilience persistence semantics
- backend/master integration
- CI gates and test invocation
- generated build-artifact hygiene

### REBUILD / RED
- ESP32 production firmware
- actual sensor abstraction for BME680 + MPU6050 + MQ2
- Raspberry Pi Master executable service
- authority dashboard
- citizen web
- live telemetry presentation path
- end-to-end integration

### REMOVE / ARCHIVE after reference search
- duplicate firmware mains such as main_integrated.c / main_milestone1_backup.c if unreferenced
- generated .next artifacts
- stale prototype-only implementations
- dead parallel contracts

## 4. Verified facts from the snapshot

- Repository contains roughly 593 files.
- Authority dashboard page is still a Phase-3 placeholder.
- Citizen web page is still a Phase-3 placeholder.
- Master service main entrypoint is still a Phase-3 placeholder.
- Canonical firmware main is DHT22-based, not the actual BME680/MPU6050/MQ2 hardware.
- Firmware has multiple main implementations; CMake selects main.c.
- The schema requires `node_id` matching `^NODE-[0-9]{3,}$`.
- Current hardware prototype identity seen elsewhere is `NEX-HW-PROTO-1`; this is incompatible with that schema as-is.
- Schema uses `power.battery_pct`; Python representation uses `battery_percent`.
- Schema distinguishes `measurement_timestamp` and server-assigned `received_timestamp`.
- Firmware/MQTT implementation currently contains comments claiming a locked topic while generating the topic from node ID.
- Backend MQTT consumer contains a hard-coded `hazard_types = ["fire"]` placeholder path.
- CI allows backend/master pytest failures via `pytest || true`.
- CI may skip firmware build when ESP-IDF is unavailable.
- Root `.gitignore` does not currently exclude `.next/`.
- `infra/docker/docker-compose.yml` in the repository currently contains PostgreSQL/PostGIS only; the Docker MQTT bridge created during the prior demo session is not present in this snapshot.
- Reference Python tests pass when executed with `PYTHONPATH=reference/python`: 333 passed.

## 5. Frozen contract rules for the recovery

### Node identity

Protocol `node_id` MUST use the canonical registered form defined by the schema/specification (e.g. `NODE-001`).

Human-facing names such as `NEX-HW-PROTO-1` belong in `display_name`/metadata, not the protocol identity.

### MQTT

Canonical topic family:

`Nexalert/telemetry/{node_id}`

Subscriber wildcard:

`Nexalert/telemetry/+`

No JSON file is used as a live transport.

### Telemetry time

`measurement_timestamp`: produced by the observation source.

`received_timestamp`: assigned by the receiving Master/backend.

These are distinct.

### Missing data

`null`/absent/explicit unavailable MUST remain semantically missing. Never convert missing to numeric zero.

### Source

Every canonical telemetry record distinguishes:
- `HARDWARE`
- `SIMULATION`

### Intelligence semantics

Keep these distinct:
- health
- quality
- reliability
- anomaly
- evidence
- confidence
- severity
- operational risk

Confidence and risk are not probabilities.

### Hazard states

`UNKNOWN`, `NORMAL`, `WATCH`, `SUSPECTED`, `CONFIRMED`, `CRITICAL`, `RESOLVED`

### Geometry

Physical footprint, operational buffer, risk surface, and exposure are separate concepts.

## 6. Hardware baseline

Actual prototype hardware:
- ESP32-S3
- BME680
- MPU6050
- MQ2

Current prototype measurements:
- temperature
- humidity
- pressure
- vibration/dynamic acceleration
- gas/smoke index from MQ2 raw signal

The MQ2 value MUST NOT be presented as calibrated ppm without a calibration model.

## 7. Recovery build order

### Phase 0 — Contract freeze
1. Reconcile schema, Python, TypeScript, firmware, backend, MQTT and UI contracts.
2. Record any intentional changes in DECISIONS.md and update source-of-truth specs when required.
3. Define one canonical telemetry envelope and one adapter for prototype hardware packets.

Gate: one versioned schema plus passing cross-language contract tests.

### Phase 1 — Edge node
1. Replace DHT22-only acquisition with a clean sensor abstraction for BME680, MPU6050 and MQ2.
2. Separate sampling from intelligence.
3. Make configuration authoritative.
4. Implement heartbeat, diagnostics, buffering and MQTT using the canonical envelope.
5. Add embedded tests/golden vectors for the portable intelligence subset.

Gate: ESP32 boots, samples real sensors, survives MQTT failure, buffers safely, reconnects, replays, emits valid canonical telemetry.

### Phase 2 — Master
1. Implement Raspberry Pi service.
2. Ingest MQTT.
3. Validate/authenticate/normalize/deduplicate.
4. Assign receive timestamp.
5. Maintain node registry/state.
6. Run full local intelligence/fusion.
7. Expose local API/WebSocket.
8. Persist/reconcile locally.

Gate: real ESP32 telemetry reaches a local Master node state without cloud dependency.

### Phase 3 — Backend
1. Repair telemetry persistence/integration contracts.
2. Remove fire-only placeholder assumptions.
3. Finish deterministic incident correlation.
4. Wire alert lifecycle and audit trail.
5. Keep long-running fire/replay work asynchronous.

Gate: end-to-end telemetry → incident persistence and traceable audit path.

### Phase 4 — Authority UI
Build from scratch against the canonical Master/backend contracts.

Primary screen: NODES & NETWORK.

A real node must appear and update without refresh.

Gate:
ESP32 → MQTT → Master/bridge → WebSocket → dashboard

### Phase 5 — Fire/GIS
Integrate the already-specified engine on the Master/backend side:
DEM + fuel + moisture + wind → directional ROS → arrival time → footprint/warning/projection → geometry → buffer → risk → exposure.

Use metric CRS, correct wind FROM → TO handling, 8-neighbor propagation, non-burnable ROS=0, deterministic recomputation/versioning.

Gate: golden-vector and geospatial regression tests plus scenario visualization.

### Phase 6 — Citizen / resilience
Implement local emergency path, offline/PWA emergency surface, canonical event model, SOS workflow, safe-place recommendations controlled by Master/backend, and explicit degraded states.

Gate: internet-loss and Master-loss scenarios behave according to the architecture.

### Phase 7 — System validation
Run L0–L5 style verification:
- static/schema
- unit
- component
- integration
- system/fault injection
- controlled physical trials

## 8. SIH final definition of done

NexAlert is release-candidate ready only when all of the following are true:

1. Real ESP32 telemetry is accepted through the canonical path.
2. Node identity, timestamps, source and missing-data semantics are correct.
3. The Raspberry Pi Master actually runs local intelligence and continuity logic.
4. A real node appears live in the Authority dashboard without refresh.
5. Sensor health is distinct from node connectivity.
6. Stale/offline behavior is deterministic.
7. Simulation and hardware use the same ingestion/reasoning path.
8. Fire spread is not a frontend-only decorative animation.
9. Physical footprint, operational buffer, risk and exposure remain distinct.
10. Internet loss does not erase local operation.
11. Master failure and internet failure are demonstrably different states.
12. High-impact alert issuance remains under human authority.
13. Audit history is traceable.
14. CI fails on broken tests instead of masking them.
15. Final demo evidence corresponds to real capabilities, not claims.

## 9. SIH submission strategy

Internal target freeze: 2026-09-20.

2026-09-21 through 2026-09-30 is buffer only for defect fixes, evidence refresh, submission corrections and presentation polish.

No major architecture changes after the internal freeze.
