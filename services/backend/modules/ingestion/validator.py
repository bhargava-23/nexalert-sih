"""Telemetry validation module

Validates incoming MQTT telemetry against canonical schema.
Preserves MISSING != ZERO semantics throughout.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from jsonschema import validate, ValidationError, Draft7Validator
from ulid import ULID

logger = logging.getLogger(__name__)


class TelemetryValidator:
    """Validates telemetry against canonical schema"""

    def __init__(self, schema_path: str):
        """Initialize validator with schema file

        Args:
            schema_path: Path to telemetry-envelope.schema.json
        """
        schema_file = Path(schema_path)
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")

        with open(schema_file, "r") as f:
            self.schema = json.load(f)

        self.validator = Draft7Validator(self.schema)
        logger.info(f"Loaded telemetry schema from {schema_path}")

    def validate(self, payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate telemetry payload

        Args:
            payload: Parsed JSON telemetry envelope

        Returns:
            (is_valid, error_message)
            - is_valid: True if valid, False otherwise
            - error_message: None if valid, error description otherwise

        MISSING != ZERO:
        - null/missing values are PRESERVED
        - validator allows null for optional measurements
        - downstream code must handle null correctly
        """
        try:
            # Validate against schema
            validate(instance=payload, schema=self.schema)

            # Additional semantic checks
            error = self._validate_semantics(payload)
            if error:
                return False, error

            return True, None

        except ValidationError as e:
            error_msg = f"Schema validation failed: {e.message}"
            logger.warning(f"Validation error: {error_msg}")
            return False, error_msg

        except Exception as e:
            error_msg = f"Validation exception: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    def _validate_semantics(self, payload: Dict[str, Any]) -> Optional[str]:
        """Additional semantic validation beyond JSON schema

        Returns:
            Error message if invalid, None if valid
        """
        # Validate telemetry_id format (ULID)
        try:
            telemetry_id = payload.get("telemetry_id")
            if telemetry_id:
                ULID.from_str(telemetry_id)
        except Exception:
            return f"Invalid telemetry_id format: {telemetry_id} (expected ULID)"

        # Validate node_id format
        node_id = payload.get("node_id", "")
        if not node_id.startswith("NODE-"):
            return f"Invalid node_id format: {node_id} (expected NODE-XXX)"

        # Validate timestamps
        try:
            measurement_ts = payload.get("measurement_timestamp")
            received_ts = payload.get("received_timestamp")
            if measurement_ts:
                datetime.fromisoformat(measurement_ts.replace("Z", "+00:00"))
            if received_ts:
                datetime.fromisoformat(received_ts.replace("Z", "+00:00"))
        except Exception as e:
            return f"Invalid timestamp format: {str(e)}"

        # Validate source enum
        source = payload.get("source")
        if source not in ["HARDWARE", "SIMULATION"]:
            return f"Invalid source: {source} (expected HARDWARE or SIMULATION)"

        # Validate location bounds
        location = payload.get("location", {})
        lat = location.get("lat")
        lon = location.get("lon")
        if lat is not None and not (-90 <= lat <= 90):
            return f"Invalid latitude: {lat} (must be [-90, 90])"
        if lon is not None and not (-180 <= lon <= 180):
            return f"Invalid longitude: {lon} (must be [-180, 180])"

        # MISSING != ZERO: Verify no measurements are set to 0 when they should be null
        # This is a WARNING, not a hard failure (node may legitimately read 0)
        measurements = payload.get("measurements", {})
        for key, value in measurements.items():
            if value == 0:
                logger.debug(
                    f"Measurement {key}=0 detected. "
                    f"Verify this is a real zero reading, not missing data. "
                    f"MISSING != ZERO invariant."
                )

        return None


def parse_telemetry_payload(raw_payload: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Parse raw MQTT payload to JSON

    Args:
        raw_payload: Raw MQTT message payload (string/bytes)

    Returns:
        (parsed_dict, error_message)
        - parsed_dict: Parsed JSON dict if successful, None otherwise
        - error_message: None if successful, error description otherwise
    """
    try:
        if isinstance(raw_payload, bytes):
            raw_payload = raw_payload.decode("utf-8")

        payload = json.loads(raw_payload)
        return payload, None

    except json.JSONDecodeError as e:
        error_msg = f"JSON parse error: {str(e)}"
        logger.warning(error_msg)
        return None, error_msg

    except Exception as e:
        error_msg = f"Parse exception: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg
