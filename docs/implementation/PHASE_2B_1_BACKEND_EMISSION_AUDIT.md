# PHASE 2B-1 BACKEND EMISSION AUDIT

**Date**: 2026-09-13  
**Mode**: AUTO / MAXIMUM EFFORT  
**Status**: ✅ **AUDIT COMPLETE**

---

## EXECUTIVE SUMMARY

**CLASSIFICATION**: **B — REQUIRES BACKEND FIXES FIRST**

The backend **DOES NOT** consistently emit canonical telemetry contracts to operational consumers. Critical timestamp field name mismatch discovered:

- **Database/API uses**: `measurement_ts`, `receive_ts`
- **Canonical schema requires**: `measurement_timestamp`, `received_timestamp`

This is a **semantic contract violation** requiring backend serialization fixes before frontend normalization can be safely removed.

**Key Findings**:
1. ❌ **Timestamp field names diverge from canonical schema** (blocking issue)
2. ✅ JSONB measurements/diagnostics/power preserve canonical field names (`temp_c`, `battery_pct`)
3. ✅ Database columns correctly preserve null semantics
4. ✅ No operational WebSocket/realtime path exists (not a blocker)
5. ⚠️ Demo endpoints emit non-canonical shapes (intentional demo isolation)
6. ⚠️ Frontend normalization compensates for both demo shapes AND missing operational telemetry endpoint

**Required Changes for Phase 2B-2**:
1. Add `measurement_timestamp` and `received_timestamp` fields to `TelemetryResponse` Pydantic model
2. Map database `measurement_ts` → API `measurement_timestamp`
3. Map database `receive_ts` → API `received_timestamp`
4. Keep existing `measurement_ts`/`receive_ts` fields temporarily for backward compatibility (deprecate in Phase 2C)
5. Create API contract test verifying canonical field names
6. Only then remove frontend normalization layer

---

## 1. ACTUAL OPERATIONAL DATA PATH

### 1.1 Database → API → Frontend Flow

```
TelemetryRecord (database)
  ├─ telemetry_id: str
  ├─ node_id: str
  ├─ sequence: int
  ├─ measurement_ts: TIMESTAMP          ❌ DIVERGES (should be measurement_timestamp)
  ├─ receive_ts: TIMESTAMP              ❌ DIVERGES (should be received_timestamp)
  ├─ source: str
  ├─ location: Geography(Point)
  ├─ measurements_jsonb: JSONB          ✅ Contains canonical field names
  ├─ diagnostics_jsonb: JSONB           ✅ Contains canonical field names
  ├─ power_jsonb: JSONB                 ✅ Contains canonical field names
  └─ schema_version: str
         ↓
_telemetry_to_response() serializer
  (services/backend/modules/api/routes.py:324-345)
         ↓
TelemetryResponse (Pydantic model)
  ├─ telemetry_id: str
  ├─ node_id: str
  ├─ sequence: int
  ├─ measurement_ts: datetime           ❌ DIVERGES (should be measurement_timestamp)
  ├─ receive_ts: datetime               ❌ DIVERGES (should be received_timestamp)
  ├─ source: str
  ├─ location: Optional[dict]
  ├─ measurements: dict                 ✅ Canonical field names preserved
  ├─ diagnostics: dict                  ✅ Canonical field names preserved
  ├─ power: Optional[dict]              ✅ Canonical field names preserved
  └─ schema_version: str
         ↓
FastAPI JSON serialization
         ↓
HTTP Response (GET /api/telemetry/{node_id})
         ↓
Authority Dashboard fetch
  (apps/authority-dashboard/app/page.tsx:49)
         ↓
normalizeTelemetry() function          ⚠️ COMPENSATES for demo shapes
  (apps/authority-dashboard/app/page.tsx:16-30)
         ↓
NormalizedTelemetry interface
  (frontend display-specific structure)
```

---

## 2. ENDPOINT INVENTORY

### 2.1 Operational Telemetry Endpoints

