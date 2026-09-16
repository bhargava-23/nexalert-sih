# Phase 2A: Telemetry Pipeline Audit

**Status**: Pre-Implementation Audit Complete  
**Date**: 2026-09-13  
**Purpose**: Map all telemetry producers, consumers, validators, and transport paths before enforcing canonical contract

---

## EXECUTIVE SUMMARY

### Canonical Contract Authority

**Authoritative Schema**: `schemas/telemetry-envelope.schema.json`  
**Pattern**: 18 required fields, typed units, null semantics, HARDWARE/SIMULATION distinction

### Contract Violations Discovered

1. **Field Name Divergence**: `battery_pct` (schema) vs `battery_percent` (packages/nexalert-events, nexalert-types)
2. **Measurement Field Names**: `temp_c` (schema) vs `temperature_c` (packages)
3. **Node Identity Enforcement**: Validator too permissive (accepts NODE-1, NODE-01)
4. **Topic Hardcoding**: Multiple locations with hardcoded "node1" instead of dynamic node_id
5. **Frontend Normalization**: Dashboard accepts multiple telemetry shapes (temporary mitigation)

### Pipeline Status

✅ **Firmware → MQTT**: Canonical envelope generation (telemetry_envelope.c)  
❌ **MQTT Topic**: Hardcoded "node1" in multiple locations  
✅ **MQTT → Backend**: Schema validation exists but not enforced at boundary  
✅ **Backend → Database**: Timestamp semantics correct (measurement_ts, receive_ts)  
❌ **Database → API**: Field name mismatches (battery_pct in schema, battery_percent in types)  
❌ **API → Frontend**: Multiple shape normalization required

---

## PART 1: TELEMETRY PRODUCERS

### 1.1 Firmware Telemetry Generation

**Module**: `firmware/components/telemetry/telemetry_envelope.c`  
**Authority**: Implements `schemas/telemetry-envelope.schema.json`

**Initialization**:
```c
esp_err_t telemetry_envelope_init(const telemetry_config_t* config)
// Input: node_id (e.g., "NODE-001"), lat, lon, alt
// State: Stores node_id, location, initializes sequence counter
```

**Generation**:
```c
esp_err_t telemetry_envelope_generate(
    const measurements_t* measurements,
    const diagnostics_t* diagnostics,
    const power_t* power,
    char** out_json
)
```

**Output Contract**:
- Schema version: `"telemetry.v1"` (hardcoded line 94)
- telemetry_id: ULID format (26 characters)
- node_id: From init config (line 24)
- sequence: Monotonic counter (line 97)
- measurement_timestamp: UTC ISO 8601 (line 109)
- received_timestamp: **NOT SET** (added by backend on receipt)
- location: lat, lon, alt from config
- measurements: temp_c, humidity_pct, pressure_hpa, pm25_ug_m3, pm10_ug_m3
- diagnostics: uptime_s, self_test_passed, comm_integrity, calibration_valid, stability_index
- power: battery_pct, battery_voltage, solar_current
- source: `"HARDWARE"` (hardcoded line 181)

**Missing ≠ Zero**: ✅ **CORRECT**
- Uses NAN for missing float values (line 36-40 of telemetry_envelope.h)
- cJSON serialization: `isnan(value) ? cJSON_CreateNull() : cJSON_CreateNumber(value)` (lines 129-176)
- JSON output: `null` for missing, never 0.0

**Field Names**: ✅ **MATCH SCHEMA**
- temp_c, humidity_pct, pressure_hpa (match schema exactly)
- battery_pct (matches schema, NOT battery_percent)

---

### 1.2 Firmware MQTT Publisher

**Module**: `firmware/components/network/mqtt_client.c`  
**Topic Construction**: Line 75-76

**Current Implementation**:
```c
snprintf(mqtt_state.topic, sizeof(mqtt_state.topic),
         "Nexalert/telemetry/%s", params->node_id);
```

