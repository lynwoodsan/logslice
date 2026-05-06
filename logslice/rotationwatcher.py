"""Detect log file rotation by inode or size changes."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RotationWatcher:
    """Watch a log file path for signs of rotation.

    Rotation is detected when:
    - The file's inode changes (rename/replace rotation).
    - The file's size shrinks below the last observed size (truncation).
    """

    path: str
    _last_inode: Optional[int] = field(default=None, init=False, repr=False)
    _last_size: int = field(default=0, init=False, repr=False)
    rotation_count: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("path must be a non-empty string")
        self._snapshot()

    def _snapshot(self) -> None:
        """Record the current inode and size, if the file exists."""
        try:
            st = os.stat(self.path)
            self._last_inode = st.st_ino
            self._last_size = st.st_size
        except FileNotFoundError:
            self._last_inode = None
            self._last_size = 0

    def check(self) -> bool:
        """Return True if a rotation has been detected since last check.

        Calling this method updates the internal snapshot so subsequent
        calls will not re-report the same rotation event.
        """
        try:
            st = os.stat(self.path)
        except FileNotFoundError:
            # File disappeared — treat as rotation.
            rotated = self._last_inode is not None
            self._last_inode = None
            self._last_size = 0
            if rotated:
                self.rotation_count += 1
            return rotated

        inode_changed = (
            self._last_inode is not None and st.st_ino != self._last_inode
        )
        size_shrank = st.st_size < self._last_size
        rotated = inode_changed or size_shrank

        if rotated:
            self.rotation_count += 1

        self._last_inode = st.st_ino
        self._last_size = st.st_size
        return rotated

    def reset(self) -> None:
        """Re-snapshot the file, clearing any pending rotation state."""
        self._snapshot()
