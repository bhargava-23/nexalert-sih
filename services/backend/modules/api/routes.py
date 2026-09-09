"""API routes for NexAlert backend

FastAPI routes for telemetry, nodes, hazards, and health.
"""
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, Field

from db.database import get_db_session
from db.models import Node, TelemetryRecord, HazardAssessment

logger = logging.getLogger(__name__)

router = APIRouter()


# Response models
class NodeResponse(BaseModel):
    """Node information response"""
    node_id: str
    status: str
    location: Optional[dict] = None
    firmware_version: Optional[str] = None
    config_version: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TelemetryResponse(BaseModel):
    """Telemetry record response"""
    telemetry_id: str
    node_id: str
    sequence: int
    measurement_ts: datetime
    receive_ts: datetime
    source: str
    location: Optional[dict] = None
    measurements: dict
    diagnostics: dict
    power: Optional[dict] = None
    schema_version: str


class HazardResponse(BaseModel):
    """Hazard assessment response"""
    assessment_id: int
    telemetry_id: str
    hazard_type: str
    evidence: Optional[float] = None
    confidence: Optional[float] = None
    severity: Optional[float] = None
    risk: Optional[float] = None
    state: Optional[str] = None
    information_condition: Optional[str] = None
    created_at: datetime


class HealthResponse(BaseModel):
    """API health check response"""
    status: str
    timestamp: datetime
    database: str
    mqtt_consumer: Optional[dict] = None


# Routes

