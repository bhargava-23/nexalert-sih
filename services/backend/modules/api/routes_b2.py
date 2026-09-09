"""Track B2 API routes for regional intelligence and incidents

Extends Track B1 API with Master/Regional Intelligence endpoints.
"""
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from pydantic import BaseModel, Field
import uuid

from db.database import get_db_session
from db.models_b2 import Incident, RegionalHazardAssessment, IncidentObservation, NodeStatus

logger = logging.getLogger(__name__)

router_b2 = APIRouter()


# Response models
class IncidentResponse(BaseModel):
    """Incident response"""
    incident_id: str
    hazard_type: str
    state: str
    information_condition: Optional[str]
    severity_index: Optional[float]
    risk_index: Optional[float]
    confidence_index: Optional[float]
    centroid: Optional[dict] = None  # {lat, lon}
    first_observed_at: datetime
    last_observed_at: datetime
    resolved_at: Optional[datetime]
    source_summary: Optional[dict]
    created_by: str
    current_version: int
    created_at: datetime
    updated_at: datetime


class RegionalHazardResponse(BaseModel):
    """Regional hazard assessment response"""
    assessment_id: int
    incident_id: str
    hazard_type: str
    regional_evidence: Optional[float]
    regional_confidence: Optional[float]
    regional_severity: Optional[float]
    regional_risk: Optional[float]
    contributing_nodes: Optional[List[dict]]
    node_count: Optional[int]
    agreement_index: Optional[float]
    spatial_extent_m: Optional[float]
    information_condition: Optional[str]
    freshness_index: Optional[float]
    created_at: datetime


class NodeStatusResponse(BaseModel):
    """Node status response"""
    node_id: str
    last_telemetry_at: Optional[datetime]
    last_heartbeat_at: Optional[datetime]
    staleness_seconds: Optional[float]
    reliability_index: Optional[float]
    uptime_pct_24h: Optional[float]
    connection_state: Optional[str]
    data_quality_index: Optional[float]
    updated_at: datetime


# Routes

