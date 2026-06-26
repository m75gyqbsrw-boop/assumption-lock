from __future__ import annotations

from datetime import date

from assumption_lock.model import Assumption, CheckResult
from assumption_lock.registry import all_assumptions


def check_all(*, today: date | None = None) -> list[CheckResult]:
    check_date = today or date.today()
    assumptions = sorted(all_assumptions(), key=lambda assumption: assumption.name)
    return [check_assumption(assumption, today=check_date) for assumption in assumptions]


def check_assumption(assumption: Assumption, *, today: date | None = None) -> CheckResult:
    check_date = today or date.today()
    issues: list[str] = []

    if not assumption.owner or not assumption.owner.strip():
        issues.append("Missing owner")

    if assumption.expires is not None and assumption.expires < check_date:
        issues.append(f"Expired on {assumption.expires.isoformat()}")

    if assumption.that is not None:
        try:
            passed = assumption.that()
        except Exception as exc:  # pragma: no cover - exercised by tests
            issues.append(f"Predicate raised {type(exc).__name__}: {exc}")
        else:
            if not passed:
                issues.append("Predicate returned False")

    if issues:
        return CheckResult(
            name=assumption.name,
            status="failed",
            message="; ".join(issues),
            severity=assumption.severity,
            file=assumption.file,
            line=assumption.line,
        )

    return CheckResult(
        name=assumption.name,
        status="passed",
        message="OK",
        severity=assumption.severity,
        file=assumption.file,
        line=assumption.line,
    )
