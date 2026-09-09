"""Database models for NexAlert backend

SQLAlchemy models matching the canonical database schema.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, BigInteger, Double, TIMESTAMP, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
from geoalchemy2 import Geography


class Base(DeclarativeBase):
    pass


class Node(Base):
    """Node registration and status

    Specification: Document 07, Section 3
    """
    __tablename__ = "nodes"

    node_id = Column(String(64), primary_key=True)
    status = Column(String(32), nullable=False)  # ACTIVE, INACTIVE, MAINTENANCE
    location = Column(Geography("Point", srid=4326))
    firmware_version = Column(String(64))
    config_version = Column(String(64))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    telemetry_records = relationship("TelemetryRecord", back_populates="node")
    sensor_assessments = relationship("SensorAssessment", back_populates="node")

    __table_args__ = (
        Index("idx_nodes_status", "status"),
    )


class TelemetryRecord(Base):
    """Immutable telemetry record

    Specification: Document 07, Section 2
    IMMUTABLE: Never update after insertion.
    """
    __tablename__ = "telemetry_records"

    telemetry_id = Column(String(64), primary_key=True)
    node_id = Column(String(64), ForeignKey("nodes.node_id"), nullable=False)
    sequence = Column(BigInteger, nullable=False)
    measurement_ts = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="When observation captured - DISTINCT from receive_ts per IMPLEMENTATION_CONSTITUTION.md Sec 12"
    )
    receive_ts = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="When backend received - server-assigned"
    )
    source = Column(String(32), nullable=False)  # HARDWARE, SIMULATION
    location = Column(Geography("Point", srid=4326))
    measurements_jsonb = Column(
        JSONB,
        nullable=False,
        comment="Sensor readings - NULL values preserve missing != zero"
    )
    diagnostics_jsonb = Column(
        JSONB,
        nullable=False,
        comment="D_ij diagnostic dimensions"
    )
    power_jsonb = Column(JSONB, comment="Power/battery state")
    schema_version = Column(String(32), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    node = relationship("Node", back_populates="telemetry_records")
    sensor_assessments = relationship("SensorAssessment", back_populates="telemetry")
    hazard_assessments = relationship("HazardAssessment", back_populates="telemetry")

    __table_args__ = (
        Index("idx_telemetry_node_seq", "node_id", "sequence", unique=True),
        Index("idx_telemetry_node_ts", "node_id", "measurement_ts"),
        Index("idx_telemetry_source", "source"),
    )


class SensorAssessment(Base):
    """Sensor-level intelligence assessments (H_i, Q_i, R_i, A_i)

    Phase 5: Edge intelligence outputs
    """
    __tablename__ = "sensor_assessments"

    assessment_id = Column(BigInteger, primary_key=True, autoincrement=True)
    telemetry_id = Column(String(64), ForeignKey("telemetry_records.telemetry_id"), nullable=False)
    node_id = Column(String(64), ForeignKey("nodes.node_id"), nullable=False)
    sensor_type = Column(String(64), nullable=False)
    health = Column(Double, comment="H_i - NULL = missing (NOT zero)")
    quality = Column(Double, comment="Q_i - NULL = missing")
    reliability = Column(Double, comment="R_i - NULL = missing")
    baseline_state = Column(String(32), comment="Phase 5")
    anomaly = Column(Double, comment="Phase 5")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    telemetry = relationship("TelemetryRecord", back_populates="sensor_assessments")
    node = relationship("Node", back_populates="sensor_assessments")

    __table_args__ = (
        Index("idx_sensor_assess_node_ts", "node_id", "created_at"),
        Index("idx_sensor_assess_telemetry", "telemetry_id"),
    )


class HazardAssessment(Base):
    """Hazard-level intelligence assessments (E_h, C_h, S_h, R_h, state)

    Phase 5: Edge intelligence outputs
    """
    __tablename__ = "hazard_assessments"

    assessment_id = Column(BigInteger, primary_key=True, autoincrement=True)
    telemetry_id = Column(String(64), ForeignKey("telemetry_records.telemetry_id"), nullable=False)
    hazard_type = Column(String(32), nullable=False)  # fire, flood, etc.
    evidence = Column(Double, comment="Phase 5")
    confidence = Column(Double, comment="Phase 5")
    severity = Column(Double, comment="Phase 5")
    risk = Column(Double, comment="Phase 5")
    state = Column(String(32), comment="Phase 5")  # NORMAL, WATCH, SUSPECTED, CONFIRMED, CRITICAL, RESOLVED
    information_condition = Column(String(32), comment="Phase 5")  # GOOD, DEGRADED, UNKNOWN
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    telemetry = relationship("TelemetryRecord", back_populates="hazard_assessments")

    __table_args__ = (
        Index("idx_hazard_assess_type_ts", "hazard_type", "created_at"),
        Index("idx_hazard_assess_telemetry", "telemetry_id"),
    )
