"""Configuration helpers for the NACC node server."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class NodeConfig(BaseModel):
    node_id: str = Field(..., description="Unique identifier for the node")
    root_dir: Path = Field(..., description="Root directory exposed by the node")
    tags: list[str] = Field(default_factory=list)
    description: str | None = None
    allowed_commands: list[str] = Field(
        default_factory=lambda: ["python", "ls", "cat", "echo"],
        description="Simple whitelist of commands allowed in ExecuteCommand",
    )
    sync_targets: dict[str, Path] = Field(
        default_factory=dict,
        description="Mapping of sync target names to directories",
    )

    @field_validator("root_dir", mode="before")
    def _expand_root(cls, value: Any) -> Path:
        return Path(value).expanduser().resolve()

    @field_validator("sync_targets", mode="before")
    def _expand_targets(cls, value: dict[str, Any]) -> dict[str, Path]:
        if not value:
            return {}
        return {key: Path(path).expanduser().resolve() for key, path in value.items()}


def load_node_config(path: str | Path) -> NodeConfig:
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Node config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return NodeConfig(**data)
