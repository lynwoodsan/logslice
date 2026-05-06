"""Redact sensitive patterns from log lines before output."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

_BUILTIN_PATTERNS: List[Tuple[str, str]] = [
    (r'(?i)(password|passwd|pwd)=[^\s&"]+', r'\1=***'),
    (r'(?i)(token|api[_-]?key|secret)=[^\s&"]+', r'\1=***'),
    (r'\b(?:\d{4}[- ]?){3}\d{4}\b', '****-****-****-****'),  # credit card
    (r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b', '[email]'),
]


@dataclass
class Redactor:
    """Apply redaction rules to log lines.

    Args:
        patterns: Extra (regex, replacement) pairs supplied by the caller.
        builtin: Whether to include the built-in sensitive-data patterns.
    """

    patterns: List[Tuple[str, str]] = field(default_factory=list)
    builtin: bool = True

    def __post_init__(self) -> None:
        combined = (_BUILTIN_PATTERNS if self.builtin else []) + list(self.patterns)
        self._rules: List[Tuple[re.Pattern[str], str]] = [
            (re.compile(pat), repl) for pat, repl in combined
        ]
        self.redacted_count: int = 0

    # ------------------------------------------------------------------
    def redact(self, line: str) -> str:
        """Return *line* with all matching patterns replaced."""
        result = line
        changed = False
        for pattern, replacement in self._rules:
            new, n = pattern.subn(replacement, result)
            if n:
                result = new
                changed = True
        if changed:
            self.redacted_count += 1
        return result

    def feed(self, line: str) -> Optional[str]:
        """Pipeline-compatible wrapper — always emits the (possibly redacted) line."""
        return self.redact(line)
