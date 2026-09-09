"""Unit tests for Track B2 regional fusion engine"""
import pytest
from datetime import datetime, timedelta

from modules.intelligence.regional_fusion import (
    NodeObservation,
    compute_freshness_weight,
    compute_spatial_distance_m,
    compute_spatial_weight,
    compute_trust_weight,
    fuse_regional_hazard,
    FRESHNESS_HALF_LIFE_SECONDS
)


def test_compute_freshness_weight():
    """Test freshness weight computation"""
    # Fresh observation (age = 0)
    weight = compute_freshness_weight(0.0)
    assert weight == pytest.approx(1.0)

    # One half-life old
    weight = compute_freshness_weight(FRESHNESS_HALF_LIFE_SECONDS)
    assert weight == pytest.approx(0.5)

    # Very old observation
    weight = compute_freshness_weight(3600.0)  # 1 hour
    assert weight < 0.1


def test_compute_spatial_distance():
    """Test spatial distance computation"""
    # Same point
    dist = compute_spatial_distance_m(12.9716, 77.5946, 12.9716, 77.5946)
    assert dist == pytest.approx(0.0, abs=1.0)

    # Known distance (approximately 111km per degree at equator)
    dist = compute_spatial_distance_m(12.0, 77.0, 13.0, 77.0)
    assert 110000 < dist < 112000  # ~111km

    # Missing coordinates
    dist = compute_spatial_distance_m(None, 77.0, 13.0, 77.0)
    assert dist is None


def test_compute_spatial_weight():
    """Test spatial proximity weight"""
    # Same location
    weight = compute_spatial_weight(0.0)
    assert weight == pytest.approx(1.0)

    # At correlation radius (50m)
    weight = compute_spatial_weight(50.0)
    assert weight == pytest.approx(0.5, abs=0.05)

    # Far away
    weight = compute_spatial_weight(5000.0)
    assert weight < 0.01

    # Missing distance
    weight = compute_spatial_weight(None)
    assert weight == 0.5


def test_compute_trust_weight():
    """Test trust weight computation"""
    # High reliability + high confidence + GOOD information
    weight = compute_trust_weight(0.9, 0.9, "GOOD")
    assert weight == pytest.approx(0.81, abs=0.01)

    # DEGRADED information reduces trust
    weight = compute_trust_weight(0.9, 0.9, "DEGRADED")
    assert weight == pytest.approx(0.567, abs=0.01)

    # UNKNOWN information significantly reduces trust
    weight = compute_trust_weight(0.9, 0.9, "UNKNOWN")
    assert weight == pytest.approx(0.243, abs=0.01)

    # Missing confidence
    weight = compute_trust_weight(0.9, None, "GOOD")
    assert weight == pytest.approx(0.45, abs=0.01)


def test_fuse_single_node():
    """Test fusion with single node observation"""
    current_time = datetime.utcnow()

    obs = NodeObservation(
        node_id="NODE-001",
        hazard_type="fire",
        state="CONFIRMED",
        evidence=0.75,
        confidence=0.82,
        severity=0.65,
        risk=0.70,
        information_condition="GOOD",
        observation_time=current_time,
        location_lat=12.9716,
        location_lon=77.5946,
        node_reliability=0.88
    )

    result = fuse_regional_hazard([obs], current_time, "fire")

    assert result.hazard_type == "fire"
    assert result.regional_evidence == pytest.approx(0.75)
    assert result.regional_confidence == pytest.approx(0.82)
    assert result.regional_severity == pytest.approx(0.65)
    assert result.regional_risk == pytest.approx(0.70)
    assert result.information_condition == "GOOD"
    assert result.node_count == 1
    assert result.centroid_lat == pytest.approx(12.9716)
    assert result.centroid_lon == pytest.approx(77.5946)


