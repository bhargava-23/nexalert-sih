# Security Tests

**Security test suite for NexAlert**

## Purpose

This directory contains security tests (SEC-01 through SEC-14) per Document 17 (Validation).

## Structure

```
security/
└── test_*.py        # pytest test files (will be added in Phase 5+)
```

## Test Coverage

Per Document 17, 14 security tests:
- SEC-01 through SEC-03: HMAC authentication and verification
- SEC-04 through SEC-05: Replay protection
- SEC-06 through SEC-08: Ed25519 signature verification
- SEC-09 through SEC-11: TLS and transport security
- SEC-12 through SEC-14: Secrets management and access control

## Usage

```bash
# Run all security tests
pytest tests/security/

# Run specific test
pytest tests/security/test_hmac.py
```

## Phase 3 Status

**Structure only** - No test implementations yet. Will be added in Phase 5+.

## Version

0.1.0
