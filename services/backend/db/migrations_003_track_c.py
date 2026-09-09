"""Alembic migration: Track C - Fire Spread and Risk Surface

Revision ID: 003_track_c_fire_spread
Revises: 002_track_b2_regional_intelligence
Create Date: 2026-09-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers
revision = '003_track_c_fire_spread'
down_revision = '002_track_b2_regional_intelligence'
branch_labels = None
depends_on = None


def upgrade():
    """Add Track C tables for fire spread simulation and risk surfaces"""

    # Fire simulations table
    op.create_table(
        'fire_simulations',
        sa.Column('simulation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True)),
        sa.Column('simulation_type', sa.String(32), nullable=False, comment='LIVE or SIMULATION'),
        sa.Column('ignition_lat', sa.Double(), nullable=False),
        sa.Column('ignition_lon', sa.Double(), nullable=False),
        sa.Column('ignition_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('simulation_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('environmental_state', postgresql.JSONB(), comment='Wind, moisture, temperature'),
        sa.Column('domain_extent', postgresql.JSONB(), comment='Simulation bbox'),
        sa.Column('crs_id', sa.String(64), comment='Projected CRS'),
        sa.Column('resolution_m', sa.Double(), comment='Grid cell size in meters'),
        sa.Column('max_time_minutes', sa.Double(), comment='Max simulation time'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.incident_id']),
        sa.PrimaryKeyConstraint('simulation_id')
    )

    op.create_index('idx_fire_sim_incident', 'fire_simulations', ['incident_id'])
    op.create_index('idx_fire_sim_type', 'fire_simulations', ['simulation_type'])
    op.create_index('idx_fire_sim_created', 'fire_simulations', ['created_at'])

    # Fire geometries table
    op.create_table(
        'fire_geometries',
        sa.Column('geometry_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('simulation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('zone_type', sa.String(32), nullable=False, comment='CURRENT, WARNING, PROJECTION'),
        sa.Column('geometry', geoalchemy2.Geography(geometry_type='GEOMETRY', srid=4326), nullable=False),
        sa.Column('physical_footprint', geoalchemy2.Geography(geometry_type='GEOMETRY', srid=4326)),
        sa.Column('operational_buffer', geoalchemy2.Geography(geometry_type='GEOMETRY', srid=4326)),
        sa.Column('area_hectares', sa.Double()),
        sa.Column('perimeter_m', sa.Double()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['simulation_id'], ['fire_simulations.simulation_id']),
        sa.PrimaryKeyConstraint('geometry_id')
    )

    op.create_index('idx_fire_geom_sim', 'fire_geometries', ['simulation_id'])
    op.create_index('idx_fire_geom_zone', 'fire_geometries', ['zone_type'])
    op.create_index('idx_fire_geom_created', 'fire_geometries', ['created_at'])

    # Risk surfaces table
    op.create_table(
        'risk_surfaces',
        sa.Column('risk_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('simulation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('risk_raster', postgresql.JSONB(), comment='Serialized risk grid'),
        sa.Column('extent', postgresql.JSONB(), comment='Risk surface bbox'),
        sa.Column('max_risk', sa.Double(), comment='Max risk value'),
        sa.Column('mean_risk', sa.Double(), comment='Mean risk value (non-zero)'),
        sa.Column('cells_at_risk', sa.BigInteger(), comment='Cells with risk > 0'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['simulation_id'], ['fire_simulations.simulation_id']),
        sa.PrimaryKeyConstraint('risk_id')
    )

    op.create_index('idx_risk_surface_sim', 'risk_surfaces', ['simulation_id'])

    # Exposures table
    op.create_table(
        'exposures',
        sa.Column('exposure_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('simulation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('zone_type', sa.String(32), nullable=False, comment='CURRENT, WARNING, PROJECTION'),
        sa.Column('population_at_risk', sa.BigInteger(), comment='Population count'),
        sa.Column('structures_threatened', sa.BigInteger(), comment='Structure count'),
        sa.Column('infrastructure_affected', postgresql.JSONB(), comment='Infrastructure by type'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['simulation_id'], ['fire_simulations.simulation_id']),
        sa.PrimaryKeyConstraint('exposure_id')
    )

    op.create_index('idx_exposure_sim', 'exposures', ['simulation_id'])
    op.create_index('idx_exposure_zone', 'exposures', ['zone_type'])


def downgrade():
    """Remove Track C tables"""
    op.drop_index('idx_exposure_zone', table_name='exposures')
    op.drop_index('idx_exposure_sim', table_name='exposures')
    op.drop_table('exposures')

    op.drop_index('idx_risk_surface_sim', table_name='risk_surfaces')
    op.drop_table('risk_surfaces')

    op.drop_index('idx_fire_geom_created', table_name='fire_geometries')
    op.drop_index('idx_fire_geom_zone', table_name='fire_geometries')
    op.drop_index('idx_fire_geom_sim', table_name='fire_geometries')
    op.drop_table('fire_geometries')

    op.drop_index('idx_fire_sim_created', table_name='fire_simulations')
    op.drop_index('idx_fire_sim_type', table_name='fire_simulations')
    op.drop_index('idx_fire_sim_incident', table_name='fire_simulations')
    op.drop_table('fire_simulations')
