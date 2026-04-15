"""
Pre-flight check — run this BEFORE alembic upgrade head or python run.py

    python check_setup.py

Checks:
  1. .env file exists
  2. DATABASE_URL points to Supabase (not a placeholder)
  3. GROQ_API_KEY is set and model is not decommissioned
  4. PINECONE_API_KEY is set
  5. RAPIDAPI_KEY is set
  6. Supabase database connection is reachable
"""

import asyncio
import os
import re
import sys


def ok(label):
    print(f"  ✅  {label}")

def fail(label, fix):
    print(f"  ❌  {label}")
    for line in fix.strip().split("\n"):
        print(f"      {line}")
    print()

def warn(label, tip):
    print(f"  ⚠️   {label}")
    for line in tip.strip().split("\n"):
        print(f"      {line}")

# ── 1. .env file ──────────────────────────────────────────────────────────────
print("\n── Step 1: Checking .env file ───────────────────────────────")
if not os.path.exists(".env"):
    fail(".env not found",
         "Run:  copy .env.example .env   (Windows)\n"
         "      cp .env.example .env     (Mac/Linux)\n"
         "Then fill in your Supabase URL and API keys.")
    sys.exit(1)
ok(".env file found")

from dotenv import load_dotenv
load_dotenv(override=True)

# ── 2. DATABASE_URL → must be Supabase ───────────────────────────────────────
print("\n── Step 2: Checking Supabase DATABASE_URL ───────────────────")
db_url = os.getenv("DATABASE_URL", "")

PLACEHOLDER_FRAGMENTS = [
    "YOUR_SUPABASE_DB_PASSWORD",
    "YOUR_PROJECT_REF",
    "[YOUR-PASSWORD]",
    "user:pass@",
    "localhost",
    "<<<",
]

db_is_placeholder = any(f in db_url for f in PLACEHOLDER_FRAGMENTS)
db_is_supabase    = "supabase.co" in db_url or "pooler.supabase.com" in db_url
db_has_asyncpg    = "postgresql+asyncpg://" in db_url

if not db_url or db_is_placeholder:
    fail("DATABASE_URL is a placeholder",
         "Go to: https://supabase.com → Your Project → Settings → Database → URI\n"
         "Copy the URI, change  postgresql://  →  postgresql+asyncpg://\n"
         "Paste into .env as DATABASE_URL=postgresql+asyncpg://postgres:PASS@db.XXX.supabase.co:5432/postgres")
    sys.exit(1)

if not db_is_supabase:
    fail("DATABASE_URL does not point to Supabase",
         "This project uses Supabase as the database.\n"
         "The URL must contain  supabase.co  or  pooler.supabase.com\n"
         "Get it from: Supabase dashboard → Settings → Database → URI")
    sys.exit(1)

if not db_has_asyncpg:
    fail("DATABASE_URL must use  postgresql+asyncpg://  not  postgresql://",
         "Change the scheme in your .env:\n"
         "  FROM:  postgresql://postgres:PASS@db.XXX.supabase.co:5432/postgres\n"
         "  TO:    postgresql+asyncpg://postgres:PASS@db.XXX.supabase.co:5432/postgres")
    sys.exit(1)

safe_url = re.sub(r":([^@]+)@", ":***@", db_url)
ok(f"DATABASE_URL → Supabase  ({safe_url[:65]})")

# ── 3. GROQ_API_KEY + model ───────────────────────────────────────────────────
print("\n── Step 3: Checking Groq ────────────────────────────────────")
groq_key   = os.getenv("GROQ_API_KEY", "")
groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
DECOMMISSIONED = ["llama3-70b-8192", "llama2-70b-4096", "gemma-7b-it"]

if not groq_key or any(x in groq_key for x in ["<<<", "YOUR_", "PASTE_", "FILL"]):
    fail("GROQ_API_KEY not set",
         "Get free key: https://console.groq.com → API Keys → Create API Key\n"
         "Set in .env: GROQ_API_KEY=gsk_...")
    sys.exit(1)
ok(f"GROQ_API_KEY set")

if groq_model in DECOMMISSIONED:
    fail(f"GROQ_MODEL={groq_model} is DECOMMISSIONED",
         "Set in .env: GROQ_MODEL=llama-3.3-70b-versatile\n"
         "Or:          GROQ_MODEL=llama-3.1-8b-instant\n"
         "See current models: https://console.groq.com/docs/models")
    sys.exit(1)
ok(f"GROQ_MODEL={groq_model} (current)")

# ── 4. PINECONE_API_KEY ───────────────────────────────────────────────────────
print("\n── Step 4: Checking Pinecone ────────────────────────────────")
pc_key = os.getenv("PINECONE_API_KEY", "")
if not pc_key or any(x in pc_key for x in ["<<<", "YOUR_", "PASTE_", "FILL"]):
    warn("PINECONE_API_KEY not set — RAG will use local dataset fallback",
         "Get free key: https://app.pinecone.io → API Keys\n"
         "Set in .env: PINECONE_API_KEY=...")
else:
    ok("PINECONE_API_KEY set")

# ── 5. RAPIDAPI_KEY ───────────────────────────────────────────────────────────
print("\n── Step 5: Checking RapidAPI ────────────────────────────────")
rapid_key = os.getenv("RAPIDAPI_KEY", "")
if not rapid_key or any(x in rapid_key for x in ["<<<", "YOUR_", "PASTE_", "FILL"]):
    warn("RAPIDAPI_KEY not set — live hotels/attractions disabled, local dataset used",
         "Get free key: https://rapidapi.com\n"
         "Subscribe to: Travel Advisor + Booking.com (both free 500 req/month)\n"
         "Set in .env: RAPIDAPI_KEY=...")
else:
    ok("RAPIDAPI_KEY set")

# ── 6. Supabase DB connectivity ───────────────────────────────────────────────
print("\n── Step 6: Testing Supabase connection ──────────────────────")

async def _test():
    try:
        import asyncpg
        dsn = db_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(dsn=dsn, timeout=15, ssl="require")
        ver  = await conn.fetchval("SELECT version()")
        await conn.close()
        return True, str(ver)[:70]
    except Exception as e:
        return False, str(e)

connected, detail = asyncio.run(_test())
if connected:
    ok(f"Supabase connected  →  {detail}")
else:
    fail("Supabase connection failed",
         f"Error: {detail}\n"
         "Check:\n"
         "  • Password in DATABASE_URL is correct (no special chars unescaped)\n"
         "  • Project ref in URL matches your Supabase project\n"
         "  • Your Supabase project is not paused (free tier pauses after 1 week idle)\n"
         "    → Go to https://supabase.com → your project → click 'Restore project'\n"
         "  • Your network allows outbound connections to port 5432")
    sys.exit(1)

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n─────────────────────────────────────────────────────────────")
print("  🎉  All critical checks passed!\n")
print("  Next steps:")
print("    1.  alembic upgrade head     ← creates tables in Supabase")
print("    2.  python run.py            ← starts the server")
print("    3.  http://localhost:8000/docs\n")
