# Fault Injection Tests

**Resilience test suite for NexAlert**

## Purpose

This directory contains fault injection tests (FI-01 through FI-14) per Document 17 (Validation).

## Structure

```
fault-injection/
└── test_*.py        # pytest test files (will be added in Phase 6+)
```

## Test Coverage

Per Document 17, 14 fault injection tests:
- FI-01 through FI-03: Node disappears, node reboots, node loses Wi-Fi
- FI-04 through FI-06: Master failure, Master reboot, Master loses internet
- FI-07 through FI-09: Backend crash, database failure, network partition
- FI-10 through FI-12: Clock skew, storage full, memory exhaustion
- FI-13 through FI-14: Message loss, message corruption

## Usage

```bash
# Run all fault injection tests
pytest tests/fault-injection/

# Run specific test
pytest tests/fault-injection/test_node_disappears.py
```

## Phase 3 Status

**Structure only** - No test implementations yet. Will be added in Phase 6+.

## Version

0.1.0
