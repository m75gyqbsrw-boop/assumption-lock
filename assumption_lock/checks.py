from __future__ import annotations

from datetime import date

from assumption_lock.config import PolicyConfig
from assumption_lock.model import Assumption, CheckResult
from assumption_lock.registry import all_assumptions
from assumption_lock.policy import evaluate_assumption


def check_all(*, today: date | None = None, config: PolicyConfig | None = None) -> list[CheckResult]:
    check_date = today or date.today()
    assumptions = sorted(all_assumptions(), key=lambda assumption: assumption.name)
    return [check_assumption(assumption, today=check_date, config=config) for assumption in assumptions]


def check_assumption(
    assumption: Assumption,
    *,
    today: date | None = None,
    config: PolicyConfig | None = None,
) -> CheckResult:
    check_date = today or date.today()
    findings = evaluate_assumption(assumption, today=check_date, config=config)

    if findings:
        return CheckResult(
            name=assumption.name,
            status="failed",
            message="; ".join(finding.message for finding in findings),
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
