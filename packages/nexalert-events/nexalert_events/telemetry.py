"""
Telemetry envelope schema - Python representation.

AUTHORITATIVE SCHEMA: schemas/telemetry-envelope.schema.json
This module synchronizes to that schema. Any divergence is a bug.

Specification: Document 07, Section 7
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class TelemetrySource(str, Enum):
    """Doc 07 Sec 7: LIVE vs SIMULATION distinction."""
    HARDWARE = "HARDWARE"
    SIMULATION = "SIMULATION"


class Location(BaseModel):
    """WGS84 coordinates. Doc 07 Sec 3."""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    alt: Optional[float] = None  # null = missing (NOT zero)


class Power(BaseModel):
    """Power/battery state. All optional - missing != zero."""
    battery_voltage: Optional[float] = None
    solar_current: Optional[float] = None
    battery_percent: Optional[float] = Field(None, ge=0, le=100)


class Measurements(BaseModel):
    """Sensor readings. All Optional to preserve missing != zero."""
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    pm25_ug_m3: Optional[float] = None
    pm10_ug_m3: Optional[float] = None

    @field_validator('*', mode='before')
    def preserve_none(cls, v):
        # Ensure None stays None, never coerced to 0
        return v


class Diagnostics(BaseModel):
    """D_ij dimensions for H_i computation. Doc 04 Sec 3.1."""
    self_test_passed: Optional[bool] = None
    comm_integrity: Optional[float] = Field(None, ge=0, le=1)
    calibration_valid: Optional[bool] = None
    stability_index: Optional[float] = Field(None, ge=0, le=1)
    uptime_s: Optional[int] = None


class TelemetryEnvelope(BaseModel):
    """
    Canonical telemetry envelope.

    Specification: Document 07, Section 7
    Authoritative schema: schemas/telemetry-envelope.schema.json

    Critical invariants:
    - measurement_timestamp != received_timestamp (IMPLEMENTATION_CONSTITUTION.md Sec 12)
    - Missing fields are None/null, NOT zero (IMPLEMENTATION_CONSTITUTION.md Sec 3)
    - source distinguishes HARDWARE from SIMULATION (Doc 07 Sec 7)
    """
    telemetry_id: str
    node_id: str
    sequence: int = Field(..., ge=0)
    measurement_timestamp: datetime
    received_timestamp: datetime
    location: Location
    measurements: Measurements
    diagnostics: Diagnostics
    power: Power
    source: TelemetrySource
    schema_version: str = "telemetry.v1"
    auth: dict = Field(default_factory=dict)  # HMAC placeholder Phase 6
