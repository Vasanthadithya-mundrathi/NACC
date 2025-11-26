"""Node MCP tool implementations and lightweight HTTP server."""

from __future__ import annotations

import json
import logging
import os
import platform
import shlex
import shutil
import subprocess
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Dict

import psutil
from pydantic import BaseModel, Field, ValidationError

from .config import NodeConfig
from .filesystem import hash_file, list_files

logger = logging.getLogger(__name__)

ToolFunc = Callable[[NodeConfig, dict[str, Any]], dict[str, Any]]


def _resolve_within_root(root: Path, requested: str) -> Path:
    candidate = Path(requested)
    candidate = candidate.expanduser()
    if not candidate.is_absolute():
        candidate = (root / candidate).resolve()
    else:
        candidate = candidate.resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise PermissionError(f"Requested path escapes root: {candidate}") from exc
    return candidate


class ListFilesRequest(BaseModel):
    path: str = "."
    recursive: bool = False
    pattern: str | None = None
    include_hash: bool = False
    limit: int | None = Field(default=None, ge=1, le=20_000)


class ReadFileRequest(BaseModel):
    path: str
    encoding: str | None = "utf-8"
    max_bytes: int | None = Field(default=None, ge=1, le=50_000_000)


class WriteFileRequest(BaseModel):
    path: str
    content: str
    encoding: str = "utf-8"
    overwrite: bool = False
    create_dirs: bool = True
    backup: bool = True


class ExecuteCommandRequest(BaseModel):
    command: list[str] | str
    timeout: float = Field(default=60.0, gt=0, le=600)
    env: dict[str, str] = Field(default_factory=dict)
    cwd: str | None = None


class SyncFilesRequest(BaseModel):
    source_path: str
    targets: list[str] = Field(..., min_length=1)
    strategy: str = Field(default="mirror", pattern=r"^(mirror|append)$")


class GetNodeInfoRequest(BaseModel):
    include_processes: bool = False


@dataclass(slots=True)
class SyncReport:
    target: str
    dest_path: str
    files_synced: int
    bytes_copied: int
    duration: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "dest_path": self.dest_path,
            "files_synced": self.files_synced,
            "bytes_copied": self.bytes_copied,
            "duration": self.duration,
        }


def list_files_tool(config: NodeConfig, payload: dict[str, Any]) -> dict[str, Any]:
    request = ListFilesRequest.model_validate(payload)
    target = _resolve_within_root(config.root_dir, request.path)
    files = list_files(
        target,
        recursive=request.recursive,
        pattern=request.pattern,
        include_hash=request.include_hash,
        root=config.root_dir,
    )
    if request.limit is not None:
        files = files[: request.limit]
    return {"files": [file.to_dict() for file in files], "count": len(files)}


def read_file_tool(config: NodeConfig, payload: dict[str, Any]) -> dict[str, Any]:
    request = ReadFileRequest.model_validate(payload)
    target = _resolve_within_root(config.root_dir, request.path)
    if not target.exists():
        raise FileNotFoundError(str(target))
    if target.is_dir():
        raise IsADirectoryError(str(target))

    data = target.read_bytes()
    if request.max_bytes and len(data) > request.max_bytes:
        raise ValueError("File exceeds max_bytes limit")

    content: str | None = None
    if request.encoding:
        content = data.decode(request.encoding)
    return {
        "path": str(target.relative_to(config.root_dir)),
        "size": len(data),
        "hash": hash_file(target),
        "content": content,
    }


def write_file_tool(config: NodeConfig, payload: dict[str, Any]) -> dict[str, Any]:
    request = WriteFileRequest.model_validate(payload)
    target = _resolve_within_root(config.root_dir, request.path)
    target.parent.mkdir(parents=True, exist_ok=request.create_dirs)

    backup_path: Path | None = None
    if target.exists():
        if not request.overwrite:
            raise FileExistsError(str(target))
        if request.backup:
            timestamp = int(time.time())
            backup_path = target.parent / f"{target.name}.bak.{timestamp}"
            shutil.copy2(target, backup_path)

    data = request.content.encode(request.encoding)
    target.write_bytes(data)
    file_hash = hash_file(target)
    return {
        "success": True,
        "path": str(target.relative_to(config.root_dir)),
        "bytes_written": len(data),
        "hash": file_hash,
        "backup_path": str(backup_path) if backup_path else None,
        "message": f"File written successfully: {target.relative_to(config.root_dir)}"
    }


def execute_command_tool(config: NodeConfig, payload: dict[str, Any]) -> dict[str, Any]:
    request = ExecuteCommandRequest.model_validate(payload)
    if isinstance(request.command, str):
        command = shlex.split(request.command)
    else:
        command = request.command

    if not command:
        raise ValueError("Command cannot be empty")

    base_cmd = Path(command[0]).name
    if base_cmd not in config.allowed_commands:
        raise PermissionError(f"Command '{base_cmd}' not on allow list")

    cwd = _resolve_within_root(config.root_dir, request.cwd) if request.cwd else config.root_dir

    env = os.environ.copy()
    env.update({key: value for key, value in request.env.items() if isinstance(value, str)})

    started = time.time()
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=request.timeout,
    )
    duration = time.time() - started
    return {
        "command": command,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "exit_code": proc.returncode,
        "duration": duration,
        "cwd": str(cwd.relative_to(config.root_dir)),
    }


