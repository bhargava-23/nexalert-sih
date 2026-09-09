"""Incident correlation engine for Track B2

Deterministic incident creation, correlation, and lifecycle management.
Correlates observations from multiple nodes into unified incidents.

Architecture invariants:
- Deterministic incident identity based on hazard + spatial-temporal correlation
- Idempotent updates (same observation linked once)
- State machine: NEW → ACTIVE → ESCALATED → RESOLVED
- Preserves audit trail and provenance
- Does NOT erase local node state
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from modules.intelligence.regional_fusion import (
    NodeObservation,
    RegionalFusionResult,
    compute_spatial_distance_m
)

logger = logging.getLogger(__name__)

# Incident correlation parameters
DEFAULT_MERGE_RADIUS_M = 50.0  # meters
DEFAULT_MERGE_WINDOW_S = 30.0  # seconds
CLEARLY_SEPARATE_RADIUS_M = 5000.0  # 5km


class IncidentState(str, Enum):
    """Incident lifecycle states"""
    NEW = "NEW"  # Just created, pending assessment
    ACTIVE = "ACTIVE"  # Confirmed and ongoing
    ESCALATED = "ESCALATED"  # Elevated severity or spreading
    RESOLVED = "RESOLVED"  # No longer active


@dataclass
class IncidentCandidate:
    """Candidate incident for correlation"""
    incident_id: uuid.UUID
    hazard_type: str
    state: str
    centroid_lat: Optional[float]
    centroid_lon: Optional[float]
    last_observed_at: datetime
    severity_index: Optional[float]
    risk_index: Optional[float]


@dataclass
class IncidentCreationResult:
    """Result of incident creation or correlation"""
    incident_id: uuid.UUID
    action: str  # "created", "updated", "merged"
    state: str
    severity_index: Optional[float]
    risk_index: Optional[float]
    centroid_lat: Optional[float]
    centroid_lon: Optional[float]
    contributing_nodes: List[str]


def generate_deterministic_incident_id() -> uuid.UUID:
    """Generate deterministic incident UUID

    For now, generates random UUID. Full deterministic implementation
    would use hash of (hazard_type, spatial_key, temporal_window).
    """
    return uuid.uuid4()


def should_correlate_with_incident(
    observation_location: Tuple[Optional[float], Optional[float]],
    observation_time: datetime,
    incident: IncidentCandidate,
    merge_radius_m: float = DEFAULT_MERGE_RADIUS_M,
    merge_window_s: float = DEFAULT_MERGE_WINDOW_S
) -> bool:
    """Determine if observation should correlate with existing incident

    Args:
        observation_location: (lat, lon) of new observation
        observation_time: Timestamp of new observation
        incident: Existing incident candidate
        merge_radius_m: Spatial correlation radius
        merge_window_s: Temporal correlation window

    Returns:
        True if observation correlates with incident
    """
    obs_lat, obs_lon = observation_location

    # Spatial correlation
    if obs_lat is not None and obs_lon is not None:
        if incident.centroid_lat is not None and incident.centroid_lon is not None:
            distance = compute_spatial_distance_m(
                obs_lat, obs_lon,
                incident.centroid_lat, incident.centroid_lon
            )
            if distance is not None:
                # If clearly separate (>5km), do not correlate
                if distance > CLEARLY_SEPARATE_RADIUS_M:
                    return False
                # If within merge radius, check temporal correlation
                if distance <= merge_radius_m:
                    # Temporal correlation
                    time_gap = abs((observation_time - incident.last_observed_at).total_seconds())
                    if time_gap <= merge_window_s:
                        return True

    # Default: do not correlate if spatial/temporal checks inconclusive
    return False


def determine_incident_state(
    regional_fusion: RegionalFusionResult,
    node_observations: List[NodeObservation]
) -> str:
    """Determine incident state from regional fusion and node observations

    Args:
        regional_fusion: Regional fusion result
        node_observations: Contributing node observations

    Returns:
        IncidentState: NEW, ACTIVE, ESCALATED, RESOLVED
    """
    # Check if any node is in CRITICAL state
    critical_count = sum(1 for obs in node_observations if obs.state == "CRITICAL")
    if critical_count > 0:
        return IncidentState.ESCALATED

    # Check if majority are CONFIRMED
    confirmed_count = sum(1 for obs in node_observations if obs.state in ["CONFIRMED", "CRITICAL"])
    total_count = len(node_observations)

    if confirmed_count >= (total_count / 2) and total_count >= 2:
        return IncidentState.ACTIVE

    # Check if all nodes are RESOLVED
    resolved_count = sum(1 for obs in node_observations if obs.state == "RESOLVED")
    if resolved_count == total_count and total_count > 0:
        return IncidentState.RESOLVED

    # Default: NEW
    return IncidentState.NEW


def correlate_observation_to_incident(
    observation: NodeObservation,
    current_time: datetime,
    active_incidents: List[IncidentCandidate],
    merge_radius_m: float = DEFAULT_MERGE_RADIUS_M,
    merge_window_s: float = DEFAULT_MERGE_WINDOW_S
) -> Optional[uuid.UUID]:
    """Correlate new observation to existing incident

    Args:
        observation: New node observation
        current_time: Current timestamp
        active_incidents: List of active incidents for this hazard type
        merge_radius_m: Spatial correlation radius
        merge_window_s: Temporal correlation window

    Returns:
        incident_id if correlated, None if new incident needed
    """
    # Filter to same hazard type and non-resolved incidents
    candidates = [inc for inc in active_incidents
                  if inc.hazard_type == observation.hazard_type
                  and inc.state != IncidentState.RESOLVED]

    if not candidates:
        return None

    # Find nearest incident within correlation thresholds
    obs_location = (observation.location_lat, observation.location_lon)

    for incident in candidates:
        if should_correlate_with_incident(
            obs_location,
            observation.observation_time,
            incident,
            merge_radius_m,
            merge_window_s
        ):
            return incident.incident_id

    return None


def create_incident_from_observations(
    observations: List[NodeObservation],
    regional_fusion: RegionalFusionResult,
    current_time: datetime,
    incident_id: Optional[uuid.UUID] = None
) -> IncidentCreationResult:
    """Create or update incident from node observations

    Args:
        observations: Contributing node observations
        regional_fusion: Regional fusion result
        current_time: Current timestamp
        incident_id: Existing incident ID for update, None for new incident

    Returns:
        IncidentCreationResult with incident details
    """
    if incident_id is None:
        incident_id = generate_deterministic_incident_id()
        action = "created"
    else:
        action = "updated"

    # Determine incident state
    state = determine_incident_state(regional_fusion, observations)

    # Extract contributing nodes
    contributing_nodes = [obs.node_id for obs in observations]

    return IncidentCreationResult(
        incident_id=incident_id,
        action=action,
        state=state,
        severity_index=regional_fusion.regional_severity,
        risk_index=regional_fusion.regional_risk,
        centroid_lat=regional_fusion.centroid_lat,
        centroid_lon=regional_fusion.centroid_lon,
        contributing_nodes=contributing_nodes
    )


def check_incident_escalation(
    previous_state: str,
    previous_severity: Optional[float],
    new_state: str,
    new_severity: Optional[float],
    severity_escalation_threshold: float = 0.2
) -> bool:
    """Check if incident should escalate

    Args:
        previous_state: Previous incident state
        previous_severity: Previous severity index
        new_state: New incident state
        new_severity: New severity index
        severity_escalation_threshold: Severity increase threshold for escalation

    Returns:
        True if incident should escalate
    """
    # State-based escalation
    state_order = {
        IncidentState.RESOLVED: 0,
        IncidentState.NEW: 1,
        IncidentState.ACTIVE: 2,
        IncidentState.ESCALATED: 3
    }

    prev_order = state_order.get(previous_state, 1)
    new_order = state_order.get(new_state, 1)

    if new_order > prev_order:
        return True

    # Severity-based escalation
    if previous_severity is not None and new_severity is not None:
        severity_increase = new_severity - previous_severity
        if severity_increase >= severity_escalation_threshold:
            return True

    return False


def check_incident_resolution(
    observations: List[NodeObservation],
    regional_fusion: RegionalFusionResult,
    resolution_threshold: float = 0.2
) -> Tuple[bool, Optional[str]]:
    """Check if incident should be resolved

    Args:
        observations: Current node observations
        regional_fusion: Regional fusion result
        resolution_threshold: Evidence/risk threshold for resolution

    Returns:
        (should_resolve, resolution_reason)
    """
    if not observations:
        return True, "No active observations"

    # Check if all nodes are RESOLVED
    resolved_count = sum(1 for obs in observations if obs.state == "RESOLVED")
    if resolved_count == len(observations):
        return True, "All nodes resolved"

    # Check if regional evidence and risk below threshold
    if (regional_fusion.regional_evidence is not None
        and regional_fusion.regional_risk is not None):
        if (regional_fusion.regional_evidence < resolution_threshold
            and regional_fusion.regional_risk < resolution_threshold):
            return True, "Evidence and risk below resolution threshold"

    return False, None


class IncidentCorrelationEngine:
    """Manages incident correlation and lifecycle

    Stateless engine - incident state persisted to database externally.
    """

    def __init__(self,
                 merge_radius_m: float = DEFAULT_MERGE_RADIUS_M,
                 merge_window_s: float = DEFAULT_MERGE_WINDOW_S):
        self.merge_radius_m = merge_radius_m
        self.merge_window_s = merge_window_s

    def process_observation(
        self,
        observation: NodeObservation,
        active_incidents: List[IncidentCandidate],
        current_time: datetime
    ) -> Tuple[Optional[uuid.UUID], str]:
        """Process new observation and correlate to incident

        Args:
            observation: New node observation
            active_incidents: List of active incidents
            current_time: Current timestamp

        Returns:
            (incident_id, action) where action is "correlated" or "new"
        """
        # Try to correlate with existing incident
        incident_id = correlate_observation_to_incident(
            observation,
            current_time,
            active_incidents,
            self.merge_radius_m,
            self.merge_window_s
        )

        if incident_id:
            return incident_id, "correlated"
        else:
            # Create new incident
            new_id = generate_deterministic_incident_id()
            return new_id, "new"

    def should_update_incident(
        self,
        incident: IncidentCandidate,
        new_observations: List[NodeObservation],
        current_time: datetime
    ) -> bool:
        """Check if incident should be updated based on new observations

        Args:
            incident: Existing incident
            new_observations: New node observations
            current_time: Current timestamp

        Returns:
            True if incident should be updated
        """
        # Always update if there are new observations for this incident
        if new_observations:
            return True

        # Check if incident is stale (no updates for merge window)
        time_since_update = (current_time - incident.last_observed_at).total_seconds()
        if time_since_update > self.merge_window_s:
            return False

        return True
