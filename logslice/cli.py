"""Command-line interface for logslice."""

import argparse
import sys
from datetime import datetime

from logslice.reader import open_log_file, stream_lines
from logslice.output import process_lines


DATETIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
]


def parse_datetime(value: str) -> datetime:
    """Parse a datetime string using several common formats."""
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Cannot parse datetime: {value!r}. "
        "Expected formats: YYYY-MM-DD, YYYY-MM-DD HH:MM, YYYY-MM-DDTHH:MM:SS"
    )


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Stream and filter large log files by time range, level, or regex pattern.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Log file to read (plain or gzip). Reads stdin if omitted.",
    )
    parser.add_argument(
        "--start",
        metavar="DATETIME",
        type=parse_datetime,
        default=None,
        help="Include lines at or after this datetime.",
    )
    parser.add_argument(
        "--end",
        metavar="DATETIME",
        type=parse_datetime,
        default=None,
        help="Include lines at or before this datetime.",
    )
    parser.add_argument(
        "--level",
        metavar="LEVEL",
        default=None,
        help="Filter by log level (e.g. ERROR, WARNING, INFO).",
    )
    parser.add_argument(
        "--pattern",
        metavar="REGEX",
        default=None,
        help="Only include lines matching this regex pattern.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colorized output.",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        default=False,
        help="Print the number of matching lines instead of the lines themselves.",
    )
    return parser


def main(argv=None) -> int:
    """Entry point for the logslice CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.file:
        fh = open_log_file(args.file)
        lines = stream_lines(fh)
    else:
        lines = stream_lines(sys.stdin)

    color = not args.no_color
    matched = process_lines(
        lines,
        start=args.start,
        end=args.end,
        level=args.level,
        pattern=args.pattern,
        output=sys.stdout,
        color=color,
        count_only=args.count,
    )

    if args.count:
        print(matched)

    return 0


if __name__ == "__main__":
    sys.exit(main())
