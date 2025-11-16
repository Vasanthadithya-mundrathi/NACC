"""Configuration helpers for the Gradio UI."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, HttpUrl


class UIConfig(BaseModel):
    orchestrator_url: HttpUrl = Field(..., description="Base URL for the orchestrator API")
    host: str = Field(default="0.0.0.0", description="Host/IP to bind the Gradio server")
    port: int = Field(default=7860, description="Port for the Gradio server")
    refresh_interval: float = Field(default=5.0, gt=1.0)


def load_ui_config(path: str | Path) -> UIConfig:
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"UI config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return UIConfig(**data)


__all__ = ["UIConfig", "load_ui_config"]
