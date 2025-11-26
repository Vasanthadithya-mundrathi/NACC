from __future__ import annotations

from pathlib import Path

import pytest

from nacc_orchestrator.config import load_orchestrator_config


def test_load_orchestrator_config(tmp_path: Path):
    config_path = tmp_path / "orch.yml"
    config_path.write_text(
        """
        orchestrator_id: test
        nodes:
          - node_id: node-a
            transport: local
            root_dir: ./data
        agent_backend:
          kind: local-heuristic
        """,
        encoding="utf-8",
    )
    config = load_orchestrator_config(config_path)
    assert config.orchestrator_id == "test"
    assert config.nodes[0].node_id == "node-a"


def test_config_requires_node(tmp_path: Path):
    config_path = tmp_path / "bad.yml"
    config_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        load_orchestrator_config(config_path)
