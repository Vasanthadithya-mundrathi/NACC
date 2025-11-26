"""Command-line entry point for the NACC node server.

Currently a stub that just prints configuration info; to be extended with
actual MCP server startup logic.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .filesystem import list_files
from .config import load_node_config
from .tools import NodeServer


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NACC node MCP server")
    subparsers = parser.add_subparsers(dest="command")

    serve = subparsers.add_parser("serve", help="Start the MCP node server")
    serve.add_argument("--host", default="0.0.0.0", help="Host/IP to bind (default 0.0.0.0)")
    serve.add_argument("--port", type=int, default=8765, help="Port to listen on")
    serve.add_argument(
        "--config",
        type=str,
        default="node-config.yml",
        help="Path to node configuration file",
    )
    serve.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and exit without starting the server",
    )

    init_parser = subparsers.add_parser("init", help="Initialize a new node and generate pairing code")

    list_parser = subparsers.add_parser("list-files", help="List files on this node")
    list_parser.add_argument("--path", default=".", help="Path to inspect")
    list_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recurse into subdirectories",
    )
    list_parser.add_argument(
        "--filter",
        dest="pattern",
        default=None,
        help="Glob filter applied to relative paths",
    )
    list_parser.add_argument(
        "--with-hash",
        action="store_true",
        help="Compute sha256 for files (slower)",
    )
    list_parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Optional node-config file to scope the path to the node root",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    parsed_args = list(argv) if argv is not None else sys.argv[1:]
    if not parsed_args or parsed_args[0].startswith("-"):
        parsed_args = ["serve", *parsed_args]
    args = parser.parse_args(parsed_args)

    if args.command == "list-files":
        root_override: Path | None = None
        target_path = Path(args.path)
        if args.config:
            config = load_node_config(args.config)
            root_override = config.root_dir
            if not target_path.is_absolute():
                target_path = (root_override / target_path).resolve()
        files = list_files(
            target_path,
            recursive=args.recursive,
            pattern=args.pattern,
            include_hash=args.with_hash,
            root=str(root_override) if root_override else None,
        )
        payload = {"files": [file.to_dict() for file in files], "count": len(files)}
        print(json.dumps(payload, indent=2))
        return

    if args.command == "init":
        import uuid
        from .pairing import create_session
        
        # Generate defaults
        node_id = str(uuid.uuid4())
        root_dir = Path.cwd().resolve()
        
        # Create config structure
        config_data = {
            "node_id": node_id,
            "root_dir": str(root_dir),
            "display_name": f"Node-{node_id[:8]}",
            "tags": ["generic"],
            "allowed_commands": ["python", "ls", "cat", "echo", "grep"],
            "sync_targets": {}
        }
        
        # Generate pairing code
        session = create_session(node_id)
        
        # Save config
        output_path = Path("node-config.yml")
        if output_path.exists():
            print(f"Config file {output_path} already exists. Skipping creation.")
        else:
            import yaml
            with open(output_path, "w") as f:
                yaml.dump(config_data, f)
            print(f"Created {output_path}")

        print("\n" + "="*40)
        print(f"🚀 Node Initialized: {config_data['display_name']}")
        print(f"🆔 Node ID: {node_id}")
        print(f"🔑 PAIRING CODE: {session.code}")
        print("="*40)
        print("\nRun this on your orchestrator to pair:")
        print(f"  nacc-orchestrator register-node {session.code} --ip <THIS_NODE_IP>")
        print("\n(Note: The code is for display only in this version. Use the ID/IP for manual registration if needed.)")
        return

    if args.command in (None, "serve"):
        config_path = getattr(args, "config", "node-config.yml")
        config = load_node_config(config_path)
        if getattr(args, "dry_run", False):
            summary = {
                "node_id": config.node_id,
                "root_dir": str(config.root_dir),
                "tags": config.tags,
                "allowed_commands": config.allowed_commands,
                "sync_targets": {key: str(value) for key, value in config.sync_targets.items()},
            }
            print(json.dumps(summary, indent=2))
            return

        host = getattr(args, "host", "0.0.0.0")
        port = getattr(args, "port", 8765)
        server = NodeServer(config, host=host, port=port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:  # pragma: no cover - manual interrupt
            print("\n[nacc-node] shutdown requested")
            server.shutdown()
        return

    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":  # pragma: no cover
    main()