def sync_files_tool(config: NodeConfig, payload: dict[str, Any]) -> dict[str, Any]:
    request = SyncFilesRequest.model_validate(payload)
    source = _resolve_within_root(config.root_dir, request.source_path)
    if not source.exists():
        raise FileNotFoundError(str(source))

    reports: list[SyncReport] = []
    source_rel = source.relative_to(config.root_dir)

    for target_name in request.targets:
        if target_name not in config.sync_targets:
            raise ValueError(f"Unknown sync target: {target_name}")
        target_dir = config.sync_targets[target_name]
        dest_root = target_dir / source_rel
        dest_root.parent.mkdir(parents=True, exist_ok=True)

        started = time.time()
        files_synced, bytes_copied = _copy_path(source, dest_root, strategy=request.strategy)
        duration = time.time() - started
        reports.append(
            SyncReport(
                target=target_name,
                dest_path=str(dest_root),
                files_synced=files_synced,
                bytes_copied=bytes_copied,
                duration=duration,
            )
        )

    return {
        "source": str(source_rel),
        "targets": [report.to_dict() for report in reports],
    }


def _copy_path(source: Path, dest: Path, *, strategy: str) -> tuple[int, int]:
    files_synced = 0
    bytes_copied = 0

    if source.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        files_synced = 1
        bytes_copied = source.stat().st_size
        return files_synced, bytes_copied

    if strategy == "mirror" and dest.exists():
        shutil.rmtree(dest)

    for src_file in source.rglob("*"):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(source)
        dest_file = dest / rel
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        files_synced += 1
        bytes_copied += src_file.stat().st_size

    return files_synced, bytes_copied


def get_node_info_tool(config: NodeConfig, payload: dict[str, Any]) -> dict[str, Any]:
    _ = GetNodeInfoRequest.model_validate(payload or {})
    cpu = psutil.cpu_percent(interval=0.05)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(str(config.root_dir))
    boot_time = psutil.boot_time()

    return {
        "node_id": config.node_id,
        "tags": config.tags,
        "description": config.description,
        "root_dir": str(config.root_dir),
        "allowed_commands": config.allowed_commands,
        "sync_targets": {key: str(value) for key, value in config.sync_targets.items()},
        "metrics": {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_total": mem.total,
            "disk_percent": disk.percent,
            "disk_total": disk.total,
            "uptime_seconds": time.time() - boot_time,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        },
        "timestamp": time.time(),
    }


class NodeServer:
    """Minimal HTTP server that exposes node tools as JSON endpoints."""

    def __init__(self, config: NodeConfig, *, host: str = "0.0.0.0", port: int = 8765):
        self.config = config
        self.host = host
        self.port = port
        self._httpd: ThreadingHTTPServer | None = None

    def serve_forever(self) -> None:
        handler = self._build_handler()
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        logger.info("[nacc-node] serving http://%s:%s", self.host, self.port)
        try:
            self._httpd.serve_forever()
        finally:
            self._httpd.server_close()
            logger.info("[nacc-node] server stopped")

    def shutdown(self) -> None:
        if self._httpd:
            self._httpd.shutdown()

    def _build_handler(self) -> type[BaseHTTPRequestHandler]:
        config = self.config
        tools: Dict[str, ToolFunc] = {
            "list-files": list_files_tool,
            "read-file": read_file_tool,
            "write-file": write_file_tool,
            "execute-command": execute_command_tool,
            "sync-files": sync_files_tool,
            "get-node-info": get_node_info_tool,
        }
        max_body = 512 * 1024

        class NodeRequestHandler(BaseHTTPRequestHandler):
            server_version = "NACCNode/0.3"

            def log_message(self, format: str, *args: Any) -> None:  # pragma: no cover - HTTP logging
                logger.info("%s - %s", self.address_string(), format % args)

            def _read_json_body(self) -> dict[str, Any]:
                content_length = int(self.headers.get("Content-Length", 0))
                if content_length > max_body:
                    raise ValueError("Payload too large")
                if content_length <= 0:
                    return {}
                body = self.rfile.read(content_length)
                if not body:
                    return {}
                return json.loads(body.decode("utf-8"))

            def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
                data = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self) -> None:  # noqa: N802 - required name
                if self.path == "/healthz" or self.path == "/":
                    self._send_json(HTTPStatus.OK, {
                        "status": "ok",
                        "service": "nacc-node",
                        "node_id": config.node_id
                    })
                    return
                if self.path == "/node":
                    payload = get_node_info_tool(config, {})
                    self._send_json(HTTPStatus.OK, payload)
                    return
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not Found"})

            def do_POST(self) -> None:  # noqa: N802 - required name
                if not self.path.startswith("/tools/"):
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "Unknown endpoint"})
                    return
                tool_name = self.path.split("/", 2)[-1]
                tool = tools.get(tool_name)
                if not tool:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": f"Tool '{tool_name}' not available"})
                    return

                try:
                    payload = self._read_json_body()
                    result = tool(config, payload)
                except json.JSONDecodeError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON", "details": str(exc)})
                    return
                except ValidationError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Validation failed", "details": exc.errors()})
                    return
                except PermissionError as exc:
                    self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
                    return
                except FileNotFoundError as exc:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
                    return
                except Exception as exc:  # pragma: no cover - defensive guard
                    logger.exception("Tool '%s' crashed", tool_name)
                    self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
                    return

                self._send_json(HTTPStatus.OK, result)

        return NodeRequestHandler


__all__ = [
    "NodeServer",
    "list_files_tool",
    "read_file_tool",
    "write_file_tool",
    "execute_command_tool",
    "sync_files_tool",
    "get_node_info_tool",
]
