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

        # 2. Start MQTT consumer
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
app.include_router(api_router, prefix="/api", tags=["api"])
app.include_router(api_router_b2, prefix="/api", tags=["api-b2"])
app.include_router(api_router_c, prefix="/api", tags=["api-c"])


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
