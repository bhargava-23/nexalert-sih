"""Phase 2C-2 Multi-Hazard Domain Tests

Tests the canonical multi-hazard domain model implementation:
- One Incident MAY contain multiple independent HazardAssessment entities
- Each HazardAssessment independently owns evidence, confidence, severity, operational_risk, state
- Multi-hazard incidents (FIRE + FLOOD simultaneously) are representable
- Independent hazard lifecycle states
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models_b2 import Incident, IncidentHazardAssessment, RegionalHazardAssessment


class TestMultiHazardDomain:
    """Test canonical multi-hazard domain model"""

    @pytest.mark.asyncio
    async def test_single_incident_single_fire_hazard(self, db_session: AsyncSession):
        """Test Case 1: One incident with only FIRE assessment

        Phase 2C-3C: Incident is pure correlation container.
        """
        # Create incident (Phase 2C-3C: no legacy scalar fields)
        incident = Incident(
            incident_id=uuid4(),
            state="ACTIVE",
            centroid_lat=37.7749,
            centroid_lon=-122.4194,
            first_observed_at=datetime.now(timezone.utc),
            last_observed_at=datetime.now(timezone.utc),
            created_by="TEST",
            current_version=1
        )
        db_session.add(incident)

        # Create hazard assessment (canonical)
        hazard_assessment = IncidentHazardAssessment(
            incident_id=incident.incident_id,
            hazard_type="FIRE",
            evidence=0.85,
            confidence=0.9,
            severity=0.8,
            operational_risk=0.75,
            state="CONFIRMED",
            information_condition="GOOD",
            assessment_timestamp=datetime.now(timezone.utc),
            model_version="test_v1"
        )
        db_session.add(hazard_assessment)

        await db_session.commit()

        # Verify (use selectinload for async relationship access)
        result = await db_session.execute(
            select(Incident)
            .options(selectinload(Incident.hazard_assessments))
            .where(Incident.incident_id == incident.incident_id)
        )
        retrieved = result.scalar_one()

        assert retrieved.incident_id == incident.incident_id
        assert len(retrieved.hazard_assessments) == 1
        assert retrieved.hazard_assessments[0].hazard_type == "FIRE"
        assert retrieved.hazard_assessments[0].severity == 0.8
        assert retrieved.hazard_assessments[0].state == "CONFIRMED"

    @pytest.mark.asyncio
    async def test_single_incident_multi_hazard_fire_flood(self, db_session: AsyncSession):
        """Test Case 2: One incident with FIRE + FLOOD simultaneously"""
        # Create incident (correlation container)
        incident = Incident(
            incident_id=uuid4(),
            # Phase 2C-3C: Incident is pure correlation container
            state="ACTIVE",
            centroid_lat=37.7749,
            centroid_lon=-122.4194,
            first_observed_at=datetime.now(timezone.utc),
            last_observed_at=datetime.now(timezone.utc),
            created_by="TEST",
            current_version=1
        )
        db_session.add(incident)

        # Create FIRE hazard assessment
        fire_assessment = IncidentHazardAssessment(
            incident_id=incident.incident_id,
            hazard_type="FIRE",
            evidence=0.75,
            confidence=0.9,
            severity=0.7,
            operational_risk=0.65,
            state="CONFIRMED",
            information_condition="GOOD",
            assessment_timestamp=datetime.now(timezone.utc),
            model_version="test_v1"
        )
        db_session.add(fire_assessment)

        # Create FLOOD hazard assessment (independent)
        flood_assessment = IncidentHazardAssessment(
            incident_id=incident.incident_id,
            hazard_type="FLOOD",
            evidence=0.5,
            confidence=0.8,
            severity=0.4,
            operational_risk=0.3,
            state="WATCH",
            information_condition="GOOD",
            assessment_timestamp=datetime.now(timezone.utc),
            model_version="test_v1"
        )
        db_session.add(flood_assessment)

        await db_session.commit()

        # Verify multi-hazard representation (use selectinload for async relationship access)
        result = await db_session.execute(
            select(Incident)
            .options(selectinload(Incident.hazard_assessments))
            .where(Incident.incident_id == incident.incident_id)
        )
        retrieved = result.scalar_one()

        assert len(retrieved.hazard_assessments) == 2

        # Verify FIRE assessment
        fire = [h for h in retrieved.hazard_assessments if h.hazard_type == "FIRE"][0]
        assert fire.severity == 0.7
        assert fire.state == "CONFIRMED"

        # Verify FLOOD assessment (independent)
        flood = [h for h in retrieved.hazard_assessments if h.hazard_type == "FLOOD"][0]
        assert flood.severity == 0.4
        assert flood.state == "WATCH"

        # Verify independence
        assert fire.severity != flood.severity
        assert fire.state != flood.state

    @pytest.mark.asyncio
    async def test_independent_hazard_states(self, db_session: AsyncSession):
        """Test Case 7: Independent lifecycle states for FIRE and FLOOD within one incident"""
        incident = Incident(
            incident_id=uuid4(),
            # Phase 2C-3C: Incident is pure correlation container
            state="ESCALATED",  # Incident-level state
            centroid_lat=37.7749,
            centroid_lon=-122.4194,
            first_observed_at=datetime.now(timezone.utc),
            last_observed_at=datetime.now(timezone.utc),
            created_by="TEST",
            current_version=1
        )
        db_session.add(incident)

        # FIRE is CRITICAL
        fire_assessment = IncidentHazardAssessment(
            incident_id=incident.incident_id,
            hazard_type="FIRE",
            severity=0.9,
            operational_risk=0.85,
            state="CRITICAL",
            assessment_timestamp=datetime.now(timezone.utc),
            model_version="test_v1"
        )
        db_session.add(fire_assessment)

        # FLOOD is WATCH (independent state)
        flood_assessment = IncidentHazardAssessment(
            incident_id=incident.incident_id,
            hazard_type="FLOOD",
            severity=0.3,
            operational_risk=0.2,
            state="WATCH",
            assessment_timestamp=datetime.now(timezone.utc),
            model_version="test_v1"
        )
        db_session.add(flood_assessment)

        await db_session.commit()

        # Verify independent states
        result = await db_session.execute(
            select(IncidentHazardAssessment)
            .where(IncidentHazardAssessment.incident_id == incident.incident_id)
        )
        assessments = result.scalars().all()

        states = {a.hazard_type: a.state for a in assessments}
        assert states["FIRE"] == "CRITICAL"
        assert states["FLOOD"] == "WATCH"

    @pytest.mark.asyncio
    async def test_independent_severity_confidence_risk(self, db_session: AsyncSession):
        """Test Case 6: Different operational risk for two hazards with similar severity"""
        incident = Incident(
            incident_id=uuid4(),
            # Phase 2C-3C: Incident is pure correlation container
            state="ACTIVE",
            centroid_lat=37.7749,
            centroid_lon=-122.4194,
            first_observed_at=datetime.now(timezone.utc),
            last_observed_at=datetime.now(timezone.utc),
            created_by="TEST",
            current_version=1
        )
        db_session.add(incident)

        # FIRE: high severity, high risk (populated area)
        fire_assessment = IncidentHazardAssessment(
            incident_id=incident.incident_id,
            hazard_type="FIRE",
            severity=0.7,
            operational_risk=0.9,  # High exposure
            confidence=0.85,
            state="CONFIRMED",
            assessment_timestamp=datetime.now(timezone.utc),
            model_version="test_v1"
        )
        db_session.add(fire_assessment)

        # FLOOD: same severity, low risk (unpopulated area)
        flood_assessment = IncidentHazardAssessment(
            incident_id=incident.incident_id,
            hazard_type="FLOOD",
            severity=0.7,  # Same severity
            operational_risk=0.3,  # Low exposure
            confidence=0.8,
            state="CONFIRMED",
            assessment_timestamp=datetime.now(timezone.utc),
            model_version="test_v1"
        )
        db_session.add(flood_assessment)

        await db_session.commit()

        # Verify independence
        result = await db_session.execute(
            select(IncidentHazardAssessment)
            .where(IncidentHazardAssessment.incident_id == incident.incident_id)
        )
        assessments = result.scalars().all()

        fire = [a for a in assessments if a.hazard_type == "FIRE"][0]
        flood = [a for a in assessments if a.hazard_type == "FLOOD"][0]

        # Same severity
        assert fire.severity == flood.severity == 0.7

        # Different operational risk (exposure-dependent)
        assert fire.operational_risk == 0.9
        assert flood.operational_risk == 0.3

        # Independent confidence
        assert fire.confidence == 0.85
        assert flood.confidence == 0.8

    @pytest.mark.asyncio
    async def test_null_preserves_missing_not_zero(self, db_session: AsyncSession):
        """Test: Missing (NULL) remains distinct from zero"""
        incident = Incident(
            incident_id=uuid4(),
            # Phase 2C-3C: Incident is pure correlation container
            state="NEW",
            centroid_lat=37.7749,
            centroid_lon=-122.4194,
            first_observed_at=datetime.now(timezone.utc),
            last_observed_at=datetime.now(timezone.utc),
            created_by="TEST",
            current_version=1
        )
        db_session.add(incident)

        # Create assessment with NULL evidence (not zero)
        assessment = IncidentHazardAssessment(
            incident_id=incident.incident_id,
            hazard_type="FIRE",
            evidence=None,  # NULL = missing (NOT zero)
            confidence=0.5,
            severity=None,  # NULL = unknown
            operational_risk=0.2,
            state="SUSPECTED",
            assessment_timestamp=datetime.now(timezone.utc),
            model_version="test_v1"
        )
        db_session.add(assessment)

        await db_session.commit()

        # Verify NULL preservation
        result = await db_session.execute(
            select(IncidentHazardAssessment)
            .where(IncidentHazardAssessment.incident_id == incident.incident_id)
        )
        retrieved = result.scalar_one()

        assert retrieved.evidence is None  # NULL preserved
        assert retrieved.severity is None  # NULL preserved
        assert retrieved.confidence == 0.5  # Value preserved
        assert retrieved.operational_risk == 0.2  # Value preserved

    @pytest.mark.asyncio
    async def test_hazard_specific_jsonb_data(self, db_session: AsyncSession):
        """Test Case 9: Hazard-specific data in JSONB (fire geometry, flood depth)"""
        incident = Incident(
            incident_id=uuid4(),
            # Phase 2C-3C: Incident is pure correlation container
            state="ACTIVE",
            centroid_lat=37.7749,
            centroid_lon=-122.4194,
            first_observed_at=datetime.now(timezone.utc),
            last_observed_at=datetime.now(timezone.utc),
            created_by="TEST",
            current_version=1
        )
        db_session.add(incident)

        # FIRE: fire-specific data (geometry, spread rate)
        fire_assessment = IncidentHazardAssessment(
            incident_id=incident.incident_id,
            hazard_type="FIRE",
            severity=0.8,
            operational_risk=0.75,
            state="CONFIRMED",
            hazard_specific_data={
                "geometry": {"type": "Polygon", "coordinates": [[[-122.42, 37.77], [-122.41, 37.77], [-122.41, 37.78]]]},
                "perimeter_m": 500,
                "spread_rate_m_s": 0.5,
                "ignition_source": "electrical"
            },
            assessment_timestamp=datetime.now(timezone.utc),
            model_version="test_v1"
        )
        db_session.add(fire_assessment)

        # FLOOD: flood-specific data (depth, velocity)
        flood_assessment = IncidentHazardAssessment(
            incident_id=incident.incident_id,
            hazard_type="FLOOD",
            severity=0.6,
            operational_risk=0.5,
            state="CONFIRMED",
            hazard_specific_data={
                "depth_m": 2.5,
                "flow_velocity_m_s": 3.0,
                "inundation_area_m2": 10000,
                "source": "river_overflow"
            },
            assessment_timestamp=datetime.now(timezone.utc),
            model_version="test_v1"
        )
        db_session.add(flood_assessment)

        await db_session.commit()

        # Verify hazard-specific data
        result = await db_session.execute(
            select(IncidentHazardAssessment)
            .where(IncidentHazardAssessment.incident_id == incident.incident_id)
        )
        assessments = result.scalars().all()

        fire = [a for a in assessments if a.hazard_type == "FIRE"][0]
        flood = [a for a in assessments if a.hazard_type == "FLOOD"][0]

        # Fire-specific data
        assert fire.hazard_specific_data["perimeter_m"] == 500
        assert fire.hazard_specific_data["spread_rate_m_s"] == 0.5
        assert "geometry" in fire.hazard_specific_data

        # Flood-specific data (no cross-contamination)
        assert flood.hazard_specific_data["depth_m"] == 2.5
        assert flood.hazard_specific_data["flow_velocity_m_s"] == 3.0
        assert "perimeter_m" not in flood.hazard_specific_data

    @pytest.mark.asyncio
    async def test_provenance_tracking(self, db_session: AsyncSession):
        """Test Case 8: Full evidence provenance for each hazard assessment"""
        incident = Incident(
            incident_id=uuid4(),
            # Phase 2C-3C: Incident is pure correlation container
            state="ACTIVE",
            centroid_lat=37.7749,
            centroid_lon=-122.4194,
            first_observed_at=datetime.now(timezone.utc),
            last_observed_at=datetime.now(timezone.utc),
            created_by="TEST",
            current_version=1
        )
        db_session.add(incident)

        # Create assessment with full provenance
        assessment = IncidentHazardAssessment(
            incident_id=incident.incident_id,
            hazard_type="FIRE",
            evidence=0.85,
            confidence=0.9,
            severity=0.8,
            operational_risk=0.75,
            state="CONFIRMED",
            assessment_timestamp=datetime.now(timezone.utc),
            model_version="b2_fusion_v1.2",
            source_summary={
                "nodes": ["NODE-001", "NODE-042"],
                "weights": [0.6, 0.4],
                "node_count": 2,
                "agreement_index": 0.85,
                "spatial_extent_m": 120.5
            }
        )
        db_session.add(assessment)

        await db_session.commit()

        # Verify provenance
        result = await db_session.execute(
            select(IncidentHazardAssessment)
            .where(IncidentHazardAssessment.incident_id == incident.incident_id)
        )
        retrieved = result.scalar_one()

        assert retrieved.model_version == "b2_fusion_v1.2"
        assert retrieved.source_summary["nodes"] == ["NODE-001", "NODE-042"]
        assert retrieved.source_summary["weights"] == [0.6, 0.4]
        assert retrieved.source_summary["node_count"] == 2
        assert retrieved.assessment_timestamp is not None

    @pytest.mark.asyncio
    async def test_two_separate_incidents_same_hazard_type(self, db_session: AsyncSession):
        """Test Case 3: Two separate incidents involving the same hazard type"""
        # Incident A (Location A)
        incident_a = Incident(
            incident_id=uuid4(),
            # Phase 2C-3C: Incident is pure correlation container
            state="ACTIVE",
            centroid_lat=37.7749,
            centroid_lon=-122.4194,
            first_observed_at=datetime.now(timezone.utc),
            last_observed_at=datetime.now(timezone.utc),
            created_by="TEST",
            current_version=1
        )
        db_session.add(incident_a)

        fire_a = IncidentHazardAssessment(
            incident_id=incident_a.incident_id,
            hazard_type="FIRE",
            severity=0.7,
            operational_risk=0.65,
            state="CONFIRMED",
            assessment_timestamp=datetime.now(timezone.utc),
            model_version="test_v1"
        )
        db_session.add(fire_a)

        # Incident B (Location B)
        incident_b = Incident(
            incident_id=uuid4(),
            # Phase 2C-3C: Incident is pure correlation container
            state="ACTIVE",
            centroid_lat=37.8049,  # Different location
            centroid_lon=-122.2711,
            first_observed_at=datetime.now(timezone.utc),
            last_observed_at=datetime.now(timezone.utc),
            created_by="TEST",
            current_version=1
        )
        db_session.add(incident_b)

        fire_b = IncidentHazardAssessment(
            incident_id=incident_b.incident_id,
            hazard_type="FIRE",
            severity=0.5,  # Different severity
            operational_risk=0.4,
            state="SUSPECTED",  # Different state
            assessment_timestamp=datetime.now(timezone.utc),
            model_version="test_v1"
        )
        db_session.add(fire_b)

        await db_session.commit()

        # Verify separate incidents (Phase 2C-3C: query via hazard assessments)
        result = await db_session.execute(
            select(Incident)
            .join(IncidentHazardAssessment)
            .where(IncidentHazardAssessment.hazard_type == "FIRE")
        )
        fire_incidents = result.scalars().all()

        assert len(fire_incidents) >= 2

        # Different locations
        assert incident_a.incident_id != incident_b.incident_id
        assert incident_a.centroid_lat != incident_b.centroid_lat
