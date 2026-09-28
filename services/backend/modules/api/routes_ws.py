import logging
from typing import Dict, List
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router_ws = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total clients: {len(self.active_connections)}")
        except ValueError:
            pass

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to websocket: {e}")
                dead_connections.append(connection)
                
        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

@router_ws.websocket("/ws/emergency-updates")
async def emergency_updates_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't actively expect messages from clients, but keep the connection open
            # and respond to pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.info(f"WebSocket error/disconnected: {e}")
        manager.disconnect(websocket)
