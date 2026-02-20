"""Centralised prompt loader with hot-reload support.

All system prompts flow through this module.  Call ``reload()`` to re-read
every prompt from disk without restarting the process.
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PERSONALITY_PATH = _PROJECT_ROOT / "PERSONALITY.md"
_PROMPTS_DIR = _PROJECT_ROOT / "prompts"

_cache: dict[str, str] = {}


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def reload() -> list[str]:
    """Clear cache and re-read all prompt files from disk.

    Returns a list of human-readable names of everything that was loaded.
    """
    _cache.clear()
    loaded: list[str] = []

    personality()
    loaded.append("PERSONALITY.md")

    if _PROMPTS_DIR.is_dir():
        for p in sorted(_PROMPTS_DIR.glob("*.md")):
            key = f"agent:{p.stem}"
            _cache[key] = p.read_text(encoding="utf-8").strip()
            loaded.append(f"prompts/{p.name}")
            log.debug("loaded prompt override: %s -> %s", key, p)

    return loaded


def personality() -> str:
    """Return the contents of PERSONALITY.md (cached until ``reload()``)."""
    if "personality" not in _cache:
        try:
            _cache["personality"] = _PERSONALITY_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            log.warning("PERSONALITY.md not found at %s", _PERSONALITY_PATH)
            _cache["personality"] = (
                "You are Broke, Jonathan Caudill's portfolio agent. "
                "Be sharp, helpful, and genuine."
            )
    return _cache["personality"]


def agent_prompt(name: str, default: str) -> str:
    """Return an agent's system prompt.

    If ``prompts/{name}.md`` exists on disk it takes precedence over
    *default* (the hardcoded fallback baked into the agent class).
    """
    key = f"agent:{name}"
    if key not in _cache:
        path = _PROMPTS_DIR / f"{name}.md"
        if path.exists():
            _cache[key] = path.read_text(encoding="utf-8").strip()
            log.debug("loaded agent prompt from file: %s", path)
        else:
            _cache[key] = default
    return _cache[key]
