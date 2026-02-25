"""
scripts/seed_superadmin.py – Create (or reset) the platform super-admin user.

Usage:
    .venv\Scripts\python.exe scripts/seed_superadmin.py

Environment variables (read from .env):
    SUPERADMIN_EMAIL    – defaults to admin@varanbook.local
    SUPERADMIN_PASSWORD – defaults to Admin@1234 (CHANGE in prod!)
    DATABASE_URL        – same as the app uses
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path

# Allow importing app modules from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

import bcrypt as _bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings


def _hash(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt(rounds=12)).decode()

SUPERADMIN_EMAIL    = os.getenv("SUPERADMIN_EMAIL", "admin@varanbook.local")
SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD", "Admin@1234")
SUPERADMIN_NAME     = os.getenv("SUPERADMIN_NAME", "Platform Super Admin")


async def seed() -> None:
    settings = get_settings()
    engine = create_async_engine(str(settings.DATABASE_URL), echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    hashed = _hash(SUPERADMIN_PASSWORD)
    email  = SUPERADMIN_EMAIL.lower()

    async with Session() as session:
        async with session.begin():
            await session.execute(
                text("""
                    INSERT INTO users (id, tenant_id, email, hashed_password, full_name,
                                       role, is_active, is_verified)
                    VALUES (gen_random_uuid(), NULL, :email, :pwd, :name,
                            'super_admin', true, true)
                    ON CONFLICT (email) DO UPDATE
                        SET hashed_password = EXCLUDED.hashed_password,
                            role            = 'super_admin',
                            is_active       = true,
                            is_verified     = true
                """),
                {"email": email, "pwd": hashed, "name": SUPERADMIN_NAME},
            )

    await engine.dispose()

    action = "Created/updated"
    print(f"[seed] {action} super-admin: {email}")
    print()
    print("─" * 50)
    print(f"  Email    : {email}")
    print(f"  Password : {SUPERADMIN_PASSWORD}")
    print(f"  Role     : super_admin")
    print("─" * 50)
    print("  Login →  POST /auth/login")
    print("  Docs  →  http://localhost:8000/docs")
    print("─" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
