"""Command-line entry point for the NACC Gradio UI."""

from __future__ import annotations

import argparse
import json

from .app import build_interface
from .config import load_ui_config


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="NACC UI (Gradio dashboard)")
    parser.add_argument(
        "--config",
        type=str,
        default="ui-config.yml",
        help="Path to UI configuration file",
    )
    parser.add_argument("--share", action="store_true", help="Launch Gradio with public share link")
    parser.add_argument("--dry-run", action="store_true", help="Validate config without starting the UI")
    args = parser.parse_args(argv)

    config = load_ui_config(args.config)
    interface = build_interface(config)
    if args.dry_run:
        print(json.dumps({"orchestrator_url": str(config.orchestrator_url), "host": config.host, "port": config.port}, indent=2))
        return

    interface.launch(
        server_name=config.host,
        server_port=config.port,
        share=args.share,
        show_api=False,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
