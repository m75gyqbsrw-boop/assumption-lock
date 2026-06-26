from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import tomllib


@dataclass(frozen=True)
class PolicyConfig:
    expiring_within_days: int = 30
    require_evidence_for_fail: bool = False


def load_policy_config(path: str | Path | None = None, *, cwd: str | Path | None = None) -> PolicyConfig:
    if path is not None:
        return _load_policy_config_from_path(Path(path))

    search_root = Path(cwd).resolve() if cwd is not None else Path.cwd().resolve()
    for candidate in (search_root / "assumption-lock.toml", search_root / "pyproject.toml"):
        if candidate.exists():
            return _load_policy_config_from_path(candidate)

    return PolicyConfig()


def _load_policy_config_from_path(path: Path) -> PolicyConfig:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    if path.name == "pyproject.toml":
        settings = payload.get("tool", {}).get("assumption_lock", {})
    else:
        settings = payload
    if not isinstance(settings, Mapping):
        raise ValueError(f"Invalid policy config in {path}: expected a table of settings.")

    return PolicyConfig(
        expiring_within_days=_parse_int(settings, "expiring_within_days", default=30, source=path),
        require_evidence_for_fail=_parse_bool(
            settings, "require_evidence_for_fail", default=False, source=path
        ),
    )


def _parse_int(settings: Mapping[str, Any], key: str, *, default: int, source: Path) -> int:
    value = settings.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Invalid policy config in {source}: {key} must be an integer.")
    if value < 0:
        raise ValueError(f"Invalid policy config in {source}: {key} must be >= 0.")
    return value


def _parse_bool(settings: Mapping[str, Any], key: str, *, default: bool, source: Path) -> bool:
    value = settings.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"Invalid policy config in {source}: {key} must be a boolean.")
    return value