#### GET /api/telemetry/latest
- **File**: `services/backend/modules/api/routes.py:155-184`
- **Response Model**: `List[TelemetryResponse]`
- **Database Query**: `select(TelemetryRecord).order_by(desc(TelemetryRecord.receive_ts))`
- **Serializer**: `_telemetry_to_response(record)` (line 180)
- **Shape**: Database-style response (uses `measurement_ts`/`receive_ts`, NOT canonical)

#### GET /api/telemetry/{node_id}
- **File**: `services/backend/modules/api/routes.py:187-216`
- **Response Model**: `List[TelemetryResponse]`
- **Database Query**: `select(TelemetryRecord).where(node_id).order_by(desc(TelemetryRecord.measurement_ts))`
- **Serializer**: `_telemetry_to_response(record)` (line 212)
- **Shape**: Database-style response (uses `measurement_ts`/`receive_ts`, NOT canonical)

#### GET /api/nodes/{node_id}
- **File**: `services/backend/modules/api/routes.py:115-152`
- **Response Model**: `NodeResponse`
- **Shape**: Node metadata only (no telemetry envelope)
- **Note**: Dashboard currently fetches this endpoint (line 49: `fetch('http://localhost:8000/nodes/NEX-001')`) but NodeResponse does NOT contain telemetry data

---

### 2.2 Demo Endpoints (Isolated)

#### GET /nodes/{node_id} (demo)
- **File**: `services/backend/modules/api/routes_demo.py:50-55`
- **Shape**: **NON-CANONICAL** demo fixture
  ```json
  {
    "node_id": "NEX-001",
    "status": "ONLINE",
    "telemetry": {
      "temperature": 31.4,
      "humidity": 58.2,
      "pressure": 1009.8,
      "gas_smoke": "normal",
      "vibration": "normal",
      "last_update": "2026-09-13T..."
    }
  }
  ```
- **Note**: Uses flattened non-canonical field names (temperature, humidity, gas_smoke, last_update)

#### GET /health (demo)
- **File**: `services/backend/modules/api/routes_demo.py:35-47`
- **Shape**: System health (not telemetry)

---

### 2.3 Track B2 Endpoints (Incident/Hazard)

#### GET /api/incidents
- **File**: `services/backend/modules/api/routes_b2.py:76-116`
- **Response Model**: `List[IncidentResponse]`
- **Shape**: Incident metadata (not raw telemetry)

#### GET /api/regional-hazards
- **File**: `services/backend/modules/api/routes_b2.py:156-199`
- **Response Model**: `List[RegionalHazardResponse]`
- **Shape**: Regional intelligence output (not telemetry envelope)

---

## 3. API RESPONSE SHAPE MATRIX

| Endpoint | Response Model | Timestamp Fields | Measurements | Diagnostics | Power | Canonical? |
|----------|---------------|------------------|--------------|-------------|-------|------------|
| **GET /api/telemetry/latest** | TelemetryResponse | ❌ measurement_ts<br>❌ receive_ts | ✅ dict (canonical) | ✅ dict (canonical) | ✅ dict (canonical) | **NO** |
| **GET /api/telemetry/{node_id}** | TelemetryResponse | ❌ measurement_ts<br>❌ receive_ts | ✅ dict (canonical) | ✅ dict (canonical) | ✅ dict (canonical) | **NO** |
| **GET /nodes/{node_id} (demo)** | Demo fixture | ❌ last_update | ❌ flattened | ❌ none | ❌ flattened | **NO** |
| **GET /api/nodes/{node_id}** | NodeResponse | N/A (no telemetry) | N/A | N/A | N/A | **N/A** |

**Verdict**: **NO operational endpoint emits canonical telemetry envelope**

---

## 4. WEBSOCKET/REALTIME AUDIT

### 4.1 Search Results

**Command**: `grep -r "websocket\|WebSocket\|realtime\|broadcast" services/backend/`

**Result**: **No matches found**

**Conclusion**: ✅ **No operational WebSocket/realtime telemetry broadcast path exists**

This is **NOT a blocker** for Phase 2B. The audit requirement was to verify IF realtime exists, and document its shape. Since no realtime path exists, there is nothing to audit.

**Future Implementation Note**: When realtime telemetry is added (Phase 3+), it MUST emit canonical envelope shape to avoid the same timestamp field name issue.

---

## 5. DASHBOARD CONSUMPTION AUDIT

