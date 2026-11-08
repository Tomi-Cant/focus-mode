"""Adaptive allowance adjustments for accepted usage-limit suggestions."""

from __future__ import annotations

import random


INCREMENTS = (5, 15, 30)


def encouragement(
    *,
    exhausted: bool,
    used_minutes: float,
    allowance_minutes: float,
    attempts: int,
    rng=None,
) -> int:
    """Return a signed allowance change in 5-, 15-, or 30-minute increments."""
    rng = rng or random
    attempts = max(0, int(attempts))
    allowance_minutes = max(0.0, float(allowance_minutes))

    remaining_ratio = (
        max(0.0, allowance_minutes - used_minutes) / allowance_minutes
        if allowance_minutes > 0 else 0.0
    )

    if exhausted or remaining_ratio <= 0:
        available = (15, 30) if attempts >= 20 else (5, 15)
        return -int(rng.choice(available))

    if remaining_ratio >= 0.60:
        return int(rng.choice(INCREMENTS))

    if attempts >= 20:
        return -int(rng.choice((15, 30)))
    if attempts >= 8:
        return -int(rng.choice((5, 15)))
    if attempts > 0:
        return -5

    return int(rng.choice((5, 15)))


def apply_adjustment(
    *,
    allowance_minutes: float,
    window_minutes: int,
    used_minutes: float,
    attempts: int,
    exhausted: bool | None = None,
    floor_minutes: float = 15.0,
    rng=None,
) -> tuple[float | None, int]:
    """Adjust an allowance and report None when it reaches the window."""
    allowance_minutes = float(allowance_minutes)
    if exhausted is None:
        exhausted = used_minutes >= allowance_minutes

    change = encouragement(
        exhausted=exhausted,
        used_minutes=used_minutes,
        allowance_minutes=allowance_minutes,
        attempts=attempts,
        rng=rng,
    )
    adjusted = max(float(floor_minutes), allowance_minutes + change)
    if adjusted >= float(window_minutes):
        return None, change
    return adjusted, change