@router_b2.get("/incidents", response_model=List[IncidentResponse])
async def get_incidents(
    hazard_type: Optional[str] = Query(None, description="Filter by hazard type"),
    state: Optional[str] = Query(None, description="Filter by state (NEW, ACTIVE, ESCALATED, RESOLVED)"),
    active_only: bool = Query(True, description="Only return non-resolved incidents"),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session)
):
    """Get list of incidents

    Args:
        hazard_type: Optional hazard type filter (fire, flood, etc.)
        state: Optional state filter
        active_only: If true, exclude RESOLVED incidents
        limit: Maximum incidents to return
        session: Database session

    Returns:
        List of incidents
    """
    try:
        query = select(Incident).order_by(desc(Incident.last_observed_at)).limit(limit)

        if hazard_type:
            query = query.where(Incident.hazard_type == hazard_type)

        if state:
            query = query.where(Incident.state == state)

        if active_only:
            query = query.where(Incident.state != "RESOLVED")

        result = await session.execute(query)
        incidents = result.scalars().all()

        return [_incident_to_response(inc) for inc in incidents]

    except Exception as e:
        logger.error(f"Failed to get incidents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router_b2.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get single incident by ID

    Args:
        incident_id: Incident UUID
        session: Database session

    Returns:
        Incident details
    """
    try:
        # Parse UUID
        try:
            incident_uuid = uuid.UUID(incident_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid incident ID format: {incident_id}")

        result = await session.execute(
            select(Incident).where(Incident.incident_id == incident_uuid)
        )
        incident = result.scalar_one_or_none()

        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident not found: {incident_id}")

        return _incident_to_response(incident)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get incident {incident_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router_b2.get("/regional-hazards", response_model=List[RegionalHazardResponse])
async def get_regional_hazards(
    hazard_type: Optional[str] = Query(None, description="Filter by hazard type"),
    incident_id: Optional[str] = Query(None, description="Filter by incident ID"),
    limit: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session)
):
    """Get regional hazard assessments

    Args:
        hazard_type: Optional hazard type filter
        incident_id: Optional incident ID filter
        limit: Maximum assessments to return
        session: Database session

    Returns:
        List of regional hazard assessments
    """
    try:
        query = select(RegionalHazardAssessment).order_by(
            desc(RegionalHazardAssessment.created_at)
        ).limit(limit)

        if hazard_type:
            query = query.where(RegionalHazardAssessment.hazard_type == hazard_type)

        if incident_id:
            try:
                incident_uuid = uuid.UUID(incident_id)
                query = query.where(RegionalHazardAssessment.incident_id == incident_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid incident ID format: {incident_id}")

        result = await session.execute(query)
        assessments = result.scalars().all()

        return [_regional_hazard_to_response(assessment) for assessment in assessments]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get regional hazards: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router_b2.get("/node-status", response_model=List[NodeStatusResponse])
async def get_node_status(
    node_id: Optional[str] = Query(None, description="Filter by node ID"),
    connection_state: Optional[str] = Query(None, description="Filter by connection state"),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session)
):
    """Get node status/freshness information

    Args:
        node_id: Optional node ID filter
        connection_state: Optional connection state filter (CONNECTED, DISCONNECTED, DEGRADED)
        limit: Maximum records to return
        session: Database session

    Returns:
        List of node status records
    """
    try:
        query = select(NodeStatus).order_by(desc(NodeStatus.updated_at)).limit(limit)

        if node_id:
            query = query.where(NodeStatus.node_id == node_id)

        if connection_state:
            query = query.where(NodeStatus.connection_state == connection_state)

        result = await session.execute(query)
        statuses = result.scalars().all()

        return [_node_status_to_response(status) for status in statuses]

    except Exception as e:
        logger.error(f"Failed to get node status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router_b2.get("/incidents/{incident_id}/observations")
async def get_incident_observations(
    incident_id: str,
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session)
):
    """Get observations contributing to an incident

    Args:
        incident_id: Incident UUID
        limit: Maximum observations to return
        session: Database session

    Returns:
        List of contributing observations
    """
    try:
        # Parse UUID
        try:
            incident_uuid = uuid.UUID(incident_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid incident ID format: {incident_id}")

        result = await session.execute(
            select(IncidentObservation)
            .where(IncidentObservation.incident_id == incident_uuid)
            .order_by(desc(IncidentObservation.created_at))
            .limit(limit)
        )
        observations = result.scalars().all()

        return [
            {
                "observation_id": obs.observation_id,
                "incident_id": str(obs.incident_id),
                "node_id": obs.node_id,
                "telemetry_id": obs.telemetry_id,
                "hazard_assessment_id": obs.hazard_assessment_id,
                "weight": obs.weight,
                "is_primary": obs.is_primary,
                "created_at": obs.created_at
            }
            for obs in observations
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get incident observations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# Helper functions

def _incident_to_response(incident: Incident) -> IncidentResponse:
    """Convert Incident model to response"""
    centroid = None
    if incident.centroid_lat is not None and incident.centroid_lon is not None:
        centroid = {
            "lat": incident.centroid_lat,
            "lon": incident.centroid_lon
        }

    return IncidentResponse(
        incident_id=str(incident.incident_id),
        hazard_type=incident.hazard_type,
        state=incident.state,
        information_condition=incident.information_condition,
        severity_index=incident.severity_index,
        risk_index=incident.risk_index,
        confidence_index=incident.confidence_index,
        centroid=centroid,
        first_observed_at=incident.first_observed_at,
        last_observed_at=incident.last_observed_at,
        resolved_at=incident.resolved_at,
        source_summary=incident.source_summary,
        created_by=incident.created_by,
        current_version=incident.current_version,
        created_at=incident.created_at,
        updated_at=incident.updated_at
    )


def _regional_hazard_to_response(assessment: RegionalHazardAssessment) -> RegionalHazardResponse:
    """Convert RegionalHazardAssessment model to response"""
    return RegionalHazardResponse(
        assessment_id=assessment.assessment_id,
        incident_id=str(assessment.incident_id),
        hazard_type=assessment.hazard_type,
        regional_evidence=assessment.regional_evidence,
        regional_confidence=assessment.regional_confidence,
        regional_severity=assessment.regional_severity,
        regional_risk=assessment.regional_risk,
        contributing_nodes=assessment.contributing_nodes,
        node_count=assessment.node_count,
        agreement_index=assessment.agreement_index,
        spatial_extent_m=assessment.spatial_extent_m,
        information_condition=assessment.information_condition,
        freshness_index=assessment.freshness_index,
        created_at=assessment.created_at
    )


def _node_status_to_response(status: NodeStatus) -> NodeStatusResponse:
    """Convert NodeStatus model to response"""
    return NodeStatusResponse(
        node_id=status.node_id,
        last_telemetry_at=status.last_telemetry_at,
        last_heartbeat_at=status.last_heartbeat_at,
        staleness_seconds=status.staleness_seconds,
        reliability_index=status.reliability_index,
        uptime_pct_24h=status.uptime_pct_24h,
        connection_state=status.connection_state,
        data_quality_index=status.data_quality_index,
        updated_at=status.updated_at
    )
