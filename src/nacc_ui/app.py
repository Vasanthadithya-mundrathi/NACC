"""Gradio Blocks application for the NACC dashboard."""

from __future__ import annotations

import json
from typing import Any

import gradio as gr
import requests

from .config import UIConfig


class OrchestratorHttpClient:
    def __init__(self, base_url: str | Any) -> None:  # type: ignore[override]
        self.base_url = str(base_url).rstrip("/")

    def list_nodes(self) -> list[dict[str, Any]]:
        response = requests.get(f"{self.base_url}/nodes", timeout=15)
        response.raise_for_status()
        return response.json()

    def list_files(self, node_id: str, path: str, recursive: bool = False) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/nodes/{node_id}/files",
            json={"path": path, "recursive": recursive},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def execute_command(
        self,
        description: str,
        command: str,
        *,
        preferred_tags: list[str] | None,
        parallelism: int,
    ) -> dict[str, Any]:
        payload = {
            "description": description,
            "command": command.strip() if isinstance(command, str) else command,
            "preferred_tags": preferred_tags,
            "parallelism": parallelism,
        }
        response = requests.post(f"{self.base_url}/commands/execute", json=payload, timeout=60)
        response.raise_for_status()
        return response.json()


def build_interface(config: UIConfig) -> gr.Blocks:
    client = OrchestratorHttpClient(config.orchestrator_url)

    def refresh_nodes() -> tuple[list[list[Any]], Any, Any]:
        nodes = client.list_nodes()
        rows = [
            [
                entry.get("node_id"),
                entry.get("display_name") or entry.get("node_id"),
                "✅" if entry.get("healthy") else "⚠️",
                (entry.get("metrics") or {}).get("cpu_percent"),
                (entry.get("metrics") or {}).get("memory_percent"),
                entry.get("last_seen"),
                ",".join(entry.get("tags") or []),
            ]
            for entry in nodes
        ]
        node_ids = [entry.get("node_id") for entry in nodes]
        default_selection = node_ids[0] if node_ids else None
        dropdown_update = gr.Dropdown.update(choices=node_ids, value=default_selection)
        file_dropdown_update = gr.Dropdown.update(choices=node_ids, value=default_selection)
        return rows, dropdown_update, file_dropdown_update

    def browse(node_id: str, path: str, recursive: bool) -> tuple[list[list[Any]], str]:
        if not node_id:
            raise gr.Error("Select a node first")
        payload = client.list_files(node_id, path, recursive)
        rows = [
            [entry["relative_path"], entry["is_dir"], entry["size"], entry["modified"], entry.get("hash")]
            for entry in payload["files"]
        ]
        return rows, json.dumps(payload, indent=2)

    def run_command(description: str, command: str, tags: str, parallelism: int) -> str:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] or None
        result = client.execute_command(description, command, preferred_tags=tag_list, parallelism=parallelism)
        return json.dumps(result, indent=2)

    with gr.Blocks(title="NACC Dashboard") as demo:
        gr.Markdown("# NACC – Network Agentic Connection Call")
        with gr.Tab("Nodes"):
            nodes_table = gr.Dataframe(headers=["Node ID", "Display", "Healthy", "CPU%", "Mem%", "Last Seen", "Tags"], datatype=["str", "str", "str", "number", "number", "number", "str"], interactive=False)
            refresh_btn = gr.Button("Refresh Nodes")
            node_dropdown = gr.Dropdown(label="Node", choices=[], interactive=True)
        with gr.Tab("Files"):
            with gr.Row():
                file_node = gr.Dropdown(label="Node", interactive=True)
                file_path = gr.Textbox(label="Path", value=".")
                file_recursive = gr.Checkbox(label="Recursive", value=False)
            file_table = gr.Dataframe(headers=["Path", "Dir?", "Size", "Modified", "Hash"], datatype=["str", "bool", "number", "number", "str"], interactive=False)
            file_json = gr.Code(language="json", label="Raw Response")
            browse_btn = gr.Button("List Files")
            browse_btn.click(fn=browse, inputs=[file_node, file_path, file_recursive], outputs=[file_table, file_json])
            node_dropdown.change(
                fn=lambda value: gr.Dropdown.update(value=value),
                inputs=node_dropdown,
                outputs=file_node,
            )
        with gr.Tab("Command Center"):
            cmd_description = gr.Textbox(label="Description", value="Ad-hoc command")
            cmd_input = gr.Textbox(label="Command", placeholder="echo 'hello from node'")
            cmd_tags = gr.Textbox(label="Preferred tags (comma separated)")
            cmd_parallel = gr.Slider(label="Parallelism", minimum=1, maximum=4, value=1, step=1)
            cmd_output = gr.Code(language="json", label="Execution Result")
            run_btn = gr.Button("Run Command")
            run_btn.click(fn=run_command, inputs=[cmd_description, cmd_input, cmd_tags, cmd_parallel], outputs=cmd_output)

        refresh_btn.click(fn=refresh_nodes, outputs=[nodes_table, node_dropdown, file_node])

    return demo


__all__ = ["build_interface"]
