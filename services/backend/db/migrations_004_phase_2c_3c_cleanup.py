"""Phase 2C-3C: Final Legacy Multi-Hazard Cleanup Migration

Remove legacy Incident-level hazard scalar fields after full migration to
canonical IncidentHazardAssessment model.

Revision ID: 004_phase_2c_3c_cleanup
Revises: 003_track_b2_multi_hazard
Create Date: 2026-09-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_phase_2c_3c_cleanup'
down_revision = '003_track_b2_multi_hazard'
branch_labels = None
depends_on = None


def upgrade():
    """Remove legacy Incident-level hazard scalar fields

    Phase 2C-3C Complete:
    - Application code migrated to IncidentHazardAssessment (Phase 2C-3A)
    - API consumers migrated (Phase 2C-3B)
    - Frontend migrated to canonical model (Phase 2C-3B)
    - Demo/test fixtures updated (Phase 2C-3C)
    - No active production consumers remain

    Removes:
    - Incident.hazard_type (single-hazard assumption)
    - Incident.severity_index (incident-level scalar)
    - Incident.risk_index (incident-level scalar)
    - Incident.confidence_index (incident-level scalar)
    - Index idx_incidents_hazard_state (hazard_type, state)

    Preserves:
    - IncidentHazardAssessment table (canonical per-hazard model)
    - All incident relationships and data
    - Incident state, geometry, timestamps
    """
    # Drop index that references hazard_type
    op.drop_index('idx_incidents_hazard_state', table_name='incidents')

    # Drop legacy scalar columns
    op.drop_column('incidents', 'hazard_type')
    op.drop_column('incidents', 'severity_index')
    op.drop_column('incidents', 'risk_index')
    op.drop_column('incidents', 'confidence_index')

    # Add index on state (for state-based queries)
    op.create_index('idx_incidents_state', 'incidents', ['state'], unique=False)


def downgrade():
    """Restore legacy Incident-level hazard scalar fields

    WARNING: Downgrade loses per-hazard data!

    Multi-hazard incidents (FIRE + FLOOD) will lose one hazard's data.
    Only first hazard assessment will be restored to Incident scalars.

    This downgrade is provided for emergency rollback only.
    Consider data migration strategy before downgrading.
    """
    # Drop state index
    op.drop_index('idx_incidents_state', table_name='incidents')

    # Restore legacy columns (nullable for safe rollback)
    op.add_column('incidents', sa.Column('hazard_type', sa.String(length=32), nullable=True))
    op.add_column('incidents', sa.Column('severity_index', sa.Double(), nullable=True))
    op.add_column('incidents', sa.Column('risk_index', sa.Double(), nullable=True))
    op.add_column('incidents', sa.Column('confidence_index', sa.Double(), nullable=True))

    # Restore composite index
    op.create_index('idx_incidents_hazard_state', 'incidents', ['hazard_type', 'state'], unique=False)

    # NOTE: Data migration from IncidentHazardAssessment back to Incident
    # is NOT performed by this downgrade. Legacy fields will be NULL.
    # Manual data migration required if downgrade is necessary.
