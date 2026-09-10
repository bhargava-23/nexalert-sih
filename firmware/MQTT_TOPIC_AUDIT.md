# MQTT Topic Audit - NexAlert Repository

**Date:** 2026-09-10  
**Canonical Topic:** `Nexalert/telemetry/node1`  
**Status:** IN PROGRESS

---

## A. Canonical Topic Definition

**LOCKED FORMAT:** `Nexalert/telemetry/node1`
- Capitalization: `Nexalert` (capital N, lowercase rest)
- Separator: `/` (forward slash)
- Prefix: `Nexalert/telemetry/`
- Node ID: `node1` (example, configurable per device)

---

## B. Publishers Found

### ESP32-S3 Firmware (Primary Publisher)

1. **firmware/components/network/mqtt_client.c:73-75**
   - Function: `mqtt_client_init()`
   - Topic Construction: `snprintf(mqtt_state.topic, sizeof(mqtt_state.topic), "Nexalert/telemetry/%s", config->node_id);`
   - Status: ✅ CORRECT - Uses locked format with configurable node_id

2. **firmware/components/config/node_config.c:40**
   - Default configuration
   - Hardcoded: `.topic = "Nexalert/telemetry/node1"`
   - Status: ✅ CORRECT - Matches canonical format

3. **firmware/main/main.c:650**
   - Logging only: `ESP_LOGI(TAG, "MQTT: %s:%u → %s", ...g_config.mqtt.topic)`
   - Status: ✅ CORRECT - Uses configuration value

4. **firmware/main/main_milestone1_backup.c:549**
   - Logging only (backup file)
   - Status: ✅ CORRECT - Uses configuration value

5. **firmware/main/main_integrated.c:549**
   - Logging only (integrated version)
   - Status: ✅ CORRECT - Uses configuration value

---

## C. Subscribers Found

### 1. Backend MQTT Consumer (Primary Subscriber)

**services/backend/modules/ingestion/mqtt_consumer.py**
- Topic: Read from environment variable `MQTT_TOPIC`
- Default: `"Nexalert/telemetry/node1"` (from config.py:34)
- Status: ✅ CORRECT

**services/backend/.env:10**
- `MQTT_TOPIC=Nexalert/telemetry/node1`
- Status: ✅ CORRECT

**services/backend/.env.example:10**
- `MQTT_TOPIC=Nexalert/telemetry/node1`
- Status: ✅ CORRECT

### 2. Raspberry Pi MQTT Subscriber Script

**scripts/pi_mqtt_subscriber.py:30**
- Topic: `MQTT_TOPIC = "nexalert/nodes/+/telemetry"`
- Status: ⚠️ **MISMATCH - CASE AND PATTERN DIFFER**
- This subscribes to: `nexalert/nodes/+/telemetry` (lowercase, different structure)
- Publisher sends: `Nexalert/telemetry/node1`
- **INCOMPATIBLE:** Subscriber will NOT receive messages from ESP32

### 3. Backend Integration Test

**services/backend/tests/test_mqtt_b2_integration.py:31**
- Topic: `MQTT_TOPIC = "nexalert/telemetry"`
- Status: ⚠️ **MISMATCH - LOWERCASE, PARTIAL TOPIC**
- Subscribes to: `nexalert/telemetry` (no wildcard, no node_id)
- Publisher sends: `Nexalert/telemetry/node1`
- **INCOMPATIBLE:** Subscriber will NOT receive messages from ESP32

---

## D. Mismatches Found and Analysis

### CRITICAL ISSUE 1: Raspberry Pi Script Subscriber

**File:** `scripts/pi_mqtt_subscriber.py`  
**Line:** 30  
**Current:** `MQTT_TOPIC = "nexalert/nodes/+/telemetry"`  
**Should be:** `MQTT_TOPIC = "Nexalert/telemetry/+"`  

**Problem:**
1. Case mismatch: `nexalert` vs `Nexalert`
2. Topic structure mismatch: `nexalert/nodes/+/telemetry` vs `Nexalert/telemetry/node1`

**Impact:** Raspberry Pi subscriber will NEVER receive telemetry from ESP32.

**Fix Options:**
- Option A: Change to `"Nexalert/telemetry/+"` (wildcard to match all nodes)
- Option B: Change to `"Nexalert/telemetry/node1"` (exact match for node1 only)
- Option C: Change to `"Nexalert/telemetry/#"` (wildcard for all subtopics)

**Recommended:** Option A - `"Nexalert/telemetry/+"` (matches all node IDs)

---

### CRITICAL ISSUE 2: Backend Integration Test

