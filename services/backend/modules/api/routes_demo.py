"""Demo API routes for NexAlert presentation

Simplified endpoints for reliable demo experience.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

router = APIRouter()

# Demo data state
DEMO_MODE = True
DEMO_NODE_DATA = {
    "node_id": "NEX-001",
    "status": "ONLINE",
    "telemetry": {
        "temperature": 31.4,
        "humidity": 58.2,
        "pressure": 1009.8,
        "gas_smoke": "normal",
        "vibration": "normal",
        "last_update": datetime.now().isoformat()
    },
    "health": {
        "signal_strength": 85,
        "battery": 94,
        "sensor_health": "operational"
    }
}

DEMO_INCIDENT = None


@router.get("/health")
async def health():
    """System health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "operational",
            "mqtt": "connected",
            "database": "operational",
            "edge_master": "operational"
        }
    }


@router.get("/nodes/{node_id}")
async def get_node(node_id: str):
    """Get node telemetry and status"""
    if node_id == "NEX-001":
        return DEMO_NODE_DATA
    raise HTTPException(status_code=404, detail="Node not found")


@router.get("/nodes")
async def list_nodes():
    """List all nodes"""
    return {
        "nodes": [DEMO_NODE_DATA],
        "total": 1
    }


@router.get("/incidents")
async def get_incidents(state: str = None):
    """Get incidents"""
    global DEMO_INCIDENT

    incidents = []
    if DEMO_INCIDENT:
        if state is None or DEMO_INCIDENT["state"] == state.upper():
            incidents.append(DEMO_INCIDENT)

    return {
        "incidents": incidents,
        "total": len(incidents)
    }


@router.post("/demo/trigger-fire")
async def trigger_fire_scenario():
    """Trigger fire demo scenario"""
    global DEMO_INCIDENT, DEMO_NODE_DATA

    # Update node telemetry to fire conditions
    DEMO_NODE_DATA["telemetry"].update({
        "temperature": 47.3,
        "humidity": 32.1,
        "pressure": 1008.2,
        "gas_smoke": "elevated",
        "vibration": "normal",
        "last_update": datetime.now().isoformat()
    })

    # Create critical incident (Phase 2C-3C: canonical multi-hazard model)
    DEMO_INCIDENT = {
        "incident_id": "INC-FIRE-001",
        "state": "CRITICAL",
        "centroid_lat": 12.9716,
        "centroid_lon": 77.5946,
        "first_observed_at": datetime.now().isoformat(),
        "last_observed_at": datetime.now().isoformat(),
        "source_summary": {
            "node_count": 1,
            "contributing_nodes": ["NEX-001"]
        },
        "hazard_assessments": [{
            "assessment_id": 1,
            "hazard_type": "FIRE",
            "confidence": 0.89,
            "severity": 0.91,
            "operational_risk": 0.87,
            "state": "CONFIRMED",
            "assessment_timestamp": datetime.now().isoformat()
        }]
    }

    return {
        "success": True,
        "message": "Fire scenario activated",
        "incident": DEMO_INCIDENT
    }


@router.post("/demo/reset")
async def reset_demo():
    """Reset demo to normal state"""
    global DEMO_INCIDENT, DEMO_NODE_DATA

    # Reset to normal telemetry
    DEMO_NODE_DATA["telemetry"].update({
        "temperature": 31.4,
        "humidity": 58.2,
        "pressure": 1009.8,
        "gas_smoke": "normal",
        "vibration": "normal",
        "last_update": datetime.now().isoformat()
    })

    DEMO_INCIDENT = None

    return {
        "success": True,
        "message": "Demo reset to normal state"
    }


@router.get("/demo/status")
async def demo_status():
    """Get current demo state"""
    return {
        "demo_mode": DEMO_MODE,
        "node_status": DEMO_NODE_DATA["status"],
        "telemetry": DEMO_NODE_DATA["telemetry"],
        "active_incident": DEMO_INCIDENT is not None,
        "incident": DEMO_INCIDENT
    }
