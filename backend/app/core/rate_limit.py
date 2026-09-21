"""In-memory rate limiting (single-worker; revisit with a Redis backend if the app ever runs
multiple workers - see the project plan's Redis decision)."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
