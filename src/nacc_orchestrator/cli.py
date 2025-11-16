"""Command-line entry point for the NACC orchestrator."""

from __future__ import annotations

import argparse
import json
import sys

import uvicorn

from .config import load_orchestrator_config
from .server import create_app
from .service import OrchestratorService


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NACC orchestrator")
    subparsers = parser.add_subparsers(dest="command")

    serve = subparsers.add_parser("serve", help="Start the orchestrator API server")
    serve.add_argument(
        "--config",
        type=str,
        default="orchestrator-config.yml",
        help="Path to orchestrator configuration file",
    )
    serve.add_argument("--host", default="0.0.0.0", help="Host/IP to bind")
    serve.add_argument("--port", type=int, default=8888, help="Port to listen on")

    list_parser = subparsers.add_parser(
        "list-files", help="Proxy ListFiles tool via the orchestrator"
    )
    list_parser.add_argument("--config", default="orchestrator-config.yml", help="Config file path")
    list_parser.add_argument("--node", default="auto", help="Node ID to target or 'auto'")
    list_parser.add_argument("--path", default=".", help="Path to inspect on the node")
    list_parser.add_argument("--recursive", action="store_true", help="Recurse into directories")
    list_parser.add_argument("--filter", dest="pattern", default=None, help="Glob filter")
    list_parser.add_argument("--with-hash", action="store_true", help="Include sha256 for files")

    exec_parser = subparsers.add_parser("exec", help="Execute a command across nodes")
    exec_parser.add_argument("--config", default="orchestrator-config.yml")
    exec_parser.add_argument("--description", default="Ad-hoc command")
    exec_parser.add_argument("--cmd", dest="cmd", nargs=argparse.REMAINDER, required=True, help="Command and arguments to run")
    exec_parser.add_argument("--tags", nargs="*", default=None)
    exec_parser.add_argument("--parallelism", type=int, default=1)
    exec_parser.add_argument("--timeout", type=float, default=None)

    agents_check = subparsers.add_parser("agents-check", help="Probe the configured LLM backend")
    agents_check.add_argument("--config", default="orchestrator-config.yml")
    agents_check.add_argument(
        "--message",
        default="Ping from NACC orchestrator",
        help="Message to send to the agent backend during the probe",
    )

    return parser


def _load_service(config_path: str) -> OrchestratorService:
    config = load_orchestrator_config(config_path)
    return OrchestratorService(config)


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    parsed_args = list(argv) if argv is not None else sys.argv[1:]
    if not parsed_args or parsed_args[0].startswith("-"):
        parsed_args = ["serve", *parsed_args]
    args = parser.parse_args(parsed_args)

    if args.command == "list-files":
        service = _load_service(args.config)
        response = service.list_files(
            args.node,
            path=args.path,
            recursive=args.recursive,
            pattern=args.pattern,
            include_hash=args.with_hash,
        )
        print(json.dumps(response, indent=2))
        return

    if args.command == "exec":
        service = _load_service(args.config)
        if not args.cmd:
            parser.error("--cmd is required")
        response = service.execute_command(
            description=args.description,
            command=args.cmd,
            preferred_tags=args.tags,
            parallelism=args.parallelism,
            timeout=args.timeout,
        )
        print(json.dumps(response, indent=2))
        return

    if args.command == "agents-check":
        service = _load_service(args.config)
        response = service.check_agent_backend(args.message)
        print(json.dumps(response, indent=2))
        return

    if args.command in (None, "serve"):
        config_path = getattr(args, "config", "orchestrator-config.yml")
        service = _load_service(config_path)
        app = create_app(service)
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
        return

    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":  # pragma: no cover
    main()
