# Detailed Usage Scenario – "Laptop + Two VMs"

This walkthrough demonstrates how to run NACC across a host laptop plus two virtual machines (or containers), exercise the MCP tools end-to-end, and capture evidence that the system is working.

## Topology

| Node | Role | Config file | Notes |
| --- | --- | --- | --- |
| Laptop | Primary orchestrator + node | `configs/node-laptop.yml` | Runs UI + orchestrator; node uses `root_dir: ./demo-root/laptop`. |
| Linux VM | Remote compute node | `configs/node-linux-vm.yml` | Exposed over SSH tunnel or LAN. |
| Windows VM | Remote compute node | `configs/node-windows-vm.yml` | Exposed over SSH tunnel or LAN. |

The orchestrator consumes `configs/orchestrator-three-node.yml` and agents use the local heuristic backend unless you export `NACC_DOCKER_LLM_CONTAINER`.

## Step 1 – Prep Demo Assets

Shortcut: run `scripts/run_demo.sh` to generate temporary configs, start three local nodes, the orchestrator, and the UI automatically. For manual multi-host demos, continue below.

```bash
cp configs/node-laptop.yml node-laptop.yml
cp configs/node-linux-vm.yml node-linux-vm.yml
cp configs/node-windows-vm.yml node-windows-vm.yml
cp configs/orchestrator-three-node.yml orchestrator.yml
cp configs/ui-config.example.yml ui.yml
```

Adjust paths/ports as needed (e.g., update `root_dir` to real directories on each machine).

## Step 2 – Start Node Servers

### Laptop (local)
```bash
source .venv/bin/activate
nacc-node serve --config node-laptop.yml --host 0.0.0.0 --port 8765
```

### Linux VM (remote)
```bash
ssh ubuntu@linux-vm 'cd /opt/nacc && source .venv/bin/activate && nacc-node serve --config node-linux-vm.yml --host 0.0.0.0 --port 8766'
```
If the VM is behind a firewall, create a tunnel back to the orchestrator host:
```bash
ssh -N -L 9876:127.0.0.1:8766 ubuntu@linux-vm
```
Then change `orchestrator.yml` to point the node at `http://127.0.0.1:9876`.

### Windows VM (PowerShell)
```powershell
cd C:\nacc
.\.venv\Scripts\activate.ps1
nacc-node serve --config node-windows-vm.yml --host 0.0.0.0 --port 8767
```
Tunnel example:
```powershell
ssh -N -L 9877:127.0.0.1:8767 user@windows-vm
```

## Step 3 – Launch Orchestrator + UI

Terminal 1 (orchestrator):
```bash
source .venv/bin/activate
nacc-orchestrator serve --config orchestrator.yml --host 127.0.0.1 --port 8888
```

Terminal 2 (agent probe):
```bash
source .venv/bin/activate
nacc-orchestrator agents-check --config orchestrator.yml --message "live demo"
```

Terminal 3 (UI):
```bash
source .venv/bin/activate
nacc-ui serve --config ui.yml --share
```
Open the provided Gradio link; you should see three nodes with health indicators.

## Step 4 – Demo Flow

1. **Nodes tab** – click *Refresh Nodes*. Verify laptop/linux-vm/windows-vm appear with ✅.
2. **Files tab** – select `laptop-dev`, browse `shared`. Upload or edit a file (e.g., `demo.txt`) using your editor, click *List Files* to confirm metadata.
3. **Sync** – run the CLI sync helper:
   ```bash
   curl -X POST http://127.0.0.1:8888/sync -H 'Content-Type: application/json' \
     -d '{"source_node":"laptop-dev","source_path":"shared/demo.txt","target_nodes":["linux-vm","windows-vm"],"strategy":"mirror"}'
   ```
   Re-run the Files tab on linux/windows nodes to see the file replicated.
4. **Parallel command** – in Command Center, set Description `"Test suite"`, Command `pytest -q`, Preferred tags `linux-vm,windows-vm`, Parallelism `2`. Observe JSON output showing two entries with exit codes.
5. **Failure simulation** – stop the Windows node process. The Nodes tab shows ⚠️; rerun the parallel command to see Router Agent target only healthy machines. Restart the node and watch it return to ✅.
6. **Audit review** – tail the audit log:
   ```bash
   tail -f logs/audit.log
   ```
   Confirm entries for `list_files`, `execute_command`, `sync_path`, `agent_probe`.

## Step 5 – CLI Proof Points

Run the following from your laptop:
```bash
nacc-orchestrator list-files --config orchestrator.yml --node linux-vm --path shared
nacc-orchestrator exec --config orchestrator.yml --description "hello" --cmd echo from-nacc
```
Capture the JSON output (node IDs, stdout, router reasoning) as evidence of end-to-end execution.

## Step 6 – Success Criteria

- All three nodes display healthy metrics in the UI.
- Agent probe succeeds (non-empty JSON response).
- ListFiles, SyncFiles, and ExecuteCommand work from both UI and CLI.
- Audit log contains every action.
- Disconnecting a node triggers Router to reroute tasks automatically.

Use this script during live demos or integration testing to show that NACC orchestrates real machines/VMs with tangible workflows.