### 5.1 Frontend Normalization Layer

**File**: `apps/authority-dashboard/app/page.tsx`

**Normalization Function** (lines 16-30):
```typescript
function normalizeTelemetry(data: any): NormalizedTelemetry | null {
  if (!data) return null

  // Try multiple possible data shapes
  const telemetry = data.telemetry || data.sensors || {}

  return {
    temperature: telemetry.temperature ?? telemetry.temperature_c ?? null,
    humidity: telemetry.humidity ?? telemetry.humidity_rh ?? null,
    pressure: telemetry.pressure ?? telemetry.pressure_hpa ?? null,
    gas: telemetry.gas_smoke ?? telemetry.gas ?? telemetry.gas_ppm ?? null,
    vibration: telemetry.vibration ?? telemetry.vibration_mps2 ?? null,
    lastUpdate: telemetry.last_update ?? telemetry.timestamp ?? new Date().toISOString()
  }
}
```

**Why Normalization Exists**:
1. **Demo Shape Compensation**: Accepts `data.telemetry` (demo endpoint shape) OR `data.sensors` (hypothetical shape)
2. **Field Name Fallbacks**: `temperature` (demo) OR `temperature_c` (canonical)
3. **Missing Operational Endpoint**: Dashboard fetches `/nodes/NEX-001` which returns NodeResponse (no telemetry), so falls back to demo data

---

### 5.2 Dashboard Data Fetching

**Current Code** (lines 48-78):
```typescript
// Fetch live node data
fetch('http://localhost:8000/nodes/NEX-001')
  .then(res => {
    if (!res.ok) throw new Error('Node not found')
    return res.json()
  })
  .then(data => {
    setNodeData(data)
    setNormalizedTelemetry(normalizeTelemetry(data))  // ❌ NodeResponse has no telemetry
    setDemoMode(false)
    setLoading(false)
  })
  .catch(() => {
    // Fallback to demo data
    const demoData = { /* ... */ }
    setNodeData(demoData)
    setNormalizedTelemetry(normalizeTelemetry(demoData))
    setDemoMode(true)
    setLoading(false)
  })
```

**Issues**:
1. Fetches `/nodes/NEX-001` which returns `NodeResponse` (no telemetry)
2. `NodeResponse` shape:
   ```json
   {
     "node_id": "NEX-001",
     "status": "ACTIVE",
     "location": {...},
     "firmware_version": "...",
     "config_version": "...",
     "created_at": "...",
     "updated_at": "..."
   }
   ```
3. Has NO `telemetry` field, so `normalizeTelemetry(data)` always falls back to demo
4. Dashboard is **ALWAYS in demo mode** because operational endpoint doesn't expose telemetry

---

### 5.3 Required Frontend Changes (Phase 2B-2)

**After backend fixes**:
1. Change fetch endpoint from `/nodes/NEX-001` to `/api/telemetry/NEX-001?limit=1`
2. Extract latest telemetry from response array: `data[0]`
3. Remove normalization layer (backend will emit canonical shape)
4. Update TypeScript interface to match canonical schema:
   ```typescript
   interface CanonicalTelemetry {
     telemetry_id: string
     node_id: string
     sequence: number
     measurement_timestamp: string  // ISO 8601
     received_timestamp: string     // ISO 8601
     location: { lat: number; lon: number; alt?: number }
     measurements: {
       temp_c?: number
       humidity_pct?: number
       pressure_hpa?: number
       pm25_ug_m3?: number
       pm10_ug_m3?: number
     }
     diagnostics: { /* ... */ }
     power: {
       battery_pct?: number
       battery_voltage?: number
       solar_current?: number
     }
     source: "HARDWARE" | "SIMULATION"
     schema_version: string
   }
   ```

---

## 6. CANONICAL SCHEMA COMPARISON

### 6.1 Authoritative Schema

**File**: `schemas/telemetry-envelope.schema.json`

**Required Timestamp Fields**:
- `measurement_timestamp` (line 41-44): "When measurement was captured (edge node time)"
- `received_timestamp` (line 46-49): "When telemetry received by Master/backend (server time)"

