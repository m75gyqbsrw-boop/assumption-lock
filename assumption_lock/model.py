from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable, Literal

Severity = Literal["warn", "fail"]
CheckStatus = Literal["passed", "failed"]


@dataclass(frozen=True)
class Assumption:
    name: str
    owner: str | None
    expires: date | None
    evidence: str | None
    severity: Severity
    that: Callable[[], bool] | None
    file: str | None = None
    line: int | None = None


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: CheckStatus
    message: str
    severity: Severity
    file: str | None
    line: int | None


@dataclass(frozen=True)
class ScannedAssumption:
    name: str | None
    file: str
    line: int
