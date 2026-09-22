"""Repo-relative paths and the threat-intel key, read directly from the environment (and `.env`
at the repo root). This package has no dependency on the backend, so it can't reuse
`app.core.config.Settings` - it loads its own, small subset of the same values.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_REPO_ROOT / ".env")

ML_MODEL_DIR = _REPO_ROOT / "ml" / "models"
KNOWLEDGE_BASE_DIR = _REPO_ROOT / "knowledge-base"

# A separate on-disk index from the backend's `.qdrant`: Qdrant's local mode allows only one
# process per storage path at a time, and this server may run concurrently with the backend (the
# LangChain agent spawns it as a subprocess while the backend's own knowledge_service is live).
# Both processes' content is derived, rebuildable from `knowledge-base/` (ADR-0002), so a second
# copy costs disk space, not correctness. Set QDRANT_URL to point both at one real Qdrant server
# instead, with no code change on either side.
QDRANT_PATH = _REPO_ROOT / ".qdrant-mcp"


def urlhaus_auth_key() -> str | None:
    return os.environ.get("URLHAUS_AUTH_KEY") or None
