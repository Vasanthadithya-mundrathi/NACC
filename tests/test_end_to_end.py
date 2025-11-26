from __future__ import annotations

from pathlib import Path

from nacc_orchestrator.config import AgentBackendConfig, AuditConfig, NodeDefinition, OrchestratorConfig
from nacc_orchestrator.service import OrchestratorService


def build_config(tmp_path: Path) -> OrchestratorConfig:
    node_a_root = tmp_path / "node-a"
    node_b_root = tmp_path / "node-b"
    for root in (node_a_root, node_b_root):
        root.mkdir()
        (root / "hello.txt").write_text("hello", encoding="utf-8")
    nodes = [
        NodeDefinition(node_id="node-a", transport="local", root_dir=node_a_root, tags=["dev"], allowed_commands=["echo"]),
        NodeDefinition(node_id="node-b", transport="local", root_dir=node_b_root, tags=["linux"], allowed_commands=["echo"]),
    ]
    return OrchestratorConfig(
        orchestrator_id="tests",
        nodes=nodes,
        agent_backend=AgentBackendConfig(kind="local-heuristic"),
        audit=AuditConfig(path=tmp_path / "audit.log", max_entries=1000),
    )


def test_full_stack_flow(tmp_path: Path) -> None:
    config = build_config(tmp_path)
    service = OrchestratorService(config)

    node_status = service.list_nodes()
    assert len(node_status) == 2
    assert {entry["node_id"] for entry in node_status} == {"node-a", "node-b"}

    file_listing = service.list_files("auto", path=str(tmp_path / "node-a"), recursive=False)
    assert file_listing["count"] >= 1

    exec_result = service.execute_command(
        description="greet",
        command=["/bin/echo", "hello-from-nacc"],
        preferred_tags=["dev"],
    )
    assert exec_result["results"]
    assert exec_result["results"][0]["exit_code"] == 0

    probe = service.check_agent_backend("sample health probe")
    assert probe["message"] == "sample health probe"

    audit_contents = config.audit.path.read_text(encoding="utf-8")
    assert "execute_command" in audit_contents