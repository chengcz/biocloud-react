"""Initialize VEP service database tables.

Usage:
    python init_db.py

This script creates all tables defined in the models package.
Safe to run multiple times (idempotent - uses CREATE TABLE IF NOT EXISTS).

Requires:
    - PostgreSQL running and accessible via DATABASE_URL env var
    - Dependencies installed (pip install -r requirements.txt)
"""
import sys
import asyncio


import dotenv
dotenv.load_dotenv()

from config.database import engine, Base
import models.annotation  # noqa: F401
import models.task        # noqa: F401


async def main():
    print("Initializing VEP service database...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully.")
    except Exception as e:
        print(f"ERROR: Database initialization failed: {e}")
        print(f"Check DATABASE_URL: {engine.url}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
