from __future__ import annotations

from pathlib import Path

from nacc_orchestrator.config import OrchestratorConfig
from nacc_orchestrator.service import OrchestratorService


def _build_config(root_dir: Path) -> OrchestratorConfig:
    return OrchestratorConfig(
        orchestrator_id="tests",
        nodes=[
            {
                "node_id": "local-dev",
                "transport": "local",
                "root_dir": str(root_dir),
                "allowed_commands": ["echo"],
                "tags": ["dev"],
            }
        ],
        agent_backend={"kind": "local-heuristic"},
    )


def test_service_list_files(tmp_path: Path):
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    (root_dir / "hello.txt").write_text("hello", encoding="utf-8")
    service = OrchestratorService(_build_config(root_dir))
    response = service.list_files("auto", path=str(root_dir), recursive=False)
    assert response["count"] >= 1
    rel_paths = {entry["relative_path"] for entry in response["files"]}
    assert "hello.txt" in rel_paths


def test_service_execute_command(tmp_path: Path):
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    service = OrchestratorService(_build_config(root_dir))
    response = service.execute_command(
        description="say hi",
        command=["/bin/echo", "hi"],
        preferred_tags=["dev"],
    )
    assert response["plan"]["nodes"] == ["local-dev"]
    assert response["results"][0]["exit_code"] == 0


def test_agent_probe(tmp_path: Path):
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    service = OrchestratorService(_build_config(root_dir))
    result = service.check_agent_backend("health check")
    assert result["message"] == "health check"
    assert "response" in result
