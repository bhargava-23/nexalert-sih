# NexAlert Repository Map

**Version**: 1.0  
**Status**: ACTIVE  
**Last Updated**: 2026-09-07  
**Purpose**: Canonical reference for directory structure, subsystem ownership, and interface boundaries

---

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Directory Structure](#directory-structure)
3. [Subsystem Ownership Matrix](#subsystem-ownership-matrix)
4. [ESP32 Code Boundaries](#esp32-code-boundaries)
5. [Interface Boundaries](#interface-boundaries)
6. [Canonical Locations](#canonical-locations)

---

## Repository Overview

```
nexalert/
├── schemas/           # Authoritative contract definitions (JSON Schema)
├── apps/              # User-facing applications (Authority dashboard, Citizen web/PWA)
├── services/          # Backend services (Python modular monolith, Master service)
├── firmware/          # ESP32-S3 embedded firmware (ESP-IDF + C/C++)
├── packages/          # Shared libraries (types, math, config, events, UI components)
├── db/                # Database schema and migrations (PostgreSQL/PostGIS)
├── reference/         # Reference implementations (validation only, never imported by production)
├── tests/             # Test suites (golden vectors, integration, scenarios, security, fault injection)
├── docs/              # Documentation (specifications, implementation governance, architecture, validation)
├── infra/             # Infrastructure as code (Ansible, Docker, K8s)
├── scripts/           # Utility scripts (calibration, provisioning, simulation, validation)
└── .github/           # CI/CD workflows (lint, test, build, deploy gates)
```

---

## Canonical Locations

### Authoritative Telemetry Contract

**File**: `schemas/telemetry-envelope.schema.json`

**Purpose**: THE single authoritative declarative source of truth for NexAlert telemetry contract. This is the canonical telemetry schema for the entire repository.

**Authority**: Document 07, Section 7 (Telemetry API Contract)

**Status**: LOCKED - This is the authoritative telemetry contract. No other file, documentation, or specification may introduce a competing telemetry contract definition.

**Contract Governance**:
- Python representation: `packages/nexalert-events/nexalert_events/telemetry.py` MUST synchronize to this schema
- TypeScript representation: `packages/nexalert-types/src/telemetry.ts` MUST synchronize to this schema
- Future firmware representation: Will synchronize to this schema
- Schema changes require review per IMPLEMENTATION_CONSTITUTION.md Section 1
- Changes must preserve locked invariants: missing ≠ zero, measurement_timestamp ≠ receive_timestamp, LIVE vs SIMULATION distinction

**Synchronization Validation**:
- Python: `packages/nexalert-events/tests/test_schema_sync.py` validates against authoritative schema
- TypeScript: `packages/nexalert-types/src/telemetry-validator.ts` validates using ajv against authoritative schema
- Gate A includes schema synchronization checks

---

## Repository Overview

## Directory Structure

### `apps/` - User-Facing Applications

```
apps/
├── authority-dashboard/        # Next.js authority dashboard
│   ├── app/                    # Next.js 13+ app router
│   │   ├── overview/
│   │   ├── incidents/
│   │   ├── fire-spread/
│   │   ├── affected-area/
│   │   ├── multi-hazard/
│   │   ├── nodes/
│   │   ├── telemetry/
│   │   ├── sos/
│   │   ├── alerts/
│   │   ├── history/
│   │   ├── response/
│   │   ├── audit/
│   │   └── system/
│   ├── components/             # React components
│   ├── lib/                    # Utilities, API clients
│   ├── styles/                 # Global styles, Tailwind config
│   ├── types/                  # TypeScript types (authority-specific)
│   └── tests/                  # Authority UI tests
│
└── citizen-web/                # Next.js citizen PWA
    ├── app/                    # Next.js app router
    │   ├── emergency/
    │   ├── safe-places/
    │   ├── sos/
    │   ├── alerts/
    │   └── map/
    ├── components/
    ├── lib/
    ├── styles/
    ├── types/
    ├── public/                 # PWA manifest, service worker
    └── tests/
```

**Owner**: Frontend Engineer  
**Responsibility**: Authority and citizen user interfaces  
**Technology**: Next.js 14+, React 18+, TypeScript, Tailwind CSS, MapLibre GL JS

---

### `services/` - Backend Services

```
services/
├── backend/                    # Python FastAPI modular monolith
│   ├── modules/
│   │   ├── ingestion/          # Telemetry acceptance (Layer 7-8)
│   │   ├── security/           # HMAC/signature verification
│   │   ├── intelligence/       # Health/quality/reliability/baseline/anomaly (Layer 9-11)
│   │   ├── hazards/            # Evidence/confidence/severity/risk/state (Layer 12-14)
│   │   ├── incidents/          # Incident correlation (Layer 15)
│   │   ├── geospatial/         # Fire spread, PostGIS operations
│   │   ├── response/           # Response recommendation engine
│   │   ├── alerts/             # Alert lifecycle management
│   │   ├── sos/                # SOS handling
│   │   ├── simulation/         # Simulation orchestration
│   │   ├── users/              # Authority/citizen identity
│   │   ├── audit/              # Audit trail (Layer 20)
│   │   ├── api/                # HTTP/WebSocket API routes
│   │   └── workers/            # Background workers
│   ├── db/                     # Alembic migrations, models
│   ├── tests/                  # Backend unit + integration tests
│   ├── pyproject.toml          # Python dependencies
│   └── main.py                 # FastAPI application entry
│
└── master-service/             # Raspberry Pi Master service (Python)
    ├── local_intelligence/     # Full intelligence stack
    ├── fire_engine/            # Arrival-time propagation engine
    ├── fusion/                 # Multi-node evidence fusion
    ├── local_portal/           # Local emergency UI gateway
    ├── resilience/             # Store-and-forward, Master-specific logic
    ├── tests/
    └── main.py
```

**Owner**: Backend Engineer (backend), Network Engineer (master-service)  
**Responsibility**: Canonical telemetry persistence, intelligence computation, incident correlation, alert management  
**Technology**: Python 3.11+, FastAPI, PostgreSQL/PostGIS, SQLAlchemy, Alembic

---

### `firmware/` - ESP32-S3 Embedded Firmware

```
firmware/
├── components/                 # ESP-IDF components
│   ├── sensors/                # Hardware abstraction (Layer 1-3)
│   │   ├── temperature/
│   │   ├── humidity/
│   │   ├── pm/
│   │   ├── gas/
│   │   ├── water_level/
│   │   ├── rainfall/
│   │   ├── soil_moisture/
│   │   └── vibration/
│   ├── diagnostics/            # Health computation (Layer 4)
│   ├── intelligence/           # Lightweight edge intelligence (Layer 5)
│   │   ├── health/             # H_i computation
│   │   ├── quality/            # Q_i computation
│   │   ├── reliability/        # R_i computation
│   │   ├── baseline/           # Median/MAD baseline
│   │   ├── anomaly/            # A_i computation
│   │   ├── evidence/           # Lightweight hazard evidence
│   │   ├── confidence/         # C_h computation
│   │   ├── severity_risk/      # S_h, R_h computation
│   │   └── hazard_state/       # Local state machine
│   ├── telemetry/              # Envelope generation (Layer 6)
│   ├── security/               # HMAC generation
│   ├── network/                # Wi-Fi/TCP, store-and-forward
│   ├── storage/                # Persistent queue, NVS
│   ├── system/                 # Boot, watchdog, power
│   └── local_ap/               # Local emergency AP/captive portal
│
├── main/                       # Firmware entry point
│   ├── main.c
│   └── Kconfig.projbuild
│
├── tests/                      # Firmware unit tests
├── sdkconfig                   # ESP-IDF configuration
├── sdkconfig.defaults
└── CMakeLists.txt
```

**Owner**: Firmware Engineer  
**Responsibility**: Sensor sampling, lightweight edge intelligence, local emergency path  
**Technology**: ESP-IDF 5.1+, C/C++, FreeRTOS

---

### `packages/` - Shared Libraries

```
packages/
├── nexalert-types/             # TypeScript shared types
│   ├── src/
│   │   ├── telemetry.ts        # Canonical telemetry schema
│   │   ├── hazards.ts          # Hazard types, states
│   │   ├── incidents.ts        # Incident entity
│   │   ├── alerts.ts           # Alert lifecycle
│   │   └── index.ts
│   ├── package.json
│   └── tsconfig.json
│
├── nexalert-math/              # Python reference math (golden vectors)
│   ├── nexalert_math/
│   │   ├── health.py           # H_i reference
│   │   ├── quality.py          # Q_i reference
│   │   ├── reliability.py      # R_i reference
│   │   ├── baseline.py         # Median/MAD baseline
│   │   ├── anomaly.py          # A_i reference
│   │   ├── confidence.py       # C_h reference
│   │   ├── severity_risk.py    # S_h, R_h reference
│   │   └── fire_spread.py      # ROS, arrival-time reference
│   ├── tests/
│   └── pyproject.toml
│
├── nexalert-config/            # Configuration schema/registry
│   ├── src/
│   │   ├── schema.py           # Configuration classes, validation
│   │   ├── registry.py         # Parameter registry from Document 19
│   │   └── profiles.py         # Environment profiles (DEV/TEST/SIM/STAGE/SIH/PROD)
│   └── pyproject.toml
│
├── nexalert-events/            # Canonical event definitions
│   ├── src/
│   │   ├── telemetry.py        # Telemetry event schema
│   │   ├── hazard.py           # Hazard assessment event
│   │   ├── incident.py         # Incident event
│   │   └── alert.py            # Alert event
│   └── pyproject.toml
│
└── nexalert-ui-components/     # Shared UI components
    ├── src/
    │   ├── map/                # MapLibre GL JS wrappers
    │   ├── charts/             # Chart components
    │   ├── hazard-cards/       # Hazard state display
    │   └── design-system/      # Design tokens, base components
    ├── package.json
    └── tsconfig.json
```

**Owner**: System Architect (nexalert-math, nexalert-config, nexalert-events), Frontend Engineer (nexalert-types, nexalert-ui-components)  
**Responsibility**: Shared contracts, reference implementations, reusable components

---

### `db/` - Database Schema

```
db/
├── migrations/                 # Alembic migrations
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_hazard_geometries.py
│   │   └── ...
│   └── env.py
│
└── schema/                     # Schema documentation
    ├── telemetry_records.md
    ├── sensor_assessments.md
    ├── hazard_assessments.md
    ├── incidents.md
    ├── hazard_geometries.md
    ├── alerts.md
    ├── sos_requests.md
    └── audit_events.md
```

**Owner**: Backend Engineer  
**Responsibility**: PostgreSQL/PostGIS schema definition and evolution  
**Technology**: PostgreSQL 15+, PostGIS 3.3+, Alembic

---

### `tests/` - Test Suites

```
tests/
├── golden-vectors/             # GV-H01 through GV-GEO02
│   ├── reference/              # Python reference implementations
│   ├── inputs/                 # Test input data
│   ├── expected/               # Expected outputs with tolerances
│   └── test_*.py               # Pytest test cases
│
├── integration/                # End-to-end traces (Gate D)
│   ├── test_telemetry_to_incident.py
│   ├── test_incident_to_alert.py
│   └── test_e2e_trace.py
│
├── scenarios/                  # G01-G15 scenario definitions
│   ├── G01_normal.yaml
│   ├── G02_fire_slow.yaml
│   ├── G03_fire_fast.yaml
│   └── ...
│
├── security/                   # SEC-01 through SEC-14
│   ├── test_hmac_authentication.py
│   ├── test_replay_protection.py
│   ├── test_signature_verification.py
│   └── ...
│
└── fault-injection/            # FI-01 through FI-14
    ├── test_node_disappears.py
    ├── test_master_failure.py
    ├── test_internet_loss.py
    └── ...
```

**Owner**: QA Engineer  
**Responsibility**: Validation framework, acceptance gates, test execution

---

### `docs/` - Documentation

```
docs/
├── specifications/             # 20 original DOCX files (PRESERVED UNTOUCHED)
│   ├── 01_master_architecture_invariants.docx
│   ├── 02_technical_requirements.docx
│   ├── ...
│   └── 20_native_mobile_app.docx
│
├── specification_text/         # 20 extracted Markdown files (PRESERVED)
│   ├── 01_master_architecture_invariants.md
│   ├── ...
│   └── 20_native_mobile_app.md
│
├── implementation/             # Implementation governance (THIS DOCUMENT)
│   ├── IMPLEMENTATION_CONSTITUTION.md
│   ├── REPOSITORY_MAP.md       # <-- YOU ARE HERE
│   ├── DEVELOPMENT_WORKFLOW.md
│   └── DECISIONS.md
│
├── architecture/               # Architecture documentation (FUTURE)
│   ├── reconnaissance_report.md
│   ├── subsystem_boundaries.md
│   ├── data_contracts.md
│   └── configuration_registry.md
│
└── validation/                 # Validation evidence/reports (FUTURE)
    ├── golden_vectors_evidence/
    ├── gate_reports/
    └── sih_demonstration_report.md
```

**Owner**: System Architect (specifications, implementation, architecture), QA Engineer (validation)

---

### `infra/` - Infrastructure as Code

```
infra/
├── ansible/                    # Deployment automation
│   ├── playbooks/
│   │   ├── deploy_master.yml
│   │   ├── deploy_backend.yml
│   │   └── provision_node.yml
│   └── roles/
│
├── docker/                     # Container definitions
│   ├── Dockerfile.backend
│   ├── Dockerfile.master
│   └── docker-compose.yml
│
└── k8s/                        # Kubernetes manifests (if needed)
    ├── backend/
    ├── postgres/
    └── ingress/
```

**Owner**: DevOps Engineer

---

### `scripts/` - Utility Scripts

```
scripts/
├── calibration/                # Sensor calibration tooling
│   ├── calibrate_temperature.py
│   ├── calibrate_pm.py
│   └── generate_calibration_profile.py
│
├── provisioning/               # Node secret provisioning
│   ├── enroll_node.py
│   ├── generate_hmac_secret.py
│   └── provision_calibration.py
│
├── simulation/                 # Scenario runners
│   ├── run_scenario.py
│   ├── generate_virtual_telemetry.py
│   └── evaluate_simulation.py
│
└── validation/                 # Golden vector execution
    ├── run_golden_vectors.py
    ├── check_parity.py
    └── generate_gate_report.py
```

**Owner**: Varies by script (Firmware Engineer for calibration, Security Engineer for provisioning, Simulation Engineer for simulation, QA Engineer for validation)

---

## Subsystem Ownership Matrix

| **Subsystem** | **Directory** | **Owner** | **Primary Responsibility** | **Technology** |
|---|---|---|---|---|
| **Authority Dashboard** | `apps/authority-dashboard/` | Frontend Engineer | Operational interface for incident command | Next.js, React, TypeScript, MapLibre |
| **Citizen Web/PWA** | `apps/citizen-web/` | Frontend Engineer | Citizen safety UI (online web, PWA) | Next.js, React, TypeScript, MapLibre |
| **Backend API** | `services/backend/` | Backend Engineer | Canonical persistence, API, intelligence computation | Python, FastAPI, PostgreSQL/PostGIS |
| **Master Service** | `services/master-service/` | Network Engineer | Local intelligence, fire spread, fusion, offline resilience | Python, PostGIS |
| **ESP32 Firmware** | `firmware/` | Firmware Engineer | Sensor sampling, edge intelligence, local emergency path | ESP-IDF, C/C++, FreeRTOS |
| **Reference Math** | `packages/nexalert-math/` | System Architect | Python reference for golden vectors | Python |
| **Configuration Registry** | `packages/nexalert-config/` | System Architect | Configuration schema, parameter registry | Python |
| **Shared Types** | `packages/nexalert-types/` | Frontend Engineer | TypeScript shared contracts | TypeScript |
| **UI Components** | `packages/nexalert-ui-components/` | Frontend Engineer | Reusable UI components | React, TypeScript |
| **Database Schema** | `db/` | Backend Engineer | PostgreSQL/PostGIS schema, migrations | PostgreSQL, PostGIS, Alembic |
| **Test Suites** | `tests/` | QA Engineer | Validation framework, acceptance gates | Pytest, scenario YAML |
| **Specifications** | `docs/specifications/`, `docs/specification_text/` | System Architect | Authoritative engineering source of truth | DOCX, Markdown (READ-ONLY) |
| **Implementation Governance** | `docs/implementation/` | System Architect | Constitution, workflow, decisions | Markdown |
| **Infrastructure** | `infra/` | DevOps Engineer | Deployment automation, containers, orchestration | Ansible, Docker, K8s |
| **Utility Scripts** | `scripts/` | Varies | Calibration, provisioning, simulation, validation tooling | Python |

---

## ESP32 Code Boundaries

### Code That BELONGS on ESP32 (firmware/)

**Mandatory (MUST be implemented):**
- Sensor sampling: `firmware/components/sensors/`
- Diagnostics: `firmware/components/diagnostics/`
- Lightweight edge intelligence: `firmware/components/intelligence/`
  * H_i (health)
  * Q_i (quality)
  * R_i (reliability)
  * Baseline (median/MAD)
  * Anomaly (A_i)
  * Hazard evidence (lightweight rules)
  * Confidence (C_h)
  * Severity/Risk (S_h, R_h)
  * Local hazard state machine
- Canonical telemetry envelope: `firmware/components/telemetry/`
- HMAC signing: `firmware/components/security/`
- Store-and-forward: `firmware/components/network/`, `firmware/components/storage/`
- Local Wi-Fi AP: `firmware/components/local_ap/`
- Captive portal: `firmware/components/local_ap/`
- Cached emergency state: `firmware/components/storage/`

### Code That MUST NOT Run on ESP32

**Prohibited (MUST stay off ESP32):**
- Fire spread propagation (arrival-time engine, ROS computation)
- Geospatial raster operations (DEM gradients, slope/aspect)
- Population exposure calculations (spatial joins, demographic overlays)
- Multi-node fusion (cross-node evidence correlation)
- Full GIS operations (PostGIS queries, geometry repair)
- Master-only intelligence layers (full evidence engine, incident correlation)
- Alert lifecycle management
- Human approval workflow
- Audit trail persistence
- Simulation orchestration
- Authority/citizen identity management

**Location for prohibited code:**
- Fire spread: `services/master-service/fire_engine/`
- Geospatial: `services/backend/modules/geospatial/`, `services/master-service/fire_engine/`
- Multi-node fusion: `services/master-service/fusion/`
- Incident correlation: `services/backend/modules/incidents/`
- Alert management: `services/backend/modules/alerts/`
- Others: `services/backend/modules/*/`

---

## Interface Boundaries

### Edge ↔ Master Interface

**Protocol**: Wi-Fi/TCP-IP (V1 PRIMARY)  
**Contract**: Canonical telemetry schema (Document 06, Section 8)  
**Authentication**: HMAC-SHA256 per-node secret  
**Replay Protection**: Sequence + timestamp  

**Edge → Master (Telemetry)**
```json
{
  "telemetry_id": "UUID",
  "node_id": "string",
  "sequence": "integer",
  "measurement_timestamp": "ISO8601",
  "receive_timestamp": "ISO8601",
  "location": {"latitude": float, "longitude": float, "altitude_m": float},
  "measurements": { /* sensor values */ },
  "diagnostics": { /* health indicators */ },
  "power": { /* battery, charging */ },
  "source": "LIVE_HARDWARE | SIMULATION",
  "schema_version": "string",
  "auth": {"hmac": "base64", "algorithm": "HMAC-SHA256"}
}
```

**Master → Edge (Commands, Future)**
- Configuration updates
- Calibration updates
- Time synchronization

**Interface Owner**: Firmware Engineer (Edge side), Network Engineer (Master side)  
**Canonical Location**: `packages/nexalert-events/src/telemetry.py`

---

### Master ↔ Backend Interface

**Protocol**: HTTP/REST + WebSocket (for real-time updates)  
**Contract**: `/api/v1/*` REST endpoints  
**Authentication**: TLS 1.2+, optional Ed25519 signed events  

**Master → Backend (Telemetry Ingestion)**
- `POST /api/v1/telemetry` - Submit canonical telemetry
- `POST /api/v1/incidents` - Report incident state changes
- `POST /api/v1/hazard-assessments` - Submit hazard assessments

**Backend → Master (Configuration, Queries)**
- `GET /api/v1/nodes/{node_id}` - Node enrollment status
- `GET /api/v1/config` - Configuration registry
- `WebSocket /api/v1/ws/alerts` - Alert stream

**Interface Owner**: Backend Engineer (Backend side), Network Engineer (Master side)  
**Canonical Location**: `services/backend/modules/api/`

---

### Backend ↔ Frontend Interface

**Protocol**: HTTP/REST + WebSocket  
**Contract**: `/api/v1/*` REST endpoints  
**Authentication**: Session cookies (Authority), JWT (Citizen), signed events (emergency)  

**Backend → Frontend (Authority)**
- `GET /api/v1/incidents` - List incidents
- `GET /api/v1/fire-spread/{incident_id}` - Fire geometry
- `POST /api/v1/alerts` - Create alert (PENDING_APPROVAL)
- `PUT /api/v1/alerts/{alert_id}/approve` - Approve alert

**Backend → Frontend (Citizen)**
- `GET /api/v1/emergency` - Current emergency state
- `GET /api/v1/safe-places` - Safe location ranking
- `POST /api/v1/sos` - Submit SOS request

**Interface Owner**: Backend Engineer (Backend side), Frontend Engineer (Frontend side)  
**Canonical Location**: `services/backend/modules/api/`, `packages/nexalert-types/`

---

### Simulation ↔ Backend Interface

**Protocol**: Same as Master ↔ Backend  
**Contract**: Same canonical telemetry schema with `source = "SIMULATION"`  
**Authentication**: SIMULATION credentials (isolated from LIVE)  

**Simulation → Backend (Virtual Telemetry)**
- `POST /api/v1/telemetry` - Submit synthetic telemetry (same endpoint, different credentials)
- `POST /api/v1/simulation/runs` - Create simulation run
- `GET /api/v1/simulation/ground-truth/{run_id}` - Retrieve ground truth (evaluator role REQUIRED)

**Interface Owner**: Simulation Engineer (Simulation side), Backend Engineer (Backend side)  
**Canonical Location**: `services/backend/modules/simulation/`

---

## Canonical Locations

### Reference Mathematics (Python)

**Location**: `packages/nexalert-math/nexalert_math/`  
**Purpose**: Golden vector generation, parity validation  
**Owner**: System Architect  
**Used By**: Backend (production), Firmware (parity tests), Tests (golden vectors)

### Production Mathematics (Backend)

**Location**: `services/backend/modules/intelligence/`, `services/backend/modules/hazards/`  
**Purpose**: Production intelligence computation  
**Owner**: Backend Engineer  
**Parity Requirement**: MUST match `packages/nexalert-math/` within documented tolerances

### Embedded Mathematics (Firmware)

**Location**: `firmware/components/intelligence/`  
**Purpose**: Lightweight edge intelligence  
**Owner**: Firmware Engineer  
**Parity Requirement**: MUST match `packages/nexalert-math/` within documented tolerances (validated via golden vectors)

### Schemas

**Telemetry Schema**: `packages/nexalert-events/src/telemetry.py`  
**Configuration Schema**: `packages/nexalert-config/src/schema.py`  
**API Contracts**: `packages/nexalert-types/src/` (TypeScript), `services/backend/modules/api/` (Python FastAPI)

### Configuration

**Registry Definition**: `packages/nexalert-config/src/registry.py` (all parameters from Document 19)  
**Environment Profiles**: `packages/nexalert-config/src/profiles.py` (DEV/TEST/SIM/STAGE/SIH/PROD)  
**Deployment Config**: `infra/ansible/` (deployment-specific values)

### Golden Vectors

**Reference Implementations**: `tests/golden-vectors/reference/`  
**Test Inputs**: `tests/golden-vectors/inputs/`  
**Expected Outputs**: `tests/golden-vectors/expected/`  
**Test Cases**: `tests/golden-vectors/test_*.py`

### Simulation

**Scenario Definitions**: `tests/scenarios/` (G01-G15 YAML files)  
**Virtual Node Generator**: `services/backend/modules/simulation/virtual_nodes.py`  
**Ground Truth Store**: `services/backend/modules/simulation/ground_truth.py`  
**Evaluator**: `services/backend/modules/simulation/evaluator.py`

### Documentation

**Specifications (READ-ONLY)**: `docs/specifications/` (DOCX), `docs/specification_text/` (Markdown)  
**Implementation Governance**: `docs/implementation/`  
**Architecture Documentation**: `docs/architecture/` (FUTURE)  
**Validation Evidence**: `docs/validation/` (FUTURE)

---

## Summary

This repository map defines:

1. **Where code belongs**: Every major subsystem has a canonical directory
2. **Who owns what**: Clear ownership for every directory
3. **ESP32 boundaries**: Explicit lists of what MUST run and MUST NOT run on ESP32
4. **Interfaces**: Contracts between Edge/Master/Backend/Frontend/Simulation
5. **Canonical locations**: Single source of truth for reference math, schemas, config, tests, docs

**When adding new code, ask**: "Which subsystem does this belong to?" and "Does this respect ESP32 boundaries?" Use this map to find the answer.

---

**END OF REPOSITORY MAP**
