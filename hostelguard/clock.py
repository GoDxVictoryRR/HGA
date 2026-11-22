"""
hostelguard/clock.py
A tiny clock helper used throughout the project.

All time-dependent logic (timestamps, token expiry, replay windows, rate
limits, lockouts) calls the clock instead of time.time() directly.  In tests
a FakeClock lets us advance time without sleeping, keeping tests fast and
deterministic.
"""

import time


class Clock:
    """Real-time clock.  Returns the actual system UNIX timestamp."""

    def now(self) -> float:
        """Return the current UNIX timestamp as a float."""
        return time.time()


class FakeClock:
    """Controllable clock for tests.

    Start at a fixed epoch so tests do not depend on the wall clock.
    Call advance() to move time forward by an exact number of seconds.
    """

    def __init__(self, start: float = 1_000_000.0) -> None:
        self._current = start

    def now(self) -> float:
        """Return the current fake timestamp."""
        return self._current

    def advance(self, seconds: float) -> None:
        """Move the clock forward by the given number of seconds."""
        self._current += seconds

    def set(self, timestamp: float) -> None:
        """Jump the clock to an absolute timestamp."""
        self._current = timestamp
