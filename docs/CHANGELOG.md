# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-15
### Added
- Initial architecture and planning docs for NACC (Network Agentic Connection Call).
- `README.md` with high-level architecture.
- `NACC-Quick-Reference.md` with daily execution checklist and hackathon plan.
- Initial project roadmap and milestone tracking.

## [0.2.0] - 2025-11-15
### Added
- Implemented `nacc_node.filesystem.list_files` with recursive traversal, glob filtering, optional hashing, and JSON helper.
- Extended `nacc-node` CLI with a `list-files` subcommand producing JSON output.
- Added `LocalNodeClient` and a matching `list-files` subcommand to `nacc-orchestrator` so the orchestrator can exercise the tool.
- Created automated tests for filesystem logic and CLI behavior.
- Introduced `docs/phase1-milestone.md` to track the single-node MCP tooling milestone.

## [0.3.0] - 2025-11-15
### Added
- Full MCP-style node server (`NodeServer`) exposing HTTP endpoints for ListFiles, ReadFile, WriteFile, ExecuteCommand, SyncFiles, and GetNodeInfo.
- YAML-driven `NodeConfig` loader plus a sample `configs/node-config.example.yml` for quick bootstrap.
- Tool implementations with path sandboxing, command allow-listing, sync support, and psutil-based node telemetry.
- Test coverage for every tool plus updated CLI smoke tests.

### Changed
- `nacc-node serve` now uses the real server, supports `--host`, `--dry-run`, and requires a config file.
- `nacc-node list-files` can scope requests to the configured root and optionally compute hashes.
- Project dependencies now include `pydantic` and `pyyaml`, and the package version bumped to `0.3.0`.

## [0.4.0] - 2025-11-15
### Added
- Full orchestrator core: node registry, FastAPI server, audit logger, Router/Execution/Security/Sync agents, and CLI commands (`serve`, `list-files`, `exec`, `agents-check`).
- Docker-backed Mistral-NeMo agent backend plus heuristic fallback, exposed through `/agents/probe` and the `agents-check` CLI for validation.
- Gradio dashboard featuring Nodes, Files, and Command Center tabs wired to the orchestrator API.
- New documentation (`docs/completion-plan.md`, `docs/end-to-end-demo.md`) outlining the roadmap and demo instructions.
- End-to-end pytest coverage (`tests/test_end_to_end.py`) that exercises the orchestrator planner, command execution, and audit logging.
- Multi-device collateral: `docs/node-discovery.md`, sample configs for laptop/linux/windows nodes, `configs/orchestrator-three-node.yml`, and `docker-compose.testnet.yml` for local testnets.

### Changed
- README upgraded with quickstart, backend instructions, and up-to-date phase tracking.
- README now highlights multi-device messaging, discovery/troubleshooting tips, security guidance, sponsor integrations, and a polished demo flow.