**✅ Correct Pattern**: `Nexalert/telemetry/<node_id>`  
**❌ Hardcoded Default**: Multiple locations use "node1" as default node_id

**Topic Hardcoding Locations**:
1. `firmware/components/config/node_config.c:40` — Default: `"Nexalert/telemetry/node1"`
2. `firmware/components/config/node_config.c:24` — Default node_id: `"node1"` (should be NODE-001)
3. `firmware/components/network/include/nexalert_mqtt.h:6` — Comment: "Topic: Nexalert/telemetry/node1"
4. `services/backend/config.py:34` — Default: `"Nexalert/telemetry/node1"`

**Required Fix**: Change default node_id from "node1" to "NODE-001" (canonical format)

---

### 1.3 Firmware Configuration

**Module**: `firmware/components/config/node_config.c`

**Default Node Identity** (Line 23-28):
```c
.identity = {
    .node_id = "node1",  // ❌ Should be "NODE-001"
    .latitude = 12.9716,
    .longitude = 77.5946,
    .altitude = 920.0f,
},
```

**MQTT Topic Validation** (Line 150-153):
```c
// MQTT topic matches canonical format (starts with "Nexalert/telemetry/")
if (strncmp(config->mqtt.topic, "Nexalert/telemetry/", 19) != 0) {
    ESP_LOGE(TAG, "MQTT topic must start with 'Nexalert/telemetry/' (got: %s)",
             config->mqtt.topic);
```

✅ **Topic prefix validation exists**  
❌ **Does NOT validate node_id format** (NODE-[0-9]{3,})

---

## PART 2: TELEMETRY TRANSPORT

### 2.1 MQTT Topics

**Canonical Format**: `Nexalert/telemetry/<node_id>`  
**Wildcard Subscription**: `Nexalert/telemetry/+`

**Producer Topics** (Firmware):
- Dynamically constructed: `Nexalert/telemetry/{node_id}` ✅
- Default: `Nexalert/telemetry/node1` ❌ (should be NODE-001)

**Consumer Topics** (Backend):
- Wildcard: `Nexalert/telemetry/+` ✅ (services/backend/tests/test_mqtt_b2_integration.py:31)
- Wildcard: `Nexalert/telemetry/+` ✅ (scripts/pi_mqtt_subscriber.py:30)

**Contract**: ✅ Topic construction correct, ❌ Default node_id incorrect

---

### 2.2 MQTT Message Format

**Encoding**: UTF-8 JSON string  
**QoS**: 1 (at least once delivery)  
**Retain**: Not retained  
**Payload**: Complete telemetry envelope JSON

**Example** (`services/backend/test_telemetry.json`):
```json
{
  "schema_version": "telemetry.v1",
  "telemetry_id": "01J0000000000000000000TEST",
  "node_id": "NODE-001",  // ✅ Canonical format
  "sequence": 1,
  "measurement_timestamp": "2026-09-09T15:30:00Z",
  "received_timestamp": "2026-09-09T15:30:01Z",
  "location": {"lat": 12.9716, "lon": 77.5946, "alt": null},
  "measurements": {
    "temp_c": 38.5,
    "humidity_pct": 22.0,
    "pressure_hpa": null,
    "pm25_ug_m3": 145.3,
    "pm10_ug_m3": null
  },
  "diagnostics": {
    "uptime_s": 86400,
    "self_test_passed": true,
    "comm_integrity": 0.98,
    "calibration_valid": true,
    "stability_index": null
  },
  "power": {
    "battery_pct": 87.5,  // ✅ Matches schema
    "battery_voltage": 3.72,
    "solar_current": null
  },
  "source": "SIMULATION"
}
```

**Field Names**: ✅ All match canonical schema

---

## PART 3: TELEMETRY CONSUMERS

### 3.1 Backend MQTT Consumer

**Module**: `services/backend/modules/ingestion/mqtt_consumer.py`

