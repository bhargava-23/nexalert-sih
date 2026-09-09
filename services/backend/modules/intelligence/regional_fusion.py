"""Regional fusion engine for Track B2

Multi-node aggregation for Master/Regional Intelligence.
Fuses node-level hazard assessments into regional intelligence while preserving
local state independence.

Architecture invariants:
- Local node state NEVER erased by regional disagreement
- Missing != zero preserved throughout
- Confidence/risk are NOT probabilities
- Multi-hazard vectors remain independent
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)

# Freshness decay parameters
FRESHNESS_HALF_LIFE_SECONDS = 300.0  # 5 minutes
MAX_STALENESS_SECONDS = 1800.0  # 30 minutes

# Spatial correlation
DEFAULT_CORRELATION_RADIUS_M = 50.0  # meters
DEFAULT_MERGE_RADIUS_M = 50.0


@dataclass
class NodeObservation:
    """Node-level hazard observation for regional fusion"""
    node_id: str
    hazard_type: str
    state: str  # NORMAL, WATCH, SUSPECTED, CONFIRMED, CRITICAL, RESOLVED
    evidence: Optional[float]
    confidence: Optional[float]
    severity: Optional[float]
    risk: Optional[float]
    information_condition: str  # GOOD, DEGRADED, UNKNOWN
    observation_time: datetime
    location_lat: Optional[float]
    location_lon: Optional[float]
    node_reliability: float = 0.8  # Default reliability

    def age_seconds(self, current_time: datetime) -> float:
        """Compute observation age in seconds"""
        delta = current_time - self.observation_time
        return delta.total_seconds()

    def is_fresh(self, current_time: datetime, max_age: float = MAX_STALENESS_SECONDS) -> bool:
        """Check if observation is fresh enough for fusion"""
        return self.age_seconds(current_time) <= max_age


@dataclass
class RegionalFusionResult:
    """Result of regional fusion across multiple nodes"""
    hazard_type: str
    regional_evidence: Optional[float]
    regional_confidence: Optional[float]
    regional_severity: Optional[float]
    regional_risk: Optional[float]
    information_condition: str
    node_count: int
    contributing_nodes: List[Dict]
    agreement_index: Optional[float]
    spatial_extent_m: Optional[float]
    freshness_index: Optional[float]
    centroid_lat: Optional[float]
    centroid_lon: Optional[float]


def compute_freshness_weight(age_seconds: float, half_life: float = FRESHNESS_HALF_LIFE_SECONDS) -> float:
    """Compute exponential freshness decay weight

    Args:
        age_seconds: Age of observation in seconds
        half_life: Half-life for exponential decay

    Returns:
        Weight in [0, 1], where 1.0 = perfectly fresh, 0.5 = one half-life old
    """
    if age_seconds < 0:
        age_seconds = 0
    return math.exp(-age_seconds * math.log(2) / half_life)


def compute_spatial_distance_m(lat1: Optional[float], lon1: Optional[float],
                                lat2: Optional[float], lon2: Optional[float]) -> Optional[float]:
    """Compute great-circle distance between two points in meters (Haversine)

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance in meters, or None if any coordinate is missing
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None

    # Earth radius in meters
    R = 6371000.0

    # Convert to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance


def compute_spatial_weight(distance_m: Optional[float],
                           correlation_radius: float = DEFAULT_CORRELATION_RADIUS_M) -> float:
    """Compute spatial proximity weight

    Args:
        distance_m: Distance in meters
        correlation_radius: Radius where weight = 0.5

    Returns:
        Weight in [0, 1], where 1.0 = same location, 0.5 = at correlation_radius
    """
    if distance_m is None:
        return 0.5  # Unknown spatial relationship, moderate weight

    if distance_m <= 0:
        return 1.0

    # Exponential decay: weight = exp(-distance / scale)
    # At correlation_radius, weight = 0.5, so scale = correlation_radius / ln(2)
    scale = correlation_radius / math.log(2)
    return math.exp(-distance_m / scale)


def compute_trust_weight(node_reliability: float,
                         confidence: Optional[float],
                         information_condition: str) -> float:
    """Compute combined trust weight from reliability, confidence, and information condition

    Args:
        node_reliability: Historical node reliability [0, 1]
        confidence: Assessment confidence [0, 1] or None
        information_condition: GOOD, DEGRADED, UNKNOWN

    Returns:
        Combined trust weight [0, 1]
    """
    # Start with node reliability
    weight = node_reliability

    # Reduce by confidence if available
    if confidence is not None:
        weight *= confidence
    else:
        weight *= 0.5  # Missing confidence reduces trust

    # Reduce by information condition
    if information_condition == "GOOD":
        weight *= 1.0
    elif information_condition == "DEGRADED":
        weight *= 0.7
    elif information_condition == "UNKNOWN":
        weight *= 0.3
    else:
        weight *= 0.5

    return weight


