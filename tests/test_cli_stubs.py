"""Basic smoke tests for CLI stubs.

These ensure the entry-point modules import and main() executes without error.
"""

from __future__ import annotations

import json
from pathlib import Path
import textwrap

from nacc_node import cli as node_cli
from nacc_orchestrator import cli as orchestrator_cli
from nacc_ui import cli as ui_cli


def test_node_cli_runs(tmp_path: Path, capsys):
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    config_path = tmp_path / "node-config.yml"
    backup_dir = tmp_path / "backup"
    config_path.write_text(
        textwrap.dedent(
            f"""
            node_id: cli-test-node
            root_dir: {root_dir}
            tags: [cli, test]
            allowed_commands: [echo]
            sync_targets:
              backup: {backup_dir}
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    node_cli.main(["serve", "--dry-run", "--config", str(config_path)])
    output = json.loads(capsys.readouterr().out)
    assert output["node_id"] == "cli-test-node"

def _write_orchestrator_config(tmp_path: Path, root_dir: Path) -> Path:
    config_path = tmp_path / "orchestrator.yml"
    config_path.write_text(
        textwrap.dedent(
            f"""
            orchestrator_id: test-orch
            nodes:
              - node_id: local-dev
                transport: local
                root_dir: {root_dir}
                allowed_commands: [echo]
                tags: [dev]
            agent_backend:
              kind: local-heuristic
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return config_path


def test_orchestrator_cli_list_files(tmp_path: Path, capsys):
    root_dir = tmp_path / "node-root"
    root_dir.mkdir()
    (root_dir / "demo.txt").write_text("hello", encoding="utf-8")
    config_path = _write_orchestrator_config(tmp_path, root_dir)
    orchestrator_cli.main([
        "list-files",
        "--config",
        str(config_path),
        "--node",
        "auto",
        "--path",
        ".",
    ])
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] >= 1


def test_ui_cli_runs():
    config_path = Path("configs/ui-config.example.yml")
    ui_cli.main(["--config", str(config_path), "--dry-run"])


def test_node_list_files_cli(tmp_path: Path, capsys):
    (tmp_path / "demo.txt").write_text("hello", encoding="utf-8")
    node_cli.main(["list-files", "--path", str(tmp_path)])
    output = json.loads(capsys.readouterr().out)
    paths = {entry["relative_path"] for entry in output["files"]}
    assert "demo.txt" in paths


def test_orchestrator_exec_cli(tmp_path: Path, capsys):
    root_dir = tmp_path / "node-root"
    root_dir.mkdir()
    config_path = _write_orchestrator_config(tmp_path, root_dir)
    orchestrator_cli.main([
        "exec",
        "--config",
        str(config_path),
        "--cmd",
        "/bin/echo",
        "hi",
    ])
    payload = json.loads(capsys.readouterr().out)
    assert payload["plan"]["nodes"] == ["local-dev"]