**Subscription**: Line 90-92
```python
client.subscribe(self.topic, qos=1)  # topic = "Nexalert/telemetry/+"
```

**Message Processing Pipeline** (Line 123-169):
```
Raw MQTT Payload (bytes)
  ↓ parse_telemetry_payload()
JSON Dict
  ↓ validator.validate()
Validated Payload
  ↓ persister.persist_telemetry()
Database Record
  ↓ B2 Coordinator (Track B2 integration)
Regional Intelligence
```

**received_timestamp Assignment**: Line 138
```python
received_timestamp = datetime.utcnow()  # ✅ Server-assigned
```

**Statistics Tracking**:
- messages_received
- messages_valid
- messages_invalid
- messages_persisted
- messages_failed
- messages_duplicate

---

### 3.2 Backend Validator

**Module**: `services/backend/modules/ingestion/validator.py`

**Schema Loading**: Line 30-34
```python
schema_file = Path(schema_path)
with open(schema_file, "r") as f:
    self.schema = json.load(f)
self.validator = Draft7Validator(self.schema)
```

**Validation**: Line 36-71
```python
def validate(self, payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    # 1. JSON schema validation
    validate(instance=payload, schema=self.schema)
    
    # 2. Semantic validation
    error = self._validate_semantics(payload)
```

**Semantic Validation** (Line 73-128):
1. **telemetry_id**: ULID format check ✅
2. **node_id**: `node_id.startswith("NODE-")` ❌ **TOO PERMISSIVE**
   - Accepts: NODE-1, NODE-01, NODE-001, NODE-0001
   - Should enforce: `^NODE-[0-9]{3,}$`
3. **Timestamps**: ISO 8601 parsing ✅
4. **Source enum**: HARDWARE | SIMULATION ✅
5. **Location bounds**: lat [-90,90], lon [-180,180] ✅
6. **Missing ≠ Zero warning**: Logs warning for value==0 (line 119-127) ✅

**Contract Violation**: Node ID validation too permissive (line 88-90)

---

### 3.3 Backend Persister

**Module**: `services/backend/modules/ingestion/persister.py`

**Persistence Pipeline**:
```
Validated Telemetry
  ↓ _upsert_node() — Register/update node
  ↓ _check_duplicate() — Idempotency check (node_id, sequence)
  ↓ _insert_telemetry() — Insert TelemetryRecord
  ↓ session.commit()
Database
```

**Timestamp Handling** (Line 26, 156-175):
```python
async def persist_telemetry(
    self,
    session: AsyncSession,
    payload: Dict[str, Any],
    received_timestamp: datetime  # ✅ Server-assigned, passed from consumer
)
```

**Database Mapping**:
- measurement_timestamp → measurement_ts ✅
- received_timestamp → receive_ts ✅
- measurements → measurements_jsonb (JSONB) ✅
- diagnostics → diagnostics_jsonb (JSONB) ✅
- power → power_jsonb (JSONB) ✅

**Missing ≠ Zero**: ✅ JSONB preserves null values

---

### 3.4 Database Schema

**Module**: `services/backend/db/models.py`

**TelemetryRecord Model** (Lines 41-87):
```python
class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"
    
    telemetry_id = Column(String(64), primary_key=True)
    node_id = Column(String(64), ForeignKey("nodes.node_id"), nullable=False)
    sequence = Column(BigInteger, nullable=False)
    
    # ✅ Two distinct timestamps
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
    
    source = Column(String(32), nullable=False)  # HARDWARE, SIMULATION
    location = Column(Geography("Point", srid=4326))
    
    # ✅ JSONB preserves null values (MISSING ≠ ZERO)
    measurements_jsonb = Column(
        JSONB,
        nullable=False,
        comment="Sensor readings - NULL values preserve missing != zero"
    )
    diagnostics_jsonb = Column(JSONB, nullable=False, comment="D_ij diagnostic dimensions")
    power_jsonb = Column(JSONB, comment="Power/battery state")
    
    schema_version = Column(String(32), nullable=False)
```

