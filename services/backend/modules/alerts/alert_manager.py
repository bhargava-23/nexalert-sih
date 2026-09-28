"""Alert creation and management module

Handles alert lifecycle from recommendation to delivery.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from db.models_alerts import Alert
from db.models_b2 import Incident
from modules.alerts.web_push import get_web_push_service

logger = logging.getLogger(__name__)


async def create_alert_from_incident(
    session: AsyncSession,
    incident: Incident,
    severity: str = "WARNING",
    created_by: str = "system"
) -> Alert:
    """Create an alert recommendation from an incident

    Args:
        session: Database session
        incident: Source incident
        severity: Alert severity (ADVISORY, WARNING, CRITICAL)
        created_by: Who created the alert

    Returns:
        Created alert in RECOMMENDATION state
    """
    # Determine primary hazard type
    hazard_assessments = incident.hazard_assessments if hasattr(incident, 'hazard_assessments') else []

    if not hazard_assessments:
        logger.warning(f"Incident {incident.incident_id} has no hazard assessments")
        hazard_type = "unknown"
    else:
        # Use the most severe hazard
        critical_hazards = [h for h in hazard_assessments if h.state == "CRITICAL"]
        confirmed_hazards = [h for h in hazard_assessments if h.state == "CONFIRMED"]

        if critical_hazards:
            hazard_type = critical_hazards[0].hazard_type
            severity = "CRITICAL"
        elif confirmed_hazards:
            hazard_type = confirmed_hazards[0].hazard_type
        else:
            hazard_type = hazard_assessments[0].hazard_type

    # Generate alert title and message
    title = _generate_alert_title(hazard_type, severity)
    message = _generate_alert_message(incident, hazard_type, severity)
    action_guidance = _generate_action_guidance(hazard_type, severity)

    # Create alert
    alert = Alert(
        alert_id=uuid.uuid4(),
        incident_id=incident.incident_id,
        state="RECOMMENDATION",
        hazard_type=hazard_type,
        severity=severity,
        title=title,
        message=message,
        action_guidance=action_guidance,
        recommended_at=datetime.now(timezone.utc),
        created_by=created_by
    )

    session.add(alert)
    await session.commit()

    logger.info(f"Created alert recommendation: {alert.alert_id} for incident {incident.incident_id}")
    return alert


async def approve_and_issue_alert(
    session: AsyncSession,
    alert_id: uuid.UUID,
    approved_by: str = "authority"
) -> Alert:
    """Approve and issue an alert

    Args:
        session: Database session
        alert_id: Alert to approve
        approved_by: Who approved the alert

    Returns:
        Updated alert in ISSUED state
    """
    # Get alert
    result = await session.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise ValueError(f"Alert {alert_id} not found")

    if alert.state not in ("RECOMMENDATION", "APPROVED"):
        raise ValueError(f"Cannot issue alert in state {alert.state}")

    # Update alert state
    now = datetime.now(timezone.utc)
    alert.state = "ISSUED"
    alert.approved_at = now
    alert.approved_by = approved_by
    alert.issued_at = now

    await session.commit()

    logger.info(f"Approved and issued alert: {alert.alert_id}")

    # Trigger Web Push delivery
    alert.state = "DELIVERING"
    await session.commit()

    web_push = get_web_push_service()
    delivery_stats = await web_push.deliver_alert_to_subscriptions(session, alert)

    # Update alert with delivery stats
    alert.state = "DELIVERED"
    alert.delivered_at = datetime.now(timezone.utc)
    alert.delivery_stats = delivery_stats

    await session.commit()

    logger.info(f"Alert delivered: {alert.alert_id}, stats={delivery_stats}")
    return alert


async def resolve_alert(
    session: AsyncSession,
    alert_id: uuid.UUID
) -> Alert:
    """Resolve (stand down) an alert

    Args:
        session: Database session
        alert_id: Alert to resolve

    Returns:
        Updated alert in STAND_DOWN state
    """
    result = await session.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise ValueError(f"Alert {alert_id} not found")

    alert.state = "STAND_DOWN"
    alert.resolved_at = datetime.now(timezone.utc)

    await session.commit()

    logger.info(f"Resolved alert: {alert.alert_id}")

    # TODO: Send stand-down notifications to affected subscriptions

    return alert


def _generate_alert_title(hazard_type: str, severity: str) -> str:
    """Generate alert title based on hazard type and severity"""
    severity_prefix = {
        "ADVISORY": "Advisory",
        "WARNING": "Warning",
        "CRITICAL": "Critical Alert"
    }.get(severity, "Alert")

    hazard_names = {
        "fire": "Fire",
        "flood": "Flood",
        "landslide": "Landslide",
        "pollution": "Air Quality",
        "heat": "Extreme Heat"
    }

    hazard_name = hazard_names.get(hazard_type, hazard_type.title())
    return f"{severity_prefix}: {hazard_name} Detected"


def _generate_alert_message(incident, hazard_type: str, severity: str) -> str:
    """Generate alert message with location and time info"""
    location = ""
    if incident.centroid_lat and incident.centroid_lon:
        location = f" near {incident.centroid_lat:.4f}, {incident.centroid_lon:.4f}"

    hazard_descriptions = {
        "fire": "A fire hazard has been detected",
        "flood": "Flooding conditions detected",
        "landslide": "Ground instability detected",
        "pollution": "Poor air quality detected",
        "heat": "Extreme heat conditions detected"
    }

    description = hazard_descriptions.get(hazard_type, f"{hazard_type.title()} hazard detected")

    if severity == "CRITICAL":
        urgency = " Immediate action may be required."
    elif severity == "WARNING":
        urgency = " Monitor conditions and be prepared to act."
    else:
        urgency = " Stay informed of developing conditions."

    return f"{description}{location}.{urgency}"


def _generate_action_guidance(hazard_type: str, severity: str) -> str:
    """Generate recommended actions based on hazard type"""
    guidance_map = {
        "fire": "If you see smoke or flames, move away immediately. Follow evacuation orders from local authorities. Do not attempt to fight the fire yourself.",
        "flood": "Move to higher ground if flooding occurs. Do not walk or drive through flood water. Follow evacuation orders from local authorities.",
        "landslide": "Move away from the affected area. Do not return until authorities declare it safe. Watch for signs of ground movement.",
        "pollution": "Limit outdoor activities. Keep windows closed. Use air purifiers if available. Follow health advisories.",
        "heat": "Stay hydrated. Seek air-conditioned spaces. Check on vulnerable individuals. Avoid strenuous outdoor activities."
    }

    return guidance_map.get(hazard_type, "Follow instructions from local authorities. Stay alert and be prepared to evacuate if necessary.")
