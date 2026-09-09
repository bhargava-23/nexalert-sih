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
            # Query incidents that are not RESOLVED
            stmt = select(Incident).where(
                and_(
                    Incident.hazard_type == hazard_type,
                    Incident.state != IncidentState.RESOLVED
                )
            ).order_by(Incident.last_observed_at.desc())

            result = await session.execute(stmt)
            incidents = result.scalars().all()

            # Convert to IncidentCandidate
            candidates = []
            for inc in incidents:
                candidates.append(IncidentCandidate(
                    incident_id=inc.incident_id,
                    hazard_type=inc.hazard_type,
                    state=inc.state,
                    centroid_lat=inc.centroid_lat,
                    centroid_lon=inc.centroid_lon,
                    last_observed_at=inc.last_observed_at,
                    severity_index=inc.severity_index,
                    risk_index=inc.risk_index
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

        # Create incident
        incident = Incident(
            incident_id=generate_deterministic_incident_id(),
            hazard_type=hazard_type,
            state=incident_state,
            severity_index=fusion_result.regional_severity,
            risk_index=fusion_result.regional_risk,
            confidence_index=fusion_result.regional_confidence,
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

        # Create regional hazard assessment
        assessment = RegionalHazardAssessment(
            incident_id=incident.incident_id,
            regional_evidence=fusion_result.regional_evidence,
            regional_confidence=fusion_result.regional_confidence,
            regional_severity=fusion_result.regional_severity,
            regional_risk=fusion_result.regional_risk,
            contributing_nodes=fusion_result.contributing_nodes,
            node_count=fusion_result.node_count,
            agreement_index=fusion_result.agreement_index,
            spatial_extent_m=fusion_result.spatial_extent_m,
            last_updated=current_time
        )

        session.add(assessment)

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
            inc.severity_index = fusion_result.regional_severity
            inc.risk_index = fusion_result.regional_risk
            inc.confidence_index = fusion_result.regional_confidence
            inc.centroid_lat = fusion_result.centroid_lat
            inc.centroid_lon = fusion_result.centroid_lon
            inc.last_observed_at = current_time
            inc.current_version += 1

            # Update regional assessment
            stmt = select(RegionalHazardAssessment).where(
                RegionalHazardAssessment.incident_id == incident.incident_id
            )
            result = await session.execute(stmt)
            assessment = result.scalar_one_or_none()

            if assessment:
                assessment.regional_evidence = fusion_result.regional_evidence
                assessment.regional_confidence = fusion_result.regional_confidence
                assessment.regional_severity = fusion_result.regional_severity
                assessment.regional_risk = fusion_result.regional_risk
                assessment.node_count = fusion_result.node_count
                assessment.agreement_index = fusion_result.agreement_index
                assessment.spatial_extent_m = fusion_result.spatial_extent_m
                assessment.last_updated = current_time

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
