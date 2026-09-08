# NexAlert Reference Math

**Canonical mathematical reference implementation for NexAlert intelligence algorithms**

## Purpose

This package contains the canonical Python reference implementation of NexAlert's intelligence algorithms.

**CRITICAL: This package is for VALIDATION ONLY**

- ✅ **ALLOWED**: Import by `tests/golden-vectors/` for golden vector generation and parity validation
- ❌ **FORBIDDEN**: Import by production code (`services/backend`, `services/master-service`, `firmware/`)

## Rationale

Production implementations (Python backend, Python Master service, C/C++ firmware) must be **independent** implementations appropriate for their runtime environment. They are **validated against** this reference via golden vectors, but **never import** this package at runtime.

This approach ensures:
- No runtime dependency on reference math
- Each implementation optimized for its environment
- Mathematical parity enforced through automated testing

## Installation

```bash
cd reference/python
pip install -e .[dev]
```

## Usage

**For test/validation code only:**

```python
from nexalert_reference import health, quality, reliability

# Generate golden vectors for validation
h_i = health.compute_health(...)
q_i = quality.compute_quality(...)
```

## Phase 3 Status

**Structure only** - No implementations yet. Algorithm implementations will be added in Phase 4+.

## Version

0.1.0
