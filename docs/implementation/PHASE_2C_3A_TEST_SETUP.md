# Phase 2C-3A: PostgreSQL Test Setup Instructions

## Current Status

Phase 2C-3A code migration is complete:
- ✅ Dataclasses migrated (IncidentCandidate, IncidentCreationResult)
- ✅ B2 coordinator operational logic migrated
- ✅ Hazard type dependencies fixed
- ✅ Track B2 regression tests pass (10/10)

**Blocking**: Phase 2C-2 multi-hazard tests require PostgreSQL with PostGIS.

## Manual PostgreSQL Setup

Since Docker and PostgreSQL are not available on this system, follow these steps:

### Option 1: Docker (Preferred)

If Docker Desktop is available:

```bash
# Start PostgreSQL with PostGIS
docker run -d \
  --name nexalert-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=nexalert_test \
  -p 5432:5432 \
  postgis/postgis:14-3.3

# Wait for PostgreSQL to be ready
sleep 10

# Run Phase 2C-2 tests
cd C:\projects\nexalert-sih\services\backend
python -m pytest tests/test_phase_2c_2_multi_hazard.py -v

# Run all Track B2 tests
python -m pytest tests/test_regional_fusion.py -v
```

### Option 2: Install PostgreSQL

If Docker is not available, install PostgreSQL directly:

1. Download PostgreSQL 14 from https://www.postgresql.org/download/windows/
2. During installation, include PostGIS extension
3. Create test database:

```sql
CREATE DATABASE nexalert_test;
\c nexalert_test
CREATE EXTENSION IF NOT EXISTS postgis;
```

4. Run tests:

```bash
cd C:\projects\nexalert-sih\services\backend
export TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/nexalert_test"
python -m pytest tests/test_phase_2c_2_multi_hazard.py -v
python -m pytest tests/test_regional_fusion.py -v
```

## What Phase 2C-3A Accomplishes

1. **Removes operational dependencies** on legacy Incident scalar fields
2. **Makes IncidentHazardAssessment the canonical source** for hazard-specific metrics
3. **Fixes multi-hazard support** by using fusion_result.hazard_type instead of inc.hazard_type
4. **Preserves API backward compatibility** via dual-write

## Verification Checklist

When PostgreSQL is available, verify:

- [ ] Phase 2C-2 multi-hazard tests pass (8 tests)
- [ ] Track B2 regression tests still pass (10 tests)
- [ ] No operational regressions

Once all tests pass, Phase 2C-3A will be complete.
