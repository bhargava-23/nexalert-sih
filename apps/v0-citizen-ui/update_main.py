import re

with open("/home/ericsri/nexalert-sih/services/backend/main.py", "r") as f:
    content = f.read()

# Make sure routes_ws is imported
if "from modules.api.routes_ws import router_ws, manager" not in content:
    content = content.replace("from modules.api.routes_test import router_test", "from modules.api.routes_test import router_test\nfrom modules.api.routes_ws import router_ws, manager")

# Include the websocket router
if "app.include_router(router_ws)" not in content:
    content = content.replace("app.include_router(router_test, prefix=\"/api\")", "app.include_router(router_test, prefix=\"/api\")\napp.include_router(router_ws)")

# Add captive portal detection endpoints
captive_portal_routes = """
# CAPTIVE PORTAL ENDPOINTS
from fastapi import Request
from fastapi.responses import RedirectResponse, Response

@app.get("/generate_204")
async def generate_204():
    \"\"\"Android captive portal detection\"\"\"
    return Response(status_code=204)

@app.get("/hotspot-detect.html")
async def hotspot_detect():
    \"\"\"iOS captive portal detection\"\"\"
    return Response(
        content="<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>",
        media_type="text/html"
    )

@app.get("/ncsi.txt")
async def windows_ncsi():
    \"\"\"Windows captive portal detection\"\"\"
    return Response(content="Microsoft NCSI", media_type="text/plain")

@app.get("/")
async def root_redirect(request: Request):
    \"\"\"Redirect unknown requests to Citizen UI\"\"\"
    host = request.headers.get("host", "")
    if "192.168" not in host and host != "localhost:8000" and host != "127.0.0.1:8000":
        # Redirect domain queries to the captive portal frontend (assuming frontend runs on port 5174 local network)
        # Note: In a real AP setup, we'd use IP to avoid DNS loops
        return RedirectResponse(url="http://192.168.4.1:5174/")
    return {"message": "NexAlert Backend System"}
"""

if "CAPTIVE PORTAL ENDPOINTS" not in content:
    # Replace the existing `@app.get("/")`
    old_root = """@app.get("/")
async def root():
    return {"message": "NexAlert IoT Gateway"}"""
    
    if old_root in content:
        content = content.replace(old_root, captive_portal_routes)
    else:
        # Just append it below the routers
        content += "\n" + captive_portal_routes

with open("/home/ericsri/nexalert-sih/services/backend/main.py", "w") as f:
    f.write(content)

