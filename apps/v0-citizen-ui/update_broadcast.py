import re

with open("/home/ericsri/nexalert-sih/services/backend/modules/api/routes_alerts.py", "r") as f:
    content = f.read()

# Make sure manager is imported
if "from modules.api.routes_ws import manager" not in content:
    content = content.replace("from modules.alerts.web_push import get_web_push_service", "from modules.alerts.web_push import get_web_push_service\nfrom modules.api.routes_ws import manager\nimport asyncio")

# Inject the broadcast into the POST /alerts endpoint (where citizen alerts are created/pushed)
if "asyncio.create_task(manager.broadcast(" not in content:
    send_push = "success, error = await web_push.send_push_notification("
    replacement = """# Broadcast to offline local WebSocket clients
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

        success, error = await web_push.send_push_notification("""
    content = content.replace(send_push, replacement)

with open("/home/ericsri/nexalert-sih/services/backend/modules/api/routes_alerts.py", "w") as f:
    f.write(content)

