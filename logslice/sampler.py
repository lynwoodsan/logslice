"""Line sampling for large log files — emit every Nth line or a random fraction."""

import random
from typing import Iterable, Iterator, Tuple


class Sampler:
    """Emit a deterministic or random subset of log lines."""

    def __init__(self, every_n: int = 1, fraction: float = 1.0, seed: int | None = None):
        if every_n < 1:
            raise ValueError("every_n must be >= 1")
        if not (0.0 < fraction <= 1.0):
            raise ValueError("fraction must be in the range (0.0, 1.0]")

        self.every_n = every_n
        self.fraction = fraction
        self._rng = random.Random(seed)

        self.total = 0
        self.emitted = 0

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def should_emit(self) -> bool:
        """Return True if the *next* line should be emitted."""
        self.total += 1
        if self.every_n > 1 and (self.total % self.every_n) != 1:
            return False
        if self.fraction < 1.0 and self._rng.random() > self.fraction:
            return False
        self.emitted += 1
        return True

    def feed(
        self, lines: Iterable[Tuple[str, bool]]
    ) -> Iterator[Tuple[str, bool]]:
        """Filter *(line, is_match)* pairs according to sampling settings.

        Only matched lines are subject to sampling; context / non-matched
        lines are passed through unchanged so surrounding context is kept.
        """
        for line, is_match in lines:
            if not is_match:
                yield line, is_match
                continue
            if self.should_emit():
                yield line, is_match

    @property
    def drop_rate(self) -> float:
        """Fraction of lines that were dropped (0.0 – 1.0)."""
        if self.total == 0:
            return 0.0
        return 1.0 - self.emitted / self.total

    def format_report(self) -> str:
        return (
            f"Sampler: {self.emitted}/{self.total} lines emitted "
            f"(drop rate {self.drop_rate:.1%})"
        )