**Unique Constraint**: (node_id, sequence) — Idempotency ✅

**Timestamp Semantics**: ✅ **CORRECT** (two distinct columns with explicit comments)

---

### 3.5 Backend API

**Module**: `services/backend/modules/api/routes.py`

**TelemetryResponse Model** (Lines 33-46):
```python
class TelemetryResponse(BaseModel):
    telemetry_id: str
    node_id: str
    sequence: int
    measurement_ts: datetime  # ✅ Matches database column
    receive_ts: datetime      # ✅ Matches database column
    source: str
    location: Optional[dict] = None
    measurements: dict        # ✅ JSONB as dict
    diagnostics: dict         # ✅ JSONB as dict
    power: Optional[dict] = None
    schema_version: str
```

**Field Names**: ✅ API response matches database schema (measurement_ts, receive_ts)

---

## PART 4: FRONTEND CONSUMERS

### 4.1 Authority Dashboard

**Module**: `apps/authority-dashboard/app/page.tsx`

**Telemetry Fetching** (Line 48-78):
```typescript
fetch('http://localhost:8000/nodes/NEX-001')  // ❌ Demo uses NEX-001
  .then(res => res.json())
  .then(data => {
    setNodeData(data)
    setNormalizedTelemetry(normalizeTelemetry(data))  // ❌ Normalization layer
    setDemoMode(false)
  })
  .catch(() => {
    // Fallback to demo data
    const demoData = { /* ... */ }
    setNormalizedTelemetry(normalizeTelemetry(demoData))
    setDemoMode(true)
  })
```

**Normalization Layer** (Lines 16-30):
```typescript
function normalizeTelemetry(data: any): NormalizedTelemetry | null {
  if (!data) return null
  
  // ❌ Accepts multiple shapes
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

**Contract Violation**: Accepts `data.telemetry` OR `data.sensors` (multiple shapes)

**Missing ≠ Zero**: ✅ **CORRECT**
```typescript
function TelemetryCard({ label, value, unit, icon }) {
  const displayValue = (() => {
    if (value === null || value === undefined) return '—'  // ✅ Renders missing as "—"
    if (typeof value === 'number') return value.toFixed(1)
    return value
  })()
  // ...
}
```

---

### 4.2 TypeScript Type Definitions

**Module**: `packages/nexalert-types/src/telemetry.ts`

**Power Interface** (Lines 21-25):
```typescript
export interface Power {
  battery_voltage?: number;
  solar_current?: number;
  battery_percent?: number;  // ❌ Schema uses battery_pct
}
```

**Measurements Interface** (Lines 27-33):
```typescript
export interface Measurements {
  temperature_c?: number;    // ❌ Schema uses temp_c
  humidity_pct?: number;     // ✅ Matches schema
  pressure_hpa?: number;     // ✅ Matches schema
  pm25_ug_m3?: number;       // ✅ Matches schema
  pm10_ug_m3?: number;       // ✅ Matches schema
}
```

**Contract Violations**:
1. `battery_percent` should be `battery_pct`
2. `temperature_c` should be `temp_c`

---

### 4.3 Python Type Definitions

**Module**: `packages/nexalert-events/nexalert_events/telemetry.py`

**Power Model** (Lines 28-32):
```python
class Power(BaseModel):
    battery_voltage: Optional[float] = None
    solar_current: Optional[float] = None
    battery_percent: Optional[float] = Field(None, ge=0, le=100)  # ❌ Schema uses battery_pct
```

**Measurements Model** (Lines 35-41):
```python
class Measurements(BaseModel):
    temperature_c: Optional[float] = None  # ❌ Schema uses temp_c
    humidity_pct: Optional[float] = None   # ✅ Matches schema
    pressure_hpa: Optional[float] = None   # ✅ Matches schema
    pm25_ug_m3: Optional[float] = None     # ✅ Matches schema
    pm10_ug_m3: Optional[float] = None     # ✅ Matches schema
