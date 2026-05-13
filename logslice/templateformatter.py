"""Template-based line formatter using named placeholders."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator, Optional

from logslice.filters import extract_timestamp, extract_level

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")

KNOWN_FIELDS = {"timestamp", "level", "message", "raw"}


def _build_vars(line: str) -> dict:
    ts = extract_timestamp(line)
    lvl = extract_level(line)
    return {
        "raw": line,
        "message": line,
        "timestamp": ts.isoformat() if ts else "",
        "level": lvl or "",
    }


def render_template(template: str, line: str) -> str:
    """Render *template* substituting known fields extracted from *line*."""
    if not template:
        return line
    vars_ = _build_vars(line)
    try:
        return template.format_map(vars_)
    except KeyError:
        # Unknown placeholder — return line unchanged
        return line


def validate_template(template: str) -> list[str]:
    """Return a list of unrecognised placeholder names in *template*."""
    names = _PLACEHOLDER_RE.findall(template)
    return [n for n in names if n not in KNOWN_FIELDS]


@dataclass
class TemplateFormatter:
    template: str
    _formatted_count: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.template:
            raise ValueError("template must be a non-empty string")

    @property
    def formatted_count(self) -> int:
        return self._formatted_count

    def format_line(self, line: str) -> str:
        result = render_template(self.template, line)
        self._formatted_count += 1
        return result

    def feed(self, lines: Iterator[str]) -> Iterator[str]:
        for line in lines:
            yield self.format_line(line)
