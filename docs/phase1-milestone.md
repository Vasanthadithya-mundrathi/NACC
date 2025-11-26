# Phase 1 Milestone – Single-Node MCP Tooling

**Date:** 2025-11-15

## Goal
Build the first functional MCP tool (`ListFiles`) inside `nacc_node` and expose it through:

1. A Python module (so orchestrator and tests can call it programmatically)
2. The `nacc-node` CLI (e.g., `nacc-node list-files --path . --recursive`)
3. A simple orchestrator helper that invokes the tool locally (future: over MCP)

## Scope
- File metadata structure
- Recursive directory traversal with optional glob filtering
- Error handling (missing paths, permission issues)
- JSON-friendly output for future MCP transport
- Unit tests covering success + edge cases
- README + CHANGELOG updates documenting the new capability

## Out of Scope (for now)
- Remote MCP transport / sockets
- Authentication, sandboxing, sync logic
- UI wiring

## Acceptance Criteria
- `pytest` includes tests for `nacc_node.fs.list_files`
- `nacc-node list-files ...` prints a machine-readable JSON payload
- README mentions the new CLI usage
- Changelog entry added under the next version tag

Next phases will extend to ReadFile / WriteFile, then orchestrator networking.
