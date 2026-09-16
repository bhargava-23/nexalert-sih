"""Phase 2C-3A Migration Verification Tests

Tests that verify Phase 2C-3A migration is correct without requiring PostgreSQL.
These tests verify the dataclass and operational logic changes.
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from modules.intelligence.incident_correlation import (
    IncidentCandidate,
    IncidentCreationResult,
    IncidentState
)
from modules.intelligence.regional_fusion import RegionalFusionResult


class TestPhase2C3AMigration:
    """Test Phase 2C-3A migration correctness"""

    def test_incident_candidate_no_legacy_fields(self):
        """Verify IncidentCandidate no longer has severity_index or risk_index"""
        # Create IncidentCandidate with only canonical fields
        candidate = IncidentCandidate(
            incident_id=uuid4(),
            hazard_type="FIRE",
            state="ACTIVE",
            centroid_lat=37.7749,
            centroid_lon=-122.4194,
            last_observed_at=datetime.now(timezone.utc)
        )

        # Verify legacy fields do NOT exist
        assert not hasattr(candidate, 'severity_index'), \
            "IncidentCandidate should NOT have severity_index field"
        assert not hasattr(candidate, 'risk_index'), \
            "IncidentCandidate should NOT have risk_index field"

        # Verify canonical fields exist
        assert hasattr(candidate, 'incident_id')
        assert hasattr(candidate, 'hazard_type')
        assert hasattr(candidate, 'state')
        assert candidate.hazard_type == "FIRE"

    def test_incident_creation_result_no_legacy_fields(self):
        """Verify IncidentCreationResult no longer has severity_index or risk_index"""
        # Create IncidentCreationResult with only canonical fields
        result = IncidentCreationResult(
            incident_id=uuid4(),
            action="created",
            state="ACTIVE",
            centroid_lat=37.7749,
            centroid_lon=-122.4194,
            contributing_nodes=["NODE-001", "NODE-002"]
        )

        # Verify legacy fields do NOT exist
        assert not hasattr(result, 'severity_index'), \
            "IncidentCreationResult should NOT have severity_index field"
        assert not hasattr(result, 'risk_index'), \
            "IncidentCreationResult should NOT have risk_index field"

        # Verify canonical fields exist
        assert hasattr(result, 'incident_id')
        assert hasattr(result, 'action')
        assert hasattr(result, 'state')
        assert result.action == "created"

    def test_regional_fusion_result_has_hazard_type(self):
        """Verify RegionalFusionResult has hazard_type field for multi-hazard support"""
        # Create RegionalFusionResult
        fusion_result = RegionalFusionResult(
            hazard_type="FIRE",
            regional_evidence=0.85,
            regional_confidence=0.9,
            regional_severity=0.8,
            regional_risk=0.75,
            information_condition="GOOD",
            node_count=3,
            contributing_nodes=[
                {"node_id": "NODE-001", "weight": 0.4},
                {"node_id": "NODE-002", "weight": 0.35},
                {"node_id": "NODE-003", "weight": 0.25}
            ],
            agreement_index=0.92,
            spatial_extent_m=45.0,
            freshness_index=0.95,
            centroid_lat=37.7749,
            centroid_lon=-122.4194
        )

        # Verify hazard_type exists (required for Phase 2C-3A multi-hazard fix)
        assert hasattr(fusion_result, 'hazard_type')
        assert fusion_result.hazard_type == "FIRE"

        # Verify other canonical fields
        assert fusion_result.regional_severity == 0.8
        assert fusion_result.regional_confidence == 0.9
        assert fusion_result.regional_risk == 0.75

    def test_dataclass_construction_without_legacy_fields(self):
        """Verify dataclasses can be constructed without legacy scalar fields"""
        now = datetime.now(timezone.utc)

        # Construct IncidentCandidate (as b2_coordinator does)
        candidate = IncidentCandidate(
            incident_id=uuid4(),
            hazard_type="FLOOD",
            state="NEW",
            centroid_lat=37.8049,
            centroid_lon=-122.2711,
            last_observed_at=now
        )

        assert candidate is not None
        assert candidate.hazard_type == "FLOOD"
        assert candidate.state == "NEW"

        # Construct IncidentCreationResult
        result = IncidentCreationResult(
            incident_id=candidate.incident_id,
            action="created",
            state="NEW",
            centroid_lat=candidate.centroid_lat,
            centroid_lon=candidate.centroid_lon,
            contributing_nodes=["NODE-010"]
        )

        assert result is not None
        assert result.action == "created"
        assert result.incident_id == candidate.incident_id


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