```

**Contract Violations**: Same as TypeScript types

---

## PART 5: FIELD NAME DIVERGENCE MATRIX

| Field | Schema | Firmware | Backend DB | Backend API | TS Types | Python Types | Status |
|-------|--------|----------|------------|-------------|----------|--------------|--------|
| **Battery** | battery_pct | battery_pct | power_jsonb | power{} | battery_percent | battery_percent | ❌ MISMATCH |
| **Temperature** | temp_c | temp_c | measurements_jsonb | measurements{} | temperature_c | temperature_c | ❌ MISMATCH |
| **Humidity** | humidity_pct | humidity_pct | measurements_jsonb | measurements{} | humidity_pct | humidity_pct | ✅ MATCH |
| **Pressure** | pressure_hpa | pressure_hpa | measurements_jsonb | measurements{} | pressure_hpa | pressure_hpa | ✅ MATCH |
| **PM2.5** | pm25_ug_m3 | pm25_ug_m3 | measurements_jsonb | measurements{} | pm25_ug_m3 | pm25_ug_m3 | ✅ MATCH |
| **PM10** | pm10_ug_m3 | pm10_ug_m3 | measurements_jsonb | measurements{} | pm10_ug_m3 | pm10_ug_m3 | ✅ MATCH |
| **Measurement TS** | measurement_timestamp | measurement_timestamp | measurement_ts | measurement_ts | measurement_timestamp | measurement_timestamp | ✅ MATCH |
| **Received TS** | received_timestamp | (server-assigned) | receive_ts | receive_ts | received_timestamp | received_timestamp | ✅ MATCH |

**Critical Mismatches**:
1. `battery_pct` (schema/firmware) ≠ `battery_percent` (packages)
2. `temp_c` (schema/firmware) ≠ `temperature_c` (packages)

---

## PART 6: NODE IDENTITY AUDIT

### 6.1 Canonical Format

**Authority**: `schemas/telemetry-envelope.schema.json` (line 31-34)  
**Pattern**: `^NODE-[0-9]{3,}$`

**Valid Examples**:
- NODE-001 ✅
- NODE-042 ✅
- NODE-1234 ✅

**Invalid Examples**:
- node1 ❌ (no NODE- prefix, insufficient digits)
- NODE-1 ❌ (only 1 digit, requires 3+)
- NODE-01 ❌ (only 2 digits, requires 3+)
- NEX-001 ❌ (wrong prefix)

### 6.2 Validator Enforcement

**Current** (`services/backend/modules/ingestion/validator.py` line 88-90):
```python
node_id = payload.get("node_id", "")
if not node_id.startswith("NODE-"):
    return f"Invalid node_id format: {node_id} (expected NODE-XXX)"
```

**Problem**: Accepts NODE-1, NODE-01 (too permissive)

**Required Fix**:
```python
import re
NODE_ID_PATTERN = re.compile(r'^NODE-[0-9]{3,}$')
if not NODE_ID_PATTERN.match(node_id):
    return f"Invalid node_id format: {node_id} (expected NODE-[0-9]{{3,}})"
