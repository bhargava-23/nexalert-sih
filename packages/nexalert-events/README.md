# NexAlert Event Schemas

**Canonical Python representation of cross-system event/message contracts**

## Purpose

This package defines the authoritative Python schemas (Pydantic models) for events exchanged between NexAlert subsystems:
- Telemetry envelopes from Edge nodes
- Hazard events
- Incident records
- Alert messages
- SOS requests

## Contract Governance

This package represents the **Python side** of the cross-system contract. There is ONE authoritative contract definition, with language-specific representations:

- **Python**: `packages/nexalert-events/` (this package - Pydantic models)
- **TypeScript**: `packages/nexalert-types/` (TypeScript interfaces)
- **Firmware**: C structs + serialization logic in `firmware/components/telemetry/`

**CRITICAL**: Python and TypeScript representations MUST NOT silently diverge. Schema changes require version bump in both representations.

## Installation

```bash
cd packages/nexalert-events
pip install -e .
```

## Usage

```python
from nexalert_events import telemetry, hazard, incident, alert

# Use Pydantic models for validation
envelope = telemetry.TelemetryEnvelope(...)
event = hazard.HazardEvent(...)
```

## Phase 3 Status

**Structure only** - No schema implementations yet. Event schemas will be added in Phase 4+.

## Version

0.1.0
