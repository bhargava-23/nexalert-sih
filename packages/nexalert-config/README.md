# NexAlert Configuration Registry

**Configuration schema/structure definitions**

## Purpose

This package defines the configuration registry structure per Document 19 (Configuration Registry).

**CRITICAL: This package defines SCHEMA/STRUCTURE ONLY, NOT VALUES.**

Configuration parameter values remain in Document 19 as the source of truth. This package provides:
- Configuration classes (CONST, TUNABLE, POLICY, LIMIT, ENUM, FLAG, SECRET, PROFILE)
- Namespace definitions (edge.*, sensor.*, intelligence.*, hazard.*, fire.*, incident.*, alert.*, comm.*, security.*, sim.*, ui.*, deploy.*, flag.*)
- Schema validation structure

## Installation

```bash
cd packages/nexalert-config
pip install -e .
```

## Usage

```python
from nexalert_config import schema, registry

# Use configuration schema definitions
config_param = schema.ConfigParameter(...)
```

## Phase 3 Status

**Structure only** - No configuration values. Schema implementations will be added in Phase 4+.

## Version

0.1.0
