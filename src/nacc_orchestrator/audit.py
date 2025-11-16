"""Simple append-only audit logging for orchestrator actions."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any


class AuditLogger:
    def __init__(self, path: Path, *, max_entries: int = 50_000) -> None:
        self.path = path
        self.max_entries = max_entries
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def record(self, action: str, **payload: Any) -> None:
        entry = {
            "timestamp": time.time(),
            "action": action,
            "payload": payload,
        }
        line = json.dumps(entry, separators=(",", ":"))
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
            self._trim_if_needed()

    def _trim_if_needed(self) -> None:
        lines: list[str]
        with self.path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()
        if len(lines) <= self.max_entries:
            return
        trimmed = lines[-self.max_entries :]
        with self.path.open("w", encoding="utf-8") as handle:
            handle.writelines(trimmed)


__all__ = ["AuditLogger"]
