"""Apply Track C migration 003 to PostgreSQL database

Executes the Track C migration SQL directly against the database.
"""
import asyncio
import asyncpg
from db.migrations_003_track_c import upgrade, downgrade


async def apply_migration():
    """Apply Track C migration to database"""

    # Connect to database
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="nexalert",
        password="nexalert_dev_password",
        database="nexalert_dev"
    )

    try:
        print("Connected to PostgreSQL database: nexalert_dev")

        # Check existing tables
        print("\nExisting tables:")
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        for table in tables:
            print(f"  - {table['tablename']}")

        # Check if Track C tables already exist
        track_c_tables = await conn.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename IN ('fire_simulations', 'fire_geometries', 'risk_surfaces', 'exposures')
        """)

        if track_c_tables:
            print(f"\n⚠ Track C tables already exist: {[t['tablename'] for t in track_c_tables]}")
            print("Migration may have already been applied.")
            return

        print("\n✓ No Track C tables found. Proceeding with migration...")

        # Since we can't use Alembic op, execute SQL directly
        # Create fire_simulations table
        await conn.execute("""
            CREATE TABLE fire_simulations (
                simulation_id UUID PRIMARY KEY,
                incident_id UUID REFERENCES incidents(incident_id),
                simulation_type VARCHAR(32) NOT NULL,
                ignition_lat DOUBLE PRECISION NOT NULL,
                ignition_lon DOUBLE PRECISION NOT NULL,
                ignition_time TIMESTAMP WITH TIME ZONE NOT NULL,
                simulation_time TIMESTAMP WITH TIME ZONE NOT NULL,
                environmental_state JSONB,
                domain_extent JSONB,
                crs_id VARCHAR(64),
                resolution_m DOUBLE PRECISION,
                max_time_minutes DOUBLE PRECISION,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            )
        """)
        print("✓ Created fire_simulations table")

        # Create indexes for fire_simulations
        await conn.execute("CREATE INDEX idx_fire_sim_incident ON fire_simulations(incident_id)")
        await conn.execute("CREATE INDEX idx_fire_sim_type ON fire_simulations(simulation_type)")
        await conn.execute("CREATE INDEX idx_fire_sim_created ON fire_simulations(created_at)")
        print("✓ Created fire_simulations indexes")

        # Create fire_geometries table with PostGIS
        await conn.execute("""
            CREATE TABLE fire_geometries (
                geometry_id BIGSERIAL PRIMARY KEY,
                simulation_id UUID NOT NULL REFERENCES fire_simulations(simulation_id),
                zone_type VARCHAR(32) NOT NULL,
                geometry GEOGRAPHY(GEOMETRY, 4326) NOT NULL,
                physical_footprint GEOGRAPHY(GEOMETRY, 4326),
                operational_buffer GEOGRAPHY(GEOMETRY, 4326),
                area_hectares DOUBLE PRECISION,
                perimeter_m DOUBLE PRECISION,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            )
        """)
        print("✓ Created fire_geometries table")

        # Create indexes for fire_geometries
        await conn.execute("CREATE INDEX idx_fire_geom_sim ON fire_geometries(simulation_id)")
        await conn.execute("CREATE INDEX idx_fire_geom_zone ON fire_geometries(zone_type)")
        await conn.execute("CREATE INDEX idx_fire_geom_created ON fire_geometries(created_at)")
        print("✓ Created fire_geometries indexes")

        # Create risk_surfaces table
        await conn.execute("""
            CREATE TABLE risk_surfaces (
                risk_id BIGSERIAL PRIMARY KEY,
                simulation_id UUID NOT NULL REFERENCES fire_simulations(simulation_id),
                risk_raster JSONB,
                extent JSONB,
                max_risk DOUBLE PRECISION,
                mean_risk DOUBLE PRECISION,
                cells_at_risk BIGINT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            )
        """)
        print("✓ Created risk_surfaces table")

        # Create index for risk_surfaces
        await conn.execute("CREATE INDEX idx_risk_surface_sim ON risk_surfaces(simulation_id)")
        print("✓ Created risk_surfaces indexes")

        # Create exposures table
        await conn.execute("""
            CREATE TABLE exposures (
                exposure_id BIGSERIAL PRIMARY KEY,
                simulation_id UUID NOT NULL REFERENCES fire_simulations(simulation_id),
                zone_type VARCHAR(32) NOT NULL,
                population_at_risk BIGINT,
                structures_threatened BIGINT,
                infrastructure_affected JSONB,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            )
        """)
        print("✓ Created exposures table")

        # Create indexes for exposures
        await conn.execute("CREATE INDEX idx_exposure_sim ON exposures(simulation_id)")
        await conn.execute("CREATE INDEX idx_exposure_zone ON exposures(zone_type)")
        print("✓ Created exposures indexes")

        print("\n✅ Track C migration 003 applied successfully!")

        # Verify all 4 tables exist
        print("\nVerifying Track C tables:")
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename IN ('fire_simulations', 'fire_geometries', 'risk_surfaces', 'exposures')
            ORDER BY tablename
        """)

        for table in tables:
            print(f"  ✓ {table['tablename']}")

        if len(tables) == 4:
            print("\n✅ All 4 Track C tables verified!")
        else:
            print(f"\n⚠ Expected 4 tables, found {len(tables)}")

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        raise
    finally:
        await conn.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    asyncio.run(apply_migration())
