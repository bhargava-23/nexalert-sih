"""Alert and Web Push API routes

Endpoints for alert management and Web Push subscription.
Specification: Document 10 (Incident Response & Alert Operations)
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from shapely.geometry import Point
from geoalchemy2.shape import from_shape
from pydantic import BaseModel, Field
import uuid

from db.database import get_db_session
from db.models_alerts import Alert, PushSubscription, AlertDelivery
from db.models_b2 import Incident
from modules.alerts.web_push import get_web_push_service
from modules.api.routes_ws import manager
import asyncio

logger = logging.getLogger(__name__)

router_alerts = APIRouter()


# Request/Response Models

class PushSubscriptionRequest(BaseModel):
    """Web Push subscription request"""
    endpoint: str = Field(..., description="Push service endpoint URL")
    p256dh_key: str = Field(..., description="Client public key (base64)")
    auth_secret: str = Field(..., description="Authentication secret (base64)")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    device_info: Optional[dict] = Field(None, description="Browser/device metadata")


class LocationUpdateRequest(BaseModel):
    """Location update for proximity alerts"""
    latitude: float
    longitude: float


class AlertResponse(BaseModel):
    """Alert response model"""
    alert_id: str
    incident_id: str
    state: str
    hazard_type: str
    severity: Optional[str]
    title: str
    message: str
    action_guidance: Optional[str]
    recommended_at: str
    approved_at: Optional[str]
    issued_at: Optional[str]
    resolved_at: Optional[str]


class PushSubscriptionResponse(BaseModel):
    """Push subscription response"""
    subscription_id: str
    is_active: bool
    subscribed_at: str


class VapidPublicKeyResponse(BaseModel):
    """VAPID public key for frontend"""
    public_key: str


# Endpoints

@router_alerts.get("/alerts/vapid-public-key", response_model=VapidPublicKeyResponse)
async def get_vapid_public_key():
    """Get VAPID public key for Web Push subscription

    Frontend uses this to subscribe browsers to push notifications.
    """
    web_push = get_web_push_service()
    return VapidPublicKeyResponse(public_key=web_push.get_public_key())


@router_alerts.post("/alerts/subscribe", response_model=PushSubscriptionResponse)
async def subscribe_to_push(
    request: PushSubscriptionRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """Subscribe browser to Web Push notifications

    Creates or updates push subscription for this browser/device.
    """
    try:
        # Check if subscription already exists
        existing = await session.execute(
            select(PushSubscription).where(PushSubscription.endpoint == request.endpoint)
        )
        subscription = existing.scalar_one_or_none()

        if subscription:
            # Update existing subscription
            subscription.p256dh_key = request.p256dh_key
            subscription.auth_secret = request.auth_secret
            subscription.is_active = True
            subscription.failure_count = 0
            if request.user_id:
                subscription.user_id = request.user_id
            if request.device_info:
                subscription.device_info = request.device_info
            logger.info(f"Updated push subscription: {subscription.subscription_id}")
        else:
            # Create new subscription
            subscription = PushSubscription(
                endpoint=request.endpoint,
                p256dh_key=request.p256dh_key,
                auth_secret=request.auth_secret,
                user_id=request.user_id,
                device_info=request.device_info
            )
            session.add(subscription)
            logger.info(f"Created push subscription: {subscription.subscription_id}")

        await session.commit()

        return PushSubscriptionResponse(
            subscription_id=str(subscription.subscription_id),
            is_active=subscription.is_active,
            subscribed_at=subscription.subscribed_at.isoformat()
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Push subscription failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Subscription failed: {str(e)}")


@router_alerts.post("/alerts/unsubscribe")
async def unsubscribe_from_push(
    endpoint: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Unsubscribe browser from Web Push notifications"""
    try:
        result = await session.execute(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        subscription.is_active = False
        await session.commit()

        logger.info(f"Unsubscribed: {subscription.subscription_id}")
        return {"success": True, "message": "Unsubscribed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unsubscribe failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unsubscribe failed: {str(e)}")


@router_alerts.post("/alerts/update-location")
async def update_subscription_location(
    endpoint: str,
    location: LocationUpdateRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """Update subscription location for proximity alerts"""
    try:
        result = await session.execute(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        subscription.location_lat = int(location.latitude * 1e6)  # Store as microdegrees
        subscription.location_lon = int(location.longitude * 1e6)
        subscription.location_updated_at = datetime.now(timezone.utc)

        await session.commit()

        return {"success": True, "message": "Location updated"}

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Location update failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Location update failed: {str(e)}")


@router_alerts.get("/alerts/citizen", response_model=List[AlertResponse])
async def get_citizen_alerts(
    active_only: bool = True,
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session)
):
    """Get alerts relevant to citizens

    Returns issued alerts that citizens should see.
    """
    try:
        query = select(Alert).where(
            Alert.state.in_(["ISSUED", "DELIVERING", "DELIVERED"])
        )

        if active_only:
            query = query.where(Alert.resolved_at.is_(None))

        query = query.order_by(desc(Alert.issued_at)).limit(limit)

        result = await session.execute(query)
        alerts = result.scalars().all()

        return [
            AlertResponse(
                alert_id=str(alert.alert_id),
                incident_id=str(alert.incident_id),
                state=alert.state,
                hazard_type=alert.hazard_type,
                severity=alert.severity,
                title=alert.title,
                message=alert.message,
                action_guidance=alert.action_guidance,
                recommended_at=alert.recommended_at.isoformat(),
                approved_at=alert.approved_at.isoformat() if alert.approved_at else None,
                issued_at=alert.issued_at.isoformat() if alert.issued_at else None,
                resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None
            )
            for alert in alerts
        ]

    except Exception as e:
        logger.error(f"Failed to get citizen alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router_alerts.post("/alerts/test-push")
async def test_push_notification(
    endpoint: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Test Web Push delivery to a specific subscription

    Sends a test notification for verification purposes.
    """
    try:
        # Find subscription
        result = await session.execute(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        # Create a test incident using actual Incident schema
        test_incident = Incident(
            incident_id=uuid.uuid4(),
            state="ACTIVE",
            information_condition="GOOD",
            first_observed_at=datetime.now(timezone.utc),
            last_observed_at=datetime.now(timezone.utc),
            created_by="test_endpoint",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            centroid_lat=13.13495,
            centroid_lon=77.56681,
            geometry=from_shape(Point(77.56681, 13.13495), srid=4326)
        )
        session.add(test_incident)
        await session.flush()

        # Create and persist test alert (omit affected_radius_m - column doesn't exist in DB)
        test_alert = Alert(
            alert_id=uuid.uuid4(),
            incident_id=test_incident.incident_id,
            state="ISSUED",
            hazard_type="fire",
            severity="WARNING",
            title="NexAlert Test Notification",
            message="This is a test notification to verify Web Push is working correctly.",
            action_guidance="No action required - this is a test.",
            recommended_at=datetime.now(timezone.utc),
            issued_at=datetime.now(timezone.utc),
            created_by="test_endpoint"
        )
        session.add(test_alert)
        await session.flush()

        # Create test delivery record
        delivery = AlertDelivery(
            alert_id=test_alert.alert_id,
            subscription_id=subscription.subscription_id,
            status="PENDING",
            attempt_count=1
        )
        session.add(delivery)
        await session.flush()

        # Send test push
        web_push = get_web_push_service()
        # Broadcast to offline local WebSocket clients
        try:
            ws_payload = {
                "type": "NEW_ALERT",
                "alert": {
                    "alert_id": str(test_alert.alert_id),
                    "headline": test_alert.headline,
                    "description": test_alert.description,
                    "severity": test_alert.severity,
                    "category": test_alert.category,
                    "instruction": test_alert.instruction,
                    "created_at": test_alert.created_at.isoformat()
                }
            }
            asyncio.create_task(manager.broadcast(ws_payload))
        except Exception as e:
            logger.error(f"Failed to broadcast websocket event: {e}")

        success, error = await web_push.send_push_notification(
            session, subscription, test_alert, delivery
        )

        if success:
            return {
                "success": True,
                "message": "Test notification sent successfully",
                "subscription_id": str(subscription.subscription_id)
            }
        else:
            raise HTTPException(status_code=500, detail=f"Push failed: {error}")

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Test push failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test push failed: {str(e)}")
