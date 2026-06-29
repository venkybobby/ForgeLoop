"""ratelimit — a tiny fixed-window limiter for expensive endpoints.

Per (user, action) fixed window of one minute, in-memory (resets on restart —
fine for a single-process MVP). Disable by setting FORGELOOP_RATE_PER_MIN=0.
"""

from __future__ import annotations

import os
import threading
import time

_LOCK = threading.Lock()
_HITS: dict[tuple, int] = {}


def per_min() -> int:
    try:
        return int(os.environ.get("FORGELOOP_RATE_PER_MIN", "30"))
    except ValueError:
        return 30


def allow(key: str) -> bool:
    """True if this call is within the limit; False if it should be rejected (429)."""
    limit = per_min()
    if limit <= 0:
        return True
    window = int(time.time() // 60)
    with _LOCK:
        # opportunistic cleanup of stale windows
        for k in [k for k in _HITS if k[1] < window - 1]:
            del _HITS[k]
        slot = (key, window)
        _HITS[slot] = _HITS.get(slot, 0) + 1
        return _HITS[slot] <= limit
