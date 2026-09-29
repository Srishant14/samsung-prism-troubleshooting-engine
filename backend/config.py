import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", None)
CONFIDENCE_THRESHOLD = 0.6

# ── Performance tuning ─────────────────────────────────────────
# Fast-path confidence gate: if the LLM/keyword classifier returns
# confidence >= this AND the KB has an exact record, skip Laya entirely.
FAST_PATH_CONFIDENCE = float(os.getenv("FAST_PATH_CONFIDENCE", "0.85"))

# LLM request timeout in seconds
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "10.0"))

# Supabase query timeout in seconds
SUPABASE_TIMEOUT = float(os.getenv("SUPABASE_TIMEOUT", "5.0"))
