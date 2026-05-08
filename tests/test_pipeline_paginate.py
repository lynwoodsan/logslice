"""Integration tests: Paginator wired into the pipeline via feed_many."""
from __future__ import annotations

from logslice.paginator import Paginator

LOG_LINES = [
    "2024-01-01 00:00:01 INFO  alpha",
    "2024-01-01 00:00:02 DEBUG beta",
    "2024-01-01 00:00:03 ERROR gamma",
    "2024-01-01 00:00:04 INFO  delta",
    "2024-01-01 00:00:05 WARN  epsilon",
]


def _run(page_size: int = 0, skip: int = 0) -> list[str]:
    p = Paginator(page_size=page_size, skip=skip)
    return list(p.feed_many(LOG_LINES))


class TestPaginateNoFilter:
    def test_all_lines_returned_by_default(self):
        result = _run()
        assert result == LOG_LINES

    def test_line_count_matches(self):
        result = _run()
        assert len(result) == 5


class TestPaginateHead:
    def test_head_3(self):
        result = _run(page_size=3)
        assert len(result) == 3
        assert result[0] == LOG_LINES[0]
        assert result[-1] == LOG_LINES[2]

    def test_head_1(self):
        result = _run(page_size=1)
        assert result == [LOG_LINES[0]]

    def test_head_exceeds_input(self):
        result = _run(page_size=100)
        assert result == LOG_LINES


class TestPaginateSkip:
    def test_skip_2(self):
        result = _run(skip=2)
        assert result == LOG_LINES[2:]

    def test_skip_all(self):
        result = _run(skip=len(LOG_LINES))
        assert result == []


class TestPaginateCombined:
    def test_skip_2_head_2(self):
        result = _run(page_size=2, skip=2)
        assert result == [LOG_LINES[2], LOG_LINES[3]]

    def test_skip_4_head_1(self):
        result = _run(page_size=1, skip=4)
        assert result == [LOG_LINES[4]]

    def test_skip_3_head_10(self):
        """page_size larger than remaining lines after skip."""
        result = _run(page_size=10, skip=3)
        assert result == LOG_LINES[3:]
