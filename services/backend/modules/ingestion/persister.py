"""Telemetry persistence module

Persists validated telemetry to PostgreSQL/PostGIS.
Handles idempotency, node upsert, and MISSING != ZERO semantics.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from geoalchemy2.elements import WKTElement

from db.models import Node, TelemetryRecord

logger = logging.getLogger(__name__)


class TelemetryPersister:
    """Persists telemetry to database"""

    async def persist_telemetry(
        self,
        session: AsyncSession,
        payload: Dict[str, Any],
        received_timestamp: datetime
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Persist validated telemetry to database

        Args:
            session: Database session
            payload: Validated telemetry envelope
            received_timestamp: Server-assigned receive timestamp

        Returns:
            (success, error_message, telemetry_id)
            - success: True if persisted (or idempotent duplicate), False on error
            - error_message: None if successful, error description otherwise
            - telemetry_id: Telemetry ID if successful, None otherwise

        Idempotency:
        - Duplicate (node_id, sequence) is safely handled
        - Returns success=True for idempotent duplicate
        - Uses unique constraint on (node_id, sequence)

        MISSING != ZERO:
        - JSON null values are preserved in JSONB columns
        - Database NULL columns preserve missing semantics
        """
        try:
            telemetry_id = payload["telemetry_id"]
            node_id = payload["node_id"]
            sequence = payload["sequence"]

            # 1. Upsert node (register or update last-seen)
            await self._upsert_node(session, payload)

            # 2. Check for duplicate telemetry (idempotency)
            existing = await self._check_duplicate(session, node_id, sequence)
            if existing:
                logger.info(
                    f"Duplicate telemetry: node_id={node_id}, sequence={sequence}. "
                    f"Existing telemetry_id={existing.telemetry_id}. "
                    f"Idempotent success."
                )
                return True, None, existing.telemetry_id

            # 3. Insert telemetry record
            await self._insert_telemetry(session, payload, received_timestamp)

            # 4. Commit transaction
            await session.commit()

            logger.info(
                f"Persisted telemetry: telemetry_id={telemetry_id}, "
                f"node_id={node_id}, sequence={sequence}"
            )
            return True, None, telemetry_id

        except IntegrityError as e:
            await session.rollback()
            # Likely duplicate (node_id, sequence) - handle gracefully
            error_msg = f"Integrity error (likely duplicate): {str(e)}"
            logger.warning(error_msg)
            return True, None, telemetry_id  # Treat as idempotent success

        except Exception as e:
            await session.rollback()
            error_msg = f"Persistence error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg, None

    async def _upsert_node(self, session: AsyncSession, payload: Dict[str, Any]):
        """Upsert node registration and update last-seen

        Args:
            session: Database session
            payload: Telemetry envelope
        """
        node_id = payload["node_id"]
        location = payload.get("location", {})
        source = payload["source"]

        # Check if node exists
        result = await session.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()

        if node:
            # Update existing node
            node.updated_at = datetime.utcnow()
            node.status = "ACTIVE"

            # Update location if provided
            if location.get("lat") is not None and location.get("lon") is not None:
                lat = location["lat"]
                lon = location["lon"]
                node.location = WKTElement(f"POINT({lon} {lat})", srid=4326)

        else:
            # Create new node
            lat = location.get("lat")
            lon = location.get("lon")
            location_geom = None
            if lat is not None and lon is not None:
                location_geom = WKTElement(f"POINT({lon} {lat})", srid=4326)

            node = Node(
                node_id=node_id,
                status="ACTIVE",
                location=location_geom,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(node)
            logger.info(f"Registered new node: {node_id}")

    async def _check_duplicate(
        self,
        session: AsyncSession,
        node_id: str,
        sequence: int
    ) -> Optional[TelemetryRecord]:
        """Check for duplicate telemetry (idempotency)

        Args:
            session: Database session
            node_id: Node ID
            sequence: Sequence number

        Returns:
            Existing TelemetryRecord if duplicate, None otherwise
        """
        result = await session.execute(
            select(TelemetryRecord).where(
                TelemetryRecord.node_id == node_id,
                TelemetryRecord.sequence == sequence
            )
        )
        return result.scalar_one_or_none()

    async def _insert_telemetry(
        self,
        session: AsyncSession,
        payload: Dict[str, Any],
        received_timestamp: datetime
    ):
        """Insert telemetry record

        Args:
            session: Database session
            payload: Telemetry envelope
            received_timestamp: Server-assigned receive timestamp

        MISSING != ZERO:
        - measurements_jsonb preserves JSON null values
        - diagnostics_jsonb preserves JSON null values
        - power_jsonb preserves JSON null values
        - Database columns preserve NULL semantics
        """
        telemetry_id = payload["telemetry_id"]
        node_id = payload["node_id"]
        sequence = payload["sequence"]

        # Parse measurement timestamp
        measurement_ts_str = payload["measurement_timestamp"]
        measurement_ts = datetime.fromisoformat(measurement_ts_str.replace("Z", "+00:00"))

        # Location
        location = payload.get("location", {})
        lat = location.get("lat")
        lon = location.get("lon")
        location_geom = None
        if lat is not None and lon is not None:
            location_geom = WKTElement(f"POINT({lon} {lat})", srid=4326)

        # Measurements (preserve NULL values in JSONB)
        measurements = payload.get("measurements", {})

        # Diagnostics (preserve NULL values in JSONB)
        diagnostics = payload.get("diagnostics", {})

        # Power (preserve NULL values in JSONB)
        power = payload.get("power", {})

        # Source
        source = payload["source"]

        # Schema version
        schema_version = payload.get("schema_version", "telemetry.v1")

        # Create telemetry record
        record = TelemetryRecord(
            telemetry_id=telemetry_id,
            node_id=node_id,
            sequence=sequence,
            measurement_ts=measurement_ts,
            receive_ts=received_timestamp,
            source=source,
            location=location_geom,
            measurements_jsonb=measurements,
            diagnostics_jsonb=diagnostics,
            power_jsonb=power,
            schema_version=schema_version,
            created_at=datetime.utcnow()
        )

        session.add(record)
