"""Apply Phase 2C-3C Migration 004 to PostgreSQL database

Executes the Phase 2C-3C legacy cleanup migration that removes Incident-level
hazard scalar fields after full migration to canonical IncidentHazardAssessment model.
"""
import asyncio
import asyncpg
import sys


async def apply_migration():
    """Apply Phase 2C-3C migration 004 to database"""

    # Connect to test database (nexalert_test from Phase 2C-3A setup)
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="nexalert_test"
        )
    except Exception as e:
        print(f"\nERROR: Database connection failed: {str(e)}")
        print("\nEnsure PostgreSQL is running:")
        print("  docker ps  # Check if nexalert-postgres container is running")
        print("  docker start nexalert-postgres  # Start if needed")
        sys.exit(1)

    try:
        print("[OK] Connected to PostgreSQL database: nexalert_test")

        # Check existing incidents table structure
        print("\n=== Current incidents table columns ===")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'incidents'
            ORDER BY ordinal_position
        """)

        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else 'NOT NULL'
            print(f"  - {col['column_name']} ({col['data_type']}, {nullable})")

        # Check if legacy columns exist
        legacy_columns = [col['column_name'] for col in columns if col['column_name'] in ['hazard_type', 'severity_index', 'risk_index', 'confidence_index']]

        if not legacy_columns:
            print(f"\n[WARN] Legacy columns not found. Migration may have already been applied.")
            print("Current state matches Phase 2C-3C target schema.")
            return

        print(f"\n[OK] Legacy columns found: {legacy_columns}")

        # Check existing indexes
        print("\n=== Current incidents table indexes ===")
        indexes = await conn.fetch("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = 'incidents'
            ORDER BY indexname
        """)

        for idx in indexes:
            print(f"  - {idx['indexname']}")

        # Execute migration
        print("\n=== Executing Phase 2C-3C Migration 004 ===")

        # Step 1: Drop index that references hazard_type
        legacy_index_exists = any(idx['indexname'] == 'idx_incidents_hazard_state' for idx in indexes)
        if legacy_index_exists:
            print("  1. Dropping index idx_incidents_hazard_state...")
            await conn.execute("DROP INDEX IF EXISTS idx_incidents_hazard_state")
            print("     [OK] Index dropped")
        else:
            print("  1. Index idx_incidents_hazard_state not found (skip)")

        # Step 2: Drop legacy columns
        print("  2. Dropping legacy columns...")
        for col_name in ['hazard_type', 'severity_index', 'risk_index', 'confidence_index']:
            if col_name in legacy_columns:
                await conn.execute(f"ALTER TABLE incidents DROP COLUMN IF EXISTS {col_name}")
                print(f"     [OK] Dropped {col_name}")
            else:
                print(f"     - {col_name} not found (skip)")

        # Step 3: Add new state index
        state_index_exists = any(idx['indexname'] == 'idx_incidents_state' for idx in indexes)
        if not state_index_exists:
            print("  3. Creating index idx_incidents_state...")
            await conn.execute("CREATE INDEX idx_incidents_state ON incidents(state)")
            print("     [OK] Index created")
        else:
            print("  3. Index idx_incidents_state already exists (skip)")

        print("\n[SUCCESS] Migration 004 completed successfully")

        # Verify final schema
        print("\n=== Final incidents table columns ===")
        final_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'incidents'
            ORDER BY ordinal_position
        """)

        for col in final_columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else 'NOT NULL'
            print(f"  - {col['column_name']} ({col['data_type']}, {nullable})")

        # Verify legacy columns are gone
        remaining_legacy = [col['column_name'] for col in final_columns if col['column_name'] in ['hazard_type', 'severity_index', 'risk_index', 'confidence_index']]
        if remaining_legacy:
            print(f"\n[ERROR] Legacy columns still exist: {remaining_legacy}")
            sys.exit(1)
        else:
            print("\n[OK] Verified: All legacy columns removed")

        # Verify IncidentHazardAssessment table still exists
        print("\n=== Verifying IncidentHazardAssessment table ===")
        iha_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'incident_hazard_assessments'
            )
        """)

        if iha_exists:
            print("  [OK] incident_hazard_assessments table exists")

            # Check row count
            iha_count = await conn.fetchval("SELECT COUNT(*) FROM incident_hazard_assessments")
            print(f"  [OK] Contains {iha_count} hazard assessments")
        else:
            print("  [ERROR] incident_hazard_assessments table not found")
            sys.exit(1)

        print("\n[SUCCESS] Phase 2C-3C Migration 004: VERIFIED COMPLETE")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await conn.close()
        print("\n[OK] Database connection closed")


if __name__ == "__main__":
    print("=" * 70)
    print("Phase 2C-3C Migration 004: Legacy Cleanup")
    print("=" * 70)

    asyncio.run(apply_migration())
