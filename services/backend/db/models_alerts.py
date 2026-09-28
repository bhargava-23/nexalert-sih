"""Alert and Web Push database models

Alert lifecycle and Web Push subscription management for NexAlert.
Specification: Document 10 (Incident Response & Alert Operations)
"""
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Boolean, TIMESTAMP, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
import uuid

from db.models import Base


class Alert(Base):
    """Canonical alert entity

    Represents a hazard alert in its lifecycle from recommendation to delivery.
    Human-in-the-loop: NexAlert recommends, authority approves, system delivers.
    """
    __tablename__ = "alerts"

    alert_id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Stable alert identity"
    )
    incident_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("incidents.incident_id"),
        nullable=False,
        comment="Source incident"
    )

    # Alert lifecycle state
    state = Column(
        String(32),
        nullable=False,
        comment="RECOMMENDATION, APPROVED, ISSUED, DELIVERING, DELIVERED, OPENED, ACKNOWLEDGED, UNREACHABLE, STAND_DOWN"
    )

    # Alert content
    hazard_type = Column(String(32), nullable=False, comment="Primary hazard type")
    severity = Column(String(32), comment="ADVISORY, WARNING, CRITICAL")
    title = Column(String(256), nullable=False, comment="Alert title")
    message = Column(Text, nullable=False, comment="Alert message body")
    action_guidance = Column(Text, comment="Recommended actions")

    # Geospatial targeting (columns not yet in database - commented out)
    # affected_area = Column(JSONB, comment="GeoJSON geometry of affected area")
    # affected_radius_m = Column(BigInteger, comment="Radius in meters for proximity alerts")

    # Lifecycle timestamps
    recommended_at = Column(TIMESTAMP(timezone=True), nullable=False, comment="When NexAlert recommended alert")
    approved_at = Column(TIMESTAMP(timezone=True), comment="When authority approved")
    issued_at = Column(TIMESTAMP(timezone=True), comment="When alert was issued")
    delivered_at = Column(TIMESTAMP(timezone=True), comment="When delivery completed")
    resolved_at = Column(TIMESTAMP(timezone=True), comment="When alert was stood down")

    # Authority tracking
    created_by = Column(String(128), comment="System or user who created alert")
    approved_by = Column(String(128), comment="Authority who approved alert")

    # Metadata
    delivery_stats = Column(JSONB, comment="Delivery success/failure counts")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()")
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()")

    __table_args__ = (
        Index("idx_alert_incident", "incident_id"),
        Index("idx_alert_state", "state"),
        Index("idx_alert_issued", "issued_at"),
    )


class PushSubscription(Base):
    """Web Push subscription storage

    Stores browser push subscriptions for citizen alert delivery.
    Manages subscription lifecycle, expiration, and delivery tracking.
    """
    __tablename__ = "push_subscriptions"

    subscription_id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Subscription identity (unique per browser/device)
    endpoint = Column(String(512), nullable=False, unique=True, comment="Push service endpoint URL")

    # VAPID keys (encrypted at rest in production)
    p256dh_key = Column(String(256), nullable=False, comment="Client public key (base64)")
    auth_secret = Column(String(256), nullable=False, comment="Authentication secret (base64)")

    # Optional user context
    user_id = Column(String(128), comment="User identifier if authenticated")
    device_info = Column(JSONB, comment="Browser/device metadata")

    # Geolocation (for proximity alerts)
    location_lat = Column(BigInteger, comment="Last known latitude (if shared)")
    location_lon = Column(BigInteger, comment="Last known longitude (if shared)")
    location_updated_at = Column(TIMESTAMP(timezone=True), comment="When location was last updated")

    # Subscription lifecycle
    subscribed_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()")
    last_delivery_at = Column(TIMESTAMP(timezone=True), comment="Last successful push")
    last_failure_at = Column(TIMESTAMP(timezone=True), comment="Last delivery failure")
    failure_count = Column(BigInteger, default=0, comment="Consecutive failure count")
    is_active = Column(Boolean, default=True, comment="Whether subscription is active")
    expires_at = Column(TIMESTAMP(timezone=True), comment="Subscription expiration")

    __table_args__ = (
        Index("idx_subscription_active", "is_active"),
        Index("idx_subscription_location", "location_lat", "location_lon"),
    )


class AlertDelivery(Base):
    """Alert delivery tracking

    Records each alert delivery attempt to each subscription.
    Enables delivery status tracking, retry logic, and analytics.
    """
    __tablename__ = "alert_deliveries"

    delivery_id = Column(BigInteger, primary_key=True, autoincrement=True)

    alert_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("alerts.alert_id"),
        nullable=False
    )
    subscription_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("push_subscriptions.subscription_id"),
        nullable=False
    )

    # Delivery status
    status = Column(
        String(32),
        nullable=False,
        comment="PENDING, SENT, DELIVERED, FAILED, EXPIRED, UNREACHABLE"
    )

    # Delivery metadata
    sent_at = Column(TIMESTAMP(timezone=True), comment="When push was sent")
    delivered_at = Column(TIMESTAMP(timezone=True), comment="When delivery confirmed")
    opened_at = Column(TIMESTAMP(timezone=True), comment="When user opened notification")
    failed_at = Column(TIMESTAMP(timezone=True), comment="When delivery failed")
    error_message = Column(Text, comment="Failure reason")

    # Retry tracking
    attempt_count = Column(BigInteger, default=0, comment="Delivery attempt number")
    next_retry_at = Column(TIMESTAMP(timezone=True), comment="Next retry time")

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()")

    __table_args__ = (
        Index("idx_delivery_alert", "alert_id"),
        Index("idx_delivery_subscription", "subscription_id"),
        Index("idx_delivery_status", "status"),
        Index("idx_delivery_retry", "next_retry_at"),
    )