**File:** `services/backend/tests/test_mqtt_b2_integration.py`  
**Line:** 31  
**Current:** `MQTT_TOPIC = "nexalert/telemetry"`  
**Should be:** `MQTT_TOPIC = "Nexalert/telemetry/node1"` OR `"Nexalert/telemetry/+"`

**Problem:**
1. Case mismatch: `nexalert` vs `Nexalert`
2. Missing node_id segment: `nexalert/telemetry` vs `Nexalert/telemetry/node1`

**Impact:** Integration test will NEVER receive test messages it publishes.

**Fix:** Change to `"Nexalert/telemetry/+"` (for test flexibility with multiple node IDs)

---

## E. Validation Performed

### Topic Prefix Validation

**firmware/components/config/node_config.c:150-153**
```c
// MQTT topic matches canonical format (starts with "Nexalert/telemetry/")
if (strncmp(config->mqtt.topic, "Nexalert/telemetry/", 19) != 0) {
    ESP_LOGE(TAG, "MQTT topic must start with 'Nexalert/telemetry/' (got: %s)",
             config->mqtt.topic);
    return false;
}
```
- Status: ✅ CORRECT - Validates exact case and prefix

---

## F. QoS and Retained Flag

### Publisher (ESP32)
- QoS: 1 (at least once delivery)
- Retained: Not set
- Source: `firmware/components/network/mqtt_client.c:129`

### Subscriber (Backend)
- QoS: Not explicitly set in subscription (defaults to broker maximum)
- Retained: Not relevant for subscriber
- Source: `services/backend/modules/ingestion/mqtt_consumer.py`

**Status:** ✅ COMPATIBLE

---

## G. Mosquitto Broker Configuration

**Search Result:** No explicit Mosquitto configuration file found in repository.

**Assumption:** Using default Mosquitto configuration on Raspberry Pi.

**Note:** Mosquitto MQTT topics ARE case-sensitive. `Nexalert/telemetry/node1` and `nexalert/telemetry/node1` are DIFFERENT topics.

---

## H. Summary of Required Fixes

### 1. scripts/pi_mqtt_subscriber.py:30
```python
# BEFORE
MQTT_TOPIC = "nexalert/nodes/+/telemetry"

# AFTER
MQTT_TOPIC = "Nexalert/telemetry/+"  # Match all node IDs with correct case
```

### 2. services/backend/tests/test_mqtt_b2_integration.py:31
```python
# BEFORE
MQTT_TOPIC = "nexalert/telemetry"

# AFTER
MQTT_TOPIC = "Nexalert/telemetry/+"  # Match all node IDs with correct case
```

---

## I. Files with Correct MQTT Topic (No Changes Needed)

✅ firmware/components/network/mqtt_client.c  
✅ firmware/components/config/node_config.c  
✅ firmware/main/main.c  
✅ services/backend/.env  
✅ services/backend/.env.example  
✅ services/backend/config.py  
✅ services/backend/modules/ingestion/mqtt_consumer.py

---

## J. Publish/Subscribe Path Trace

**Complete Data Flow:**

```
ESP32-S3 Firmware
  ↓ PUBLISH: Nexalert/telemetry/node1, QoS 1
  ↓
Mosquitto MQTT Broker (localhost:1883)
  ↓ SUBSCRIBE: Nexalert/telemetry/+ (after fix)
  ↓
[Backend MQTT Consumer] ✅ (Already correct)
  ↓
Backend Ingestion Pipeline
  ↓
PostgreSQL Database

[Pi MQTT Subscriber Script] ⚠️ (Needs fix)
```

**Current State:**
- ESP32 → Broker: ✅ Working (publishes to `Nexalert/telemetry/node1`)
- Broker → Backend: ✅ Working (subscribes to `Nexalert/telemetry/node1` exactly)
- Broker → Pi Script: ❌ BROKEN (subscribes to wrong topic pattern)
- Broker → Test: ❌ BROKEN (subscribes to wrong topic)

---

## K. Next Steps

1. Fix `scripts/pi_mqtt_subscriber.py` line 30
2. Fix `services/backend/tests/test_mqtt_b2_integration.py` line 31
3. Test end-to-end: ESP32 → Mosquitto → Backend
4. Test end-to-end: ESP32 → Mosquitto → Pi Script (after fix)
5. Verify integration test passes (after fix)

---

**AUDIT STATUS:** COMPLETE  
**CRITICAL ISSUES FOUND:** 2  
**NON-CRITICAL ISSUES:** 0  
**FILES REQUIRING CHANGES:** 2
