"""Filesystem tooling for the NACC node server.

Provides the "ListFiles" capability that other components (orchestrator, UI,
CLI) can call directly. This will later be wrapped in MCP transport but
remains a simple Python module for local development and testing.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable
import hashlib
import json
import os
import time


@dataclass(slots=True)
class FileMetadata:
    """Serializable metadata for a single filesystem entry."""

    path: str
    relative_path: str
    is_dir: bool
    size: int | None
    modified: float
    hash: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class FileSystemError(RuntimeError):
    """Raised when a filesystem operation fails unexpectedly."""


def hash_file(path: Path, chunk_size: int = 1 << 16) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_entries(root: Path, recursive: bool) -> Iterable[Path]:
    if root.is_file():
        yield root
        return

    yield root
    if recursive:
        yield from root.rglob("*")
    else:
        for child in root.iterdir():
            yield child


def list_files(
    path: str | os.PathLike[str],
    *,
    recursive: bool = False,
    pattern: str | None = None,
    include_hash: bool = False,
    root: str | None = None,
) -> list[FileMetadata]:
    """Return metadata for files/directories under ``path``.

    Parameters
    ----------
    path: str | PathLike
        Root path to inspect.
    recursive: bool
        Whether to recurse into subdirectories (default False).
    pattern: str | None
        Optional glob-style pattern matching against the relative path.
    include_hash: bool
        If True, compute sha256 for regular files.
    root: str | None
        Custom root to compute ``relative_path``; defaults to ``path`` when it
        points to a directory, or the parent directory when pointing to a file.
    """

    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"Path does not exist: {target}")

    root_path = Path(root).expanduser().resolve() if root else (target if target.is_dir() else target.parent)
    results: list[FileMetadata] = []

    for entry in iter_entries(target, recursive):
        rel = os.path.relpath(entry, root_path)
        if pattern and not (fnmatch(rel, pattern) or fnmatch(entry.name, pattern)):
            continue

        stat_info = entry.stat()
        is_dir = entry.is_dir()
        size = None if is_dir else stat_info.st_size
        modified = stat_info.st_mtime

        file_hash: str | None = None
        if include_hash and not is_dir:
            try:
                file_hash = hash_file(entry)
            except OSError as exc:  # pragma: no cover (hard to trigger reliably)
                raise FileSystemError(f"Failed to hash {entry}: {exc}") from exc

        results.append(
            FileMetadata(
                path=str(entry),
                relative_path=rel,
                is_dir=is_dir,
                size=size,
                modified=modified,
                hash=file_hash,
            )
        )

    results.sort(key=lambda meta: meta.relative_path)
    return results


def list_files_json(**kwargs) -> str:
    files = list_files(**kwargs)
    payload = {
        "generated_at": time.time(),
        "count": len(files),
        "files": [f.to_dict() for f in files],
    }
    return json.dumps(payload, indent=2)
