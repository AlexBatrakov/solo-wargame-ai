"""Thin explicit agent-loading helpers for exact/policy workflows."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass

from solo_wargame_ai.agents.base import Agent


@dataclass(frozen=True, slots=True)
class ExplicitAgentLoaderSpec:
    """Explicit module-based agent construction spec.

    This stays intentionally small and avoids introducing a broad registry.
    """

    agent_factory: str | None = None
    agent_module: str | None = None
    agent_expr: str | None = None
    agent_name: str | None = None


def validate_agent_loader_spec(
    spec: ExplicitAgentLoaderSpec,
    *,
    require_loader: bool,
) -> None:
    """Validate an explicit agent loader spec."""

    if spec.agent_factory is not None:
        if spec.agent_module is not None or spec.agent_expr is not None:
            raise ValueError(
                "agent_factory is mutually exclusive with agent_module / agent_expr",
            )
        return

    if spec.agent_module is not None and spec.agent_expr is None:
        raise ValueError("agent_expr is required when agent_module is provided")
    if spec.agent_module is None and spec.agent_expr is not None:
        raise ValueError("agent_module is required when agent_expr is provided")
    if require_loader and spec.agent_module is None:
        raise ValueError("an explicit agent loader is required")


def build_explicit_agent_factory(spec: ExplicitAgentLoaderSpec) -> Callable[[], Agent]:
    """Build a zero-arg factory from an explicit loader spec."""

    validate_agent_loader_spec(spec, require_loader=True)

    if spec.agent_factory is not None:
        module_name, function_name = spec.agent_factory.split(":", 1)
        module = importlib.import_module(module_name)
        factory = getattr(module, function_name)
        if not callable(factory):
            raise TypeError(f"agent factory {spec.agent_factory!r} is not callable")

        def build_from_factory() -> Agent:
            agent = factory()
            return agent

        return build_from_factory

    assert spec.agent_module is not None
    assert spec.agent_expr is not None
    module = importlib.import_module(spec.agent_module)

    def build_from_expr() -> Agent:
        scope = module.__dict__.copy()
        agent = eval(spec.agent_expr, scope, {})
        return agent

    return build_from_expr


def resolve_explicit_agent_name(
    spec: ExplicitAgentLoaderSpec,
    *,
    agent_factory: Callable[[], Agent] | None = None,
) -> str:
    """Resolve a stable display name for the explicit loader target."""

    if spec.agent_name:
        return spec.agent_name

    if agent_factory is None:
        agent_factory = build_explicit_agent_factory(spec)
    agent = agent_factory()
    return str(getattr(agent, "name", type(agent).__name__))


__all__ = [
    "ExplicitAgentLoaderSpec",
    "build_explicit_agent_factory",
    "resolve_explicit_agent_name",
    "validate_agent_loader_spec",
]
