"""Track C Coordinator for B2 Integration

Handles triggering of fire simulations from Track B2 incidents.
Follows B2 coordinator pattern: singleton, non-blocking, statistics tracking.

CRITICAL: This is the ONLY integration point between Track B2 and Track C.
No modifications to B1/B2 code except one minimal hook in b2_coordinator.py.
"""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from db.models_b2 import Incident
from modules.simulation.fire_simulation import FireSimulation

logger = logging.getLogger(__name__)


class C_Coordinator:
    """Track C coordinator for fire simulation triggers"""

    def __init__(self):
        """Initialize coordinator"""
        self.stats = {
            "triggers_total": 0,
            "simulations_started": 0,
            "simulations_failed": 0,
            "errors": 0
        }

    async def on_incident_created(
        self,
        session: AsyncSession,
        incident_id: str,
        incident_data: dict
    ) -> None:
        """Trigger fire simulation when incident is created

        Called by Track B2 coordinator after incident creation.
        Runs fire simulation for FIRE hazard type incidents.

        Args:
            session: Database session
            incident_id: Track B2 incident ID
            incident_data: Incident metadata dict

        Non-blocking: Errors are logged but do not propagate to caller.
        """
        try:
            self.stats["triggers_total"] += 1

            # Only trigger for FIRE hazard type
            hazard_type = incident_data.get("hazard_type", "")
            if hazard_type.upper() != "FIRE":
                logger.debug(
                    f"Skipping Track C simulation for non-fire incident: {incident_id}, "
                    f"hazard_type={hazard_type}"
                )
                return

            # Extract ignition location from incident
            centroid_lat = incident_data.get("centroid_lat")
            centroid_lon = incident_data.get("centroid_lon")

            if centroid_lat is None or centroid_lon is None:
                logger.warning(
                    f"Cannot start fire simulation: incident {incident_id} missing centroid"
                )
                self.stats["simulations_failed"] += 1
                return

            # Start fire simulation (LIVE mode)
            logger.info(
                f"Starting LIVE fire simulation for incident {incident_id} "
                f"at ({centroid_lat}, {centroid_lon})"
            )

            # Create and run simulation
            # TODO: Persist to database after full integration
            sim = FireSimulation(
                ignition_lon=centroid_lon,
                ignition_lat=centroid_lat,
                ignition_time=datetime.utcnow(),
                simulation_type="LIVE",
                incident_id=incident_id,
                domain_size_m=10000.0,
                cell_size_m=50.0,
                max_time_minutes=180.0
            )

            # Setup environment with default conditions
            sim.setup_environment(
                fuel_type="uniform_grass",
                moisture_index=0.3,
                wind_speed_ms=5.0,
                wind_from_deg=270.0,
                dem_type="flat"
            )

            # Run propagation
            sim.run_propagation()

            # Extract geometries
            sim.extract_geometries(
                current_time_minutes=0.0,
                warning_horizon_minutes=30.0,
                projection_horizon_minutes=180.0
            )

            # Compute risk
            sim.compute_risk(current_time_minutes=0.0)

            self.stats["simulations_started"] += 1

            logger.info(
                f"Fire simulation completed for incident {incident_id}. "
                f"Stats: {sim.get_simulation_summary()}"
            )

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(
                f"Track C simulation trigger failed for incident {incident_id}: {str(e)}",
                exc_info=True
            )
            # Non-blocking: do not propagate error to B2

    def get_stats(self) -> dict:
        """Get coordinator statistics

        Returns:
            Statistics dict
        """
        return self.stats.copy()


# Singleton instance
_coordinator_instance: Optional[C_Coordinator] = None


def get_c_coordinator() -> C_Coordinator:
    """Get Track C coordinator singleton

    Returns:
        C_Coordinator instance
    """
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = C_Coordinator()
    return _coordinator_instance
