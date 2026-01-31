from __future__ import annotations

import time
import threading
from typing import Dict, List, Tuple

_LOCK = threading.Lock()
_HITS: Dict[str, List[float]] = {}


def check_rate_limit(key: str, *, max_requests: int, window_sec: int) -> Tuple[bool, float]:
    """Sliding-window rate limit.

    Returns (allowed, retry_after_seconds).
    """
    if max_requests <= 0 or window_sec <= 0:
        return True, 0.0

    now = time.time()
    with _LOCK:
        hits = _HITS.get(key, [])
        cutoff = now - float(window_sec)
        hits = [t for t in hits if t >= cutoff]

        if len(hits) >= int(max_requests):
            retry_after = float(window_sec) - (now - hits[0])
            _HITS[key] = hits
            return False, max(0.0, retry_after)

        hits.append(now)
        _HITS[key] = hits
        return True, 0.0


def reset_rate_limits() -> None:
    with _LOCK:
        _HITS.clear()
