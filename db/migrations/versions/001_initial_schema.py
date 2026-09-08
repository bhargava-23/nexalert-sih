"""Initial schema: nodes, telemetry_records, sensor_assessments, hazard_assessments

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-09-08

Specification: Document 07, Section 3
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geography

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Enable PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')

    # nodes table
    op.create_table('nodes',
        sa.Column('node_id', sa.String(64), primary_key=True),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('location', Geography('Point', srid=4326)),
        sa.Column('firmware_version', sa.String(64)),
        sa.Column('config_version', sa.String(64)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('idx_nodes_status', 'nodes', ['status'])
    op.execute('CREATE INDEX idx_nodes_location ON nodes USING GIST(location)')

    # telemetry_records table - IMMUTABLE (Doc 07 Sec 2)
    op.create_table('telemetry_records',
        sa.Column('telemetry_id', sa.String(64), primary_key=True),
        sa.Column('node_id', sa.String(64), sa.ForeignKey('nodes.node_id'), nullable=False),
        sa.Column('sequence', sa.BigInteger, nullable=False),
        sa.Column('measurement_ts', sa.TIMESTAMP(timezone=True), nullable=False,
                  comment='When observation captured - DISTINCT from receive_ts per IMPLEMENTATION_CONSTITUTION.md Sec 12'),
        sa.Column('receive_ts', sa.TIMESTAMP(timezone=True), nullable=False,
                  comment='When backend received - server-assigned'),
        sa.Column('source', sa.String(32), nullable=False),
        sa.Column('location', Geography('Point', srid=4326)),
        sa.Column('measurements_jsonb', JSONB, nullable=False,
                  comment='Sensor readings - NULL values preserve missing != zero'),
        sa.Column('diagnostics_jsonb', JSONB, nullable=False,
                  comment='D_ij diagnostic dimensions'),
        sa.Column('power_jsonb', JSONB,
                  comment='Power/battery state'),
        sa.Column('schema_version', sa.String(32), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.execute("ALTER TABLE telemetry_records ADD CONSTRAINT chk_source CHECK (source IN ('HARDWARE', 'SIMULATION'))")
    op.create_index('idx_telemetry_node_seq', 'telemetry_records', ['node_id', 'sequence'], unique=True)
    op.create_index('idx_telemetry_node_ts', 'telemetry_records', ['node_id', 'measurement_ts'])
    op.execute('CREATE INDEX idx_telemetry_location ON telemetry_records USING GIST(location)')
    op.create_index('idx_telemetry_source', 'telemetry_records', ['source'])

    # sensor_assessments table (H_i, Q_i, R_i storage)
    op.create_table('sensor_assessments',
        sa.Column('assessment_id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('telemetry_id', sa.String(64), sa.ForeignKey('telemetry_records.telemetry_id'), nullable=False),
        sa.Column('node_id', sa.String(64), sa.ForeignKey('nodes.node_id'), nullable=False),
        sa.Column('sensor_type', sa.String(64), nullable=False),
        sa.Column('health', sa.Double, comment='H_i - NULL = missing (NOT zero)'),
        sa.Column('quality', sa.Double, comment='Q_i - NULL = missing'),
        sa.Column('reliability', sa.Double, comment='R_i - NULL = missing'),
        sa.Column('baseline_state', sa.String(32), comment='Phase 5'),
        sa.Column('anomaly', sa.Double, comment='Phase 5'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('idx_sensor_assess_node_ts', 'sensor_assessments', ['node_id', 'created_at'])
    op.create_index('idx_sensor_assess_telemetry', 'sensor_assessments', ['telemetry_id'])

    # hazard_assessments table (Phase 5 computation, Phase 4 schema)
    op.create_table('hazard_assessments',
        sa.Column('assessment_id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('telemetry_id', sa.String(64), sa.ForeignKey('telemetry_records.telemetry_id'), nullable=False),
        sa.Column('hazard_type', sa.String(32), nullable=False),
        sa.Column('evidence', sa.Double, comment='Phase 5'),
        sa.Column('confidence', sa.Double, comment='Phase 5'),
        sa.Column('severity', sa.Double, comment='Phase 5'),
        sa.Column('risk', sa.Double, comment='Phase 5'),
        sa.Column('state', sa.String(32), comment='Phase 5'),
        sa.Column('information_condition', sa.String(32), comment='Phase 5'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('idx_hazard_assess_type_ts', 'hazard_assessments', ['hazard_type', 'created_at'])
    op.create_index('idx_hazard_assess_telemetry', 'hazard_assessments', ['telemetry_id'])


def downgrade():
    op.drop_table('hazard_assessments')
    op.drop_table('sensor_assessments')
    op.drop_table('telemetry_records')
    op.drop_table('nodes')
    op.execute('DROP EXTENSION IF EXISTS postgis CASCADE')
