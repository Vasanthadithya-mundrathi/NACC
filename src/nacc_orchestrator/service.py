"""Core orchestrator service that wires registry, agents, and audit logging."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from .agents import AgentSuite, CommandRequest
from .audit import AuditLogger
from .config import OrchestratorConfig
from .nodes import NodeRegistry


def _ensure_list(command: list[str] | str) -> list[str]:
    return command if isinstance(command, list) else command.split()


@dataclass(slots=True)
class CommandResult:
    node_id: str
    stdout: str
    stderr: str
    exit_code: int
    duration: float


class OrchestratorService:
    def __init__(self, config: OrchestratorConfig) -> None:
        self.config = config
        self.registry = NodeRegistry(config.nodes)
        self.agents = AgentSuite(config.agent_backend, self.registry)
        self.audit = AuditLogger(config.audit.path, max_entries=config.audit.max_entries)

    def list_nodes(self) -> list[dict[str, Any]]:
        statuses = self.registry.refresh_all()
        return [
            {
                "node_id": status.node_id,
                "display_name": status.display_name,
                "tags": status.tags,
                "healthy": status.healthy,
                "metrics": status.metrics,
                "last_seen": status.last_seen,
                "error": status.error,
            }
            for status in statuses
        ]

    def get_node_info(self, node_id: str) -> dict[str, Any]:
        client = self.registry.get_client(node_id)
        info = client.get_node_info()
        self.audit.record("get_node_info", node_id=node_id)
        return info

    def list_files(
        self,
        node_id: str,
        *,
        path: str,
        recursive: bool = False,
        pattern: str | None = None,
        include_hash: bool = False,
    ) -> dict[str, Any]:
        target_node = node_id
        if node_id == "auto":
            decision = self.agents.select_node(description=f"List files under {path}")
            target_node = decision.nodes[0]
        client = self.registry.get_client(target_node)
        files = client.list_files(path, recursive=recursive, pattern=pattern, include_hash=include_hash)
        self.audit.record("list_files", node_id=target_node, path=path, count=len(files))
        return {
            "node_id": target_node,
            "count": len(files),
            "files": [file.to_dict() for file in files],
        }

    def execute_command(
        self,
        *,
        description: str,
        command: list[str] | str,
        preferred_tags: list[str] | None = None,
        parallelism: int = 1,
        timeout: float | None = None,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        request = CommandRequest(
            description=description,
            command=command,
            preferred_tags=preferred_tags,
            parallelism=parallelism,
        )
        plan = self.agents.plan_command(request)
        results: list[CommandResult] = []
        for node_id in plan.nodes:
            client = self.registry.get_client(node_id)
            response = client.execute_command(
                command,
                timeout=timeout or plan.timeout,
                cwd=cwd,
                env=env,
            )
            results.append(
                CommandResult(
                    node_id=node_id,
                    stdout=response.get("stdout", ""),
                    stderr=response.get("stderr", ""),
                    exit_code=response.get("exit_code", -1),
                    duration=response.get("duration", 0.0),
                )
            )
        command_list = _ensure_list(command)
        self.audit.record(
            "execute_command",
            nodes=plan.nodes,
            command=command_list,
            timeout=timeout or plan.timeout,
            router_reason=plan.router_reason,
        )
        return {
            "plan": {
                "nodes": plan.nodes,
                "mode": plan.mode,
                "timeout": plan.timeout,
                "reason": plan.reason,
                "router_reason": plan.router_reason,
            },
            "results": [asdict(result) for result in results],
        }

    def sync_path(self, source_node: str, *, source_path: str, target_nodes: list[str], strategy: str = "mirror") -> dict[str, Any]:
        plan = self.agents.plan_sync(source_node, target_nodes, strategy=strategy)
        
        # Manual sync implementation (Orchestrator-driven)
        source_client = self.registry.get_client(plan.source_node)
        
        # List files to sync (recursive)
        try:
            files = source_client.list_files(source_path, recursive=True)
        except Exception as e:
            return {"error": f"Failed to list source files: {e}"}
            
        results = []
        for target_node_id in plan.target_nodes:
            target_client = self.registry.get_client(target_node_id)
            synced_count = 0
            
            for file_meta in files:
                # Read from source
                # Construct full path for read (file_meta.path is relative to listing root?)
                # list_files returns paths relative to the listing root if root provided?
                # nacc-node list_files returns path relative to node root.
                # So we can use file_meta.path directly for read/write if we want to preserve structure relative to root.
                # But source_path might be a subdirectory.
                # We want to sync source_path content to target_node.
                
                # Simple approach: Read file content
                try:
                    file_data = source_client.read_file(file_meta.path)
                    content = file_data.get("content")
                    if content is None:
                        # Binary file or encoding issue, skip for now
                        print(f"[DEBUG] Sync skipping binary/empty file: {file_meta.path}", flush=True)
                        continue
                        
                    # Write to target using RELATIVE path to avoid permission errors
                    target_path = file_meta.relative_path
                    print(f"[DEBUG] Sync writing {target_path} to {target_node_id} (len={len(content)})", flush=True)
                    target_client.write_file(target_path, content, overwrite=True)
                    synced_count += 1
                except Exception as e:
                    # Log error but continue
                    print(f"Failed to sync {file_meta.path}: {e}", flush=True)
                    
            results.append({
                "target": target_node_id,
                "files_synced": synced_count,
                "status": "success"
            })

        self.audit.record(
            "sync_path",
            source_node=source_node,
            source_path=source_path,
            target_nodes=target_nodes,
            strategy=strategy,
        )
        return {"source": source_path, "targets": results}

    def write_file(
        self,
        path: str,
        content: str,
        preferred_tags: list[str] | None = None,
        overwrite: bool = True
    ) -> dict[str, Any]:
        """Write content to a file on a node"""
        # Choose target node
        node_def = self.registry.choose_node(preferred_tags)
        client = self.registry.get_client(node_def.node_id)
        
        # Write file
        response = client.write_file(path, content, overwrite=overwrite)
        
        self.audit.record(
            "write_file",
            node=node_def.node_id,
            path=path,
            content_length=len(content)
        )
        
        return {
            "node_id": node_def.node_id,
            "path": path,
            "success": response.get("success", False),
            "message": response.get("message", ""),
            "details": response
        }

    def check_agent_backend(self, message: str = "NACC agent health check", context: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self.agents.probe_backend(message, context=context)
        self.audit.record("agent_probe", message=message)
        return {"message": message, "response": response}


__all__ = ["OrchestratorService"]
