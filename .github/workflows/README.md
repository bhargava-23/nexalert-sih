# NexAlert CI/CD

**Continuous Integration workflows for NexAlert**

## GitHub Actions Workflows

### CI Workflow

`.github/workflows/ci.yml` runs on every push and pull request:

**Platform-independent jobs** (always run):
- `format-python`: Python formatting and linting (black, ruff)
- `lint-typescript`: TypeScript linting and type checking
- `test-python`: Python unit tests (with PostgreSQL service)
- `build-frontend`: Next.js builds
- `format-cpp`: C/C++ formatting (clang-format)

**ESP-IDF firmware build** (separate optional job):
- Checks for ESP-IDF availability
- Skips with informational message if ESP-IDF not available
- Builds firmware if ESP-IDF 5.1.x present
- Fails if build fails (when ESP-IDF available)

## Local CI Verification

```bash
# Run all linters locally
./scripts/lint-all.sh

# Run Python tests
cd services/backend && pytest
cd services/master-service && pytest

# Build frontend
npm run build

# Build firmware (requires ESP-IDF 5.1.x)
cd firmware && idf.py build
```

## Phase 3 Status

**CI skeleton only** - Platform-independent checks configured. Additional test jobs will be added in Phase 4+.

## Version

0.1.0
