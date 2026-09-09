"""Test database connection and verify Track C tables"""
import asyncio
import asyncpg


async def test_connection():
    """Test connection to PostgreSQL and query Track C tables"""
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="nexalert",
            password="nexalert_dev_password",
            database="nexalert_dev"
        )

        print("✓ Connected to PostgreSQL database: nexalert_dev")

        # Query Track C tables
        tables = ["fire_simulations", "fire_geometries", "risk_surfaces", "exposures"]

        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"  ✓ {table}: {count} rows")

        await conn.close()
        print("\n✅ Database connection test successful!")

    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(test_connection())
