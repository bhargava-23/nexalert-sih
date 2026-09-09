"""Track C database models for fire spread simulation

Follows Track B2 patterns from db/models_b2.py:
- Import from db.models Base class
- Use geoalchemy2.Geography for spatial columns
- Use PGUUID for UUID columns
- Use TIMESTAMP(timezone=True) for timestamps
- Define __table_args__ with Index objects
"""
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Double, TIMESTAMP, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from geoalchemy2 import Geography
import uuid

from db.models import Base


class FireSimulation(Base):
    """Track C fire spread simulation"""
    __tablename__ = "fire_simulations"

    simulation_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("incidents.incident_id"),
        nullable=True,
        comment="Link to Track B2 incident (nullable for SIMULATION mode)"
    )
    simulation_type = Column(
        String(32),
        nullable=False,
        comment="LIVE (from incident) or SIMULATION (manual)"
    )
    ignition_lat = Column(Double, nullable=False, comment="Ignition latitude (WGS84)")
    ignition_lon = Column(Double, nullable=False, comment="Ignition longitude (WGS84)")
    ignition_time = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="Ignition timestamp"
    )
    simulation_time = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="Current simulation time (now for the simulation)"
    )
    environmental_state = Column(
        JSONB,
        comment="Wind, moisture, temperature snapshot"
    )
    domain_extent = Column(JSONB, comment="Simulation domain bbox")
    crs_id = Column(String(64), comment="Projected CRS used for simulation (e.g., EPSG:32643)")
    resolution_m = Column(Double, comment="Grid cell size in meters")
    max_time_minutes = Column(Double, comment="Maximum simulation time in minutes")
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="now()"
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="now()"
    )

    __table_args__ = (
        Index("idx_fire_sim_incident", "incident_id"),
        Index("idx_fire_sim_type", "simulation_type"),
        Index("idx_fire_sim_created", "created_at"),
    )


class FireGeometry(Base):
    """Physical fire footprint and zones"""
    __tablename__ = "fire_geometries"

    geometry_id = Column(BigInteger, primary_key=True, autoincrement=True)
    simulation_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("fire_simulations.simulation_id"),
        nullable=False
    )
    zone_type = Column(
        String(32),
        nullable=False,
        comment="CURRENT, WARNING, PROJECTION"
    )
    geometry = Column(
        Geography("Geometry", srid=4326),
        nullable=False,
        comment="Fire area Polygon/MultiPolygon (WGS84)"
    )
    physical_footprint = Column(
        Geography("Geometry", srid=4326),
        comment="Model-derived footprint (physics output)"
    )
    operational_buffer = Column(
        Geography("Geometry", srid=4326),
        comment="Policy-defined safety buffer (NOT physics)"
    )
    area_hectares = Column(Double, comment="Area in hectares")
    perimeter_m = Column(Double, comment="Perimeter in meters")
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="now()"
    )

    __table_args__ = (
        Index("idx_fire_geom_sim", "simulation_id"),
        Index("idx_fire_geom_zone", "zone_type"),
        Index("idx_fire_geom_created", "created_at"),
    )


class RiskSurface(Base):
    """Risk heatmap/surface

    CRITICAL: Risk surface is continuous operational index, NOT probability.
    Risk surface is DISTINCT from physical fire footprint.
    """
    __tablename__ = "risk_surfaces"

    risk_id = Column(BigInteger, primary_key=True, autoincrement=True)
    simulation_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("fire_simulations.simulation_id"),
        nullable=False
    )
    risk_raster = Column(
        JSONB,
        comment="Serialized risk grid (sparse or dense format)"
    )
    extent = Column(JSONB, comment="Risk surface bbox")
    max_risk = Column(Double, comment="Maximum risk value [0, 1]")
    mean_risk = Column(Double, comment="Mean risk value (non-zero cells)")
    cells_at_risk = Column(BigInteger, comment="Number of cells with risk > 0")
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="now()"
    )

    __table_args__ = (
        Index("idx_risk_surface_sim", "simulation_id"),
    )


class Exposure(Base):
    """Exposure metrics

    CRITICAL: Exposure is downstream of physical hazard, NOT part of hazard itself.
    """
    __tablename__ = "exposures"

    exposure_id = Column(BigInteger, primary_key=True, autoincrement=True)
    simulation_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("fire_simulations.simulation_id"),
        nullable=False
    )
    zone_type = Column(
        String(32),
        nullable=False,
        comment="CURRENT, WARNING, PROJECTION"
    )
    population_at_risk = Column(
        BigInteger,
        comment="Population count in zone"
    )
    structures_threatened = Column(
        BigInteger,
        comment="Structure count in zone"
    )
    infrastructure_affected = Column(
        JSONB,
        comment="Infrastructure items at risk (by type)"
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="now()"
    )

    __table_args__ = (
        Index("idx_exposure_sim", "simulation_id"),
        Index("idx_exposure_zone", "zone_type"),
    )
