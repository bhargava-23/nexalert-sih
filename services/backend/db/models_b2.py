"""Track B2 database models for Master/Regional Intelligence

Additional models for incident correlation, regional fusion, and multi-node aggregation.
These extend the existing Track B1 models without modifying them.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, BigInteger, Double, TIMESTAMP, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
import uuid

from db.models import Base


class Incident(Base):
    """Regional incident entity

    Specification: Document 10, Section 2
    Tracks correlated hazard observations across multiple nodes.
    """
    __tablename__ = "incidents"

    incident_id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Stable operational incident identity"
    )
    hazard_type = Column(String(32), nullable=False)  # FIRE, FLOOD, etc.
    state = Column(
        String(32),
        nullable=False,
        comment="NEW, ACTIVE, ESCALATED, RESOLVED"
    )
    information_condition = Column(String(32), comment="GOOD, DEGRADED, UNKNOWN")
    severity_index = Column(Double, comment="Regional severity [0,1]")
    risk_index = Column(Double, comment="Regional risk [0,1]")
    confidence_index = Column(Double, comment="Regional confidence [0,1]")

    # Geometry
    geometry = Column(
        Geography("Geometry", srid=4326),
        comment="Affected area (Point/Polygon/MultiPolygon)"
    )
    centroid_lat = Column(Double)
    centroid_lon = Column(Double)

    # Temporal tracking
    first_observed_at = Column(TIMESTAMP(timezone=True), nullable=False)
    last_observed_at = Column(TIMESTAMP(timezone=True), nullable=False)
    resolved_at = Column(TIMESTAMP(timezone=True))

    # Provenance
    source_summary = Column(
        JSONB,
        comment="Contributing node IDs and observation counts"
    )
    created_by = Column(
        String(32),
        nullable=False,
        comment="SYSTEM, OPERATOR, CITIZEN_SOS"
    )
    resolution_reason = Column(String(128))

    # Versioning
    current_version = Column(BigInteger, nullable=False, default=1)

    # Audit
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    observations = relationship("IncidentObservation", back_populates="incident")
    regional_assessments = relationship("RegionalHazardAssessment", back_populates="incident")

    __table_args__ = (
        Index("idx_incidents_hazard_state", "hazard_type", "state"),
        Index("idx_incidents_last_observed", "last_observed_at"),
        Index("idx_incidents_created", "created_at"),
    )


class IncidentObservation(Base):
    """Link between incidents and contributing node observations

    Tracks which telemetry/hazard assessments contribute to each incident.
    """
    __tablename__ = "incident_observations"

    observation_id = Column(BigInteger, primary_key=True, autoincrement=True)
    incident_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("incidents.incident_id"),
        nullable=False
    )
    node_id = Column(String(64), ForeignKey("nodes.node_id"), nullable=False)
    telemetry_id = Column(
        String(64),
        ForeignKey("telemetry_records.telemetry_id"),
        nullable=False
    )
    hazard_assessment_id = Column(
        BigInteger,
        ForeignKey("hazard_assessments.assessment_id")
    )

    # Contribution metrics
    weight = Column(
        Double,
        comment="Contribution weight based on trust/confidence/freshness"
    )
    is_primary = Column(
        String(1),
        comment="Y if primary detection, N if corroborating"
    )

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    incident = relationship("Incident", back_populates="observations")

    __table_args__ = (
        Index("idx_incident_obs_incident", "incident_id"),
        Index("idx_incident_obs_node", "node_id"),
        Index("idx_incident_obs_telemetry", "telemetry_id"),
    )


class RegionalHazardAssessment(Base):
    """Master/regional aggregated hazard assessment

    Fuses multiple node-level hazard assessments into regional intelligence.
    """
    __tablename__ = "regional_hazard_assessments"

    assessment_id = Column(BigInteger, primary_key=True, autoincrement=True)
    incident_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("incidents.incident_id"),
        nullable=False
    )
    hazard_type = Column(String(32), nullable=False)

    # Fused metrics
    regional_evidence = Column(Double, comment="Fused evidence [0,1]")
    regional_confidence = Column(Double, comment="Fused confidence [0,1]")
    regional_severity = Column(Double, comment="Fused severity [0,1]")
    regional_risk = Column(Double, comment="Fused risk [0,1]")

    # Node context
    contributing_nodes = Column(
        JSONB,
        comment="Array of {node_id, weight, state, freshness}"
    )
    node_count = Column(BigInteger, comment="Number of contributing nodes")
    agreement_index = Column(
        Double,
        comment="Inter-node agreement [0,1]"
    )

    # Spatial context
    spatial_extent_m = Column(Double, comment="Spatial extent in meters")

    # Information quality
    information_condition = Column(String(32), comment="GOOD, DEGRADED, UNKNOWN")
    freshness_index = Column(
        Double,
        comment="Temporal freshness [0,1], recent = 1.0"
    )

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    incident = relationship("Incident", back_populates="regional_assessments")

    __table_args__ = (
        Index("idx_regional_assess_incident", "incident_id"),
        Index("idx_regional_assess_hazard_ts", "hazard_type", "created_at"),
    )


class NodeStatus(Base):
    """Node health/freshness tracking for Master fusion

    Tracks node connectivity, data freshness, and reliability for regional fusion.
    """
    __tablename__ = "node_status"

    status_id = Column(BigInteger, primary_key=True, autoincrement=True)
    node_id = Column(String(64), ForeignKey("nodes.node_id"), nullable=False)

    # Freshness
    last_telemetry_at = Column(TIMESTAMP(timezone=True))
    last_heartbeat_at = Column(TIMESTAMP(timezone=True))
    staleness_seconds = Column(Double, comment="Time since last data")

    # Reliability
    reliability_index = Column(
        Double,
        comment="Historical reliability [0,1]"
    )
    uptime_pct_24h = Column(Double, comment="24-hour uptime percentage")

    # Connectivity
    connection_state = Column(
        String(32),
        comment="CONNECTED, DISCONNECTED, DEGRADED"
    )
    consecutive_failures = Column(BigInteger, default=0)

    # Quality
    data_quality_index = Column(
        Double,
        comment="Recent data quality [0,1]"
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_node_status_node", "node_id", unique=True),
        Index("idx_node_status_updated", "updated_at"),
    )