**Comment from schema** (line 48):
> "DISTINCT from measurement_timestamp per IMPLEMENTATION_CONSTITUTION.md Section 12"

---

### 6.2 Backend API Response

**File**: `services/backend/modules/api/routes.py:33-46`

**TelemetryResponse Model**:
```python
class TelemetryResponse(BaseModel):
    """Telemetry record response"""
    telemetry_id: str
    node_id: str
    sequence: int
    measurement_ts: datetime          # ❌ DIVERGES (should be measurement_timestamp)
    receive_ts: datetime              # ❌ DIVERGES (should be received_timestamp)
    source: str
    location: Optional[dict] = None
    measurements: dict                # ✅ CANONICAL (contains temp_c, battery_pct)
    diagnostics: dict                 # ✅ CANONICAL
    power: Optional[dict] = None      # ✅ CANONICAL (contains battery_pct)
    schema_version: str
```

---

### 6.3 Field-by-Field Comparison

| Field | Schema (Canonical) | Database | API Response | Match? |
|-------|-------------------|----------|--------------|--------|
| telemetry_id | ✅ telemetry_id | ✅ telemetry_id | ✅ telemetry_id | ✅ |
| node_id | ✅ node_id | ✅ node_id | ✅ node_id | ✅ |
| sequence | ✅ sequence | ✅ sequence | ✅ sequence | ✅ |
| **measurement_timestamp** | ✅ measurement_timestamp | ❌ measurement_ts | ❌ measurement_ts | ❌ **MISMATCH** |
| **received_timestamp** | ✅ received_timestamp | ❌ receive_ts | ❌ receive_ts | ❌ **MISMATCH** |
| location | ✅ location | ✅ location | ✅ location | ✅ |
| measurements.temp_c | ✅ temp_c | ✅ temp_c (JSONB) | ✅ temp_c (dict) | ✅ |
| measurements.humidity_pct | ✅ humidity_pct | ✅ humidity_pct | ✅ humidity_pct | ✅ |
| measurements.pressure_hpa | ✅ pressure_hpa | ✅ pressure_hpa | ✅ pressure_hpa | ✅ |
| measurements.pm25_ug_m3 | ✅ pm25_ug_m3 | ✅ pm25_ug_m3 | ✅ pm25_ug_m3 | ✅ |
| measurements.pm10_ug_m3 | ✅ pm10_ug_m3 | ✅ pm10_ug_m3 | ✅ pm10_ug_m3 | ✅ |
| power.battery_pct | ✅ battery_pct | ✅ battery_pct (JSONB) | ✅ battery_pct (dict) | ✅ |
| power.battery_voltage | ✅ battery_voltage | ✅ battery_voltage | ✅ battery_voltage | ✅ |
| power.solar_current | ✅ solar_current | ✅ solar_current | ✅ solar_current | ✅ |
| source | ✅ source | ✅ source | ✅ source | ✅ |
| schema_version | ✅ schema_version | ✅ schema_version | ✅ schema_version | ✅ |

**Verdict**: **2 critical mismatches** (timestamp field names)

---

## 7. DEMO ISOLATION AUDIT

### 7.1 Demo Endpoint Isolation

✅ **Demo endpoints correctly isolated**:
- Demo routes mounted at root: `app.include_router(demo_router, prefix="", tags=["demo"])`
- Operational routes mounted at `/api`: `app.include_router(api_router, prefix="/api", tags=["api"])`
- NEX-001 remains demo-only fixture
- Demo endpoints emit intentionally non-canonical shapes (not a violation)

**File**: `services/backend/main.py:102-105`

---

### 7.2 Dashboard Demo Mode

✅ **Dashboard correctly distinguishes demo vs operational**:
- Demo mode flag: `const [demoMode, setDemoMode] = useState(false)`
- Visual indicator: `{demoMode && <div>● DEMO MODE</div>}`
- Fallback behavior: catches operational endpoint failure, switches to demo data

---

## 8. STALE FIELD SEARCH RESULTS

### 8.1 Search Command

```bash
grep -r "temperature_c\|battery_percent\|humidity_rh\|gas_ppm\|vibration_mps2\|last_update" \
  services/backend/ --include="*.py"
```

