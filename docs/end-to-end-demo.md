# End-to-End Demo Guide

Run the full NACC stack (node server → orchestrator → agents → UI) on a single machine, a trio of VMs, or a hybrid cloud.

## 1. Prerequisites
- Python 3.12 (run `./setup_nacc.sh` to bootstrap a virtualenv and install deps).
- At least one directory to expose via `nacc_node` (`demo-root` works for local tests).
- Optional: a Docker container running Mistral-NeMo (`ccdfa597c64`) if you want real LLM routing.

## 2. Configure the Components
1. **Node:**
   ```bash
   cp configs/node-config.example.yml node-local.yml
   sed -i '' 's#./demo-root#/absolute/path/to/share#g' node-local.yml
   ```
2. **Orchestrator:**
   ```bash
   cp configs/orchestrator-config.example.yml orchestrator.yml
   # Point `root_dir` entries to the same folder as above when using `transport: local`.
   ```
3. **UI:**
   ```bash
   cp configs/ui-config.example.yml ui.yml
   ```

## 3. Start the Services
1. **Node server** (terminal 1):
   ```bash
   source .venv/bin/activate
   nacc-node serve --config node-local.yml --host 127.0.0.1 --port 8765
   ```
2. **(Optional) VMs/containers** – repeat the command with `node-linux-vm.yml` / `node-windows-vm.yml` and unique ports (8766/8767). Use SSH tunnels if they run remotely.
3. **Orchestrator API** (terminal 2):
   ```bash
   source .venv/bin/activate
   nacc-orchestrator serve --config orchestrator.yml --host 127.0.0.1 --port 8888
   ```
4. **Agent backend probe** (terminal 3):
   ```bash
   source .venv/bin/activate
   nacc-orchestrator agents-check --config orchestrator.yml --message "health check"
   ```
5. **Gradio UI** (terminal 4):
   ```bash
   source .venv/bin/activate
   nacc-ui serve --config ui.yml --share
   ```

## 4. Multi-Node Demo Script

1. **File browser** – choose each node in the Files tab, list `.` and show metadata.
2. **Edit & sync** – modify `shared/demo.txt` on `laptop-dev`, run `SyncFiles` targeting the VMs, then re-list to show updated checksum.
3. **Parallel jobs** – in Command Center, run `python -c "print('hello from', __import__('socket').gethostname())"` with `parallelism=3` to show simultaneous logs.
4. **Resilience** – stop `linux-vm`; it turns ⚠️ in Nodes tab. `nacc-orchestrator exec` automatically reroutes to healthy nodes.
5. **Reconnect** – restart the VM/node; router picks it up within the refresh interval.
6. **CLI parity** – run:
    ```bash
    nacc-orchestrator list-files --config orchestrator.yml --node laptop-dev --path shared
    nacc-orchestrator exec --config orchestrator.yml --description "smoke" --cmd echo demo-complete
    ```
7. **Audit proof** – `tail -f logs/audit.log` to show every action recorded.

## 5. Docker-Based LLM Backend
- Ensure the Mistral container is running and export its ID if different:
  ```bash
  export NACC_DOCKER_LLM_CONTAINER=$(docker ps -qf name=mistral-nemo)
  ```
- Update `orchestrator.yml`:
  ```yaml
  agent_backend:
    kind: docker-mistral
    container_id: ${NACC_DOCKER_LLM_CONTAINER}
    command: ["python", "/opt/mistral/mcp_router.py"]
  ```
- Re-run `nacc-orchestrator agents-check --config orchestrator.yml`. Successful responses indicate the Docker backend is reachable.

## 6. Testnet & CI Modes

- **Docker Compose:** `docker-compose -f docker-compose.testnet.yml up --build` launches the orchestrator + two nodes locally.
- **Pytest:** run `pytest` (21 tests) or `pytest tests/test_end_to_end.py -vv` for the orchestrator-focused flow.
- **GitHub Actions idea:** spin up a self-hosted runner, install `nacc`, register it as a node, run builds/tests via `nacc-orchestrator exec`, then deregister on teardown.
- **Shortcut script:** create `scripts/testnet.sh` that spawns three `nacc-node` processes with different configs for rapid local iteration.

## 7. Troubleshooting
- `agents-check` hangs → ensure Docker container ID is correct, or switch to `local-heuristic` backend.
- Nodes missing → confirm `node_id` matches YAML on both sides and that ports 8765/8766/8767 are reachable (firewall/VPN).
- UI stale → click **Refresh Nodes** or reduce `refresh_interval` in `ui.yml`.
- Cloud VM blocked → use `ssh -L 9876:localhost:8765 user@vm` and point `base_url` to `http://127.0.0.1:9876`.
