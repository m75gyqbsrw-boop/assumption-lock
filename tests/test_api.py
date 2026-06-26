from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from assumption_lock import assume
from assumption_lock.registry import all_assumptions, clear_registry


@pytest.fixture(autouse=True)
def reset_registry() -> None:
    clear_registry()


def test_successful_registration_captures_metadata() -> None:
    assume(
        "payments.stripe_webhook_latency",
        owner="payments-team",
        expires="2026-09-01",
        evidence="runbook:payments/webhooks",
        severity="fail",
    )

    assumptions = all_assumptions()

    assert len(assumptions) == 1
    assumption = assumptions[0]
    assert assumption.name == "payments.stripe_webhook_latency"
    assert assumption.owner == "payments-team"
    assert assumption.expires == date(2026, 9, 1)
    assert assumption.evidence == "runbook:payments/webhooks"
    assert assumption.severity == "fail"
    assert assumption.file is not None
    assert assumption.line is not None


def test_missing_name_raises() -> None:
    with pytest.raises(ValueError, match="Assumption name is required"):
        assume("")


def test_invalid_severity_raises() -> None:
    with pytest.raises(ValueError, match="Invalid severity"):
        assume("example", severity="error")  # type: ignore[arg-type]


def test_invalid_expiry_raises() -> None:
    with pytest.raises(ValueError, match="Invalid expiry date"):
        assume("example", expires="2026-99-99")


def test_duplicate_names_raise() -> None:
    assume("duplicate")

    with pytest.raises(ValueError, match="Duplicate assumption name: duplicate"):
        assume("duplicate")


def test_predicate_is_not_called_during_registration() -> None:
    called = False

    def predicate() -> bool:
        nonlocal called
        called = True
        return True

    assume("runtime.only", that=predicate)

    assert called is False


def test_registration_captures_user_callsite() -> None:
    expected_file = str(Path(__file__).resolve())
    expected_line = _register_callsite_assumption()

    assumption = all_assumptions()[0]

    assert assumption.file == expected_file
    assert assumption.line == expected_line


def _register_callsite_assumption() -> int:
    line = _register_callsite_assumption.__code__.co_firstlineno + 2
    assume("callsite.example")
    return line
