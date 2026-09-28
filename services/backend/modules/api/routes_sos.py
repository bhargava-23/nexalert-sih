"""SOS Emergency Request API routes

Simple SOS/emergency request endpoints for citizen safety alerts.
"""
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from pydantic import BaseModel, Field
from geoalchemy2.functions import ST_SetSRID, ST_MakePoint

from db.database import get_db_session
from db.models_sos import SOSRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sos", tags=["sos"])


# Request/Response models
class SOSCreateRequest(BaseModel):
    """Create new SOS request"""
    location_lat: Optional[float] = Field(None, ge=-90, le=90)
    location_lon: Optional[float] = Field(None, ge=-180, le=180)
    message: Optional[str] = Field(None, max_length=500)
    device_info: Optional[str] = Field(None, max_length=256)


class SOSResponse(BaseModel):
    """SOS request response"""
    sos_id: str
    status: str
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    message: Optional[str] = None
    device_info: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class SOSUpdateRequest(BaseModel):
    """Update SOS status"""
    status: str = Field(..., pattern="^(QUEUED|SENT|ACKNOWLEDGED|UNREACHABLE|RESOLVED)$")


# Routes

@router.post("", response_model=SOSResponse, status_code=201)
async def create_sos(
    request: SOSCreateRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """Create new SOS emergency request

    Args:
        request: SOS request details (location, message, device info)
        session: Database session

    Returns:
        Created SOS request with ID and status
    """
    try:
        # Create SOS request
        sos = SOSRequest(
            status="QUEUED",
            location_lat=request.location_lat,
            location_lon=request.location_lon,
            message=request.message,
            device_info=request.device_info
        )

        # Set PostGIS geography point if location provided
        if request.location_lat is not None and request.location_lon is not None:
            sos.location = ST_SetSRID(
                ST_MakePoint(request.location_lon, request.location_lat),
                4326
            )

        session.add(sos)
        await session.commit()
        await session.refresh(sos)

        logger.info(f"Created SOS request: {sos.sos_id}")

        return SOSResponse(
            sos_id=str(sos.sos_id),
            status=sos.status,
            location_lat=sos.location_lat,
            location_lon=sos.location_lon,
            message=sos.message,
            device_info=sos.device_info,
            created_at=sos.created_at,
            updated_at=sos.updated_at,
            acknowledged_at=sos.acknowledged_at,
            resolved_at=sos.resolved_at
        )

    except Exception as e:
        logger.error(f"Failed to create SOS request: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to create SOS request")


@router.get("", response_model=List[SOSResponse])
async def list_sos_requests(
    status: Optional[str] = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session)
):
    """List SOS requests

    Args:
        status: Optional status filter
        limit: Maximum requests to return
        session: Database session

    Returns:
        List of SOS requests, newest first
    """
    try:
        query = select(SOSRequest).order_by(desc(SOSRequest.created_at))

        if status:
            query = query.where(SOSRequest.status == status)

        query = query.limit(limit)

        result = await session.execute(query)
        requests = result.scalars().all()

        return [
            SOSResponse(
                sos_id=str(r.sos_id),
                status=r.status,
                location_lat=r.location_lat,
                location_lon=r.location_lon,
                message=r.message,
                device_info=r.device_info,
                created_at=r.created_at,
                updated_at=r.updated_at,
                acknowledged_at=r.acknowledged_at,
                resolved_at=r.resolved_at
            )
            for r in requests
        ]

    except Exception as e:
        logger.error(f"Failed to list SOS requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to list SOS requests")


@router.get("/{sos_id}", response_model=SOSResponse)
async def get_sos_request(
    sos_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get specific SOS request

    Args:
        sos_id: SOS request UUID
        session: Database session

    Returns:
        SOS request details
    """
    try:
        result = await session.execute(
            select(SOSRequest).where(SOSRequest.sos_id == sos_id)
        )
        sos = result.scalar_one_or_none()

        if not sos:
            raise HTTPException(status_code=404, detail="SOS request not found")

        return SOSResponse(
            sos_id=str(sos.sos_id),
            status=sos.status,
            location_lat=sos.location_lat,
            location_lon=sos.location_lon,
            message=sos.message,
            device_info=sos.device_info,
            created_at=sos.created_at,
            updated_at=sos.updated_at,
            acknowledged_at=sos.acknowledged_at,
            resolved_at=sos.resolved_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get SOS request {sos_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get SOS request")


@router.patch("/{sos_id}", response_model=SOSResponse)
async def update_sos_status(
    sos_id: str,
    request: SOSUpdateRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """Update SOS request status

    Args:
        sos_id: SOS request UUID
        request: Status update
        session: Database session

    Returns:
        Updated SOS request
    """
    try:
        # Get existing SOS request
        result = await session.execute(
            select(SOSRequest).where(SOSRequest.sos_id == sos_id)
        )
        sos = result.scalar_one_or_none()

        if not sos:
            raise HTTPException(status_code=404, detail="SOS request not found")

        # Update status and timestamps
        sos.status = request.status
        sos.updated_at = datetime.utcnow()

        if request.status == "ACKNOWLEDGED" and not sos.acknowledged_at:
            sos.acknowledged_at = datetime.utcnow()
        elif request.status == "RESOLVED" and not sos.resolved_at:
            sos.resolved_at = datetime.utcnow()

        await session.commit()
        await session.refresh(sos)

        logger.info(f"Updated SOS {sos_id} status to {request.status}")

        return SOSResponse(
            sos_id=str(sos.sos_id),
            status=sos.status,
            location_lat=sos.location_lat,
            location_lon=sos.location_lon,
            message=sos.message,
            device_info=sos.device_info,
            created_at=sos.created_at,
            updated_at=sos.updated_at,
            acknowledged_at=sos.acknowledged_at,
            resolved_at=sos.resolved_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update SOS {sos_id}: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to update SOS status")