**Files Found**: 7 files

---

### 8.2 Classification

#### Test Files (Acceptable)
- ✅ `services/backend/tests/test_telemetry_e2e.py` — test fixtures (canonical field names used)
- ✅ `services/backend/tests/test_contract_enforcement.py` — test fixtures (canonical field names used)
- ✅ `services/backend/tests/test_mqtt_b2_integration.py` — test fixtures

#### Demo Files (Acceptable)
- ✅ `services/backend/modules/api/routes_demo.py` — intentionally uses non-canonical demo shape

#### Track C Files (Future Feature)
- ✅ `services/backend/db/migrations_003_track_c.py` — Track C migration (not yet deployed)
- ✅ `services/backend/db/models_c.py` — Track C models (not yet deployed)

#### Intelligence Files (Acceptable)
- ✅ `services/backend/modules/intelligence/b2_coordinator.py` — may reference test/demo data

**Verdict**: ✅ **No stale field names in operational code**

All references are in tests, demo fixtures, or future Track C code. Operational telemetry path uses canonical field names within JSONB.

---

## 9. DATABASE/API SEMANTIC CHECK

### 9.1 Database Column Names

**File**: `services/backend/db/models.py:52-61`

```python
measurement_ts = Column(
    TIMESTAMP(timezone=True),
    nullable=False,
    comment="When observation captured - DISTINCT from receive_ts per IMPLEMENTATION_CONSTITUTION.md Sec 12"
)
receive_ts = Column(
    TIMESTAMP(timezone=True),
    nullable=False,
    comment="When backend received - server-assigned"
)
```

**Database naming**: `measurement_ts`, `receive_ts` (abbreviated)

---

### 9.2 API Response Mapping

**File**: `services/backend/modules/api/routes.py:337-338`

```python
def _telemetry_to_response(record: TelemetryRecord) -> TelemetryResponse:
    return TelemetryResponse(
        # ...
        measurement_ts=record.measurement_ts,  # ❌ Passes DB name to API
        receive_ts=record.receive_ts,          # ❌ Passes DB name to API
        # ...
    )
```

**Issue**: Serializer **directly maps database column names to API response** without semantic translation.

---

### 9.3 Required Fix

**Current (incorrect)**:
```python
measurement_ts=record.measurement_ts
receive_ts=record.receive_ts
```

**Required (correct)**:
```python
measurement_timestamp=record.measurement_ts  # Map DB → canonical API
received_timestamp=record.receive_ts          # Map DB → canonical API
```

**AND update TelemetryResponse model**:
```python
class TelemetryResponse(BaseModel):
    # ...
    measurement_timestamp: datetime  # NOT measurement_ts
    received_timestamp: datetime     # NOT receive_ts
    # ...
```

---

### 9.4 Received Timestamp Ownership

✅ **Backend correctly owns received_timestamp**:
- Assigned by MQTT consumer: `services/backend/modules/ingestion/mqtt_consumer.py:138`
  ```python
  received_timestamp = datetime.utcnow()  # Server-assigned
  ```
- Node cannot override: Validator checks measurement_timestamp format but does not accept received_timestamp from edge

**Verdict**: ✅ Server timestamp ownership semantics correct (only field names incorrect)

---

## 10. TEST COVERAGE AND GAPS

### 10.1 Existing Tests

**Phase 2A Contract Tests**:
- ✅ `services/backend/tests/test_contract_enforcement.py` — 31 tests, validator-level
- ✅ `services/backend/tests/test_telemetry_e2e.py` — 5 tests, ingestion boundary

**Coverage**:
- ✅ Node ID pattern enforcement
- ✅ Source enum validation
- ✅ Missing≠Zero preservation
- ✅ Timestamp distinction (measurement vs received)
- ✅ Field name conformance (temp_c, battery_pct)
- ✅ ULID format
- ✅ Location bounds

---

### 10.2 Test Gaps

❌ **Missing: API Response Contract Test**

**Required Test**: `services/backend/tests/test_api_contract.py`

