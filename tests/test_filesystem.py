from __future__ import annotations

from pathlib import Path

import pytest

from nacc_node import filesystem


def _setup_tree(tmp_path: Path) -> tuple[Path, Path]:
    (tmp_path / "dirA").mkdir()
    (tmp_path / "dirA" / "file1.txt").write_text("alpha", encoding="utf-8")
    (tmp_path / "dirB").mkdir()
    (tmp_path / "dirB" / "file2.log").write_text("beta", encoding="utf-8")
    lone_file = tmp_path / "root.txt"
    lone_file.write_text("root", encoding="utf-8")
    return tmp_path, lone_file


def test_list_files_recursive(tmp_path: Path) -> None:
    root, lone_file = _setup_tree(tmp_path)

    result = filesystem.list_files(root, recursive=True)

    paths = {entry.relative_path for entry in result}
    assert "dirA" in paths
    assert "dirA/file1.txt" in paths
    assert "dirB/file2.log" in paths
    assert "root.txt" in paths

    lone_entry = next(entry for entry in result if entry.path == str(lone_file))
    assert lone_entry.size == 4
    assert lone_entry.is_dir is False


def test_list_files_pattern(tmp_path: Path) -> None:
    root, _ = _setup_tree(tmp_path)

    result = filesystem.list_files(root, recursive=True, pattern="*.log")

    assert len(result) == 1
    assert result[0].relative_path.endswith("file2.log")


def test_list_files_include_hash(tmp_path: Path) -> None:
    root, lone_file = _setup_tree(tmp_path)

    result = filesystem.list_files(lone_file, include_hash=True)

    assert len(result) == 1
    assert result[0].hash == filesystem.hash_file(lone_file)


def test_list_files_missing_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        filesystem.list_files(tmp_path / "nope")
