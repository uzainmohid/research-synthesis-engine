"""
Config loader — reads secrets from a local .env file so the API key
never gets hardcoded or committed to GitHub.
"""

import os

def load_env(path: str = ".env"):
    """Minimal .env loader — no extra dependency needed."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

load_env()

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-v4-flash"  # current DeepSeek Flash model ID (as of July 2026)
