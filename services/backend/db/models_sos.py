"""SOS Emergency Request models

Simple SOS/emergency request tracking for citizen safety alerts.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, BigInteger, Double, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from geoalchemy2 import Geography
import uuid

from db.models import Base


class SOSRequest(Base):
    """Citizen emergency SOS request

    Tracks emergency assistance requests from citizens.
    """
    __tablename__ = "sos_requests"

    sos_id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique SOS request identifier"
    )
    status = Column(
        String(32),
        nullable=False,
        default="QUEUED",
        comment="QUEUED, SENT, ACKNOWLEDGED, UNREACHABLE, RESOLVED"
    )

    # Location
    location = Column(
        Geography("Point", srid=4326),
        comment="Citizen location at time of SOS"
    )
    location_lat = Column(Double)
    location_lon = Column(Double)

    # Optional context
    message = Column(Text, comment="Optional message from citizen")
    device_info = Column(String(256), comment="User agent / device info")

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    acknowledged_at = Column(TIMESTAMP(timezone=True))
    resolved_at = Column(TIMESTAMP(timezone=True))
