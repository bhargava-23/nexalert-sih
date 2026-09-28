"""Web Push delivery implementation

Real browser push notifications via VAPID for NexAlert citizen alerts.
Uses pywebpush for standardized Web Push protocol.
"""
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Tuple
from pywebpush import webpush, WebPushException
from py_vapid import Vapid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import os

from db.models_alerts import Alert, PushSubscription, AlertDelivery

logger = logging.getLogger(__name__)


class WebPushService:
    """Web Push notification service with VAPID authentication"""

    def __init__(self):
        """Initialize Web Push service with VAPID keys"""
        self.vapid: Optional[Vapid] = None  # Store Vapid object, not PEM string
        self.vapid_public_key: Optional[str] = None
        self.vapid_claims: Dict[str, str] = {}
        self._initialize_vapid()

    def _initialize_vapid(self):
        """Initialize or load VAPID keys"""
        # Check for existing VAPID keys in environment
        private_key_path = os.getenv("VAPID_PRIVATE_KEY_PATH", ".vapid_private.pem")
        public_key_path = os.getenv("VAPID_PUBLIC_KEY_PATH", ".vapid_public.pem")

        try:
            # Try to load existing keys
            if os.path.exists(private_key_path) and os.path.exists(public_key_path):
                # Load Vapid object from file (pywebpush requires Vapid object, not PEM string)
                # IMPORTANT: Vapid.from_file() is a static method that returns a NEW object
                self.vapid = Vapid.from_file(private_key_path)

                with open(public_key_path, 'r') as f:
                    self.vapid_public_key = f.read().strip()
                logger.info("Loaded existing VAPID keys")
            else:
                # Generate new VAPID keys
                self.vapid = Vapid()
                self.vapid.generate_keys()

                # Get public key in correct format for Web Push
                from cryptography.hazmat.primitives import serialization
                public_key_bytes = self.vapid.public_key.public_bytes(
                    encoding=serialization.Encoding.X962,
                    format=serialization.PublicFormat.UncompressedPoint
                )
                # Convert to URL-safe base64 without padding
                import base64
                self.vapid_public_key = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')

                # Save keys for persistence
                self.vapid.save_key(private_key_path)
                with open(public_key_path, 'w') as f:
                    f.write(self.vapid_public_key)

                logger.info(f"Generated new VAPID keys")
                logger.info(f"Public key (for frontend): {self.vapid_public_key}")

        except Exception as e:
            logger.error(f"Failed to initialize VAPID keys: {e}")
            raise

        # Set VAPID claims
        self.vapid_claims = {
            "sub": os.getenv("VAPID_SUBJECT", "mailto:alerts@nexalert.local")
        }

    def get_public_key(self) -> str:
        """Get VAPID public key for frontend subscription"""
        return self.vapid_public_key

    async def send_push_notification(
        self,
        session: AsyncSession,
        subscription: PushSubscription,
        alert: Alert,
        delivery: AlertDelivery
    ) -> Tuple[bool, Optional[str]]:
        """Send push notification to one subscription

        Args:
            session: Database session
            subscription: Push subscription to send to
            alert: Alert to deliver
            delivery: Delivery tracking record

        Returns:
            (success, error_message) tuple
        """
        try:
            # Construct notification payload
            payload = {
                "title": alert.title,
                "body": alert.message,
                "icon": self._get_hazard_icon(alert.hazard_type),
                "badge": "/badge-96x96.png",
                "tag": str(alert.alert_id),  # Prevents duplicate notifications
                "data": {
                    "alert_id": str(alert.alert_id),
                    "incident_id": str(alert.incident_id),
                    "hazard_type": alert.hazard_type,
                    "severity": alert.severity,
                    "url": f"/",  # Citizen UI homepage (emergency mode will activate)
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "requireInteraction": alert.severity == "CRITICAL",  # Persistent for critical alerts
                "vibrate": [200, 100, 200] if alert.severity in ("WARNING", "CRITICAL") else None
            }

            # Build subscription info for pywebpush
            subscription_info = {
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh_key,
                    "auth": subscription.auth_secret
                }
            }

            # Send Web Push notification
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.vapid,  # Pass Vapid object, not PEM string
                vapid_claims=self.vapid_claims,
                ttl=3600  # 1 hour TTL
            )

            # Update delivery record
            delivery.status = "SENT"
            delivery.sent_at = datetime.now(timezone.utc)

            # Update subscription last delivery
            subscription.last_delivery_at = datetime.now(timezone.utc)
            subscription.failure_count = 0

            await session.commit()

            logger.info(f"Sent push notification: alert={alert.alert_id}, subscription={subscription.subscription_id}")
            return True, None

        except WebPushException as e:
            error_msg = str(e)
            logger.error(f"Web Push failed: {error_msg}, alert={alert.alert_id}, subscription={subscription.subscription_id}")

            # Handle specific failure cases
            if e.response and e.response.status_code in (404, 410):
                # Subscription expired or invalid - deactivate
                subscription.is_active = False
                subscription.last_failure_at = datetime.now(timezone.utc)
                delivery.status = "UNREACHABLE"
                delivery.error_message = "Subscription expired or invalid"
                logger.info(f"Deactivated expired subscription: {subscription.subscription_id}")
            else:
                # Temporary failure - increment failure count
                subscription.failure_count += 1
                subscription.last_failure_at = datetime.now(timezone.utc)
                delivery.status = "FAILED"
                delivery.error_message = error_msg[:500]

                # Deactivate after 5 consecutive failures
                if subscription.failure_count >= 5:
                    subscription.is_active = False
                    logger.warning(f"Deactivated subscription after 5 failures: {subscription.subscription_id}")

            delivery.failed_at = datetime.now(timezone.utc)
            await session.commit()
            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Push notification error: {error_msg}", exc_info=True)

            delivery.status = "FAILED"
            delivery.error_message = error_msg[:500]
            delivery.failed_at = datetime.now(timezone.utc)

            subscription.failure_count += 1
            subscription.last_failure_at = datetime.now(timezone.utc)

            await session.commit()
            return False, error_msg

    async def deliver_alert_to_subscriptions(
        self,
        session: AsyncSession,
        alert: Alert,
        radius_m: Optional[float] = None
    ) -> Dict[str, int]:
        """Deliver alert to all relevant subscriptions

        Args:
            session: Database session
            alert: Alert to deliver
            radius_m: Optional proximity radius for geospatial filtering

        Returns:
            Delivery statistics dict
        """
        stats = {
            "total": 0,
            "sent": 0,
            "failed": 0,
            "unreachable": 0
        }

        # Query active subscriptions
        # TODO: Add geospatial filtering if radius_m provided and alert has location
        query = select(PushSubscription).where(
            PushSubscription.is_active == True
        )

        result = await session.execute(query)
        subscriptions = result.scalars().all()

        logger.info(f"Delivering alert {alert.alert_id} to {len(subscriptions)} active subscriptions")

        for subscription in subscriptions:
            stats["total"] += 1

            # Create delivery tracking record
            delivery = AlertDelivery(
                alert_id=alert.alert_id,
                subscription_id=subscription.subscription_id,
                status="PENDING",
                attempt_count=1
            )
            session.add(delivery)
            await session.flush()

            # Send push notification
            success, error = await self.send_push_notification(
                session, subscription, alert, delivery
            )

            if success:
                stats["sent"] += 1
            elif delivery.status == "UNREACHABLE":
                stats["unreachable"] += 1
            else:
                stats["failed"] += 1

        logger.info(f"Alert delivery complete: {stats}")
        return stats

    def _get_hazard_icon(self, hazard_type: str) -> str:
        """Get notification icon URL for hazard type"""
        icon_map = {
            "fire": "/icons/fire-96x96.png",
            "flood": "/icons/flood-96x96.png",
            "landslide": "/icons/landslide-96x96.png",
            "pollution": "/icons/pollution-96x96.png",
            "heat": "/icons/heat-96x96.png"
        }
        return icon_map.get(hazard_type, "/icons/alert-96x96.png")


# Global Web Push service instance
_web_push_service: Optional[WebPushService] = None


def get_web_push_service() -> WebPushService:
    """Get global Web Push service instance"""
    global _web_push_service
    if _web_push_service is None:
        _web_push_service = WebPushService()
    return _web_push_service
