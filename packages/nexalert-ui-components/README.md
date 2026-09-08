# NexAlert UI Components

**Shared React components for NexAlert applications**

## Purpose

This package provides shared React components used across NexAlert frontend applications:
- Map components (MapLibre GL JS wrappers)
- Chart components
- Hazard display cards
- Design system tokens

## Installation

```bash
cd packages/nexalert-ui-components
npm install
```

## Usage

```typescript
import { HazardCard, Map } from 'nexalert-ui-components'

// Use shared components
<HazardCard hazard={...} />
<Map center={...} />
```

## Phase 3 Status

**Structure only** - No component implementations yet. Components will be added in Phase 4+.

## Version

0.1.0