def fuse_regional_hazard(observations: List[NodeObservation],
                         current_time: datetime,
                         hazard_type: str,
                         reference_location: Optional[Tuple[float, float]] = None) -> RegionalFusionResult:
    """Fuse multiple node observations into regional hazard assessment

    Aggregates node-level hazard assessments using weighted fusion.
    Weights account for:
    - Node reliability/trust
    - Assessment confidence
    - Information condition
    - Temporal freshness
    - Spatial proximity (if reference location given)

    Architecture invariants:
    - Does NOT modify or erase local node states
    - Preserves missing != zero (None values remain None)
    - Does NOT treat confidence/risk as probability
    - Multi-hazard vectors independent (filter by hazard_type)

    Args:
        observations: List of node observations to fuse
        current_time: Current time for freshness computation
        hazard_type: Hazard type to fuse (e.g., "fire")
        reference_location: Optional (lat, lon) for spatial weighting

    Returns:
        RegionalFusionResult with fused metrics
    """
    # Filter to relevant hazard type and fresh observations
    relevant = [obs for obs in observations
                if obs.hazard_type == hazard_type and obs.is_fresh(current_time)]

    if not relevant:
        # No fresh observations for this hazard type
        return RegionalFusionResult(
            hazard_type=hazard_type,
            regional_evidence=None,
            regional_confidence=None,
            regional_severity=None,
            regional_risk=None,
            information_condition="UNKNOWN",
            node_count=0,
            contributing_nodes=[],
            agreement_index=None,
            spatial_extent_m=None,
            freshness_index=None,
            centroid_lat=None,
            centroid_lon=None
        )

    # Compute weights for each observation
    weighted_observations = []
    total_weight = 0.0

    for obs in relevant:
        # Freshness weight
        freshness_weight = compute_freshness_weight(obs.age_seconds(current_time))

        # Spatial weight
        spatial_weight = 1.0
        if reference_location and obs.location_lat and obs.location_lon:
            distance = compute_spatial_distance_m(
                reference_location[0], reference_location[1],
                obs.location_lat, obs.location_lon
            )
            spatial_weight = compute_spatial_weight(distance)

        # Trust weight
        trust_weight = compute_trust_weight(
            obs.node_reliability,
            obs.confidence,
            obs.information_condition
        )

        # Combined weight
        combined_weight = freshness_weight * spatial_weight * trust_weight

        weighted_observations.append({
            "node_id": obs.node_id,
            "weight": combined_weight,
            "state": obs.state,
            "freshness": freshness_weight,
            "trust": trust_weight,
            "spatial": spatial_weight
        })

        total_weight += combined_weight

    if total_weight == 0:
        # All observations have zero weight
        return RegionalFusionResult(
            hazard_type=hazard_type,
            regional_evidence=None,
            regional_confidence=None,
            regional_severity=None,
            regional_risk=None,
            information_condition="UNKNOWN",
            node_count=len(relevant),
            contributing_nodes=weighted_observations,
            agreement_index=None,
            spatial_extent_m=None,
            freshness_index=None,
            centroid_lat=None,
            centroid_lon=None
        )

    # Fuse metrics using weighted average (preserve None for missing)
    def weighted_avg(values: List[Optional[float]], weights: List[float]) -> Optional[float]:
        """Weighted average preserving None semantics"""
        valid_pairs = [(v, w) for v, w in zip(values, weights) if v is not None]
        if not valid_pairs:
            return None
        numerator = sum(v * w for v, w in valid_pairs)
        denominator = sum(w for v, w in valid_pairs)
        if denominator == 0:
            return None
        return numerator / denominator

    weights = [wo["weight"] for wo in weighted_observations]

    regional_evidence = weighted_avg([obs.evidence for obs in relevant], weights)
    regional_confidence = weighted_avg([obs.confidence for obs in relevant], weights)
    regional_severity = weighted_avg([obs.severity for obs in relevant], weights)
    regional_risk = weighted_avg([obs.risk for obs in relevant], weights)
    freshness_index = weighted_avg(
        [compute_freshness_weight(obs.age_seconds(current_time)) for obs in relevant],
        weights
    )

    # Compute information condition (most restrictive)
    info_conditions = [obs.information_condition for obs in relevant]
    if "UNKNOWN" in info_conditions:
        regional_info = "UNKNOWN"
    elif "DEGRADED" in info_conditions:
        regional_info = "DEGRADED"
    else:
        regional_info = "GOOD"

    # Compute agreement index (variance of weighted states)
    # Simplified: fraction of nodes in CONFIRMED or CRITICAL
    confirmed_weight = sum(wo["weight"] for wo, obs in zip(weighted_observations, relevant)
                           if obs.state in ["CONFIRMED", "CRITICAL"])
    agreement_index = confirmed_weight / total_weight if total_weight > 0 else 0.0

    # Compute spatial extent (max pairwise distance)
    spatial_extent = None
    locations = [(obs.location_lat, obs.location_lon) for obs in relevant
                 if obs.location_lat is not None and obs.location_lon is not None]
    if len(locations) >= 2:
        distances = []
        for i, (lat1, lon1) in enumerate(locations):
            for lat2, lon2 in locations[i+1:]:
                dist = compute_spatial_distance_m(lat1, lon1, lat2, lon2)
                if dist is not None:
                    distances.append(dist)
        spatial_extent = max(distances) if distances else None

    # Compute centroid (simple average of locations)
    centroid_lat = None
    centroid_lon = None
    if locations:
        centroid_lat = sum(lat for lat, lon in locations) / len(locations)
        centroid_lon = sum(lon for lat, lon in locations) / len(locations)

    return RegionalFusionResult(
        hazard_type=hazard_type,
        regional_evidence=regional_evidence,
        regional_confidence=regional_confidence,
        regional_severity=regional_severity,
        regional_risk=regional_risk,
        information_condition=regional_info,
        node_count=len(relevant),
        contributing_nodes=weighted_observations,
        agreement_index=agreement_index,
        spatial_extent_m=spatial_extent,
        freshness_index=freshness_index,
        centroid_lat=centroid_lat,
        centroid_lon=centroid_lon
    )
