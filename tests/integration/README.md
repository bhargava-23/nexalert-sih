# Integration Tests

**End-to-end trace validation for NexAlert**

## Purpose

This directory contains integration tests that validate complete telemetry → incident → alert traces through the NexAlert system.

## Structure

```
integration/
└── test_*.py        # pytest test files (will be added in Phase 4+)
```

## Test Coverage

Integration tests validate:
- Telemetry ingestion and persistence
- Intelligence computation pipeline
- Hazard assessment and incident correlation
- Alert generation and approval workflow
- Multi-node scenarios
- Resilience failure modes

## Usage

```bash
# Run all integration tests
pytest tests/integration/

# Run specific test file
pytest tests/integration/test_telemetry_to_incident.py
```

## Phase 3 Status

**Structure only** - No test implementations yet. Will be added in Phase 4+.

## Version

0.1.0