@router.get("/nodes", response_model=List[NodeResponse])
async def get_nodes(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session)
):
    """Get list of nodes

    Args:
        status: Optional status filter (ACTIVE, INACTIVE, MAINTENANCE)
        limit: Maximum nodes to return (default 100, max 1000)
        session: Database session

    Returns:
        List of nodes with current status and location
    """
    try:
        query = select(Node).order_by(desc(Node.updated_at)).limit(limit)

        if status:
            query = query.where(Node.status == status)

        result = await session.execute(query)
        nodes = result.scalars().all()

        return [
            NodeResponse(
                node_id=node.node_id,
                status=node.status,
                location=_geography_to_dict(node.location),
                firmware_version=node.firmware_version,
                config_version=node.config_version,
                created_at=node.created_at,
                updated_at=node.updated_at
            )
            for node in nodes
        ]

    except Exception as e:
        logger.error(f"Failed to get nodes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get single node by ID

    Args:
        node_id: Node identifier
        session: Database session

    Returns:
        Node information
    """
    try:
        result = await session.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()

        if not node:
            raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")

        return NodeResponse(
            node_id=node.node_id,
            status=node.status,
            location=_geography_to_dict(node.location),
            firmware_version=node.firmware_version,
            config_version=node.config_version,
            created_at=node.created_at,
            updated_at=node.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get node {node_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/telemetry/latest", response_model=List[TelemetryResponse])
async def get_latest_telemetry(
    node_id: Optional[str] = Query(None, description="Filter by node_id"),
    limit: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session)
):
    """Get latest telemetry records

    Args:
        node_id: Optional node_id filter
        limit: Maximum records to return (default 50, max 500)
        session: Database session

    Returns:
        List of recent telemetry records
    """
    try:
        query = select(TelemetryRecord).order_by(desc(TelemetryRecord.receive_ts)).limit(limit)

        if node_id:
            query = query.where(TelemetryRecord.node_id == node_id)

        result = await session.execute(query)
        records = result.scalars().all()

        return [_telemetry_to_response(record) for record in records]

    except Exception as e:
        logger.error(f"Failed to get latest telemetry: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/telemetry/{node_id}", response_model=List[TelemetryResponse])
async def get_node_telemetry(
    node_id: str,
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session)
):
    """Get telemetry for specific node

    Args:
        node_id: Node identifier
        limit: Maximum records to return (default 100, max 1000)
        session: Database session

    Returns:
        List of telemetry records for node, ordered by measurement timestamp
    """
    try:
        result = await session.execute(
            select(TelemetryRecord)
            .where(TelemetryRecord.node_id == node_id)
            .order_by(desc(TelemetryRecord.measurement_ts))
            .limit(limit)
        )
        records = result.scalars().all()

        return [_telemetry_to_response(record) for record in records]

    except Exception as e:
        logger.error(f"Failed to get telemetry for node {node_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/hazards", response_model=List[HazardResponse])
async def get_hazards(
    hazard_type: Optional[str] = Query(None, description="Filter by hazard type"),
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session)
):
    """Get hazard assessments

    Args:
        hazard_type: Optional hazard type filter (fire, flood, etc.)
        state: Optional state filter (NORMAL, WATCH, SUSPECTED, CONFIRMED, CRITICAL, RESOLVED)
        limit: Maximum assessments to return (default 100, max 1000)
        session: Database session

    Returns:
        List of recent hazard assessments
    """
    try:
        query = select(HazardAssessment).order_by(desc(HazardAssessment.created_at)).limit(limit)

        if hazard_type:
            query = query.where(HazardAssessment.hazard_type == hazard_type)

        if state:
            query = query.where(HazardAssessment.state == state)

        result = await session.execute(query)
        assessments = result.scalars().all()

        return [_hazard_to_response(assessment) for assessment in assessments]

    except Exception as e:
        logger.error(f"Failed to get hazards: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", response_model=HealthResponse)
async def health_check(session: AsyncSession = Depends(get_db_session)):
    """Health check endpoint

    Returns:
        Backend health status
    """
    try:
        # Test database connection
        await session.execute(select(1))
        db_status = "connected"

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}", exc_info=True)
        db_status = "disconnected"

    # Get MQTT consumer stats (if available)
    mqtt_stats = None
    try:
        from ..ingestion.mqtt_consumer import mqtt_consumer
        if mqtt_consumer:
            mqtt_stats = mqtt_consumer.get_stats()
    except:
        pass

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        timestamp=datetime.utcnow(),
        database=db_status,
        mqtt_consumer=mqtt_stats
    )


# Helper functions

def _geography_to_dict(geography) -> Optional[dict]:
    """Convert PostGIS Geography to dict

    Args:
        geography: GeoAlchemy2 Geography object (WKB binary representation)

    Returns:
        {"lat": float, "lon": float} or None
    """
    if geography is None:
        return None

    try:
        # GeoAlchemy2 Geography stores as WKB (Well-Known Binary)
        # Use geoalchemy2.shape to convert to shapely geometry, then extract coords
        from geoalchemy2 import shape
        from shapely import wkb

        # Convert WKB to shapely Point
        if hasattr(geography, 'data'):
            # WKBElement - extract binary data
            point = wkb.loads(bytes(geography.data))
        else:
            # Already a shapely geometry or string WKB
            point = shape(geography)

        # Extract coordinates (Point.x = lon, Point.y = lat)
        return {"lat": point.y, "lon": point.x}
    except Exception as e:
        logger.warning(f"Failed to parse geography: {str(e)}")
        return None


def _telemetry_to_response(record: TelemetryRecord) -> TelemetryResponse:
    """Convert TelemetryRecord to response model

    Args:
        record: TelemetryRecord database model

    Returns:
        TelemetryResponse pydantic model
    """
    return TelemetryResponse(
        telemetry_id=record.telemetry_id,
        node_id=record.node_id,
        sequence=record.sequence,
        measurement_ts=record.measurement_ts,
        receive_ts=record.receive_ts,
        source=record.source,
        location=_geography_to_dict(record.location),
        measurements=record.measurements_jsonb or {},
        diagnostics=record.diagnostics_jsonb or {},
        power=record.power_jsonb,
        schema_version=record.schema_version
    )


def _hazard_to_response(assessment: HazardAssessment) -> HazardResponse:
    """Convert HazardAssessment to response model

    Args:
        assessment: HazardAssessment database model

    Returns:
        HazardResponse pydantic model
    """
    return HazardResponse(
        assessment_id=assessment.assessment_id,
        telemetry_id=assessment.telemetry_id,
        hazard_type=assessment.hazard_type,
        evidence=assessment.evidence,
        confidence=assessment.confidence,
        severity=assessment.severity,
        risk=assessment.risk,
        state=assessment.state,
        information_condition=assessment.information_condition,
        created_at=assessment.created_at
    )
