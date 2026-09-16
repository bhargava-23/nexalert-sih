"""Track B2 Multi-Hazard Domain Migration (Phase 2C-2)

Adds incident-level HazardAssessment table to support multi-hazard domain model.

Architectural Decision:
- One Incident MAY contain multiple independent HazardAssessment entities
- Each HazardAssessment independently owns evidence, confidence, severity, operational_risk, state
- Incident becomes correlation container, NOT universal hazard scalar holder

Critical Distinction:
- This is incident-level/regional HazardAssessment (linked to incident_id)
- Separate from edge-level models.HazardAssessment (linked to telemetry_id)
- Both concepts coexist in different architectural layers

Revision: 003_track_b2_multi_hazard
Down Revision: 002_track_b2_regional_intelligence
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# Revision identifiers
revision = '003_track_b2_multi_hazard'
down_revision = '002_track_b2_regional_intelligence'
branch_labels = None
depends_on = None


def upgrade():
    """Add incident-level HazardAssessment table and migrate existing data"""

    # Create incident_hazard_assessments table
    op.create_table(
        'incident_hazard_assessments',
        sa.Column('assessment_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False,
                  comment='Incident this assessment belongs to'),
        sa.Column('hazard_type', sa.String(length=32), nullable=False,
                  comment='FIRE, FLOOD, STRUCTURAL, GAS, etc.'),

        # Core assessment (relational, queryable, indexed)
        sa.Column('evidence', sa.Double(),
                  comment='Hazard-specific evidence index [0,1] - NULL = missing (NOT zero)'),
        sa.Column('confidence', sa.Double(),
                  comment='Trust in assessment [0,1] - NOT probability'),
        sa.Column('severity', sa.Double(),
                  comment='Hazard intensity/consequence [0,1]'),
        sa.Column('operational_risk', sa.Double(),
                  comment='Operational prioritization index [0,1] - NOT probability'),
        sa.Column('state', sa.String(length=32),
                  comment='NORMAL, WATCH, SUSPECTED, CONFIRMED, CRITICAL, RESOLVED'),
        sa.Column('information_condition', sa.String(length=32),
                  comment='GOOD, DEGRADED, UNKNOWN'),

        # Hazard-specific data (JSONB, flexible)
        sa.Column('hazard_specific_data', postgresql.JSONB(),
                  comment='Hazard-specific attributes (fire geometry, flood depth, etc.)'),

        # Provenance
        sa.Column('assessment_timestamp', sa.TIMESTAMP(timezone=True), nullable=False,
                  comment='When assessment was computed'),
        sa.Column('model_version', sa.String(length=64),
                  comment='Algorithm/model version (e.g. "state_machine_v1.2")'),
        sa.Column('source_summary', postgresql.JSONB(),
                  comment='Contributing nodes/observations (provenance)'),

        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()'),
                  comment='Database insertion timestamp'),

        sa.PrimaryKeyConstraint('assessment_id'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.incident_id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('idx_incident_hazard_assess_incident', 'incident_hazard_assessments', ['incident_id'])
    op.create_index('idx_incident_hazard_assess_type', 'incident_hazard_assessments', ['hazard_type'])
    op.create_index('idx_incident_hazard_assess_state', 'incident_hazard_assessments', ['state'])
    op.create_index('idx_incident_hazard_assess_incident_type', 'incident_hazard_assessments', ['incident_id', 'hazard_type'])
    op.create_index('idx_incident_hazard_assess_severity', 'incident_hazard_assessments', ['severity'])

    # Migrate existing incident data to hazard assessments
    # For each existing incident with severity/confidence/risk scalars,
    # create corresponding HazardAssessment row
    op.execute("""
        INSERT INTO incident_hazard_assessments (
            incident_id,
            hazard_type,
            evidence,
            confidence,
            severity,
            operational_risk,
            state,
            information_condition,
            assessment_timestamp,
            model_version,
            source_summary,
            created_at
        )
        SELECT
            i.incident_id,
            i.hazard_type,
            NULL,  -- evidence not stored at incident level currently
            i.confidence_index,
            i.severity_index,
            i.risk_index,
            CASE
                WHEN i.state = 'NEW' THEN 'SUSPECTED'
                WHEN i.state = 'ACTIVE' THEN 'CONFIRMED'
                WHEN i.state = 'ESCALATED' THEN 'CRITICAL'
                WHEN i.state = 'RESOLVED' THEN 'RESOLVED'
                ELSE 'NORMAL'
            END,
            i.information_condition,
            i.last_observed_at,  -- Use last_observed as assessment timestamp
            'migrated_v1',
            i.source_summary,
            i.created_at
        FROM incidents i
        WHERE i.severity_index IS NOT NULL
           OR i.confidence_index IS NOT NULL
           OR i.risk_index IS NOT NULL
    """)


def downgrade():
    """Remove incident_hazard_assessments table"""

    # Drop indexes first
    op.drop_index('idx_incident_hazard_assess_severity', 'incident_hazard_assessments')
    op.drop_index('idx_incident_hazard_assess_incident_type', 'incident_hazard_assessments')
    op.drop_index('idx_incident_hazard_assess_state', 'incident_hazard_assessments')
    op.drop_index('idx_incident_hazard_assess_type', 'incident_hazard_assessments')
    op.drop_index('idx_incident_hazard_assess_incident', 'incident_hazard_assessments')

    # Drop table
    op.drop_table('incident_hazard_assessments')

    # Note: Cannot restore original incident scalar fields without data loss
    # Downgrade destroys HazardAssessment data created after migration
