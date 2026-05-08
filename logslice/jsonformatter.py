"""Format matched log lines as JSON objects for structured output."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from logslice.filters import extract_timestamp, extract_level


def line_to_dict(
    line: str,
    source: Optional[str] = None,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convert a raw log line into a structured dictionary.

    Args:
        line: The raw log line text.
        source: Optional filename or label for the log source.
        extra_fields: Optional mapping of additional key/value pairs to include.

    Returns:
        A dictionary with at minimum a ``message`` key.
    """
    record: Dict[str, Any] = {"message": line}

    ts = extract_timestamp(line)
    if ts is not None:
        record["timestamp"] = ts.isoformat()

    level = extract_level(line)
    if level is not None:
        record["level"] = level

    if source is not None:
        record["source"] = source

    if extra_fields:
        record.update(extra_fields)

    return record


def format_as_json(
    line: str,
    source: Optional[str] = None,
    extra_fields: Optional[Dict[str, Any]] = None,
    indent: Optional[int] = None,
) -> str:
    """Serialise a log line to a JSON string.

    Args:
        line: The raw log line text.
        source: Optional filename or label for the log source.
        extra_fields: Optional mapping of additional key/value pairs to include.
        indent: If given, pretty-print with this many spaces of indentation.

    Returns:
        A JSON string (no trailing newline).
    """
    record = line_to_dict(line, source=source, extra_fields=extra_fields)
    return json.dumps(record, indent=indent, ensure_ascii=False)


def feed(
    lines,
    source: Optional[str] = None,
    extra_fields: Optional[Dict[str, Any]] = None,
    indent: Optional[int] = None,
):
    """Yield JSON-formatted strings for each line in *lines*.

    Args:
        lines: Iterable of raw log line strings.
        source: Optional filename or label for the log source.
        extra_fields: Optional mapping of additional key/value pairs to include.
        indent: If given, pretty-print JSON output.

    Yields:
        JSON string for each input line.
    """
    for line in lines:
        yield format_as_json(line, source=source, extra_fields=extra_fields, indent=indent)
