"""Alembic migration: Track B2 - Regional Intelligence and Incidents

Revision ID: 002_track_b2_regional_intelligence
Revises: 001_initial_schema
Create Date: 2026-09-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers
revision = '002_track_b2_regional_intelligence'
down_revision = None  # Will be set to 001 hash after 001 is created
branch_labels = None
depends_on = None


def upgrade():
    """Add Track B2 tables for regional intelligence and incident correlation"""

    # Incidents table
    op.create_table(
        'incidents',
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hazard_type', sa.String(32), nullable=False),
        sa.Column('state', sa.String(32), nullable=False, comment='NEW, ACTIVE, ESCALATED, RESOLVED'),
        sa.Column('information_condition', sa.String(32)),
        sa.Column('severity_index', sa.Double()),
        sa.Column('risk_index', sa.Double()),
        sa.Column('confidence_index', sa.Double()),
        sa.Column('geometry', geoalchemy2.Geography(geometry_type='GEOMETRY', srid=4326)),
        sa.Column('centroid_lat', sa.Double()),
        sa.Column('centroid_lon', sa.Double()),
        sa.Column('first_observed_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('last_observed_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('source_summary', postgresql.JSONB()),
        sa.Column('created_by', sa.String(32), nullable=False),
        sa.Column('resolution_reason', sa.String(128)),
        sa.Column('current_version', sa.BigInteger(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('incident_id')
    )

    op.create_index('idx_incidents_hazard_state', 'incidents', ['hazard_type', 'state'])
    op.create_index('idx_incidents_last_observed', 'incidents', ['last_observed_at'])
    op.create_index('idx_incidents_created', 'incidents', ['created_at'])

    # Incident observations table
    op.create_table(
        'incident_observations',
        sa.Column('observation_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('node_id', sa.String(64), nullable=False),
        sa.Column('telemetry_id', sa.String(64), nullable=False),
        sa.Column('hazard_assessment_id', sa.BigInteger()),
        sa.Column('weight', sa.Double()),
        sa.Column('is_primary', sa.String(1)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.incident_id']),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.node_id']),
        sa.ForeignKeyConstraint(['telemetry_id'], ['telemetry_records.telemetry_id']),
        sa.ForeignKeyConstraint(['hazard_assessment_id'], ['hazard_assessments.assessment_id']),
        sa.PrimaryKeyConstraint('observation_id')
    )

    op.create_index('idx_incident_obs_incident', 'incident_observations', ['incident_id'])
    op.create_index('idx_incident_obs_node', 'incident_observations', ['node_id'])
    op.create_index('idx_incident_obs_telemetry', 'incident_observations', ['telemetry_id'])

    # Regional hazard assessments table
    op.create_table(
        'regional_hazard_assessments',
        sa.Column('assessment_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hazard_type', sa.String(32), nullable=False),
        sa.Column('regional_evidence', sa.Double()),
        sa.Column('regional_confidence', sa.Double()),
        sa.Column('regional_severity', sa.Double()),
        sa.Column('regional_risk', sa.Double()),
        sa.Column('contributing_nodes', postgresql.JSONB()),
        sa.Column('node_count', sa.BigInteger()),
        sa.Column('agreement_index', sa.Double()),
        sa.Column('spatial_extent_m', sa.Double()),
        sa.Column('information_condition', sa.String(32)),
        sa.Column('freshness_index', sa.Double()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.incident_id']),
        sa.PrimaryKeyConstraint('assessment_id')
    )

    op.create_index('idx_regional_assess_incident', 'regional_hazard_assessments', ['incident_id'])
    op.create_index('idx_regional_assess_hazard_ts', 'regional_hazard_assessments', ['hazard_type', 'created_at'])

    # Node status table
    op.create_table(
        'node_status',
        sa.Column('status_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('node_id', sa.String(64), nullable=False),
        sa.Column('last_telemetry_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('last_heartbeat_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('staleness_seconds', sa.Double()),
        sa.Column('reliability_index', sa.Double()),
        sa.Column('uptime_pct_24h', sa.Double()),
        sa.Column('connection_state', sa.String(32)),
        sa.Column('consecutive_failures', sa.BigInteger(), server_default='0'),
        sa.Column('data_quality_index', sa.Double()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.node_id']),
        sa.PrimaryKeyConstraint('status_id')
    )

    op.create_index('idx_node_status_node', 'node_status', ['node_id'], unique=True)
    op.create_index('idx_node_status_updated', 'node_status', ['updated_at'])


def downgrade():
    """Remove Track B2 tables"""
    op.drop_index('idx_node_status_updated', table_name='node_status')
    op.drop_index('idx_node_status_node', table_name='node_status')
    op.drop_table('node_status')

    op.drop_index('idx_regional_assess_hazard_ts', table_name='regional_hazard_assessments')
    op.drop_index('idx_regional_assess_incident', table_name='regional_hazard_assessments')
    op.drop_table('regional_hazard_assessments')

    op.drop_index('idx_incident_obs_telemetry', table_name='incident_observations')
    op.drop_index('idx_incident_obs_node', table_name='incident_observations')
    op.drop_index('idx_incident_obs_incident', table_name='incident_observations')
    op.drop_table('incident_observations')

    op.drop_index('idx_incidents_created', table_name='incidents')
    op.drop_index('idx_incidents_last_observed', table_name='incidents')
    op.drop_index('idx_incidents_hazard_state', table_name='incidents')
    op.drop_table('incidents')
