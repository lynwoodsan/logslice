"""Line truncation utility for logslice.

Truncates long log lines to a maximum length, optionally appending
a configurable suffix to indicate truncation occurred.
"""

DEFAULT_MAX_LENGTH = 200
DEFAULT_SUFFIX = "..."


class Truncator:
    """Truncates lines that exceed a maximum character length."""

    def __init__(self, max_length: int = DEFAULT_MAX_LENGTH, suffix: str = DEFAULT_SUFFIX):
        if max_length < 1:
            raise ValueError(f"max_length must be at least 1, got {max_length}")
        if len(suffix) >= max_length:
            raise ValueError(
                f"suffix length ({len(suffix)}) must be less than max_length ({max_length})"
            )
        self.max_length = max_length
        self.suffix = suffix
        self._truncated_count = 0
        self._total_count = 0

    def truncate(self, line: str) -> str:
        """Return the line, truncated if it exceeds max_length."""
        self._total_count += 1
        if len(line) <= self.max_length:
            return line
        self._truncated_count += 1
        cut = self.max_length - len(self.suffix)
        return line[:cut] + self.suffix

    def feed(self, line: str) -> str:
        """Alias for truncate; used for pipeline compatibility."""
        return self.truncate(line)

    @property
    def truncated_count(self) -> int:
        """Number of lines that were truncated."""
        return self._truncated_count

    @property
    def total_count(self) -> int:
        """Total number of lines processed."""
        return self._total_count

    @property
    def drop_rate(self) -> float:
        """Fraction of lines that were truncated (0.0 to 1.0)."""
        if self._total_count == 0:
            return 0.0
        return self._truncated_count / self._total_count