def test_fuse_multiple_nearby_nodes():
    """Test fusion with multiple nearby nodes"""
    current_time = datetime.utcnow()

    observations = [
        NodeObservation(
            node_id="NODE-001",
            hazard_type="fire",
            state="CONFIRMED",
            evidence=0.75,
            confidence=0.82,
            severity=0.65,
            risk=0.70,
            information_condition="GOOD",
            observation_time=current_time,
            location_lat=12.9716,
            location_lon=77.5946,
            node_reliability=0.88
        ),
        NodeObservation(
            node_id="NODE-002",
            hazard_type="fire",
            state="CONFIRMED",
            evidence=0.80,
            confidence=0.85,
            severity=0.70,
            risk=0.75,
            information_condition="GOOD",
            observation_time=current_time,
            location_lat=12.9717,
            location_lon=77.5947,
            node_reliability=0.90
        )
    ]

    result = fuse_regional_hazard(observations, current_time, "fire")

    # Regional metrics should be weighted average, roughly between the two nodes
    assert 0.75 < result.regional_evidence < 0.80
    assert 0.82 < result.regional_confidence < 0.85
    assert result.information_condition == "GOOD"
    assert result.node_count == 2
    assert result.spatial_extent_m is not None
    assert result.spatial_extent_m > 0  # Non-zero distance between nodes


def test_fuse_stale_observation():
    """Test that stale observations have reduced weight"""
    current_time = datetime.utcnow()

    observations = [
        # Fresh observation
        NodeObservation(
            node_id="NODE-001",
            hazard_type="fire",
            state="CONFIRMED",
            evidence=0.70,
            confidence=0.80,
            severity=0.60,
            risk=0.65,
            information_condition="GOOD",
            observation_time=current_time,
            location_lat=12.9716,
            location_lon=77.5946,
            node_reliability=0.85
        ),
        # Stale observation (10 minutes old)
        NodeObservation(
            node_id="NODE-002",
            hazard_type="fire",
            state="CONFIRMED",
            evidence=0.90,
            confidence=0.95,
            severity=0.85,
            risk=0.90,
            information_condition="GOOD",
            observation_time=current_time - timedelta(minutes=10),
            location_lat=12.9717,
            location_lon=77.5947,
            node_reliability=0.90
        )
    ]

    result = fuse_regional_hazard(observations, current_time, "fire")

    # Fresh observation should dominate despite lower values
    # Regional evidence should be closer to 0.70 than 0.90
    assert result.regional_evidence < 0.80
    assert result.node_count == 2


def test_fuse_degraded_information():
    """Test fusion with degraded information condition"""
    current_time = datetime.utcnow()

    observations = [
        NodeObservation(
            node_id="NODE-001",
            hazard_type="fire",
            state="CONFIRMED",
            evidence=0.75,
            confidence=0.82,
            severity=0.65,
            risk=0.70,
            information_condition="GOOD",
            observation_time=current_time,
            location_lat=12.9716,
            location_lon=77.5946,
            node_reliability=0.88
        ),
        NodeObservation(
            node_id="NODE-002",
            hazard_type="fire",
            state="CONFIRMED",
            evidence=0.80,
            confidence=0.50,
            severity=0.70,
            risk=0.75,
            information_condition="DEGRADED",
            observation_time=current_time,
            location_lat=12.9717,
            location_lon=77.5947,
            node_reliability=0.90
        )
    ]

    result = fuse_regional_hazard(observations, current_time, "fire")

    # Regional information condition should be DEGRADED (most restrictive)
    assert result.information_condition == "DEGRADED"
    assert result.node_count == 2


def test_fuse_no_observations():
    """Test fusion with no observations"""
    current_time = datetime.utcnow()

    result = fuse_regional_hazard([], current_time, "fire")

    assert result.hazard_type == "fire"
    assert result.regional_evidence is None
    assert result.regional_confidence is None
    assert result.information_condition == "UNKNOWN"
    assert result.node_count == 0
    assert result.contributing_nodes == []


def test_fuse_missing_values_preserved():
    """Test that None values are preserved (missing != zero)"""
    current_time = datetime.utcnow()

    obs = NodeObservation(
        node_id="NODE-001",
        hazard_type="fire",
        state="WATCH",
        evidence=None,  # Missing
        confidence=0.60,
        severity=None,  # Missing
        risk=0.35,
        information_condition="DEGRADED",
        observation_time=current_time,
        location_lat=12.9716,
        location_lon=77.5946,
        node_reliability=0.80
    )

    result = fuse_regional_hazard([obs], current_time, "fire")

    # Missing values should remain None, not converted to zero
    assert result.regional_evidence is None
    assert result.regional_severity is None
    # Non-missing values should be present
    assert result.regional_confidence == pytest.approx(0.60)
    assert result.regional_risk == pytest.approx(0.35)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
