"""Node transport, registry, and client helpers for the orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time
from pathlib import Path
from typing import Any, Iterable, Protocol

import requests

from nacc_node.config import NodeConfig
from nacc_node.filesystem import FileMetadata, list_files
from nacc_node.tools import (
    get_node_info_tool,
    read_file_tool,
    write_file_tool,
    execute_command_tool,
    sync_files_tool,
)

from .config import NodeDefinition


class NodeClient(Protocol):
    """Protocol implemented by node transports."""

    def list_files(
        self,
        path: str,
        *,
        recursive: bool = False,
        pattern: str | None = None,
        include_hash: bool = False,
    ) -> list[FileMetadata]:
        ...

    def read_file(self, path: str) -> dict[str, Any]:
        ...

    def write_file(self, path: str, content: str, *, overwrite: bool = False) -> dict[str, Any]:
        ...

    def execute_command(
        self,
        command: list[str] | str,
        *,
        timeout: float | None = None,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        ...

    def sync_files(self, source_path: str, targets: list[str], *, strategy: str = "mirror") -> dict[str, Any]:
        ...

    def get_node_info(self) -> dict[str, Any]:
        ...


class HTTPNodeClient:
    """Client that talks to a remote node HTTP server."""

    def __init__(self, definition: NodeDefinition, *, timeout: float = 30.0) -> None:
        if not definition.base_url:
            raise ValueError("HTTP transport requires base_url")
        self.definition = definition
        self.timeout = timeout
        self._session = requests.Session()

    def _tool_url(self, name: str) -> str:
        base = str(self.definition.base_url).rstrip("/")
        return f"{base}/tools/{name}"

    def _post_tool(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.definition.auth_token:
            headers["Authorization"] = f"Bearer {self.definition.auth_token}"
        response = self._session.post(
            self._tool_url(name),
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def list_files(self, path: str, *, recursive: bool = False, pattern: str | None = None, include_hash: bool = False) -> list[FileMetadata]:
        payload = {
            "path": path,
            "recursive": recursive,
            "pattern": pattern,
            "include_hash": include_hash,
        }
        result = self._post_tool("list-files", payload)
        return [FileMetadata(**entry) for entry in result.get("files", [])]

    def read_file(self, path: str) -> dict[str, Any]:
        return self._post_tool("read-file", {"path": path})

    def write_file(self, path: str, content: str, *, overwrite: bool = False) -> dict[str, Any]:
        return self._post_tool(
            "write-file",
            {"path": path, "content": content, "overwrite": overwrite},
        )

    def execute_command(
        self,
        command: list[str] | str,
        *,
        timeout: float | None = None,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        payload = {"command": command}
        if timeout:
            payload["timeout"] = timeout
        if cwd:
            payload["cwd"] = cwd
        if env:
            payload["env"] = env
        return self._post_tool("execute-command", payload)

    def sync_files(self, source_path: str, targets: list[str], *, strategy: str = "mirror") -> dict[str, Any]:
        return self._post_tool(
            "sync-files",
            {"source_path": source_path, "targets": targets, "strategy": strategy},
        )

    def get_node_info(self) -> dict[str, Any]:
        return self._post_tool("get-node-info", {})


class LocalNodeClient:
    """Client that calls the in-process node tools (useful for tests/dev)."""

    def __init__(self, definition: NodeDefinition) -> None:
        if not definition.root_dir:
            raise ValueError("Local transport requires root_dir")
        allowed = definition.allowed_commands or ["python", "ls", "cat", "echo"]
        sync_targets = definition.sync_targets or {}
        self.config = NodeConfig(
            node_id=definition.node_id,
            root_dir=definition.root_dir,
            tags=definition.tags,
            description=definition.display_name,
            allowed_commands=allowed,
            sync_targets=sync_targets,
        )

    def list_files(self, path: str, *, recursive: bool = False, pattern: str | None = None, include_hash: bool = False) -> list[FileMetadata]:
        target = Path(path)
        if not target.is_absolute():
            target = (self.config.root_dir / path).resolve()
        files = list_files(
            path=target,
            recursive=recursive,
            pattern=pattern,
            include_hash=include_hash,
            root=str(self.config.root_dir),
        )
        return files

    def read_file(self, path: str) -> dict[str, Any]:
        return read_file_tool(self.config, {"path": path})

    def write_file(self, path: str, content: str, *, overwrite: bool = False) -> dict[str, Any]:
        return write_file_tool(
            self.config,
            {"path": path, "content": content, "overwrite": overwrite, "create_dirs": True, "backup": True},
        )

    def execute_command(
        self,
        command: list[str] | str,
        *,
        timeout: float | None = None,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        payload = {"command": command}
        if timeout is not None:
            payload["timeout"] = timeout
        if cwd:
            payload["cwd"] = cwd
        if env:
            payload["env"] = env
        return execute_command_tool(self.config, payload)

    def sync_files(self, source_path: str, targets: list[str], *, strategy: str = "mirror") -> dict[str, Any]:
        return sync_files_tool(
            self.config,
            {"source_path": source_path, "targets": targets, "strategy": strategy},
        )

    def get_node_info(self) -> dict[str, Any]:
        return get_node_info_tool(self.config, {})


@dataclass(slots=True)
class NodeStatus:
    node_id: str
    display_name: str | None
    tags: list[str]
    last_seen: float | None = None
    healthy: bool = False
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class NodeRegistry:
    """Registry wrapping all configured nodes and their clients."""

    def __init__(self, definitions: Iterable[NodeDefinition]) -> None:
        self._definitions = {definition.node_id: definition for definition in definitions}
        self._clients: dict[str, NodeClient] = {
            node_id: self._build_client(definition)
            for node_id, definition in self._definitions.items()
        }
        self._status: dict[str, NodeStatus] = {
            node_id: NodeStatus(node_id=node_id, display_name=definition.display_name, tags=definition.tags)
            for node_id, definition in self._definitions.items()
        }
        self._lock = threading.Lock()

    def _build_client(self, definition: NodeDefinition) -> NodeClient:
        if definition.transport == "http":
            return HTTPNodeClient(definition)
        return LocalNodeClient(definition)

    def get_client(self, node_id: str) -> NodeClient:
        try:
            return self._clients[node_id]
        except KeyError as exc:  # pragma: no cover - defensive
            raise KeyError(f"Unknown node_id: {node_id}") from exc

    def definitions(self) -> list[NodeDefinition]:
        return list(self._definitions.values())

    def get_definition(self, node_id: str) -> NodeDefinition:
        try:
            return self._definitions[node_id]
        except KeyError as exc:  # pragma: no cover - defensive
            raise KeyError(f"Unknown node_id: {node_id}") from exc

    def statuses(self) -> list[NodeStatus]:
        return list(self._status.values())

    def refresh_status(self, node_id: str) -> NodeStatus:
        client = self.get_client(node_id)
        status = self._status[node_id]
        try:
            info = client.get_node_info()
            status.metrics = info.get("metrics", {})
            status.healthy = True
            status.error = None
            status.last_seen = time.time()
        except Exception as exc:  # pragma: no cover - network failures
            status.healthy = False
            status.error = str(exc)
        return status

    def refresh_all(self) -> list[NodeStatus]:
        with self._lock:
            return [self.refresh_status(node_id) for node_id in self._definitions]

    def choose_node(self, preferred_tags: list[str] | None = None) -> NodeDefinition:
        candidates = self.definitions()
        if preferred_tags:
            filtered = [node for node in candidates if set(preferred_tags).intersection(node.tags)]
            if filtered:
                candidates = filtered
        return sorted(candidates, key=lambda node: (node.priority, node.node_id))[0]

    def to_dict(self) -> list[dict[str, Any]]:
        return [
            {
                "node_id": status.node_id,
                "display_name": status.display_name,
                "tags": status.tags,
                "healthy": status.healthy,
                "last_seen": status.last_seen,
                "metrics": status.metrics,
                "error": status.error,
            }
            for status in self._status.values()
        ]


__all__ = [
    "NodeClient",
    "HTTPNodeClient",
    "LocalNodeClient",
    "NodeRegistry",
    "NodeStatus",
]