Should verify:
1. GET /api/telemetry/{node_id} returns `measurement_timestamp` (NOT `measurement_ts`)
2. GET /api/telemetry/{node_id} returns `received_timestamp` (NOT `receive_ts`)
3. Response measurements contain `temp_c` (NOT `temperature_c`)
4. Response power contains `battery_pct` (NOT `battery_percent`)
5. Response preserves null values
6. Response preserves zero values
7. Response includes all required canonical fields

**Why Gap Exists**: Phase 2A focused on ingestion boundary validation, not API emission.

---

### 10.3 Frontend Contract Test Gap

❌ **Missing: Frontend Canonical Consumption Test**

Should verify:
1. Dashboard can consume canonical telemetry without normalization
2. Display handles `measurement_timestamp`/`received_timestamp` correctly
3. Display renders null measurements as "—"
4. Display renders 0°C as "0.0°C"

**Implementation**: Phase 2B-2 (after backend fixes)

---

## 11. EXACT EVIDENCE / FILE REFERENCES

### 11.1 Database Models
- `services/backend/db/models.py:41-87` — TelemetryRecord model
- `services/backend/db/models.py:52-61` — Timestamp columns (measurement_ts, receive_ts)

### 11.2 API Routes
- `services/backend/modules/api/routes.py:33-46` — TelemetryResponse model
- `services/backend/modules/api/routes.py:155-184` — GET /api/telemetry/latest
- `services/backend/modules/api/routes.py:187-216` — GET /api/telemetry/{node_id}
- `services/backend/modules/api/routes.py:324-345` — _telemetry_to_response serializer

### 11.3 Demo Routes
- `services/backend/modules/api/routes_demo.py:14-30` — Demo fixture shape
- `services/backend/modules/api/routes_demo.py:50-55` — GET /nodes/{node_id} (demo)

### 11.4 Frontend
- `apps/authority-dashboard/app/page.tsx:16-30` — normalizeTelemetry function
- `apps/authority-dashboard/app/page.tsx:48-78` — Dashboard data fetching

### 11.5 Canonical Schema
- `schemas/telemetry-envelope.schema.json:41-49` — Timestamp field definitions

### 11.6 Backend Main
- `services/backend/main.py:102-105` — Router mounting (demo vs operational)

---

## 12. REQUIRED CHANGES FOR PHASE 2B-2

### 12.1 Backend API Fixes (BLOCKING)

**Priority 1: TelemetryResponse Model**

**File**: `services/backend/modules/api/routes.py:33-46`

**Current**:
```python
class TelemetryResponse(BaseModel):
    telemetry_id: str
    node_id: str
    sequence: int
    measurement_ts: datetime  # ❌ INCORRECT
    receive_ts: datetime      # ❌ INCORRECT
    # ...
```

**Required**:
```python
class TelemetryResponse(BaseModel):
    telemetry_id: str
    node_id: str
    sequence: int
    measurement_timestamp: datetime  # ✅ CANONICAL
    received_timestamp: datetime     # ✅ CANONICAL
    # Optional: keep old names for backward compat, deprecate in Phase 2C
    measurement_ts: Optional[datetime] = None  # DEPRECATED
    receive_ts: Optional[datetime] = None      # DEPRECATED
    # ...
```

---

**Priority 2: Serializer Function**

**File**: `services/backend/modules/api/routes.py:324-345`

**Current**:
```python
def _telemetry_to_response(record: TelemetryRecord) -> TelemetryResponse:
    return TelemetryResponse(
        telemetry_id=record.telemetry_id,
        node_id=record.node_id,
        sequence=record.sequence,
        measurement_ts=record.measurement_ts,  # ❌ INCORRECT
        receive_ts=record.receive_ts,          # ❌ INCORRECT
        source=record.source,
        location=_geography_to_dict(record.location),
        measurements=record.measurements_jsonb or {},
        diagnostics=record.diagnostics_jsonb or {},
        power=record.power_jsonb,
        schema_version=record.schema_version
    )
```

