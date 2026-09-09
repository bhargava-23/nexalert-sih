"""Track C API routes for fire simulation and risk surfaces

Following Track B2 pattern from modules/api/routes_b2.py:
- FastAPI router with async endpoints
- Pydantic response models
- Database session dependency
- Error handling with HTTPException
"""
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, Field
import uuid

from db.database import get_db_session
from db.models_c import FireSimulation as FireSimulationModel, FireGeometry, RiskSurface, Exposure
from modules.simulation.fire_simulation import run_fire_simulation

logger = logging.getLogger(__name__)

router_c = APIRouter()


# Response models
class SimulationResponse(BaseModel):
    """Fire simulation response"""
    simulation_id: str
    incident_id: Optional[str]
    simulation_type: str
    ignition_lat: float
    ignition_lon: float
    ignition_time: str
    simulation_time: str
    environmental_state: Optional[dict]
    domain_extent: Optional[dict]
    crs_id: Optional[str]
    resolution_m: Optional[float]
    created_at: str


class GeometryResponse(BaseModel):
    """Fire geometry response"""
    geometry_id: int
    simulation_id: str
    zone_type: str
    geometry_wkt: str
    area_hectares: Optional[float]
    perimeter_m: Optional[float]
    created_at: str


class RiskResponse(BaseModel):
    """Risk surface response"""
    risk_id: int
    simulation_id: str
    extent: Optional[dict]
    max_risk: Optional[float]
    mean_risk: Optional[float]
    cells_at_risk: Optional[int]
    created_at: str


class ExposureResponse(BaseModel):
    """Exposure response"""
    exposure_id: int
    simulation_id: str
    zone_type: str
    population_at_risk: Optional[int]
    structures_threatened: Optional[int]
    infrastructure_affected: Optional[dict]
    created_at: str


class SimulationStartRequest(BaseModel):
    """Request to start fire simulation"""
    ignition_lat: float = Field(..., description="Ignition latitude (WGS84)")
    ignition_lon: float = Field(..., description="Ignition longitude (WGS84)")
    incident_id: Optional[str] = Field(None, description="Track B2 incident ID (for LIVE mode)")
    simulation_type: str = Field("SIMULATION", description="LIVE or SIMULATION")
    domain_size_m: float = Field(10000.0, description="Domain size in meters")
    cell_size_m: float = Field(50.0, description="Cell size in meters")
    max_time_minutes: float = Field(180.0, description="Max simulation time in minutes")
    wind_speed_ms: float = Field(5.0, description="Wind speed (m/s)")
    wind_from_deg: float = Field(270.0, description="Wind FROM direction (degrees)")
    moisture_index: float = Field(0.3, description="Moisture index [0, 1]")


