# NexAlert SIH 2026

**Resilient AI-Powered Environmental Monitoring and Early Warning System**

---

## Project Overview

NexAlert is a distributed intelligence system for environmental hazard detection and citizen safety. It combines edge computing, geospatial reasoning, and human-in-the-loop decision-making to provide reliable early warnings for fire, flood, pollution, landslide, and extreme heat events.

**SIH 2026 Problem Statement**: SIH26178 - Resilient Environmental Monitoring and Early Warning

---

## Architecture

**Distributed Intelligence**:
```
ESP32-S3 Field Nodes → Raspberry Pi Master → Cloud Backend
     (Edge)              (Local Fusion)      (Canonical Persistence)
```

**Key Characteristics**:
- **Multi-hazard framework**: Fire (hero), Flood, Pollution, Landslide, Extreme Heat, Unknown
- **Offline resilience**: Local emergency path survives Master/internet failure
- **Human approval mandatory**: NexAlert recommends → authorized humans approve
- **Simulation-first validation**: Deterministic scenarios with ground truth separation

---

## Technology Stack

| **Component** | **Technology** |
|---|---|
| **Firmware** | ESP-IDF 5.1+, C/C++, FreeRTOS |
| **Backend** | Python 3.11+, FastAPI, PostgreSQL/PostGIS |
| **Master Service** | Python 3.11+, PostGIS |
| **Frontend** | Next.js 14+, React 18+, TypeScript, MapLibre GL JS |
| **Database** | PostgreSQL 15+, PostGIS 3.3+ |
| **Deployment** | Modular monolith (NOT microservices) |

---

## Documentation

### Primary Sources

- **Specifications** (Engineering source of truth):
  * `docs/specifications/` - 20 original DOCX files (authoritative)
  * `docs/specification_text/` - 20 extracted Markdown files (machine-readable)

### Implementation Governance

- **Constitution**: `docs/implementation/IMPLEMENTATION_CONSTITUTION.md` (26 non-negotiable rules)
- **Repository Map**: `docs/implementation/REPOSITORY_MAP.md` (subsystem boundaries, ownership)
- **Workflow**: `docs/implementation/DEVELOPMENT_WORKFLOW.md` (planning → implementation → verification → review → commit)
- **Decisions**: `docs/implementation/DECISIONS.md` (architectural decisions, clarifications)

---

## Repository Status

**Current Phase**: Phase 3: Repository Initialization (COMPLETE)

**Completed**:
- ✅ Phase 1: Architectural Reconnaissance (20 specifications analyzed, no material contradictions found)
- ✅ Phase 2: Implementation Governance (4 governance documents created, Git initialized)
- ✅ Phase 3: Repository Initialization (Complete repository skeleton and tooling foundation created)

**Next Phase**: Phase 4: Canonical Telemetry Contract + Database
- Implement PostgreSQL/PostGIS schema
- Create canonical telemetry JSON schema
- Implement Python reference math (H_i, Q_i, R_i)
- Set up golden vector framework
- Establish first acceptance gate (Gate A: Build Integrity)

---

## Key Architectural Principles

### Non-Negotiable Invariants (from Document 01)

1. **Missing ≠ zero**: Semantic distinction preserved throughout all layers
2. **measurement_timestamp ≠ receive_timestamp**: Always separate fields
3. **Confidence ≠ probability**: C_h is operational evidence-quality index, NOT calibrated probability
4. **Risk ≠ probability**: R_h is decision urgency index, NOT statistical forecast
5. **Physical footprint ≠ operational buffer**: Distinct geometric layers
6. **Master failure ≠ internet failure**: Distinct failure modes with distinct handling
7. **Multi-hazard independence**: Each hazard maintains independent reasoning vector

### Subsystem Boundaries

**ESP32 Edge Node MUST run**: Sensor sampling, lightweight edge intelligence (H_i, Q_i, R_i, baseline, anomaly, evidence, confidence, severity, risk, local hazard state), local emergency AP/captive portal

**ESP32 Edge Node MUST NOT run**: Fire spread propagation, geospatial raster operations, population exposure calculations, multi-node fusion

**Master (Raspberry Pi) MUST run**: Full intelligence stack, fire spread geospatial engine (arrival-time propagation), multi-node fusion, incident correlation

**Backend MUST run**: Canonical telemetry persistence, HMAC/signature verification, alert lifecycle, human approval workflow, audit trail, simulation orchestration

---

## Security

**Authentication**:
- Node telemetry: HMAC-SHA256 per-node secrets
- Emergency events: Ed25519 signatures
- Transport: TLS 1.2+
- Passwords: Argon2id/scrypt

**Critical Rules**:
- Secrets NEVER in source control, frontend bundles, or public config
- Replay protection: sequence + timestamp + nonce
- Human approval required for alert issuance (flag.authority_auto_dispatch = false, MUST REMAIN OFF)
- SIMULATION credentials isolated from LIVE environment

---

## Testing

**Verification Levels**: L0 (static) → L1 (unit) → L2 (component) → L3 (integration) → L4 (system) → L5 (field)

**Golden Vectors**: 11 sets (GV-H01 through GV-GEO02) for mathematical parity validation

**Acceptance Gates**: 10 gates (A-J, all PASS/BLOCK) required before release candidate

**Performance Targets**:
- Telemetry ingestion: p95 ≤ 500ms
- Critical alert decision: p95 ≤ 2s
- Soak stability: 8+ hours (24 hours preferred)

---

## Quick Start

**Prerequisites**:
- Python 3.11+
- Node.js 20+
- ESP-IDF 5.1+
- PostgreSQL 15+ with PostGIS 3.3+
- Git

**Phase 3 (Next)**: Repository initialization will create full directory structure and tooling setup.

---

## Contributing

**Workflow**: Planning → Implementation → Verification → Review → Commit

**Key Rules**:
1. **Test-before-done**: No task complete until relevant tests pass
2. **Architecture compliance**: Check IMPLEMENTATION_CONSTITUTION.md before merging
3. **Golden vector parity**: Mathematical changes MUST maintain parity
4. **Security gates**: Security-relevant changes MUST pass security tests
5. **Surface ambiguity**: When specification unclear, ask (don't guess)

See `docs/implementation/DEVELOPMENT_WORKFLOW.md` for complete workflow.

---

## License

[To be determined]

---

## Contact

[To be determined]

---

**Architecture reconnaissance complete. Ready for Phase 3: Repository Initialization.**

