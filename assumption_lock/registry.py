from __future__ import annotations

from assumption_lock.model import Assumption

_REGISTRY: dict[str, Assumption] = {}


def register(assumption: Assumption) -> None:
    if assumption.name in _REGISTRY:
        raise ValueError(f"Duplicate assumption name: {assumption.name}")
    _REGISTRY[assumption.name] = assumption


def all_assumptions() -> list[Assumption]:
    return list(_REGISTRY.values())


def clear_registry() -> None:
    _REGISTRY.clear()
