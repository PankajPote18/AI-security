"""Shannon entropy of a string, used as a randomness signal (DGA-style hosts, encoded paths)."""

from __future__ import annotations

import math
from collections import Counter


def shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    length = len(text)
    return -sum((n / length) * math.log2(n / length) for n in counts.values())
