"""Test API routes for NexAlert canonical incident testing

Creates REAL PostgreSQL incidents through the canonical domain model.
Safe for testing - can be cleanly resolved.
"""
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shapely.geometry import Point, Polygon
from geoalchemy2.shape import from_shape

from db.database import get_db_session
from db.models_b2 import Incident, IncidentHazardAssessment
from db.models_c import FireGeometry, FireSimulation
from db.models import Node

logger = logging.getLogger(__name__)

router_test = APIRouter()


@router_test.post("/test/create-fire-incident")
async def create_test_fire_incident(
    node_id: str = "NODE-001",
    lat: float = 13.13495,
    lon: float = 77.56681,
    session: AsyncSession = Depends(get_db_session)
):
    """Create a canonical test FIRE incident in PostgreSQL

    This creates a REAL incident record through the canonical domain model:
    - Persists to PostgreSQL incidents table
    - Visible through GET /api/incidents
    - Can be resolved/cleaned up via /test/resolve-incident
    - Same data structure as production incidents

    Args:
        node_id: Contributing node ID (default: NODE-001)
        lat: Incident centroid latitude (default: 13.13495)
        lon: Incident centroid longitude (default: 77.56681)
        session: Database session

    Returns:
        Created incident with incident_id
    """
    try:
        # Generate deterministic UUID for test incident
        incident_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        # Create Point geometry for Incident
        pt = Point(lon, lat)

        # Create canonical Incident record (Phase 2C-3C multi-hazard model)
        incident = Incident(
            incident_id=incident_id,
            state="ACTIVE",  # ACTIVE = confirmed and ongoing
            information_condition="GOOD",
            centroid_lat=lat,
            centroid_lon=lon,
            geometry=from_shape(pt, srid=4326),
            first_observed_at=now,
            last_observed_at=now,
            resolved_at=None,
            source_summary={
                "node_count": 1,
                "contributing_nodes": [node_id],
                "test": True  # Mark as test incident
            },
            created_by="test_endpoint",
            current_version=1
        )
        session.add(incident)

        # Create canonical IncidentHazardAssessment for FIRE
        hazard_assessment = IncidentHazardAssessment(
            incident_id=incident_id,
            hazard_type="fire",
            evidence=0.89,
            confidence=0.85,
            severity=0.78,
            operational_risk=0.82,
            state="CONFIRMED",  # CONFIRMED = hazard verified
            information_condition="GOOD",
            hazard_specific_data={
                "temperature_c": 47.3,
                "gas_level": "elevated",
                "test": True
            },
            assessment_timestamp=now,
            model_version="test_v1",
            source_summary={
                "contributing_nodes": [node_id],
                "method": "test_endpoint"
            }
        )
        session.add(hazard_assessment)

        # Create fire simulation for this incident (required by Track C architecture)
        fire_simulation = FireSimulation(
            simulation_id=uuid.uuid4(),
            incident_id=incident_id,
            simulation_type="LIVE",
            ignition_lat=lat,
            ignition_lon=lon,
            ignition_time=now,
            simulation_time=now,
            max_time_minutes=120.0
        )
        session.add(fire_simulation)
        await session.flush()  # Get simulation_id

        # Create test geometries (Current, Warning, Projection)
        # Using a very simple approximation for degrees vs meters just for the test dummy data
        # ~111km per degree
        buffer_current = 100 / 111000.0  # 100m
        buffer_warning = 300 / 111000.0  # 300m
        buffer_projection = 600 / 111000.0 # 600m

        current_geom = pt.buffer(buffer_current)
        warning_geom = pt.buffer(buffer_warning)
        projection_geom = pt.buffer(buffer_projection).convex_hull

        # Calculate areas in hectares
        area_current = (buffer_current * 111000) ** 2 * 3.14159 / 10000  # rough circle area
        area_warning = (buffer_warning * 111000) ** 2 * 3.14159 / 10000
        area_projection = (buffer_projection * 111000) ** 2 * 3.14159 / 10000

        geom_current = FireGeometry(
            simulation_id=fire_simulation.simulation_id,
            zone_type="CURRENT",
            geometry=from_shape(current_geom, srid=4326),
            area_hectares=area_current
        )
        geom_warning = FireGeometry(
            simulation_id=fire_simulation.simulation_id,
            zone_type="WARNING",
            geometry=from_shape(warning_geom, srid=4326),
            area_hectares=area_warning
        )
        geom_projection = FireGeometry(
            simulation_id=fire_simulation.simulation_id,
            zone_type="PROJECTION",
            geometry=from_shape(projection_geom, srid=4326),
            area_hectares=area_projection
        )
        session.add_all([geom_current, geom_warning, geom_projection])

        # Commit to PostgreSQL
        await session.commit()

        logger.info(
            f"Created test FIRE incident: {incident_id} "
            f"(lat={lat}, lon={lon}, node={node_id})"
        )

        return {
            "success": True,
            "message": "Test FIRE incident created in PostgreSQL",
            "incident_id": str(incident_id),
            "state": "ACTIVE",
            "hazard_type": "fire",
            "hazard_state": "CONFIRMED",
            "centroid": {"lat": lat, "lon": lon},
            "created_at": now.isoformat(),
            "note": "This is a REAL incident record. Visible through GET /api/incidents. Resolve with POST /test/resolve-incident"
        }

    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to create test incident: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create test incident: {str(e)}")


@router_test.post("/test/resolve-incident/{incident_id}")
async def resolve_test_incident(
    incident_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Resolve a test incident (mark as RESOLVED, set resolved_at timestamp)

    Args:
        incident_id: UUID of incident to resolve
        session: Database session

    Returns:
        Resolution confirmation
    """
    try:
        # Parse UUID
        try:
            incident_uuid = uuid.UUID(incident_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid incident ID format: {incident_id}")

        # Query incident
        result = await session.execute(
            select(Incident).where(Incident.incident_id == incident_uuid)
        )
        incident = result.scalar_one_or_none()

        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident not found: {incident_id}")

        # Update to RESOLVED state
        incident.state = "RESOLVED"
        incident.resolved_at = datetime.now(timezone.utc)
        incident.last_observed_at = datetime.now(timezone.utc)

        await session.commit()

        logger.info(f"Resolved test incident: {incident_id}")

        return {
            "success": True,
            "message": "Test incident resolved",
            "incident_id": str(incident_id),
            "state": "RESOLVED",
            "resolved_at": incident.resolved_at.isoformat(),
            "note": "Incident no longer returned by GET /api/incidents?active_only=true"
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to resolve incident {incident_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to resolve incident: {str(e)}")


@router_test.get("/test/list-test-incidents")
async def list_test_incidents(
    session: AsyncSession = Depends(get_db_session)
):
    """List all incidents created by test endpoint (source_summary.test = true)

    Returns:
        List of test incidents
    """
    try:
        result = await session.execute(
            select(Incident).where(
                Incident.created_by == "test_endpoint"
            ).order_by(Incident.created_at.desc())
        )
        incidents = result.scalars().all()

        return {
            "test_incidents": [
                {
                    "incident_id": str(inc.incident_id),
                    "state": inc.state,
                    "created_at": inc.created_at.isoformat(),
                    "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None
                }
                for inc in incidents
            ],
            "total": len(incidents)
        }

    except Exception as e:
        logger.error(f"Failed to list test incidents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list test incidents: {str(e)}")
