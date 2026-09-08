# Database Migrations

**PostgreSQL/PostGIS schema migrations for NexAlert**

## Overview

This directory contains Alembic database migrations for the NexAlert backend database.

## Configuration

- **Database**: PostgreSQL 15+ with PostGIS 3.3+
- **Migration Tool**: Alembic
- **ORM**: SQLAlchemy 2.0

## Files

```
migrations/
├── alembic.ini         # Alembic configuration
├── env.py              # Alembic environment script
└── versions/           # Migration scripts (will be added in Phase 4+)
```

## Usage

```bash
# Create a new migration
alembic revision -m "description"

# Run migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current version
alembic current
```

## Phase 3 Status

**Structure only** - No business schema migrations yet. Migration framework setup only.

Business schema migrations will be added in Phase 4+ (Canonical Telemetry Contract + Database).

## Version

0.1.0
