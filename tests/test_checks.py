from __future__ import annotations

from datetime import date

import pytest

from assumption_lock import assume
from assumption_lock.checks import check_all
from assumption_lock.registry import clear_registry


@pytest.fixture(autouse=True)
def reset_registry() -> None:
    clear_registry()


def test_predicate_is_called_during_checking() -> None:
    called = False

    def predicate() -> bool:
        nonlocal called
        called = True
        return True

    assume("example", that=predicate, owner="platform")

    results = check_all(today=date(2026, 1, 1))

    assert called is True
    assert results[0].status == "passed"


def test_failed_predicate_produces_failed_result() -> None:
    assume("example", that=lambda: False, owner="platform", severity="fail")

    result = check_all(today=date(2026, 1, 1))[0]

    assert result.status == "failed"
    assert result.message == "Predicate returned False"
    assert result.severity == "fail"


def test_predicate_exception_produces_failed_result() -> None:
    def predicate() -> bool:
        raise RuntimeError("boom")

    assume("example", that=predicate, owner="platform")

    result = check_all(today=date(2026, 1, 1))[0]

    assert result.status == "failed"
    assert result.message == "Predicate raised RuntimeError: boom"


def test_expired_assumption_produces_failed_result() -> None:
    assume("example", owner="platform", expires="2025-12-31", severity="fail")

    result = check_all(today=date(2026, 1, 1))[0]

    assert result.status == "failed"
    assert result.message == "Expired on 2025-12-31"


def test_missing_owner_produces_failed_result() -> None:
    assume("example")

    result = check_all(today=date(2026, 1, 1))[0]

    assert result.status == "failed"
    assert result.message == "Missing owner"


def test_expiring_soon_produces_warning_result() -> None:
    assume("example", owner="platform", expires="2026-01-15", severity="warn")

    result = check_all(today=date(2026, 1, 1))[0]

    assert result.status == "failed"
    assert result.message == "Expiring on 2026-01-15 within 30 days"
    assert result.severity == "warn"
