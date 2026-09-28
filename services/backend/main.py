"""NexAlert Backend Service

FastAPI backend with MQTT telemetry ingestion and API endpoints.
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db.database import DatabaseConfig, db_config
from modules.api.routes import router as api_router
from modules.api.routes_b2 import router_b2 as api_router_b2
from modules.api.routes_c import router_c as api_router_c
from modules.api.routes_demo import router as demo_router
from modules.api.routes_test import router_test
from modules.api.routes_ws import router_ws, manager as ws_manager
from modules.api.routes_alerts import router_alerts
from modules.api.routes_sos import router as router_sos
from modules.ingestion.mqtt_consumer import MQTTTelemetryConsumer

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global MQTT consumer
mqtt_consumer: MQTTTelemetryConsumer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    global mqtt_consumer

    logger.info("Starting NexAlert Backend...")

    global_db_config = None

    try:
        # 1. Initialize database
        logger.info(f"Connecting to database: {settings.database_url}")
        from db import database
        database.db_config = DatabaseConfig(settings.database_url)
        global_db_config = database.db_config

        # Optionally create tables (for development)
        # await global_db_config.init_db()
        logger.info("Database connection established")

        # 2. Initialize node registry (required for Track 3C normalization)
        logger.info("Initializing node registry...")
        from modules.ingestion.node_registry import initialize_registry, refresh_registry
        registry = initialize_registry()

        # Load nodes from database
        async for session in global_db_config.get_session():
            await refresh_registry(session)
            break  # Only need one session to load registry

        logger.info(f"Node registry initialized with {registry.size()} nodes")

        # 3. Start MQTT consumer
        logger.info("Starting MQTT telemetry consumer...")
        mqtt_consumer = MQTTTelemetryConsumer(
            broker_host=settings.mqtt_broker_host,
            broker_port=settings.mqtt_broker_port,
            topic=settings.mqtt_topic,
            client_id=settings.mqtt_client_id,
            username=settings.mqtt_username,
            password=settings.mqtt_password,
            reconnect_delay_s=settings.mqtt_reconnect_delay_s,
            schema_path=settings.telemetry_schema_path
        )
        await mqtt_consumer.start()
        logger.info("MQTT consumer started")

        logger.info("NexAlert Backend started successfully")
        logger.info(
            f"Track 3C normalization ready: {registry.size()} nodes registered"
        )

        yield

    finally:
        # Shutdown
        logger.info("Shutting down NexAlert Backend...")

        if mqtt_consumer:
            await mqtt_consumer.stop()
            logger.info("MQTT consumer stopped")

        if global_db_config:
            await global_db_config.close()
            logger.info("Database connection closed")

        logger.info("NexAlert Backend shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="NexAlert Backend",
    version="0.2.0",
    description="Backend API for NexAlert wildfire detection system",
    lifespan=lifespan
)

# CORS middleware (configure appropriately for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1", tags=["api"])
app.include_router(api_router_b2, prefix="/api", tags=["api-b2"])
app.include_router(api_router_c, prefix="/api", tags=["api-c"])
app.include_router(router_alerts, prefix="/api/v1", tags=["alerts"])  # Alert & Web Push routes
app.include_router(router_sos, prefix="/api/v1", tags=["sos"])  # SOS emergency requests
app.include_router(demo_router, prefix="", tags=["demo"])  # Demo routes at root for simplicity
app.include_router(router_test, prefix="/api", tags=["test"])  # Canonical test routes


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NexAlert Backend",
        "version": "0.2.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    """Legacy health endpoint (use /api/health for detailed status)"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )


# CAPTIVE PORTAL ENDPOINTS
from fastapi import Request
from fastapi.responses import RedirectResponse, Response

@app.get("/generate_204")
async def generate_204():
    """Android captive portal detection"""
    return Response(status_code=204)

@app.get("/hotspot-detect.html")
async def hotspot_detect():
    """iOS captive portal detection"""
    return Response(
        content="<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>",
        media_type="text/html"
    )

@app.get("/ncsi.txt")
async def windows_ncsi():
    """Windows captive portal detection"""
    return Response(content="Microsoft NCSI", media_type="text/plain")

@app.get("/")
async def root_redirect(request: Request):
    """Redirect unknown requests to Citizen UI"""
    host = request.headers.get("host", "")
    if "192.168" not in host and host != "localhost:8000" and host != "127.0.0.1:8000":
        # Redirect domain queries to the captive portal frontend (assuming frontend runs on port 5174 local network)
        # Note: In a real AP setup, we'd use IP to avoid DNS loops
        return RedirectResponse(url="http://192.168.4.1:5174/")
    return {"message": "NexAlert Backend System"}
