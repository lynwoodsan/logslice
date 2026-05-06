"""Bookmark support: save and restore the last read position in a log file."""

import json
import os
from pathlib import Path
from typing import Optional


DEFAULT_BOOKMARK_DIR = Path.home() / ".logslice" / "bookmarks"


class Bookmark:
    """Persists the last byte offset read for a given log file."""

    def __init__(self, log_path: str, bookmark_dir: Optional[Path] = None):
        self.log_path = os.path.abspath(log_path)
        self.bookmark_dir = Path(bookmark_dir) if bookmark_dir else DEFAULT_BOOKMARK_DIR
        self._bookmark_file = self.bookmark_dir / self._safe_name()

    def _safe_name(self) -> str:
        """Convert the log path to a safe filename."""
        safe = self.log_path.replace(os.sep, "_").replace(":", "_").lstrip("_")
        return safe + ".bookmark"

    def load(self) -> int:
        """Return the saved byte offset, or 0 if no bookmark exists."""
        if not self._bookmark_file.exists():
            return 0
        try:
            data = json.loads(self._bookmark_file.read_text())
            return int(data.get("offset", 0))
        except (json.JSONDecodeError, ValueError, OSError):
            return 0

    def save(self, offset: int) -> None:
        """Persist the byte offset for the log file."""
        self.bookmark_dir.mkdir(parents=True, exist_ok=True)
        data = {"log_path": self.log_path, "offset": offset}
        self._bookmark_file.write_text(json.dumps(data))

    def clear(self) -> None:
        """Remove the bookmark file if it exists."""
        if self._bookmark_file.exists():
            self._bookmark_file.unlink()

    def exists(self) -> bool:
        """Return True if a bookmark has been saved."""
        return self._bookmark_file.exists()