```

### 6.3 Demo Fixture Exception

**Demo Code** (routes_demo.py, dashboard demo mode):
- Uses NEX-001 ✅ **ACCEPTABLE** (Phase 1 decision: DEMO FIXTURE outside operational ingestion)

**Operational Telemetry**:
- MUST use NODE-XXX format
- Validator MUST reject NEX-XXX in operational ingestion

---

## PART 7: TIMESTAMP SEMANTICS AUDIT

### 7.1 Two-Timestamp Contract

**Authority**: Schema + Constitution §12

**measurement_timestamp**:
- **Owner**: Edge node
- **Semantics**: When observation was captured (edge node clock)
- **Trust**: MUST NOT be trusted as server receive time
- **Format**: UTC ISO 8601

**received_timestamp**:
- **Owner**: Backend server/Master
- **Semantics**: When server received telemetry
- **Assignment**: Server-assigned (node CANNOT set this)
- **Format**: UTC ISO 8601

### 7.2 Implementation Audit

| Layer | measurement_timestamp | received_timestamp | Status |
|-------|----------------------|-------------------|--------|
| **Firmware Generation** | ✅ Set (line 109) | ❌ Not set (server-assigned) | ✅ CORRECT |
| **MQTT Transport** | ✅ Preserved | N/A | ✅ CORRECT |
| **Backend Consumer** | ✅ Preserved | ✅ Assigned (datetime.utcnow()) | ✅ CORRECT |
| **Database** | ✅ measurement_ts column | ✅ receive_ts column | ✅ CORRECT |
| **API Response** | ✅ measurement_ts field | ✅ receive_ts field | ✅ CORRECT |

**Verdict**: ✅ Timestamp semantics correctly implemented throughout pipeline

---

## PART 8: MISSING ≠ ZERO AUDIT

### 8.1 Contract

**Authority**: Constitution §11 + Schema line 69

**Principle**: null/absent = missing, 0 = legitimate measurement value

### 8.2 Implementation Audit

| Layer | Representation | Handling | Status |
|-------|---------------|----------|--------|
| **Firmware (C)** | NAN for missing floats | cJSON_CreateNull() if isnan() | ✅ CORRECT |
| **MQTT (JSON)** | `null` | Preserved | ✅ CORRECT |
| **Backend Validator** | `null`/absent in dict | Warns on 0 (not error) | ✅ CORRECT |
| **Database (JSONB)** | NULL in JSONB | Preserved | ✅ CORRECT |
| **API Response** | `null` in JSON dict | Preserved | ✅ CORRECT |
| **Frontend (TS)** | `null`/`undefined` | Rendered as "—" | ✅ CORRECT |

**Verdict**: ✅ Missing ≠ Zero correctly preserved through entire pipeline

---

## PART 9: SOURCE SEMANTICS AUDIT

### 9.1 Canonical Enum

**Authority**: Schema line 154-157

**Values**:
- HARDWARE: Live sensor telemetry from real physical nodes
- SIMULATION: Synthetic telemetry through canonical ingestion path

### 9.2 Implementation Audit

| Layer | HARDWARE | SIMULATION | Status |
|-------|----------|------------|--------|
| **Firmware** | ✅ Hardcoded "HARDWARE" (line 181) | N/A | ✅ CORRECT |
| **Validator** | ✅ Accepted (line 104-106) | ✅ Accepted | ✅ CORRECT |
| **Database** | ✅ Stored in source column | ✅ Stored | ✅ CORRECT |
| **Demo Fixture** | N/A (outside operational) | Uses "SIMULATION" | ✅ CORRECT |

**Verdict**: ✅ Source semantics correctly implemented

---

## PART 10: REQUIRED FIXES

### Priority 1: Schema Enforcement (CRITICAL)

**Current**: Validator validates but backend API does not enforce at all ingestion boundaries

**Required**:
1. Add validator middleware to MQTT consumer ingestion boundary
2. Reject non-conforming telemetry with structured error
3. Update statistics (messages_invalid counter)
4. Do NOT allow malformed telemetry to reach persistence

**Files to Modify**:
- `services/backend/modules/ingestion/mqtt_consumer.py` — Already validates (line 148-150) ✅

**Status**: ✅ Already enforced at MQTT ingestion boundary

---

### Priority 2: Node Identity Enforcement (HIGH)

**Current**: Validator accepts NODE-1, NODE-01 (too permissive)

**Required**:
1. Update validator to enforce full `^NODE-[0-9]{3,}$` pattern
2. Reject NODE-1, NODE-01 with clear error message
3. Accept NODE-001, NODE-042, NODE-1234
4. Demo fixture (NEX-001) remains outside operational ingestion

**Files to Modify**:
- `services/backend/modules/ingestion/validator.py` line 88-90

**Implementation**:
```python
import re

