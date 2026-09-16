"""Verify Phase 2C-3C Migration 004 database schema"""
import asyncio
import asyncpg


async def verify_schema():
    """Verify post-migration schema matches SQLAlchemy model"""

    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="nexalert_test"
    )

    try:
        print("=" * 70)
        print("Phase 2C-3C Migration 004: Schema Verification")
        print("=" * 70)

        # 1. Verify incidents table structure
        print("\n=== Incidents Table Verification ===")
        incidents_cols = await conn.fetch("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'incidents'
            ORDER BY ordinal_position
        """)

        incident_columns = [col['column_name'] for col in incidents_cols]
        print(f"[OK] Incidents table has {len(incident_columns)} columns")

        # Check legacy columns are absent
        legacy = ['hazard_type', 'severity_index', 'risk_index', 'confidence_index']
        found_legacy = [c for c in legacy if c in incident_columns]

        if found_legacy:
            print(f"[ERROR] Legacy columns still exist: {found_legacy}")
            return False
        else:
            print("[OK] No legacy columns found")

        # 2. Verify IncidentHazardAssessment table exists and has correct structure
        print("\n=== IncidentHazardAssessment Table Verification ===")
        iha_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'incident_hazard_assessments'
            )
        """)

        if not iha_exists:
            print("[ERROR] incident_hazard_assessments table not found")
            return False

        print("[OK] incident_hazard_assessments table exists")

        iha_cols = await conn.fetch("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'incident_hazard_assessments'
            ORDER BY ordinal_position
        """)

        iha_columns = [col['column_name'] for col in iha_cols]
        required_iha_cols = ['assessment_id', 'incident_id', 'hazard_type', 'evidence',
                             'confidence', 'severity', 'operational_risk', 'state']

        missing_cols = [c for c in required_iha_cols if c not in iha_columns]
        if missing_cols:
            print(f"[ERROR] Missing columns in incident_hazard_assessments: {missing_cols}")
            return False

        print(f"[OK] incident_hazard_assessments has all required columns")

        # 3. Verify indexes
        print("\n=== Index Verification ===")
        indexes = await conn.fetch("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'incidents'
            ORDER BY indexname
        """)

        index_names = [idx['indexname'] for idx in indexes]

        # Check legacy index is gone
        if 'idx_incidents_hazard_state' in index_names:
            print("[ERROR] Legacy index idx_incidents_hazard_state still exists")
            return False
        else:
            print("[OK] Legacy index idx_incidents_hazard_state removed")

        # Check new state index exists
        if 'idx_incidents_state' in index_names:
            print("[OK] New index idx_incidents_state exists")
        else:
            print("[ERROR] New index idx_incidents_state not found")
            return False

        # 4. Verify foreign key relationship intact
        print("\n=== Foreign Key Verification ===")
        fk_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_name = 'incident_hazard_assessments'
                AND constraint_type = 'FOREIGN KEY'
            )
        """)

        if fk_exists:
            print("[OK] Foreign key constraint exists on incident_hazard_assessments")
        else:
            print("[WARN] No foreign key constraint found (may be expected)")

        print("\n" + "=" * 70)
        print("[SUCCESS] Phase 2C-3C Migration 004: Schema verification PASSED")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n[ERROR] Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await conn.close()


if __name__ == "__main__":
    result = asyncio.run(verify_schema())
    exit(0 if result else 1)
