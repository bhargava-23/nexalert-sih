"""Alert delivery and Web Push module

Real browser push notifications for NexAlert citizen alerts.
"""
from modules.alerts.web_push import get_web_push_service, WebPushService

__all__ = ['get_web_push_service', 'WebPushService']