# Add at module level
NODE_ID_PATTERN = re.compile(r'^NODE-[0-9]{3,}$')

# Update _validate_semantics method
node_id = payload.get("node_id", "")
if not NODE_ID_PATTERN.match(node_id):
    return f"Invalid node_id format: {node_id} (expected NODE-[0-9]{{3,}}, e.g., NODE-001)"
```

---

### Priority 3: Field Name Synchronization (HIGH)

**Current**: `battery_percent` and `temperature_c` in packages diverge from schema

**Required**:
1. Update `packages/nexalert-types/src/telemetry.ts`:
   - `battery_percent` → `battery_pct`
   - `temperature_c` → `temp_c`
2. Update `packages/nexalert-events/nexalert_events/telemetry.py`:
   - `battery_percent` → `battery_pct`
   - `temperature_c` → `temp_c`
3. Update tests to use canonical field names

**Files to Modify**:
- `packages/nexalert-types/src/telemetry.ts` (lines 24, 28)
- `packages/nexalert-types/src/telemetry.test.ts` (line 57)
- `packages/nexalert-events/nexalert_events/telemetry.py` (lines 32, 37)
- `packages/nexalert-events/tests/test_telemetry.py` (line 25)
- `packages/nexalert-events/tests/test_schema_sync.py` (line 49)

---

### Priority 4: Node Identity Defaults (MEDIUM)

**Current**: Default node_id = "node1" (incorrect format)

**Required**:
1. Change all default node_id from "node1" to "NODE-001"
2. Update MQTT topic defaults from "Nexalert/telemetry/node1" to "Nexalert/telemetry/NODE-001"

**Files to Modify**:
- `firmware/components/config/node_config.c` line 24 — node_id default
- `firmware/components/config/node_config.c` line 40 — MQTT topic default
- `services/backend/config.py` line 34 — Backend default topic

---

### Priority 5: Frontend Normalization Removal (LOW)

**Current**: Dashboard accepts multiple telemetry shapes (temporary mitigation)

**Required** (AFTER backend enforces canonical schema):
1. Remove `data.telemetry || data.sensors` multi-shape support
2. Accept ONLY canonical shape from API
3. Keep demo mode fallback (DEMO FIXTURE exception)

**Files to Modify**:
- `apps/authority-dashboard/app/page.tsx` lines 16-30 — Remove normalization layer

**Blocked By**: Backend must emit canonical shape consistently first

---

## PART 11: TEST REQUIREMENTS

### 11.1 Contract Validation Tests

**File**: `services/backend/tests/test_contract_enforcement.py` (new)

**Required Tests**:
1. ✅ Valid canonical telemetry accepted
2. ✅ NODE-001 accepted
3. ❌ NODE-01 rejected
4. ❌ NODE-1 rejected
5. ❌ NEX-001 rejected (in operational ingestion)
6. ✅ HARDWARE source accepted
7. ✅ SIMULATION source accepted
8. ❌ DEMO source rejected
9. ✅ Null measurement preserved
10. ✅ Zero measurement preserved
11. ✅ measurement_timestamp preserved
12. ✅ received_timestamp server-assigned
13. ❌ Invalid JSON rejected
14. ❌ Missing required field rejected
15. ❌ Wrong MQTT topic ignored/logged

### 11.2 End-to-End Contract Test

**File**: `services/backend/tests/test_telemetry_e2e.py` (new)

**Pipeline**:
```
Canonical telemetry packet (NODE-001, HARDWARE)
  → MQTT ingestion
  → Schema validation
  → Persistence
  → Database retrieval
  → API response
  → Verify all fields preserved
