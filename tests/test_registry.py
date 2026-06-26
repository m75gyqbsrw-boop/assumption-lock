from __future__ import annotations

from datetime import date

from assumption_lock.model import Assumption
from assumption_lock.registry import all_assumptions, clear_registry, register


def test_clear_registry_removes_all_assumptions() -> None:
    register(
        Assumption(
            name="example",
            owner="team",
            expires=date(2026, 1, 1),
            evidence=None,
            severity="warn",
            that=None,
        )
    )

    clear_registry()

    assert all_assumptions() == []
