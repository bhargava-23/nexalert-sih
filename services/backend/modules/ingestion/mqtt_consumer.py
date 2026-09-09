"""MQTT telemetry consumer

Subscribes to MQTT broker, receives telemetry, validates, and persists to database.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
import paho.mqtt.client as mqtt
from sqlalchemy.ext.asyncio import AsyncSession

from .validator import TelemetryValidator, parse_telemetry_payload
from .persister import TelemetryPersister
from db.database import get_db_config
from modules.intelligence.b2_coordinator import get_coordinator

logger = logging.getLogger(__name__)


class MQTTTelemetryConsumer:
    """MQTT consumer for telemetry ingestion"""

    _loop: Optional[asyncio.AbstractEventLoop] = None

    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        topic: str,
        client_id: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        reconnect_delay_s: int = 5,
        schema_path: str = "../../schemas/telemetry-envelope.schema.json"
    ):
        """Initialize MQTT consumer

        Args:
            broker_host: MQTT broker hostname/IP
            broker_port: MQTT broker port
            topic: MQTT topic to subscribe (e.g., "Nexalert/telemetry/node1")
            client_id: MQTT client ID
            username: MQTT username (None = no auth)
            password: MQTT password (None = no auth)
            reconnect_delay_s: Reconnect delay in seconds
            schema_path: Path to telemetry-envelope.schema.json
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.client_id = client_id
        self.username = username
        self.password = password
        self.reconnect_delay_s = reconnect_delay_s

        # Initialize validator and persister
        self.validator = TelemetryValidator(schema_path)
        self.persister = TelemetryPersister()

        # MQTT client
        self.client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv5)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # Authentication
        if username and password:
            self.client.username_pw_set(username, password)
            logger.info(f"MQTT authentication configured for user: {username}")

        # State
        self.running = False
        self._reconnect_task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = {
            "messages_received": 0,
            "messages_valid": 0,
            "messages_invalid": 0,
            "messages_persisted": 0,
            "messages_failed": 0,
            "messages_duplicate": 0,
        }

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """MQTT connection callback"""
        if rc == 0:
            logger.info(
                f"MQTT connected to {self.broker_host}:{self.broker_port}. "
                f"Subscribing to: {self.topic}"
            )
            client.subscribe(self.topic, qos=1)
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        """MQTT disconnection callback"""
        logger.warning(
            f"MQTT disconnected from {self.broker_host}:{self.broker_port}. "
            f"Code: {rc}"
        )
        if self.running and self._reconnect_task is None and self._loop:
            logger.info(f"Scheduling reconnect in {self.reconnect_delay_s}s")
            self._loop.call_soon_threadsafe(
                self._schedule_reconnect
            )

    def _on_message(self, client, userdata, msg):
        """MQTT message callback

        Processes telemetry messages asynchronously.
        Does NOT crash on a single bad message.
        """
        self.stats["messages_received"] += 1
        logger.debug(f"Received MQTT message on topic: {msg.topic}")

        # Process message asynchronously (thread-safe from MQTT thread)
        if self._loop:
            self._loop.call_soon_threadsafe(
                lambda: self._loop.create_task(self._process_message(msg.payload))
            )

    async def _process_message(self, raw_payload: bytes):
        """Process single telemetry message

        Args:
            raw_payload: Raw MQTT payload

        Pipeline:
        1. Parse JSON
        2. Validate against schema
        3. Persist to database
        4. Update statistics

        Does NOT crash on errors - logs and continues.
        """
        try:
            received_timestamp = datetime.utcnow()

            # 1. Parse JSON
            payload, parse_error = parse_telemetry_payload(raw_payload)
            if parse_error:
                logger.warning(f"Parse failed: {parse_error}")
                self.stats["messages_invalid"] += 1
                return

            # 2. Validate against schema
            is_valid, validation_error = self.validator.validate(payload)
            if not is_valid:
                logger.warning(
                    f"Validation failed: {validation_error}. "
                    f"Telemetry ID: {payload.get('telemetry_id', 'UNKNOWN')}"
                )
                self.stats["messages_invalid"] += 1
                return

            self.stats["messages_valid"] += 1

            # 3. Persist to database
            db_config = get_db_config()
            async for session in db_config.get_session():
                success, persist_error, telemetry_id = await self.persister.persist_telemetry(
                    session, payload, received_timestamp
                )

                if success:
                    self.stats["messages_persisted"] += 1
                    logger.info(
                        f"Telemetry persisted: {telemetry_id}, "
                        f"node_id={payload.get('node_id')}, "
                        f"seq={payload.get('sequence')}"
                    )

                    # Check if idempotent duplicate
                    if persist_error is None and telemetry_id != payload.get("telemetry_id"):
                        self.stats["messages_duplicate"] += 1

                    # TRACK B2 INTEGRATION: Trigger regional intelligence pipeline
                    # after successful persistence (non-blocking)
                    try:
                        coordinator = get_coordinator()

                        # Extract measurement timestamp
                        measurement_ts = datetime.fromisoformat(
                            payload.get("timestamp").replace("Z", "+00:00")
                        )

                        # For now, assume fire hazard type detected
                        # TODO: Extract actual hazard types from node-level assessment
                        hazard_types = ["fire"]

                        # Trigger B2 pipeline (non-blocking, errors logged internally)
                        await coordinator.trigger_after_persistence(
                            session=session,
                            node_id=payload.get("node_id"),
                            hazard_types=hazard_types,
                            measurement_ts=measurement_ts
                        )

                    except Exception as b2_error:
                        # Non-blocking: log but do not propagate
                        logger.warning(
                            f"B2 coordinator trigger failed (non-blocking): {str(b2_error)}"
                        )

                else:
                    self.stats["messages_failed"] += 1
                    logger.error(
                        f"Persistence failed: {persist_error}. "
                        f"Telemetry ID: {payload.get('telemetry_id')}"
                    )

        except Exception as e:
            self.stats["messages_failed"] += 1
            logger.error(f"Message processing exception: {str(e)}", exc_info=True)

    def _schedule_reconnect(self):
        """Schedule reconnect from the event loop thread (called via call_soon_threadsafe)"""
        self._reconnect_task = asyncio.ensure_future(self._reconnect())

    async def _reconnect(self):
        """Reconnect to MQTT broker after delay"""
        try:
            await asyncio.sleep(self.reconnect_delay_s)
            if self.running:
                logger.info("Attempting MQTT reconnect...")
                self.client.reconnect()
        except Exception as e:
            logger.error(f"Reconnect failed: {str(e)}", exc_info=True)
        finally:
            self._reconnect_task = None

    async def start(self):
        """Start MQTT consumer"""
        if self.running:
            logger.warning("MQTT consumer already running")
            return

        self.running = True
        self._loop = asyncio.get_running_loop()
        logger.info(
            f"Starting MQTT consumer: "
            f"broker={self.broker_host}:{self.broker_port}, "
            f"topic={self.topic}, "
            f"client_id={self.client_id}"
        )

        try:
            # Connect to broker
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)

            # Start MQTT loop in background
            self.client.loop_start()

            logger.info("MQTT consumer started successfully")

        except Exception as e:
            self.running = False
            logger.error(f"MQTT consumer start failed: {str(e)}", exc_info=True)
            raise

    async def stop(self):
        """Stop MQTT consumer"""
        if not self.running:
            return

        self.running = False
        logger.info("Stopping MQTT consumer...")

        try:
            # Cancel reconnect task if pending
            if self._reconnect_task:
                self._reconnect_task.cancel()
                self._reconnect_task = None

            # Unsubscribe
            self.client.unsubscribe(self.topic)

            # Stop MQTT loop
            self.client.loop_stop()

            # Disconnect
            self.client.disconnect()

            logger.info(
                f"MQTT consumer stopped. Stats: {self.stats}"
            )

        except Exception as e:
            logger.error(f"MQTT consumer stop error: {str(e)}", exc_info=True)

    def get_stats(self) -> dict:
        """Get consumer statistics"""
        return self.stats.copy()
