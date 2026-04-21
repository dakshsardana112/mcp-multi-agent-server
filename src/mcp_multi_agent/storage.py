"""Tiny JSON-file persistence layer.

Each agent that wants to store data gets its own JsonStore pointed at a file
inside the data dir. We keep this deliberately simple - atomic writes via a
tempfile + rename, no indexes, no querying. The whole idea of this project is
learning, so clarity beats cleverness.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any


class JsonStore:
    """A thread-safe JSON document store backed by a single file.

    The "document" is whatever you want it to be - a list, a dict, whatever.
    Callers pick a structure and stick to it. Each agent owns its own store.
    """

    def __init__(self, path: Path, default: Any = None) -> None:
        self.path = Path(path)
        self._default = default if default is not None else {}
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write(self._default)

    # ------------------------------------------------------------------ read
    def load(self) -> Any:
        """Return the whole document. Reads are cheap - this is a demo store."""
        with self._lock:
            try:
                with self.path.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except FileNotFoundError:
                return json.loads(json.dumps(self._default))
            except json.JSONDecodeError:
                # Corrupted file - restore defaults. Better than crashing.
                self._write(self._default)
                return json.loads(json.dumps(self._default))

    # ----------------------------------------------------------------- write
    def save(self, data: Any) -> None:
        """Write the document atomically: write-to-temp then rename."""
        with self._lock:
            self._write(data)

    def update(self, fn) -> Any:
        """Read-modify-write under the lock. ``fn`` takes current data,
        returns new data. Returns the new data so callers can inspect it.
        """
        with self._lock:
            try:
                with self.path.open("r", encoding="utf-8") as f:
                    current = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                current = json.loads(json.dumps(self._default))
            new_data = fn(current)
            self._write(new_data)
            return new_data

    # ---------------------------------------------------------------- helper
    def _write(self, data: Any) -> None:
        """Atomic write: create a sibling tempfile, fsync, then rename over."""
        tmp_fd, tmp_path = tempfile.mkstemp(
            prefix=self.path.name + ".", dir=str(self.path.parent)
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=False, ensure_ascii=False)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except OSError:
                    # Best-effort; some filesystems (e.g. bind mounts) refuse fsync.
                    pass
            os.replace(tmp_path, self.path)
        except Exception:
            # Clean up the temp file if we failed mid-write.
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
