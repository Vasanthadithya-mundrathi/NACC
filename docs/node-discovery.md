# Node Discovery & Registration Guide

Use this guide to mix real hardware, VMs, and containers inside a single NACC deployment.

## 1. Mental Model

```
Laptop (host)
  ├─ VM #1 (Linux) ──> nacc-node (transport=http) ──> Orchestrator
  ├─ VM #2 (Windows) ─> nacc-node (transport=http) ──> Orchestrator
  └─ Local sandbox     ─> nacc-node (transport=local)
```

Every node exposes the same MCP surface—only the transport differs.

## 2. Manual Registration (Today)

Add entries to `orchestrator.yml`:

```yaml
nodes:
  - node_id: laptop
    transport: local
    root_dir: /Users/you/nacc-sandbox
    tags: [mac, primary]
  - node_id: vm-linux
    transport: http
    base_url: http://192.168.64.10:8765
    tags: [linux, vm]
  - node_id: vm-windows
    transport: http
    base_url: http://192.168.64.11:8765
    tags: [windows, vm]
```

Restart `nacc-orchestrator` (hot reload coming soon) and refresh the UI.

## 3. Automatic Discovery (Roadmap)

`nacc-orchestrator discover` will:

1. Broadcast Zeroconf/mDNS packets (`_nacc._tcp.local`).
2. Nodes respond with signed metadata.
3. Orchestrator proposes entries; operators approve/deny.

This mode is perfect for labs and hackathons where multicast is allowed.

## 4. Troubleshooting Checklist

| Symptom | Fix |
| --- | --- |
| Node missing in UI | Confirm `node_id` matches between node + orchestrator configs; restart orchestrator. |
| Health shows ⚠️ | Check `logs/audit.log`, run `curl http://node:port/healthz` directly. |
| Remote VM unreachable | Use `ssh -L`/`ssh -R` tunnels or Tailscale; ensure security groups allow port 8765. |
| Windows VM path issues | Set `root_dir` to a Windows path (e.g., `C:/Users/runner/nacc`) and escape backslashes in YAML. |

## 5. Cloud / VPN Patterns

- **SSH tunnel:** `ssh -N -L 9876:127.0.0.1:8765 user@vm`
- **Reverse tunnel:** `ssh -N -R 9876:127.0.0.1:8765 user@orchestrator`
- **WireGuard/Tailscale:** add all nodes to the mesh and point `base_url` to their tailnet IPs.
- **HTTPS ingress:** terminate TLS via Caddy/Traefik/ngrok; configure client certs and `auth_token`.

## 6. Sample Configurations

| File | Purpose |
| --- | --- |
| `configs/node-laptop.yml` | Local developer machine sandbox |
| `configs/node-linux-vm.yml` | Headless Ubuntu VM (LAN or cloud) |
| `configs/node-windows-vm.yml` | Windows Server / desktop VM |
| `configs/orchestrator-three-node.yml` | Registers the three configs above |

Copy/modify these files to get a three-node environment running in minutes.

## 7. Future Automations

- Azure VM Scale Set bootstrap script (cloud-init + systemd).
- AWS Auto Scaling Group with User Data installing `nacc` + registering to orchestrator.
- GCP Managed Instance Group template with startup script.
- `nacc discover --accept` CLI to auto-approve nodes based on JWT-signed metadata.

Feedback welcome—open an issue if you need additional deployment scenarios documented.
