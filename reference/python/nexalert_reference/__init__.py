"""NexAlert Reference Math Package

This package contains the canonical mathematical reference implementation
for NexAlert intelligence algorithms.

PURPOSE: Golden vector generation and parity validation ONLY.

CRITICAL: This package MUST NOT be imported by production code.
- ALLOWED: tests/golden-vectors/ (for validation)
- FORBIDDEN: services/backend, services/master-service, firmware

Production implementations must be independent and validated against
this reference via golden vectors.
"""

__version__ = "0.1.0"
