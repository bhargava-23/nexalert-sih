#!/usr/bin/env python3
"""
NexAlert Raspberry Pi MQTT Subscriber

Receives telemetry from ESP32 nodes via local Mosquitto broker.
Validates against canonical schema and persists to database.

MILESTONE 1: ESP32 → MQTT → Pi → Schema Validation → Persistence
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any

import paho.mqtt.client as mqtt
from jsonschema import validate, ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('nexalert-subscriber')

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "nexalert/nodes/+/telemetry"  # Subscribe to all nodes
MQTT_CLIENT_ID = "nexalert-pi-subscriber"

# Schema path (relative to this file)
SCHEMA_PATH = "../../../schemas/telemetry-envelope.schema.json"

class TelemetrySubscriber:
    """
    MQTT subscriber for NexAlert telemetry envelopes.

    Validates against canonical schema and persists to database.
    Preserves missing != zero invariant throughout.
    """

    def __init__(self, schema_path: str):
        """Initialize subscriber with schema validation."""
        self.schema = self._load_schema(schema_path)
        self.client = None
        self.message_count = 0

    def _load_schema(self, schema_path: str) -> Dict[str, Any]:
        """Load canonical telemetry schema."""
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            logger.info(f"Loaded schema from {schema_path}")
            return schema
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            sys.exit(1)

    def _validate_telemetry(self, payload: Dict[str, Any]) -> bool:
        """
        Validate telemetry against canonical schema.

        CRITICAL: Schema enforces missing != zero via ["number", "null"] types.
        """
        try:
            validate(instance=payload, schema=self.schema)
            return True
        except ValidationError as e:
            logger.error(f"Schema validation failed: {e.message}")
            logger.error(f"Failed at: {e.json_path}")
            return False

    def _persist_telemetry(self, payload: Dict[str, Any]) -> bool:
        """
        Persist telemetry to local storage.

        MILESTONE 1: Simple file persistence for demonstration.
        Production: TimescaleDB/PostgreSQL integration.
        """
        try:
            # Create timestamped filename
            telemetry_id = payload.get('telemetry_id', 'unknown')
            node_id = payload.get('node_id', 'unknown')
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"telemetry_{node_id}_{telemetry_id}_{timestamp}.json"

            # Write to file
            with open(filename, 'w') as f:
                json.dump(payload, f, indent=2)

            logger.info(f"Persisted telemetry to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to persist telemetry: {e}")
            return False

    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            client.subscribe(MQTT_TOPIC)
            logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
        else:
            logger.error(f"Connection failed with code {rc}")

    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT message."""
        self.message_count += 1
        logger.info(f"=== Message {self.message_count} ===")
        logger.info(f"Topic: {msg.topic}")
        logger.info(f"Payload size: {len(msg.payload)} bytes")

        try:
            # Parse JSON payload
            payload = json.loads(msg.payload.decode('utf-8'))

            # Extract key fields
            telemetry_id = payload.get('telemetry_id', 'N/A')
            node_id = payload.get('node_id', 'N/A')
            sequence = payload.get('sequence', 'N/A')
            source = payload.get('source', 'N/A')

            logger.info(f"Telemetry ID: {telemetry_id}")
            logger.info(f"Node ID: {node_id}")
            logger.info(f"Sequence: {sequence}")
            logger.info(f"Source: {source}")

            # Log measurements (preserving missing != zero)
            measurements = payload.get('measurements', {})
            temp = measurements.get('temp_c')
            humid = measurements.get('humidity_pct')

            if temp is not None:
                logger.info(f"Temperature: {temp} °C")
            else:
                logger.info("Temperature: MISSING (null)")

            if humid is not None:
                logger.info(f"Humidity: {humid} %")
            else:
                logger.info("Humidity: MISSING (null)")

            # Validate against canonical schema
            if self._validate_telemetry(payload):
                logger.info("✓ Schema validation PASSED")

                # Persist to storage
                if self._persist_telemetry(payload):
                    logger.info("✓ Telemetry persisted successfully")
                else:
                    logger.error("✗ Persistence FAILED")
            else:
                logger.error("✗ Schema validation FAILED")

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection."""
        if rc != 0:
            logger.warning(f"Unexpected disconnect (code {rc}), will reconnect")
        else:
            logger.info("Disconnected from MQTT broker")

    def start(self):
        """Start MQTT subscriber."""
        logger.info("Starting NexAlert MQTT subscriber...")
        logger.info(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
        logger.info(f"Topic: {MQTT_TOPIC}")

        # Create MQTT client
        self.client = mqtt.Client(client_id=MQTT_CLIENT_ID)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # Connect to broker
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            logger.info("MQTT connection initiated")

            # Start loop
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            self.client.disconnect()
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    logger.info("=== NexAlert Raspberry Pi MQTT Subscriber ===")
    logger.info("Track A: Hardware Vertical Slice - Milestone 1")
    logger.info("ESP32 → MQTT → Pi → Schema Validation → Persistence")

    # Create and start subscriber
    subscriber = TelemetrySubscriber(schema_path=SCHEMA_PATH)
    subscriber.start()