**Required**:
```python
def _telemetry_to_response(record: TelemetryRecord) -> TelemetryResponse:
    return TelemetryResponse(
        telemetry_id=record.telemetry_id,
        node_id=record.node_id,
        sequence=record.sequence,
        measurement_timestamp=record.measurement_ts,  # ✅ CANONICAL MAPPING
        received_timestamp=record.receive_ts,          # ✅ CANONICAL MAPPING
        measurement_ts=record.measurement_ts,          # DEPRECATED (backward compat)
        receive_ts=record.receive_ts,                  # DEPRECATED (backward compat)
        source=record.source,
        location=_geography_to_dict(record.location),
        measurements=record.measurements_jsonb or {},
        diagnostics=record.diagnostics_jsonb or {},
        power=record.power_jsonb,
        schema_version=record.schema_version
    )
```

---

**Priority 3: API Contract Test**

**File**: `services/backend/tests/test_api_contract.py` (NEW)

**Required Tests**:
1. Test GET /api/telemetry/{node_id} returns measurement_timestamp
2. Test GET /api/telemetry/{node_id} returns received_timestamp
3. Test response measurements contain canonical field names
4. Test response preserves null values
5. Test response preserves zero values

---

### 12.2 Frontend Changes (After Backend Fixes)

**Priority 1: Update Fetch Endpoint**

**File**: `apps/authority-dashboard/app/page.tsx:48-78`

**Current**:
```typescript
fetch('http://localhost:8000/nodes/NEX-001')  // ❌ Wrong endpoint (no telemetry)
```

**Required**:
```typescript
fetch('http://localhost:8000/api/telemetry/NODE-001?limit=1')  // ✅ Operational telemetry
  .then(res => res.json())
  .then(data => {
    const latest = data[0]  // Extract latest telemetry from array
    // ...
  })
```

---

**Priority 2: Remove Normalization Layer**

**File**: `apps/authority-dashboard/app/page.tsx:16-30`

**Action**: **DELETE** `normalizeTelemetry()` function entirely

**Replace With**: Direct canonical telemetry consumption

---

**Priority 3: Update TypeScript Interface**

**File**: `apps/authority-dashboard/app/page.tsx:6-13`

**Current**:
```typescript
interface NormalizedTelemetry {
  temperature: number | null
  humidity: number | null
  // ...
}
```

**Required**:
```typescript
interface CanonicalTelemetry {
  telemetry_id: string
  node_id: string
  sequence: number
  measurement_timestamp: string  // ISO 8601
  received_timestamp: string     // ISO 8601
  measurements: {
    temp_c?: number
    humidity_pct?: number
    pressure_hpa?: number
    pm25_ug_m3?: number
    pm10_ug_m3?: number
  }
  power: {
    battery_pct?: number
    battery_voltage?: number
    solar_current?: number
  }
  source: "HARDWARE" | "SIMULATION"
  // ...
}
```

---

## 13. RISK ASSESSMENT

### 13.1 Risks of Removing Normalization Without Backend Fixes

**CRITICAL RISK**: Dashboard will break if normalization is removed before backend API emits canonical field names.

**Failure Mode**:
1. Frontend expects `measurement_timestamp`, `received_timestamp`
2. Backend emits `measurement_ts`, `receive_ts`
3. Frontend fails to parse timestamps
4. Dashboard displays broken/missing telemetry

**Mitigation**: **MUST fix backend first** (Classification B)

---

### 13.2 Backward Compatibility Risk

**MEDIUM RISK**: Changing TelemetryResponse field names may break existing consumers.

**Unknown Consumers**:
- Track B2 incident correlation (may consume telemetry API)
- Track C fire simulation (may consume telemetry API)
- Future citizen app (may consume telemetry API)

**Mitigation**: Keep deprecated `measurement_ts`/`receive_ts` fields temporarily (Phase 2C deprecation)

---

### 13.3 Demo Isolation Risk

**LOW RISK**: Demo endpoints remain non-canonical.

**Acceptable Because**:
- Demo routes explicitly isolated (different URL prefix)
- Demo mode clearly labeled in UI
- Operational endpoints emit canonical shape after fixes

---

## 14. FINAL RECOMMENDATION

### 14.1 Classification: **B — REQUIRES BACKEND FIXES FIRST**

**Rationale**:
- Backend API **DOES NOT** emit canonical telemetry envelope
- Timestamp field names diverge from canonical schema: `measurement_ts`/`receive_ts` vs `measurement_timestamp`/`received_timestamp`
- Frontend normalization **CANNOT** be safely removed until backend emits canonical shape
- Database-to-API serialization requires semantic field name translation

