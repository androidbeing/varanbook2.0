import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv; load_dotenv()
from app.config import get_settings
import asyncpg

async def check():
    s = get_settings()
    url = str(s.DATABASE_URL).replace("postgresql+asyncpg", "postgresql")
    conn = await asyncpg.connect(url)

    pp_cols = await conn.fetch(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name = 'partner_preferences' ORDER BY ordinal_position"
    )
    print("partner_preferences columns:")
    for r in pp_cols:
        print(f"  {r['column_name']}: {r['data_type']}")

    pc = await conn.fetch(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name='profiles' AND column_name IN "
        "('qualification','income_range','rashi','star','dhosam') ORDER BY column_name"
    )
    print("\nprofiles converted cols:")
    for r in pc:
        print(f"  {r['column_name']}: {r['data_type']}")

    await conn.close()

asyncio.run(check())
