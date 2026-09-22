"""Track 3C Normalizer - Hardware JSON → Canonical telemetry.v1

Implements the Track 3C normalization layer at Master MQTT ingestion boundary.
Converts ESP32 hardware JSON to canonical telemetry.v1 envelope.

Architecture (Phase 2D):
    ESP32 → Hardware JSON (locked contract)
    → MQTT (Nexalert/telemetry/node1)
    → Track 3C normalization (THIS MODULE)
    → Canonical telemetry.v1
    → PostgreSQL persistence
    → Master intelligence
    → B2 regional fusion

Contract Mapping:
    Hardware JSON (ESP32)           → Canonical telemetry.v1 (Master/Backend)
    ─────────────────────────────────────────────────────────────────────────
    node_id                         → node_id
    timestamp_ms                    → measurement_timestamp
    sequence                        → sequence
    (Master receive time)           → received_timestamp
    (Node registry location)        → location
    sensors.*                       → measurements.*
    availability.*                  → diagnostics (availability representation)
    power.*                         → power.*
    (constant)                      → source: "HARDWARE"
    (constant)                      → schema_version: "telemetry.v1"
    (generate ULID)                 → telemetry_id

Critical Rules:
    - Missing != Zero: null/NAN preserved throughout
    - MQ-2 gas_ppm is RAW ADC (0-4095), NOT calibrated ppm
    - Location comes from Node registry (NEVER fabricated)
    - If node has no valid location, normalization fails safely
    - Rejects malformed hardware JSON at boundary
    - Unknown nodes fail normalization (node must be registered)
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from ulid import ULID

logger = logging.getLogger(__name__)


class Track3CNormalizer:
    """Normalizes hardware JSON to canonical telemetry.v1"""

    def __init__(self, node_registry):
        """Initialize normalizer with node registry

        Args:
            node_registry: NodeRegistry instance
                          Location must be present and valid for normalization to succeed
        """
        self.node_registry = node_registry
        logger.info("Track 3C normalizer initialized")

    async def normalize_hardware_json(
        self,
        hardware_json: Dict[str, Any],
        received_timestamp: datetime
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Normalize hardware JSON to canonical telemetry.v1

        Args:
            hardware_json: Raw hardware JSON from ESP32 MQTT message
            received_timestamp: Master receive time (server-assigned)

        Returns:
            (canonical_telemetry, error_message)
            - canonical_telemetry: telemetry.v1 envelope if successful, None on error
            - error_message: None if successful, error description otherwise

        Normalization Rules:
            1. Validate hardware JSON structure
            2. Resolve node location from registry
            3. Map hardware sensors to canonical measurements
            4. Map hardware availability to diagnostics representation
            5. Generate canonical telemetry_id (ULID)
            6. Preserve MISSING != ZERO semantics
            7. Fail safely if node unknown or location missing
        """
        try:
            # Extract required fields
            node_id = hardware_json.get("node_id")
            if not node_id:
                return None, "Missing node_id in hardware JSON"

            timestamp_ms = hardware_json.get("timestamp_ms")
            if timestamp_ms is None:
                return None, "Missing timestamp_ms in hardware JSON"

            sequence = hardware_json.get("sequence")
            if sequence is None:
                return None, "Missing sequence in hardware JSON"

            sensors = hardware_json.get("sensors", {})
            availability = hardware_json.get("availability", {})
            power = hardware_json.get("power", {})

            # Resolve node location from registry
            location = self.node_registry.get_location(node_id)
            if not location:
                return None, f"Unknown node or missing location: {node_id}"

            if "lat" not in location or "lon" not in location:
                return None, f"Node {node_id} has incomplete location in registry"

            # Generate canonical telemetry_id (ULID)
            telemetry_id = str(ULID())

            # Convert timestamp_ms to ISO 8601
            # === TEMPORARY DEBUG: Log Track 3C timestamp conversion ===
            timestamp_sec = timestamp_ms / 1000.0
            measurement_timestamp = datetime.fromtimestamp(
                timestamp_sec, tz=timezone.utc
            ).isoformat().replace("+00:00", "Z")

            logger.info(
                f"[TIMESTAMP DEBUG] Track3C: timestamp_ms={timestamp_ms}, "
                f"epoch_sec={timestamp_sec:.3f}, "
                f"converted_to={measurement_timestamp}"
            )
            # === END DEBUG ===

            received_timestamp_str = received_timestamp.isoformat().replace("+00:00", "Z")

            # Map hardware sensors to canonical measurements
            # CRITICAL: Preserve null for missing values (MISSING != ZERO)
            # MQ-2 gas_ppm field preserved but value is RAW ADC (0-4095), NOT calibrated ppm
            measurements = {
                "temp_c": sensors.get("temperature_c"),  # null if missing
                "humidity_pct": sensors.get("humidity_rh"),
                "pressure_hpa": sensors.get("pressure_hpa"),
                "gas_adc": sensors.get("gas_ppm"),  # Renamed: gas_ppm → gas_adc (semantic fix)
                "vibration_mps2": sensors.get("vibration_mps2"),
                "pm25_ug_m3": sensors.get("pm25_ugm3"),
                "pm10_ug_m3": sensors.get("pm10_ugm3"),
                "water_level_m": sensors.get("water_level_m"),
                "rainfall_mm_h": sensors.get("rainfall_mm_h"),
                "soil_moisture_vwc_pct": sensors.get("soil_moisture_vwc_pct"),
            }

            # Map hardware availability to diagnostics representation
            # availability flags become part of diagnostics context
            diagnostics = {
                "sensor_availability": {
                    "temperature": availability.get("temperature", False),
                    "humidity": availability.get("humidity", False),
                    "pressure": availability.get("pressure", False),
                    "gas": availability.get("gas", False),
                    "vibration": availability.get("vibration", False),
                    "pm25": availability.get("pm25", False),
                    "pm10": availability.get("pm10", False),
                    "water_level": availability.get("water_level", False),
                    "rainfall": availability.get("rainfall", False),
                    "soil_moisture": availability.get("soil_moisture", False),
                }
            }

            # Map power fields
            canonical_power = {
                "battery_pct": power.get("battery_pct"),  # null if missing
                "solar_state": power.get("solar_state"),  # null if missing
            }

            # Construct canonical telemetry.v1 envelope
            canonical_telemetry = {
                "schema_version": "telemetry.v1",
                "telemetry_id": telemetry_id,
                "node_id": node_id,
                "sequence": sequence,
                "measurement_timestamp": measurement_timestamp,
                "received_timestamp": received_timestamp_str,
                "location": {
                    "lat": location["lat"],
                    "lon": location["lon"],
                    "alt": location.get("alt"),  # Optional altitude
                },
                "measurements": measurements,
                "diagnostics": diagnostics,
                "power": canonical_power,
                "source": "HARDWARE",  # Always HARDWARE for ESP32 telemetry
            }

            logger.info(
                f"Normalized hardware JSON: node={node_id}, seq={sequence}, "
                f"telemetry_id={telemetry_id}"
            )

            return canonical_telemetry, None

        except Exception as e:
            error_msg = f"Track 3C normalization failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg


def create_normalizer_from_db(db_session) -> Track3CNormalizer:
    """Create normalizer with node registry loaded from database

    Args:
        db_session: SQLAlchemy async session

    Returns:
        Configured Track3CNormalizer instance

    NOTE: This is a helper for async context. The actual node registry
    loading should be done by the caller and passed to Track3CNormalizer.__init__
    """
    # Placeholder - actual implementation will query Node table
    # and build registry: {node_id: {location: {lat, lon, alt}, status, ...}}
    raise NotImplementedError(
        "create_normalizer_from_db() requires async node registry loading - "
        "caller must query db.models.Node and build registry"
    )
