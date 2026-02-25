"""sscripts/seed_demo_data.py - Seed one demo tenant + admin + 2 members with profiles.

Usage:
    .venv/Scripts/python.exe scripts/seed_demo_data.py

What it creates (idempotent - safe to run multiple times):
  Tenant  : Nadar Matrimony Centre   (slug: nadar-matrimony)
  Admin   : admin@nadar.local        (role: admin)
  Member1 : arjun@nadar.local        (role: member, male profile)
  Member2 : priya@nadar.local        (role: member, female profile)

Credentials (all passwords):  Demo@1234

After seeding:
  Log in as Super Admin -> GET /admin/tenants         (list of all tenants)
  Log in as Admin       -> GET /users/members         (members of the tenant)
  Log in as Member      -> GET /profiles/me           (own profile)
"""

import asyncio
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

import bcrypt as _bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings

PASSWORD = "Demo@1234"
SEP = "-" * 60


def _hash(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt(rounds=12)).decode()


async def seed() -> None:
    settings = get_settings()
    engine = create_async_engine(str(settings.DATABASE_URL), echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    hashed_pw = _hash(PASSWORD)

    async with Session() as session:
        async with session.begin():

            # 1. Tenant
            row = (await session.execute(
                text("SELECT id FROM tenants WHERE slug = :slug"),
                {"slug": "nadar-matrimony"},
            )).fetchone()

            if row:
                tenant_id = row[0]
                print(f"[seed] Tenant already exists -> id={tenant_id}")
            else:
                row = (await session.execute(
                    text("""
                        INSERT INTO tenants (
                            id, name, slug, contact_email, contact_person,
                            contact_number, whatsapp_number, pin, address,
                            plan, max_users, max_admins, castes, is_active
                        ) VALUES (
                            gen_random_uuid(),
                            'Nadar Matrimony Centre',
                            'nadar-matrimony',
                            'contact@nadarmatrimony.local',
                            'Ravi Kumar',
                            '+919876543210',
                            '+919876543210',
                            '600001',
                            '12, Anna Salai, Chennai, Tamil Nadu',
                            'starter', 500, 5,
                            ARRAY['Nadar'],
                            true
                        ) RETURNING id
                    """),
                )).fetchone()
                tenant_id = row[0]
                print("[seed] Created tenant 'Nadar Matrimony Centre'")

            # 2. Admin user
            exists = (await session.execute(
                text("SELECT 1 FROM users WHERE email = :e"),
                {"e": "admin@nadar.local"},
            )).fetchone()

            if exists:
                print("[seed] Admin already exists -> admin@nadar.local")
            else:
                await session.execute(
                    text("""
                        INSERT INTO users (
                            id, tenant_id, email, hashed_password, full_name,
                            phone, role, is_active, is_verified
                        ) VALUES (
                            gen_random_uuid(), :tid, 'admin@nadar.local', :pwd,
                            'Nadar Admin', '+919876543211', 'admin', true, true
                        )
                    """),
                    {"tid": tenant_id, "pwd": hashed_pw},
                )
                print("[seed] Created admin -> admin@nadar.local")

            # 3. Member 1
            row = (await session.execute(
                text("SELECT id FROM users WHERE email = :e"),
                {"e": "arjun@nadar.local"},
            )).fetchone()

            if row:
                member1_id = row[0]
                print("[seed] Member 1 already exists -> arjun@nadar.local")
            else:
                row = (await session.execute(
                    text("""
                        INSERT INTO users (
                            id, tenant_id, email, hashed_password, full_name,
                            phone, role, is_active, is_verified
                        ) VALUES (
                            gen_random_uuid(), :tid, 'arjun@nadar.local', :pwd,
                            'Arjun Kumar', '+919876543212', 'member', true, true
                        ) RETURNING id
                    """),
                    {"tid": tenant_id, "pwd": hashed_pw},
                )).fetchone()
                member1_id = row[0]
                print("[seed] Created member 1 -> arjun@nadar.local")

            exists = (await session.execute(
                text("SELECT 1 FROM profiles WHERE user_id = :uid"),
                {"uid": member1_id},
            )).fetchone()

            if exists:
                print("[seed] Profile for member 1 already exists")
            else:
                await session.execute(
                    text("""
                        INSERT INTO profiles (
                            id, user_id, tenant_id, gender, date_of_birth,
                            marital_status, height_cm, religion, caste,
                            mother_tongue, city, state, country,
                            profession, status
                        ) VALUES (
                            gen_random_uuid(), :uid, :tid, 'male', :dob,
                            'never_married', 175, 'Hindu', 'Nadar',
                            'Tamil', 'Chennai', 'Tamil Nadu', 'India',
                            'Software Engineer', 'active'
                        )
                    """),
                    {"uid": member1_id, "tid": tenant_id, "dob": date(1995, 6, 14)},
                )
                print("[seed] Created profile for member 1 (Arjun Kumar)")

            # 4. Member 2
            row = (await session.execute(
                text("SELECT id FROM users WHERE email = :e"),
                {"e": "priya@nadar.local"},
            )).fetchone()

            if row:
                member2_id = row[0]
                print("[seed] Member 2 already exists -> priya@nadar.local")
            else:
                row = (await session.execute(
                    text("""
                        INSERT INTO users (
                            id, tenant_id, email, hashed_password, full_name,
                            phone, role, is_active, is_verified
                        ) VALUES (
                            gen_random_uuid(), :tid, 'priya@nadar.local', :pwd,
                            'Priya Selvam', '+919876543213', 'member', true, true
                        ) RETURNING id
                    """),
                    {"tid": tenant_id, "pwd": hashed_pw},
                )).fetchone()
                member2_id = row[0]
                print("[seed] Created member 2 -> priya@nadar.local")

            exists = (await session.execute(
                text("SELECT 1 FROM profiles WHERE user_id = :uid"),
                {"uid": member2_id},
            )).fetchone()

            if exists:
                print("[seed] Profile for member 2 already exists")
            else:
                await session.execute(
                    text("""
                        INSERT INTO profiles (
                            id, user_id, tenant_id, gender, date_of_birth,
                            marital_status, height_cm, religion, caste,
                            mother_tongue, city, state, country,
                            profession, status
                        ) VALUES (
                            gen_random_uuid(), :uid, :tid, 'female', :dob,
                            'never_married', 162, 'Hindu', 'Nadar',
                            'Tamil', 'Madurai', 'Tamil Nadu', 'India',
                            'Teacher', 'active'
                        )
                    """),
                    {"uid": member2_id, "tid": tenant_id, "dob": date(1998, 3, 22)},
                )
                print("[seed] Created profile for member 2 (Priya Selvam)")

    await engine.dispose()

    print()
    print(SEP)
    print("  DEMO SEED COMPLETE")
    print(SEP)
    print(f"  All demo passwords : {PASSWORD}")
    print(SEP)
    print("  [SUPER ADMIN]")
    print("    Email    : admin@varanbook.local")
    print("    Password : Admin@1234  (or SUPERADMIN_PASSWORD env var)")
    print("    Access   : GET /admin/tenants   -> list all tenants")
    print(SEP)
    print("  [TENANT ADMIN]")
    print("    Email    : admin@nadar.local")
    print(f"    Password : {PASSWORD}")
    print("    Tenant   : Nadar Matrimony Centre")
    print("    Access   : GET /users/members   -> list tenant members")
    print(SEP)
    print("  [MEMBER 1]")
    print("    Email    : arjun@nadar.local")
    print("    Name     : Arjun Kumar  (male, Chennai)")
    print(f"    Password : {PASSWORD}")
    print("    Access   : GET /profiles/me     -> own profile")
    print(SEP)
    print("  [MEMBER 2]")
    print("    Email    : priya@nadar.local")
    print("    Name     : Priya Selvam  (female, Madurai)")
    print(f"    Password : {PASSWORD}")
    print("    Access   : GET /profiles/me     -> own profile")
    print(SEP)
    print("  Login -> POST /auth/login")
    print("  Docs  -> http://localhost:8000/docs")
    print(SEP)
int(f"    Name     : {MEMBER2_USER['full_name']}")
    print(f"    Password : {PASSWORD}")
    print(f"    Access   : GET /profiles/me    → own profile")
    print(SEPARATOR)
    print(f"  Login → POST /auth/login")
    print(f"  Docs  → http://localhost:8000/docs")
    print(SEPARATOR)
int(f"    Name     : {MEMBER2_USER['full_name']}")
    print(f"    Password : {PASSWORD}")
    print(f"    Access   : GET /profiles/me    → own profile")
    print(SEPARATOR)
    print(f"  Login → POST /auth/login")
    print(f"  Docs  → http://localhost:8000/docs")
    print(SEPARATOR)


if __name__ == "__main__":
    asyncio.run(seed())
