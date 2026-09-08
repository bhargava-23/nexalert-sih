# Scenario Tests

**Deterministic replay scenarios for NexAlert**

## Purpose

This directory contains scenario test definitions (G01-G15) per Document 17 (Validation).

## Structure

```
scenarios/
└── *.yaml          # YAML scenario definitions (will be added in Phase 5+)
```

## Scenario Coverage

Per Document 17, 15 ground truth scenarios:
- G01-G05: Fire scenarios (detection, spread, escalation)
- G06-G08: Flood scenarios
- G09-G10: Multi-hazard scenarios
- G11-G13: Resilience scenarios (node failure, Master failure, internet loss)
- G14-G15: False alarm scenarios

## Usage

```bash
# Run all scenario tests
pytest tests/scenarios/

# Run specific scenario
pytest tests/scenarios/ -k G01
```

## Phase 3 Status

**Structure only** - No scenario definitions or test implementations yet. Will be added in Phase 5+.

## Version

0.1.0
