from __future__ import annotations

from pathlib import Path

import pytest

from nacc_node.config import NodeConfig
from nacc_node.tools import (
    execute_command_tool,
    get_node_info_tool,
    list_files_tool,
    read_file_tool,
    sync_files_tool,
    write_file_tool,
)


@pytest.fixture()
def node_config(tmp_path: Path) -> NodeConfig:
    root = tmp_path / "root"
    root.mkdir()
    (root / "sample.txt").write_text("hello", encoding="utf-8")
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    return NodeConfig(
        node_id="test-node",
        root_dir=root,
        tags=["test"],
        description="Test node",
        allowed_commands=["echo", "python"],
        sync_targets={"backup": backup_dir},
    )


def test_list_files_tool(node_config: NodeConfig):
    result = list_files_tool(node_config, {"path": ".", "recursive": True})
    assert result["count"] >= 1
    assert any(entry["relative_path"] == "sample.txt" for entry in result["files"])


def test_read_file_tool(node_config: NodeConfig):
    result = read_file_tool(node_config, {"path": "sample.txt"})
    assert result["content"] == "hello"
    assert result["size"] == 5


def test_write_file_tool_overwrite(node_config: NodeConfig):
    payload = {
        "path": "sample.txt",
        "content": "updated",
        "overwrite": True,
    }
    result = write_file_tool(node_config, payload)
    assert result["bytes_written"] == len("updated".encode("utf-8"))
    assert Path(node_config.root_dir, "sample.txt").read_text(encoding="utf-8") == "updated"


def test_execute_command_tool(node_config: NodeConfig):
    result = execute_command_tool(node_config, {"command": ["/bin/echo", "hi"]})
    assert result["exit_code"] == 0
    assert "hi" in result["stdout"].strip()


def test_sync_files_tool(node_config: NodeConfig):
    payload = {"source_path": "sample.txt", "targets": ["backup"]}
    result = sync_files_tool(node_config, payload)
    assert result["targets"][0]["files_synced"] == 1


def test_get_node_info_tool(node_config: NodeConfig):
    result = get_node_info_tool(node_config, {})
    assert result["node_id"] == "test-node"
    assert "metrics" in result
