"""Agent layer connecting to Docker-hosted Mistral-NeMo or heuristic fallbacks."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable, Literal

from .config import AgentBackendConfig
from .nodes import NodeRegistry, NodeStatus

logger = logging.getLogger(__name__)


class AgentBackendError(RuntimeError):
    """Raised when the LLM backend cannot satisfy a completion request."""


class LLMBackend:
    def complete(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class DockerMistralBackend(LLMBackend):
    """Uses Docker Desktop AI models (docker model run) for LLM completion."""

    def __init__(
        self,
        *,
        container_id: str,  # Actually the model name for docker model run
        command: list[str] | None,
        timeout: float,
        environment: dict[str, str],
    ) -> None:
        self.model_name = container_id or "mistral-nemo"  # Default to mistral-nemo
        self.timeout = timeout
        self.environment = environment

    def complete(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:
        # Merge prompt with context
        merged_prompt = prompt
        if context:
            merged_prompt = prompt + "\n\nContext:\n" + json.dumps(context, indent=2)
        
        # Run Docker AI model
        env = os.environ.copy()
        env.update(self.environment)
        
        proc = subprocess.run(
            ["docker", "model", "run", self.model_name, merged_prompt],
            text=True,
            capture_output=True,
            timeout=self.timeout,
            env=env,
        )
        
        if proc.returncode != 0:
            logger.error("Docker model backend failed: %s", proc.stderr.strip())
            raise AgentBackendError(proc.stderr.strip() or "docker model run failed")
        
        return proc.stdout.strip()


class LocalHeuristicBackend(LLMBackend):
    """Deterministic fallback backend for development/testing."""

    def complete(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:
        summary = {
            "prompt_hash": hash(prompt) & 0xFFFFFFFF,
            "context_keys": sorted(list((context or {}).keys())),
        }
        return json.dumps({"summary": summary, "explanation": "Heuristic backend generated plan."})


def build_backend(config: AgentBackendConfig) -> LLMBackend:
    if config.kind == "docker-mistral":
        container_id = config.container_id or os.environ.get("NACC_DOCKER_LLM_CONTAINER")
        return DockerMistralBackend(
            container_id=container_id,
            command=config.command,
            timeout=config.timeout,
            environment=config.environment,
        )
    elif config.kind == "cerebras":
        # Import here to avoid dependency if not using Cerebras
        from .cerebras_backend import CerebrasBackend
        api_key = config.container_id or os.environ.get("CEREBRAS_API_KEY")
        model = config.environment.get("model", "zai-glm-4.6") if config.environment else "zai-glm-4.6"
        return CerebrasBackend(api_key=api_key, model=model)
    elif config.kind == "blaxel" or config.kind == "blaxel-openai" or config.kind == "blaxel-gemini":
        # Import here to avoid dependency if not using Blaxel
        from .blaxel_backend import BlaxelBackend
        api_key = config.container_id or os.environ.get("BLAXEL_API_KEY")
        workspace = config.environment.get("workspace") if config.environment else os.environ.get("BLAXEL_WORKSPACE")
        model = config.environment.get("model", "gpt-4o-mini") if config.environment else "gpt-4o-mini"
        
        # Determine endpoint type from config kind
        endpoint_type = "openai"
        if config.kind == "blaxel-gemini":
            endpoint_type = "gemini"
            model = config.environment.get("model", "gemini-2-0-flash-exp") if config.environment else "gemini-2-0-flash-exp"
        
        return BlaxelBackend(
            api_key=api_key,
            workspace=workspace,
            model=model,
            endpoint_type=endpoint_type
        )
    elif config.kind == "modal":
        # Import here to avoid dependency if not using Modal
        from .modal_backend import ModalBackend
        endpoint_url = config.container_id  # Use container_id field for endpoint URL
        return ModalBackend(endpoint_url=endpoint_url)
    return LocalHeuristicBackend()


@dataclass(slots=True)
class RouterRequest:
    task: str
    required_tags: list[str] | None = None
    parallelism: int = 1


@dataclass(slots=True)
class RouterDecision:
    nodes: list[str]
    mode: Literal["single", "parallel"]
    reason: str


@dataclass(slots=True)
class CommandRequest:
    description: str
    command: list[str] | str
    preferred_tags: list[str] | None = None
    parallelism: int = 1


@dataclass(slots=True)
class ExecutionPlan:
    nodes: list[str]
    mode: Literal["single", "parallel"]
    timeout: float
    reason: str
    router_reason: str


@dataclass(slots=True)
class SyncPlan:
    source_node: str
    target_nodes: list[str]
    strategy: str
    reason: str


class RouterAgent:
    def __init__(self, backend: LLMBackend, registry: NodeRegistry) -> None:
        self.backend = backend
        self.registry = registry

    def select_nodes(self, request: RouterRequest) -> RouterDecision:
        statuses = self.registry.refresh_all()
        chosen = self._choose_by_metrics(statuses, request)
        reason = self._compose_reason(request, statuses, chosen)
        mode = "parallel" if request.parallelism > 1 or len(chosen) > 1 else "single"
        return RouterDecision(nodes=[status.node_id for status in chosen], mode=mode, reason=reason)

    def _choose_by_metrics(self, statuses: list[NodeStatus], request: RouterRequest) -> list[NodeStatus]:
        candidates = [status for status in statuses if status.healthy]
        if request.required_tags:
            candidates = [status for status in candidates if set(request.required_tags).intersection(status.tags)]
        if not candidates:
            candidates = statuses
        sorted_nodes = sorted(
            candidates,
            key=lambda status: (
                not status.healthy,
                status.metrics.get("cpu_percent", 100.0),
                status.metrics.get("memory_percent", 100.0),
            ),
        )
        parallelism = max(1, request.parallelism)
        return sorted_nodes[:parallelism]

    def _compose_reason(
        self,
        request: RouterRequest,
        statuses: list[NodeStatus],
        chosen: list[NodeStatus],
    ) -> str:
        context = {
            "request": asdict(request),
            "nodes": [asdict(status) for status in statuses],
            "selected": [asdict(status) for status in chosen],
        }
        prompt = (
            "You are the Router Agent inside NACC. Given node telemetry and a task description, "
            "explain in one concise sentence why the selected nodes are a good fit."
        )
        try:
            response = self.backend.complete(prompt, context=context)
            if response:
                return response
        except AgentBackendError:
            logger.warning("RouterAgent backend unavailable; falling back to heuristic reason")
        node_list = ", ".join(status.node_id for status in chosen)
        return f"Selected {node_list} based on lowest CPU utilization"


class ExecutionAgent:
    def plan(self, request: CommandRequest, decision: RouterDecision) -> ExecutionPlan:
        base_timeout = 30.0 + len(str(request.command)) * 0.5
        timeout = min(max(base_timeout, 15.0), 600.0)
        reason = f"Execute {request.command!r} via {decision.mode} mode"
        return ExecutionPlan(nodes=decision.nodes, mode=decision.mode, timeout=timeout, reason=reason, router_reason=decision.reason)


class SecurityAgent:
    def __init__(self, registry: NodeRegistry) -> None:
        self.registry = registry

    def authorize(self, plan: ExecutionPlan, command: list[str] | str) -> None:
        cmd_list = command if isinstance(command, list) else command.split()
        base = Path(cmd_list[0]).name
        for node_id in plan.nodes:
            definition = self.registry.get_definition(node_id)
            allow_list = definition.allowed_commands
            if allow_list and base not in allow_list:
                raise PermissionError(f"Command '{base}' not allowed on node {node_id}")


class SyncAgent:
    def __init__(self, backend: LLMBackend, registry: NodeRegistry) -> None:
        self.backend = backend
        self.registry = registry

    def plan(self, source_node: str, candidate_targets: Iterable[str], *, strategy: str = "mirror") -> SyncPlan:
        targets = list(candidate_targets)
        if not targets:
            raise ValueError("At least one sync target must be provided")
        reason = f"Syncing from {source_node} to {', '.join(targets)} via {strategy}"
        return SyncPlan(source_node=source_node, target_nodes=targets, strategy=strategy, reason=reason)


class AgentSuite:
    def __init__(self, config: AgentBackendConfig, registry: NodeRegistry) -> None:
        backend = build_backend(config)
        self.backend = backend
        self.router = RouterAgent(backend, registry)
        self.execution = ExecutionAgent()
        self.security = SecurityAgent(registry)
        self.sync = SyncAgent(backend, registry)

    def plan_command(self, request: CommandRequest) -> ExecutionPlan:
        router_request = RouterRequest(
            task=request.description,
            required_tags=request.preferred_tags,
            parallelism=request.parallelism,
        )
        decision = self.router.select_nodes(router_request)
        plan = self.execution.plan(request, decision)
        self.security.authorize(plan, request.command)
        return plan

    def plan_sync(self, source_node: str, targets: Iterable[str], strategy: str = "mirror") -> SyncPlan:
        return self.sync.plan(source_node, targets, strategy=strategy)

    def select_node(self, description: str, preferred_tags: list[str] | None = None) -> RouterDecision:
        request = RouterRequest(task=description, required_tags=preferred_tags, parallelism=1)
        return self.router.select_nodes(request)

    def probe_backend(self, message: str = "NACC orchestrator health check", context: dict[str, Any] | None = None) -> str:
        probe_context = context or {"source": "nacc-orchestrator", "kind": "health-check"}
        return self.backend.complete(message, context=probe_context)


__all__ = [
    "AgentBackendError",
    "AgentSuite",
    "CommandRequest",
    "ExecutionPlan",
    "RouterDecision",
    "RouterRequest",
    "SyncPlan",
]