```

---

## PART 12: REGRESSION PREVENTION

### 12.1 Existing Tests to Run

**Reference Python**:
```bash
cd reference/python && pytest tests/ -v
# Expected: 219 tests pass (no regressions)
```

**Backend Tests**:
```bash
cd services/backend && pytest tests/test_validator.py -v
cd services/backend && pytest tests/test_regional_fusion.py -v
cd services/backend && pytest tests/track_b2_scenarios.py -v
```

**Firmware Tests**:
```bash
cd firmware/components/intelligence/test
# Run existing unit tests for intelligence modules
```

### 12.2 Test Count Tracking

**Baseline** (before Phase 2A):
- Reference Python: 219 tests
- Backend validator: (count existing tests)
- Backend Track B2: (count existing tests)
- Firmware intelligence: (count existing tests)

**After Phase 2A**:
- All baseline tests MUST still pass
- Additional contract tests added

---

## PART 13: MIGRATION STRATEGY

### 13.1 Backward Compatibility

**Field Name Changes**:
- `battery_percent` → `battery_pct` (breaking change for packages)
- `temperature_c` → `temp_c` (breaking change for packages)

**Mitigation**:
- Packages are internal (nexalert-types, nexalert-events)
- Update all consumers simultaneously
- No external API consumers to break

### 13.2 Phased Rollout

**Phase 2A-1**: Backend contract enforcement
1. Update validator (node_id pattern)
2. Update field names in packages
3. Update tests
4. Run regression tests

**Phase 2A-2**: Firmware defaults
1. Update node_id default (node1 → NODE-001)
2. Update MQTT topic defaults
3. Test firmware generation

**Phase 2A-3**: Frontend
1. Verify backend emits canonical shape
2. Remove frontend normalization layer
3. Test dashboard with canonical telemetry

---

## PART 14: COMPLETION CRITERIA

Phase 2A is COMPLETE when:

✅ **Schema Enforcement**:
- Validator enforces canonical schema at all operational ingestion boundaries
- Non-conforming telemetry rejected with structured errors
- Demo fixtures remain isolated

✅ **Node Identity**:
- Validator enforces `NODE-[0-9]{3,}` pattern fully
- Rejects NODE-1, NODE-01
- Accepts NODE-001, NODE-042, NODE-1234
- Demo NEX-001 isolated from operational ingestion

✅ **Field Names**:
- All layers use canonical field names from schema
- battery_pct (not battery_percent)
- temp_c (not temperature_c)
- No field name divergence

✅ **MQTT Topics**:
- All defaults use NODE-XXX format (not "node1")
- Topic construction consistent

✅ **Timestamps**:
- measurement_timestamp vs received_timestamp distinction preserved (already correct)

✅ **Missing ≠ Zero**:
- Null handling correct through entire pipeline (already correct)

✅ **Source Semantics**:
- HARDWARE/SIMULATION distinction correct (already correct)

✅ **Frontend**:
- Operational frontend consumes canonical shape only
- Demo fixtures clearly separate

✅ **Tests**:
- 15+ contract validation tests passing
- End-to-end contract test passing
- All existing tests still passing (no regressions)

✅ **Evidence**:
- Test results documented
- No known contract contradictions
- Change report complete

---

## DOCUMENT CONTROL

**Version**: 1.0  
**Status**: Pre-Implementation Audit Complete  
**Next Action**: Implement Priority 1-4 fixes

**Files Requiring Changes** (7 files):
1. `services/backend/modules/ingestion/validator.py` — Node ID pattern enforcement
2. `packages/nexalert-types/src/telemetry.ts` — Field name sync
3. `packages/nexalert-events/nexalert_events/telemetry.py` — Field name sync
4. `firmware/components/config/node_config.c` — Default node_id
5. `services/backend/config.py` — Default MQTT topic
6. (+ test files)
7. `apps/authority-dashboard/app/page.tsx` — Remove normalization (deferred)

**Test Files to Create** (2 files):
1. `services/backend/tests/test_contract_enforcement.py` — 15+ validation tests
2. `services/backend/tests/test_telemetry_e2e.py` — End-to-end pipeline test

---

**END OF TELEMETRY PIPELINE AUDIT**
