"""Shared retry wrapper for Groq calls — handles 429 TPM rate limits."""
import re
import time
import random

from groq import RateLimitError


def invoke_with_retry(llm, prompt: str, max_retries: int = 5):
    for attempt in range(max_retries):
        try:
            return llm.invoke(prompt)
        except RateLimitError as e:
            wait = _extract_wait_seconds(str(e)) or (2 ** attempt + random.uniform(0, 1))
            if attempt == max_retries - 1:
                raise
            print(f"[llm_retry] Groq 429, retrying in {wait:.1f}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait + 0.5)


def _extract_wait_seconds(msg: str):
    m = re.search(r"try again in ([\d.]+)s", msg)
    return float(m.group(1)) if m else None
