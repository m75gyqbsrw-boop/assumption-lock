from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from assumption_lock.config import PolicyConfig
from assumption_lock.model import Assumption

PolicySeverity = Literal["info", "warn", "error"]


@dataclass(frozen=True)
class PolicyFinding:
    code: str
    message: str
    severity: PolicySeverity


def evaluate_assumption(
    assumption: Assumption,
    *,
    today: date | None = None,
    config: PolicyConfig | None = None,
) -> list[PolicyFinding]:
    check_date = today or date.today()
    policy_config = config or PolicyConfig()
    findings: list[PolicyFinding] = []

    findings.extend(_check_owner(assumption))
    findings.extend(_check_expiry(assumption, check_date=check_date))
    findings.extend(
        _check_expiring_soon(
            assumption,
            check_date=check_date,
            expiring_within_days=policy_config.expiring_within_days,
        )
    )
    findings.extend(_check_evidence_for_fail(assumption, config=policy_config))
    findings.extend(_check_predicate(assumption))
    return findings


def _check_owner(assumption: Assumption) -> list[PolicyFinding]:
    if assumption.owner and assumption.owner.strip():
        return []
    return [
        PolicyFinding(
            code="missing_owner",
            message="Missing owner",
            severity="error",
        )
    ]


def _check_expiry(assumption: Assumption, *, check_date: date) -> list[PolicyFinding]:
    if assumption.expires is None:
        return []
    if assumption.expires < check_date:
        return [
            PolicyFinding(
                code="expired",
                message=f"Expired on {assumption.expires.isoformat()}",
                severity="error",
            )
        ]
    return []


def _check_expiring_soon(
    assumption: Assumption,
    *,
    check_date: date,
    expiring_within_days: int,
) -> list[PolicyFinding]:
    if assumption.expires is None:
        return []
    if assumption.expires < check_date:
        return []
    if assumption.expires > check_date + timedelta(days=expiring_within_days):
        return []
    return [
        PolicyFinding(
            code="expiring_soon",
            message=(
                f"Expiring on {assumption.expires.isoformat()} "
                f"within {expiring_within_days} days"
            ),
            severity="warn",
        )
    ]


def _check_predicate(assumption: Assumption) -> list[PolicyFinding]:
    if assumption.that is None:
        return []

    try:
        passed = assumption.that()
    except Exception as exc:  # pragma: no cover - exercised by tests
        return [
            PolicyFinding(
                code="predicate_exception",
                message=f"Predicate raised {type(exc).__name__}: {exc}",
                severity="error",
            )
        ]

    if passed:
        return []

    return [
        PolicyFinding(
            code="predicate_failed",
            message="Predicate returned False",
            severity="error",
        )
    ]


def _check_evidence_for_fail(assumption: Assumption, *, config: PolicyConfig) -> list[PolicyFinding]:
    if not config.require_evidence_for_fail:
        return []
    if assumption.severity != "fail":
        return []
    if assumption.evidence and assumption.evidence.strip():
        return []
    return [
        PolicyFinding(
            code="missing_evidence",
            message="Missing evidence for fail severity",
            severity="error",
        )
    ]