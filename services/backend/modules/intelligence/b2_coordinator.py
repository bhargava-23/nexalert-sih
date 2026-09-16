"""Track B2 Coordinator - Integration between MQTT ingestion and regional intelligence

Wires the existing MQTT telemetry ingestion pipeline to Track B2 regional fusion
and incident correlation after telemetry persistence.

Architecture:
- Triggered AFTER valid telemetry is persisted
- Queries recent node observations from database
- Triggers regional fusion for affected hazard types
- Triggers incident correlation when fusion conditions are met
- Preserves idempotency and multi-hazard independence
- Non-blocking: runs asynchronously, does not block MQTT ingestion
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import uuid

from db.models_b2 import (
    Incident,
    IncidentObservation,
    RegionalHazardAssessment,
    IncidentHazardAssessment,
    NodeStatus
)
from modules.intelligence.regional_fusion import (
    NodeObservation,
    RegionalFusionResult,
    fuse_regional_hazard
)
from modules.intelligence.incident_correlation import (
    IncidentState,
    IncidentCandidate,
    IncidentCreationResult,
    should_correlate_with_incident,
    determine_incident_state,
    generate_deterministic_incident_id
)

logger = logging.getLogger(__name__)


# Configuration (TODO: move to config file)
OBSERVATION_WINDOW_SECONDS = 600.0  # 10 minutes - query recent observations
MIN_NODES_FOR_REGIONAL = 2  # Minimum nodes to trigger regional fusion
CORRELATION_RADIUS_M = 50.0
CORRELATION_WINDOW_S = 30.0


class B2Coordinator:
    """Coordinates Track B2 regional intelligence pipeline"""

    def __init__(self):
        """Initialize coordinator"""
        self.stats = {
            "triggers_total": 0,
            "fusion_runs": 0,
            "incidents_created": 0,
            "incidents_updated": 0,
            "errors": 0
        }

    def _map_incident_state_to_hazard_state(self, incident_state: str) -> str:
        """Map incident lifecycle state to hazard assessment state

        Args:
            incident_state: Incident state (NEW, ACTIVE, ESCALATED, RESOLVED)

        Returns:
            Hazard state (NORMAL, WATCH, SUSPECTED, CONFIRMED, CRITICAL, RESOLVED)
        """
        mapping = {
            "NEW": "SUSPECTED",
            "ACTIVE": "CONFIRMED",
            "ESCALATED": "CRITICAL",
            "RESOLVED": "RESOLVED"
        }
        return mapping.get(incident_state, "NORMAL")

    async def trigger_after_persistence(
        self,
        session: AsyncSession,
        node_id: str,
        hazard_types: List[str],
        measurement_ts: datetime
    ) -> None:
        """Trigger Track B2 pipeline after telemetry persistence

        Called by MQTT ingestion after successful telemetry persistence.
        Runs regional fusion and incident correlation for affected hazard types.

        Args:
            session: Database session
            node_id: Node that produced the telemetry
            hazard_types: List of hazard types detected (e.g., ["fire", "flood"])
            measurement_ts: Timestamp of the measurement

        Non-blocking: Errors are logged but do not propagate to caller.
        """
        try:
            self.stats["triggers_total"] += 1

            # For each hazard type detected, trigger regional intelligence
            for hazard_type in hazard_types:
                await self._process_hazard_type(
                    session=session,
                    node_id=node_id,
                    hazard_type=hazard_type,
                    measurement_ts=measurement_ts
                )

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(
                f"B2 coordinator error for node {node_id}: {str(e)}",
                exc_info=True
            )
            # Non-blocking: do not propagate error

    async def _process_hazard_type(
        self,
        session: AsyncSession,
        node_id: str,
        hazard_type: str,
        measurement_ts: datetime
    ) -> None:
        """Process one hazard type for regional intelligence

        Args:
            session: Database session
            node_id: Triggering node
            hazard_type: Hazard type to process
            measurement_ts: Measurement timestamp
        """
        # Step 1: Query recent observations for this hazard type
        observations = await self._query_recent_observations(
            session=session,
            hazard_type=hazard_type,
            window_seconds=OBSERVATION_WINDOW_SECONDS,
            reference_time=measurement_ts
        )

        if len(observations) < MIN_NODES_FOR_REGIONAL:
            logger.debug(
                f"Insufficient nodes for regional fusion: {len(observations)} < {MIN_NODES_FOR_REGIONAL}"
            )
            return

        # Step 2: Run regional fusion
        fusion_result = await self._run_regional_fusion(
            observations=observations,
            current_time=measurement_ts
        )

        if fusion_result is None:
            logger.warning(f"Regional fusion failed for {hazard_type}")
            return

        self.stats["fusion_runs"] += 1

        # Step 3: Trigger incident correlation
        await self._run_incident_correlation(
            session=session,
            hazard_type=hazard_type,
            observations=observations,
            fusion_result=fusion_result,
            current_time=measurement_ts
        )

    async def _query_recent_observations(
        self,
        session: AsyncSession,
        hazard_type: str,
        window_seconds: float,
        reference_time: datetime
    ) -> List[NodeObservation]:
        """Query recent node observations from database

        For now, returns mock observations since we don't have node-level
        hazard assessments persisted yet. In full integration, this would
        query the actual node hazard state from the database.

        Args:
            session: Database session
            hazard_type: Hazard type to query
            window_seconds: Time window for observations
            reference_time: Reference timestamp

        Returns:
            List of NodeObservation objects
        """
        # TODO: Query actual node hazard assessments from database when available
        # For now, return empty list - full integration requires node-level
        # hazard state persistence from Phase 5 reference implementation

        logger.debug(
            f"Query observations: hazard={hazard_type}, "
            f"window={window_seconds}s, ref_time={reference_time}"
        )

        return []

    async def _run_regional_fusion(
        self,
        observations: List[NodeObservation],
        current_time: datetime
    ) -> Optional[RegionalFusionResult]:
        """Run regional fusion on observations

        Args:
            observations: List of node observations
            current_time: Current timestamp

        Returns:
            RegionalFusionResult or None on error
        """
        if not observations:
            return None

        try:
            hazard_type = observations[0].hazard_type
            result = fuse_regional_hazard(
                observations=observations,
                current_time=current_time,
                hazard_type=hazard_type
            )

            logger.info(
                f"Regional fusion: hazard={hazard_type}, "
                f"nodes={result.node_count}, "
                f"evidence={result.regional_evidence}, "
                f"confidence={result.regional_confidence}"
            )

            return result

        except Exception as e:
            logger.error(f"Regional fusion error: {str(e)}", exc_info=True)
            return None

    async def _run_incident_correlation(
        self,
        session: AsyncSession,
        hazard_type: str,
        observations: List[NodeObservation],
        fusion_result: RegionalFusionResult,
        current_time: datetime
    ) -> None:
        """Run incident correlation and persist to database

        Args:
            session: Database session
            hazard_type: Hazard type
            observations: Node observations
            fusion_result: Regional fusion result
            current_time: Current timestamp
        """
        try:
            # Query existing incidents for this hazard type
            existing_incidents = await self._query_active_incidents(
                session=session,
                hazard_type=hazard_type
            )

            # Check if observations correlate with existing incident
            correlated_incident = None
            if fusion_result.centroid_lat is not None and fusion_result.centroid_lon is not None:
                for inc in existing_incidents:
                    if should_correlate_with_incident(
                        observation_location=(fusion_result.centroid_lat, fusion_result.centroid_lon),
                        observation_time=current_time,
                        incident=inc,
                        merge_radius_m=CORRELATION_RADIUS_M,
                        merge_window_s=CORRELATION_WINDOW_S
                    ):
                        correlated_incident = inc
                        break

            if correlated_incident:
                # Update existing incident
                await self._update_incident(
                    session=session,
                    incident=correlated_incident,
                    observations=observations,
                    fusion_result=fusion_result,
                    current_time=current_time
                )
                self.stats["incidents_updated"] += 1
                logger.info(f"Updated incident {correlated_incident.incident_id}")

            else:
                # Create new incident
                await self._create_incident(
                    session=session,
                    hazard_type=hazard_type,
                    observations=observations,
                    fusion_result=fusion_result,
                    current_time=current_time
                )
                self.stats["incidents_created"] += 1
                logger.info(f"Created new incident for {hazard_type}")

        except Exception as e:
            logger.error(f"Incident correlation error: {str(e)}", exc_info=True)

    async def _query_active_incidents(
        self,
        session: AsyncSession,
        hazard_type: str
    ) -> List[IncidentCandidate]:
        """Query active incidents for hazard type

        Args:
            session: Database session
            hazard_type: Hazard type to query

        Returns:
            List of IncidentCandidate objects
        """
        try:
            # Phase 2C-3C: Query via IncidentHazardAssessment JOIN (Incident has no hazard_type)
            stmt = (
                select(Incident)
                .join(IncidentHazardAssessment)
                .where(
                    and_(
                        IncidentHazardAssessment.hazard_type == hazard_type,
                        Incident.state != IncidentState.RESOLVED
                    )
                )
                .distinct()
                .order_by(Incident.last_observed_at.desc())
            )

            result = await session.execute(stmt)
            incidents = result.scalars().all()

            # Convert to IncidentCandidate (Phase 2C-3C: no longer using legacy scalar fields)
            candidates = []
            for inc in incidents:
                candidates.append(IncidentCandidate(
                    incident_id=inc.incident_id,
                    hazard_type=hazard_type,  # Pass as parameter, not from inc
                    state=inc.state,
                    centroid_lat=inc.centroid_lat,
                    centroid_lon=inc.centroid_lon,
                    last_observed_at=inc.last_observed_at
                ))

            return candidates

        except Exception as e:
            logger.error(f"Query active incidents error: {str(e)}", exc_info=True)
            return []

    async def _create_incident(
        self,
        session: AsyncSession,
        hazard_type: str,
        observations: List[NodeObservation],
        fusion_result: RegionalFusionResult,
        current_time: datetime
    ) -> None:
        """Create new incident

        Args:
            session: Database session
            hazard_type: Hazard type
            observations: Node observations
            fusion_result: Regional fusion result
            current_time: Current timestamp
        """
        # Determine incident state
        incident_state = determine_incident_state(
            regional_fusion=fusion_result,
            node_observations=observations
        )

        # Create incident (correlation container only)
        # Phase 2C-3C: Incident is a pure correlation container
        # No single-hazard semantics; per-hazard data in IncidentHazardAssessment
        incident = Incident(
            incident_id=generate_deterministic_incident_id(),
            state=incident_state,
            centroid_lat=fusion_result.centroid_lat,
            centroid_lon=fusion_result.centroid_lon,
            first_observed_at=current_time,
            last_observed_at=current_time,
            source_summary={
                "node_count": fusion_result.node_count,
                "contributing_nodes": [obs.node_id for obs in observations]
            },
            created_by="B2_COORDINATOR",
            current_version=1
        )

        session.add(incident)

        # Create incident-level hazard assessment (Phase 2C-2: canonical model)
        hazard_assessment = IncidentHazardAssessment(
            incident_id=incident.incident_id,
            hazard_type=hazard_type,
            evidence=fusion_result.regional_evidence,
            confidence=fusion_result.regional_confidence,
            severity=fusion_result.regional_severity,
            operational_risk=fusion_result.regional_risk,
            state=self._map_incident_state_to_hazard_state(incident_state),
            information_condition=fusion_result.information_condition if hasattr(fusion_result, 'information_condition') else None,
            assessment_timestamp=current_time,
            model_version="b2_fusion_v1",
            source_summary={
                "node_count": fusion_result.node_count,
                "contributing_nodes": fusion_result.contributing_nodes,
                "agreement_index": fusion_result.agreement_index,
                "spatial_extent_m": fusion_result.spatial_extent_m
            }
        )

        session.add(hazard_assessment)

        # Create regional hazard assessment (Track B2 existing structure)
        regional_assessment = RegionalHazardAssessment(
            incident_id=incident.incident_id,
            hazard_type=hazard_type,
            regional_evidence=fusion_result.regional_evidence,
            regional_confidence=fusion_result.regional_confidence,
            regional_severity=fusion_result.regional_severity,
            regional_risk=fusion_result.regional_risk,
            contributing_nodes=fusion_result.contributing_nodes,
            node_count=fusion_result.node_count,
            agreement_index=fusion_result.agreement_index,
            spatial_extent_m=fusion_result.spatial_extent_m,
            information_condition=fusion_result.information_condition if hasattr(fusion_result, 'information_condition') else None
        )

        session.add(regional_assessment)

        # Create incident observations
        for obs in observations:
            inc_obs = IncidentObservation(
                incident_id=incident.incident_id,
                node_id=obs.node_id,
                telemetry_id=None,  # TODO: Link to actual telemetry_id
                weight=1.0,  # TODO: Compute actual weight from fusion
                is_primary="N",
                observed_at=obs.observation_time
            )
            session.add(inc_obs)

        await session.commit()

        # Track C Integration Hook: Trigger fire simulation for FIRE incidents
        if hazard_type.upper() == "FIRE":
            try:
                from modules.simulation.c_coordinator import get_c_coordinator
                c_coord = get_c_coordinator()
                await c_coord.on_incident_created(
                    session,
                    incident.incident_id,
                    {
                        "hazard_type": hazard_type,
                        "centroid_lat": fusion_result.centroid_lat,
                        "centroid_lon": fusion_result.centroid_lon,
                        "confidence": fusion_result.regional_confidence
                    }
                )
            except Exception as c_error:
                logger.warning(f"Track C trigger failed (non-blocking): {str(c_error)}")

    async def _update_incident(
        self,
        session: AsyncSession,
        incident: IncidentCandidate,
        observations: List[NodeObservation],
        fusion_result: RegionalFusionResult,
        current_time: datetime
    ) -> None:
        """Update existing incident

        Args:
            session: Database session
            incident: Existing incident
            observations: Node observations
            fusion_result: Regional fusion result
            current_time: Current timestamp
        """
        # Determine new state
        new_state = determine_incident_state(
            regional_fusion=fusion_result,
            node_observations=observations
        )

        # Update incident
        stmt = select(Incident).where(Incident.incident_id == incident.incident_id)
        result = await session.execute(stmt)
        inc = result.scalar_one_or_none()

        if inc:
            inc.state = new_state
            # Phase 2C-3C: Incident is a pure correlation container
            # No single-hazard semantics; per-hazard data in IncidentHazardAssessment
            inc.centroid_lat = fusion_result.centroid_lat
            inc.centroid_lon = fusion_result.centroid_lon
            inc.last_observed_at = current_time
            inc.current_version += 1

            # Update incident-level hazard assessment (Phase 2C-3C: canonical model)
            # Query by hazard_type from fusion_result for multi-hazard support
            stmt_hazard = select(IncidentHazardAssessment).where(
                and_(
                    IncidentHazardAssessment.incident_id == incident.incident_id,
                    IncidentHazardAssessment.hazard_type == fusion_result.hazard_type
                )
            )
            result_hazard = await session.execute(stmt_hazard)
            hazard_assessment = result_hazard.scalar_one_or_none()

            if hazard_assessment:
                # Update existing hazard assessment
                hazard_assessment.evidence = fusion_result.regional_evidence
                hazard_assessment.confidence = fusion_result.regional_confidence
                hazard_assessment.severity = fusion_result.regional_severity
                hazard_assessment.operational_risk = fusion_result.regional_risk
                hazard_assessment.state = self._map_incident_state_to_hazard_state(new_state)
                hazard_assessment.assessment_timestamp = current_time
                if hasattr(fusion_result, 'information_condition'):
                    hazard_assessment.information_condition = fusion_result.information_condition
                hazard_assessment.source_summary = {
                    "node_count": fusion_result.node_count,
                    "contributing_nodes": fusion_result.contributing_nodes,
                    "agreement_index": fusion_result.agreement_index,
                    "spatial_extent_m": fusion_result.spatial_extent_m
                }
            else:
                # Create hazard assessment if missing (should not happen, but defensive)
                # Phase 2C-3A FIX: Use fusion_result.hazard_type, not inc.hazard_type
                hazard_assessment = IncidentHazardAssessment(
                    incident_id=incident.incident_id,
                    hazard_type=fusion_result.hazard_type,
                    evidence=fusion_result.regional_evidence,
                    confidence=fusion_result.regional_confidence,
                    severity=fusion_result.regional_severity,
                    operational_risk=fusion_result.regional_risk,
                    state=self._map_incident_state_to_hazard_state(new_state),
                    information_condition=fusion_result.information_condition if hasattr(fusion_result, 'information_condition') else None,
                    assessment_timestamp=current_time,
                    model_version="b2_fusion_v1",
                    source_summary={
                        "node_count": fusion_result.node_count,
                        "contributing_nodes": fusion_result.contributing_nodes,
                        "agreement_index": fusion_result.agreement_index,
                        "spatial_extent_m": fusion_result.spatial_extent_m
                    }
                )
                session.add(hazard_assessment)

            # Update regional assessment (Track B2 existing structure)
            stmt = select(RegionalHazardAssessment).where(
                RegionalHazardAssessment.incident_id == incident.incident_id
            )
            result = await session.execute(stmt)
            regional_assessment = result.scalar_one_or_none()

            if regional_assessment:
                regional_assessment.regional_evidence = fusion_result.regional_evidence
                regional_assessment.regional_confidence = fusion_result.regional_confidence
                regional_assessment.regional_severity = fusion_result.regional_severity
                regional_assessment.regional_risk = fusion_result.regional_risk
                regional_assessment.node_count = fusion_result.node_count
                regional_assessment.agreement_index = fusion_result.agreement_index
                regional_assessment.spatial_extent_m = fusion_result.spatial_extent_m
                if hasattr(fusion_result, 'information_condition'):
                    regional_assessment.information_condition = fusion_result.information_condition

            await session.commit()

    def get_stats(self) -> Dict:
        """Get coordinator statistics"""
        return self.stats.copy()


# Global coordinator instance
_coordinator: Optional[B2Coordinator] = None


def get_coordinator() -> B2Coordinator:
    """Get global B2 coordinator instance"""
    global _coordinator
    if _coordinator is None:
        _coordinator = B2Coordinator()
    return _coordinator
