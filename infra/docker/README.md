# NexAlert Infrastructure

**Infrastructure configuration for NexAlert**

## Docker Compose

Local development database (PostgreSQL 15 + PostGIS 3.3).

### Usage

```bash
# Start PostgreSQL
docker compose -f infra/docker/docker-compose.yml up -d

# Check status
docker compose -f infra/docker/docker-compose.yml ps

# Stop
docker compose -f infra/docker/docker-compose.yml down

# Stop and remove data
docker compose -f infra/docker/docker-compose.yml down -v
```

### Connection

```
Host: localhost
Port: 5432
Database: nexalert_dev
User: nexalert
Password: nexalert_dev_password
```

## Phase 3 Status

**Docker Compose for PostgreSQL only** - No production deployment configuration.

Production deployment will use modular monolith (NOT Docker/Kubernetes).

## Version

0.1.0
