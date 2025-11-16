"""Configuration helpers for the NACC orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, HttpUrl, ValidationError, field_validator, model_validator


class NodeDefinition(BaseModel):
    node_id: str
    display_name: str | None = None
    transport: Literal["http", "local"] = "http"
    base_url: HttpUrl | None = Field(
        default=None,
        description="Base URL for the node HTTP server when transport='http'",
    )
    root_dir: Path | None = Field(
        default=None,
        description="Local filesystem root when transport='local'",
    )
    tags: list[str] = Field(default_factory=list)
    priority: int = Field(default=100, description="Lower values considered first by Router agent")
    weight: float = Field(default=1.0, description="Relative weight for agent scoring")
    auth_token: str | None = None
    allowed_commands: list[str] | None = None
    sync_targets: dict[str, Path] | None = None

    @field_validator("root_dir", mode="before")
    def _expand_root(cls, value: Any) -> Path | None:
        if not value:
            return None
        return Path(value).expanduser().resolve()

    @field_validator("sync_targets", mode="before")
    def _expand_sync_targets(cls, value: dict[str, Any] | None) -> dict[str, Path] | None:
        if not value:
            return None
        return {name: Path(path).expanduser().resolve() for name, path in value.items()}

    @model_validator(mode="after")
    def _validate_transport(self) -> "NodeDefinition":
        if self.transport == "http" and not self.base_url:
            raise ValueError("base_url is required when transport='http'")
        if self.transport == "local" and not self.root_dir:
            raise ValueError("root_dir is required when transport='local'")
        return self


class AgentBackendConfig(BaseModel):
    kind: Literal["docker-mistral", "local-heuristic"] = "docker-mistral"
    container_id: str | None = Field(
        default=None,
        description="Docker container exposing the Mistral-NeMo runtime",
    )
    command: list[str] | None = Field(
        default=None,
        description="Optional custom command to invoke inside the container",
    )
    timeout: float = Field(default=90.0, gt=1.0, le=600.0)
    environment: dict[str, str] = Field(default_factory=dict)


class AuditConfig(BaseModel):
    path: Path = Field(default=Path("logs/audit.log"))
    max_entries: int = Field(default=50_000, ge=1000)

    @field_validator("path", mode="before")
    def _expand_path(cls, value: Any) -> Path:
        return Path(value).expanduser().resolve()


class OrchestratorConfig(BaseModel):
    orchestrator_id: str = "nacc-orchestrator"
    nodes: list[NodeDefinition]
    agent_backend: AgentBackendConfig = Field(default_factory=AgentBackendConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    refresh_interval: float = Field(default=10.0, gt=1.0, description="Node metrics refresh interval in seconds")

    @model_validator(mode="after")
    def _ensure_unique_nodes(self) -> "OrchestratorConfig":
        seen: set[str] = set()
        for node in self.nodes:
            if node.node_id in seen:
                raise ValueError(f"Duplicate node_id detected: {node.node_id}")
            seen.add(node.node_id)
        if not self.nodes:
            raise ValueError("At least one node must be configured")
        return self


def load_orchestrator_config(path: str | Path) -> OrchestratorConfig:
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Orchestrator config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    try:
        return OrchestratorConfig(**payload)
    except ValidationError as exc:  # pragma: no cover - converted error surface
        raise ValueError(f"Invalid orchestrator config: {exc}") from exc


__all__ = [
    "NodeDefinition",
    "AgentBackendConfig",
    "AuditConfig",
    "OrchestratorConfig",
    "load_orchestrator_config",
]
