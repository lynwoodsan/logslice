"""Extract structured fields (key=value pairs) from log lines."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Matches key=value or key="quoted value" patterns
_FIELD_RE = re.compile(
    r'(?P<key>[\w.\-]+)=(?P<value>"[^"]*"|\S+)'
)


@dataclass
class FieldExtractor:
    """Extracts key=value fields from log lines and filters by field values."""

    required_fields: Dict[str, str] = field(default_factory=dict)
    _extracted: int = field(default=0, init=False, repr=False)
    _matched: int = field(default=0, init=False, repr=False)

    def extract(self, line: str) -> Dict[str, str]:
        """Return all key=value fields found in *line*."""
        fields: Dict[str, str] = {}
        for m in _FIELD_RE.finditer(line):
            key = m.group("key")
            value = m.group("value").strip('"')
            fields[key] = value
        return fields

    def matches(self, line: str) -> bool:
        """Return True when all required_fields are present and match."""
        self._extracted += 1
        if not self.required_fields:
            self._matched += 1
            return True
        fields = self.extract(line)
        for key, expected in self.required_fields.items():
            actual = fields.get(key)
            if actual is None:
                return False
            if not re.search(expected, actual):
                return False
        self._matched += 1
        return True

    def feed(self, lines: List[str]) -> List[str]:
        """Filter *lines*, keeping only those matching required_fields."""
        return [line for line in lines if self.matches(line)]

    @property
    def match_rate(self) -> float:
        """Fraction of lines that matched, or 1.0 if no lines seen."""
        if self._extracted == 0:
            return 1.0
        return self._matched / self._extracted


def parse_field_filters(specs: List[str]) -> Dict[str, str]:
    """Parse a list of 'key=value' spec strings into a dict.

    Raises ValueError for malformed specs.
    """
    result: Dict[str, str] = {}
    for spec in specs:
        if '=' not in spec:
            raise ValueError(
                f"Invalid field filter {spec!r}: expected 'key=value' format"
            )
        key, _, value = spec.partition('=')
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(
                f"Invalid field filter {spec!r}: key must not be empty"
            )
        result[key] = value
    return result
