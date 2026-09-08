# Golden Vector Tests

**Mathematical parity validation for NexAlert intelligence algorithms**

## Purpose

This directory contains golden vector tests (GV-H01 through GV-GEO02) that validate mathematical parity between:
- Python reference implementation (`reference/python/`)
- Production backend implementation (`services/backend/`)
- Production Master implementation (`services/master-service/`)
- Embedded firmware implementation (`firmware/`)

## Structure

```
golden-vectors/
├── inputs/          # Test input data (will be added in Phase 4+)
├── expected/        # Expected outputs from reference implementation
└── test_*.py        # pytest test files
```

## Test Sets

Per Document 17 (Validation), 11 golden vector sets:
- GV-H01 through GV-H03: Health, Quality, Reliability computation
- GV-A01 through GV-A02: Baseline and Anomaly detection
- GV-C01 through GV-C02: Confidence and Evidence aggregation
- GV-S01 through GV-S02: Severity and Risk computation
- GV-GEO01 through GV-GEO02: Geospatial operations

## Usage

```bash
# Run all golden vector tests
pytest tests/golden-vectors/

# Run specific test set
pytest tests/golden-vectors/test_health.py
```

## Phase 3 Status

**Structure only** - No test data or test implementations yet. Will be added in Phase 4+.

## Version

0.1.0