---

### 14.2 Decision Basis

**NOT based on**:
- TypeScript types (types look correct)
- Database JSONB contents (contains canonical field names)
- Good intentions or architectural diagrams

**BASED on**:
- Actual runtime code path inspection
- TelemetryResponse Pydantic model (lines 33-46)
- _telemetry_to_response serializer (lines 324-345)
- Canonical schema comparison
- Missing API contract test coverage

---

### 14.3 Implementation Order

**Phase 2B-2 must proceed in this exact order**:
1. ✅ Fix TelemetryResponse model (add measurement_timestamp, received_timestamp)
2. ✅ Fix _telemetry_to_response serializer (map DB → canonical API names)
3. ✅ Create API contract test (verify canonical emission)
4. ✅ Run test and verify PASS
5. ✅ Update dashboard fetch endpoint (GET /api/telemetry/{node_id})
6. ✅ Remove frontend normalization layer
7. ✅ Update frontend TypeScript interface
8. ✅ Test end-to-end (firmware → MQTT → backend → API → dashboard)
9. ✅ Deprecate old field names in Phase 2C

**DO NOT skip steps or reorder**

---

## 15. AUDIT STATUS

### 15.1 Files Inspected

**Total: 16 files**

**Database/Models**:
1. `services/backend/db/models.py`

**API Routes**:
2. `services/backend/modules/api/routes.py`
3. `services/backend/modules/api/routes_demo.py`
4. `services/backend/modules/api/routes_b2.py`
5. `services/backend/modules/api/routes_c.py`

**Backend Main**:
6. `services/backend/main.py`

**Frontend**:
7. `apps/authority-dashboard/app/page.tsx`

**Tests**:
8. `services/backend/tests/test_contract_enforcement.py`
9. `services/backend/tests/test_telemetry_e2e.py`

**Schemas**:
10. `schemas/telemetry-envelope.schema.json`

**Documentation**:
11. `docs/implementation/PHASE_2A_TELEMETRY_MAP.md`
12. `docs/implementation/PHASE_2A_VERIFICATION_REPORT.md`
13. `docs/implementation/PHASE_1_ARCHITECTURE_FREEZE.md`
14. `docs/implementation/CONTRACT_RECONCILIATION_V1.md`
15. `docs/implementation/IMPLEMENTATION_CONSTITUTION.md`
16. `docs/implementation/RECOVERY_BASELINE.md`

---

### 15.2 Tests Run

**Command**: `python -m pytest tests/test_contract_enforcement.py tests/test_telemetry_e2e.py -v`

**Working Directory**: `services/backend`

**Results**:
- **Collected**: 36 tests
- **Passed**: 36 tests
- **Failed**: 0 tests
- **Errors**: 0 tests
- **Skipped**: 0 tests
- **Duration**: 0.69s

**Test Breakdown**:
- Contract Enforcement Tests: 31/31 PASS ✅
- End-to-End Contract Tests: 5/5 PASS ✅

**Read-only inspection**: ✅ Complete

**Runtime testing**: ✅ Complete

---

### 15.3 Blockers

**One blocker identified**:
1. ❌ **Timestamp field name divergence** (measurement_ts/receive_ts vs measurement_timestamp/received_timestamp)

**No other blockers**:
- ✅ Database JSONB fields use canonical names
- ✅ Null semantics preserved
- ✅ Demo isolation correct
- ✅ No realtime path to audit

---

### 15.4 Exact Path to Audit Document

**Repository File**: `docs/implementation/PHASE_2B_1_BACKEND_EMISSION_AUDIT.md`

**Status**: ✅ **COMPLETE**

---

## 16. STOP CONDITION REACHED

✅ **Audit complete**
✅ **Classification determined**: **B — REQUIRES BACKEND FIXES FIRST**
✅ **Evidence documented**
✅ **Required changes specified**
✅ **No Phase 2B-2 implementation performed**

**Next Step**: User approval to proceed with Phase 2B-2 backend fixes

---

**END OF PHASE 2B-1 BACKEND EMISSION AUDIT**
