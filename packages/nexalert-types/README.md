# NexAlert TypeScript Shared Types

**TypeScript representation of cross-system event/message contracts**

## Purpose

This package defines the TypeScript type definitions for events exchanged between NexAlert subsystems.

## Contract Governance

This package represents the **TypeScript side** of the cross-system contract. There is ONE authoritative contract definition, with language-specific representations:

- **Python**: `packages/nexalert-events/` (Pydantic models)
- **TypeScript**: `packages/nexalert-types/` (this package - TypeScript interfaces)
- **Firmware**: C structs + serialization logic in `firmware/components/telemetry/`

**CRITICAL**: Python and TypeScript representations MUST NOT silently diverge. Schema changes require version bump in both representations.

## Installation

```bash
cd packages/nexalert-types
npm install
```

## Usage

```typescript
import { TelemetryEnvelope, HazardEvent } from 'nexalert-types'

// Use TypeScript types for type safety
const envelope: TelemetryEnvelope = {...}
```

## Phase 3 Status

**Structure only** - No type definitions yet. Type definitions will be added in Phase 4+.

## Version

0.1.0
