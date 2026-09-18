"""Node Registry - Track 3C normalization dependency

Loads and caches node registry for hardware JSON normalization.
Location resolution for Track 3C canonical telemetry mapping.
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.functions import ST_X, ST_Y, ST_Z

from db.models import Node

logger = logging.getLogger(__name__)


class NodeRegistry:
    """Node registry cache for Track 3C normalization"""

    def __init__(self):
        """Initialize empty registry"""
        self._registry: Dict[str, Dict[str, Any]] = {}
        logger.info("Node registry initialized (empty)")

    async def load_from_db(self, session: AsyncSession) -> None:
        """Load node registry from database

        Args:
            session: Database session

        Registry Format:
            {
                "NODE-001": {
                    "location": {"lat": 12.34, "lon": 56.78, "alt": 920.0},
                    "status": "ACTIVE",
                    "firmware_version": "1.0.0"
                },
                ...
            }

        Critical: Location must be present and valid for normalization to succeed
        """
        try:
            # Query all nodes with location geometry
            result = await session.execute(
                select(
                    Node.node_id,
                    Node.status,
                    Node.firmware_version,
                    Node.location,
                    ST_Y(Node.location).label("lat"),
                    ST_X(Node.location).label("lon"),
                    ST_Z(Node.location).label("alt")
                )
            )
            rows = result.all()

            # Build registry
            registry = {}
            for row in rows:
                node_id = row.node_id

                # Extract location (required for normalization)
                location = None
                if row.location is not None:
                    location = {
                        "lat": float(row.lat) if row.lat is not None else None,
                        "lon": float(row.lon) if row.lon is not None else None,
                    }
                    # Alt is optional
                    if row.alt is not None:
                        location["alt"] = float(row.alt)

                registry[node_id] = {
                    "location": location,
                    "status": row.status,
                    "firmware_version": row.firmware_version
                }

            self._registry = registry
            logger.info(f"Node registry loaded: {len(registry)} nodes")

            # Log nodes without valid location (these will fail normalization)
            nodes_without_location = [
                node_id for node_id, info in registry.items()
                if info["location"] is None or
                   info["location"].get("lat") is None or
                   info["location"].get("lon") is None
            ]
            if nodes_without_location:
                logger.warning(
                    f"Nodes without valid location (normalization will fail): "
                    f"{nodes_without_location}"
                )

        except Exception as e:
            logger.error(f"Failed to load node registry: {str(e)}", exc_info=True)
            # Keep empty registry on error (normalization will fail for all nodes)
            self._registry = {}

    def get_node_info(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node information from registry

        Args:
            node_id: Node ID

        Returns:
            Node info dict if found, None otherwise
        """
        return self._registry.get(node_id)

    def get_location(self, node_id: str) -> Optional[Dict[str, float]]:
        """Get node location from registry

        Args:
            node_id: Node ID

        Returns:
            Location dict {lat, lon, alt?} if found and valid, None otherwise
        """
        node_info = self._registry.get(node_id)
        if node_info is None:
            return None
        return node_info.get("location")

    def size(self) -> int:
        """Get registry size"""
        return len(self._registry)

    def clear(self) -> None:
        """Clear registry (for testing)"""
        self._registry = {}
        logger.info("Node registry cleared")


# Global registry instance (initialized at MQTT consumer startup)
_global_registry: Optional[NodeRegistry] = None


def get_registry() -> NodeRegistry:
    """Get global node registry instance

    Returns:
        Global NodeRegistry instance

    Raises:
        RuntimeError: If registry not initialized
    """
    global _global_registry
    if _global_registry is None:
        raise RuntimeError(
            "Node registry not initialized. "
            "Call initialize_registry() at startup."
        )
    return _global_registry


def initialize_registry() -> NodeRegistry:
    """Initialize global node registry

    Returns:
        Initialized NodeRegistry instance
    """
    global _global_registry
    _global_registry = NodeRegistry()
    logger.info("Global node registry initialized")
    return _global_registry


async def refresh_registry(session: AsyncSession) -> None:
    """Refresh global node registry from database

    Args:
        session: Database session
    """
    registry = get_registry()
    await registry.load_from_db(session)