@router_c.post("/simulations/start", response_model=SimulationResponse)
async def start_simulation(
    request: SimulationStartRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """Start fire simulation

    Runs fire spread simulation and persists results to database.
    """
    try:
        logger.info(
            f"Starting fire simulation at ({request.ignition_lat}, {request.ignition_lon}), "
            f"type={request.simulation_type}"
        )

        # Run simulation (placeholder - full integration later)
        summary = run_fire_simulation(
            ignition_lon=request.ignition_lon,
            ignition_lat=request.ignition_lat,
            simulation_type=request.simulation_type,
            incident_id=request.incident_id,
            domain_size_m=request.domain_size_m,
            cell_size_m=request.cell_size_m,
            max_time_minutes=request.max_time_minutes
        )

        # Create simulation record
        simulation = FireSimulationModel(
            simulation_id=uuid.uuid4(),
            incident_id=uuid.UUID(request.incident_id) if request.incident_id else None,
            simulation_type=request.simulation_type,
            ignition_lat=request.ignition_lat,
            ignition_lon=request.ignition_lon,
            ignition_time=datetime.utcnow(),
            simulation_time=datetime.utcnow(),
            environmental_state={
                "wind_speed_ms": request.wind_speed_ms,
                "wind_from_deg": request.wind_from_deg,
                "moisture_index": request.moisture_index,
            },
            domain_extent=summary["domain"],
            crs_id=summary["domain"]["crs"],
            resolution_m=request.cell_size_m,
            max_time_minutes=request.max_time_minutes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        session.add(simulation)
        await session.commit()
        await session.refresh(simulation)

        logger.info(f"Fire simulation created: {simulation.simulation_id}")

        return SimulationResponse(
            simulation_id=str(simulation.simulation_id),
            incident_id=str(simulation.incident_id) if simulation.incident_id else None,
            simulation_type=simulation.simulation_type,
            ignition_lat=simulation.ignition_lat,
            ignition_lon=simulation.ignition_lon,
            ignition_time=simulation.ignition_time.isoformat(),
            simulation_time=simulation.simulation_time.isoformat(),
            environmental_state=simulation.environmental_state,
            domain_extent=simulation.domain_extent,
            crs_id=simulation.crs_id,
            resolution_m=simulation.resolution_m,
            created_at=simulation.created_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to start simulation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router_c.get("/simulations/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(
    simulation_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get simulation by ID"""
    try:
        try:
            sim_uuid = uuid.UUID(simulation_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid simulation ID format: {simulation_id}")

        stmt = select(FireSimulationModel).where(FireSimulationModel.simulation_id == sim_uuid)
        result = await session.execute(stmt)
        simulation = result.scalar_one_or_none()

        if not simulation:
            raise HTTPException(status_code=404, detail=f"Simulation not found: {simulation_id}")

        return _simulation_to_response(simulation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get simulation {simulation_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router_c.get("/simulations", response_model=List[SimulationResponse])
async def list_simulations(
    simulation_type: Optional[str] = Query(None, description="Filter by type (LIVE or SIMULATION)"),
    incident_id: Optional[str] = Query(None, description="Filter by incident ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    session: AsyncSession = Depends(get_db_session)
):
    """List fire simulations"""
    try:
        stmt = select(FireSimulationModel).order_by(desc(FireSimulationModel.created_at))

        if simulation_type:
            stmt = stmt.where(FireSimulationModel.simulation_type == simulation_type)

        if incident_id:
            try:
                inc_uuid = uuid.UUID(incident_id)
                stmt = stmt.where(FireSimulationModel.incident_id == inc_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid incident ID format: {incident_id}")

        stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        simulations = result.scalars().all()

        return [_simulation_to_response(sim) for sim in simulations]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list simulations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router_c.get("/simulations/{simulation_id}/geometries", response_model=List[GeometryResponse])
async def get_fire_geometries(
    simulation_id: str,
    zone_type: Optional[str] = Query(None, description="Filter by zone (CURRENT, WARNING, PROJECTION)"),
    session: AsyncSession = Depends(get_db_session)
):
    """Get fire geometries for simulation"""
    try:
        try:
            sim_uuid = uuid.UUID(simulation_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid simulation ID format: {simulation_id}")

        stmt = select(FireGeometry).where(FireGeometry.simulation_id == sim_uuid)

        if zone_type:
            stmt = stmt.where(FireGeometry.zone_type == zone_type)

        stmt = stmt.order_by(FireGeometry.created_at)

        result = await session.execute(stmt)
        geometries = result.scalars().all()

        return [_geometry_to_response(geom) for geom in geometries]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get geometries for {simulation_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


def _simulation_to_response(simulation: FireSimulationModel) -> SimulationResponse:
    """Convert FireSimulation model to response"""
    return SimulationResponse(
        simulation_id=str(simulation.simulation_id),
        incident_id=str(simulation.incident_id) if simulation.incident_id else None,
        simulation_type=simulation.simulation_type,
        ignition_lat=simulation.ignition_lat,
        ignition_lon=simulation.ignition_lon,
        ignition_time=simulation.ignition_time.isoformat(),
        simulation_time=simulation.simulation_time.isoformat(),
        environmental_state=simulation.environmental_state,
        domain_extent=simulation.domain_extent,
        crs_id=simulation.crs_id,
        resolution_m=simulation.resolution_m,
        created_at=simulation.created_at.isoformat(),
    )


def _geometry_to_response(geom: FireGeometry) -> GeometryResponse:
    """Convert FireGeometry model to response"""
    from geoalchemy2.shape import to_shape
    from shapely import wkt as shapely_wkt

    # Convert PostGIS geometry to WKT
    geom_shape = to_shape(geom.geometry)
    geom_wkt = geom_shape.wkt

    return GeometryResponse(
        geometry_id=geom.geometry_id,
        simulation_id=str(geom.simulation_id),
        zone_type=geom.zone_type,
        geometry_wkt=geom_wkt,
        area_hectares=geom.area_hectares,
        perimeter_m=geom.perimeter_m,
        created_at=geom.created_at.isoformat(),
    )
