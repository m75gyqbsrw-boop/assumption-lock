from __future__ import annotations

import inspect
from datetime import date
from os import PathLike
from pathlib import Path
from typing import Callable

from assumption_lock.model import Assumption, Severity
from assumption_lock.registry import register


def assume(
    name: str,
    *,
    that: Callable[[], bool] | None = None,
    owner: str | None = None,
    expires: str | date | None = None,
    evidence: str | None = None,
    severity: Severity = "warn",
) -> None:
    assumption = Assumption(
        name=_validate_name(name),
        owner=owner,
        expires=_parse_expiry(expires),
        evidence=evidence,
        severity=_validate_severity(severity),
        that=that,
        file=_caller_file(),
        line=_caller_line(),
    )
    register(assumption)


def _validate_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Assumption name is required.")
    return name


def _validate_severity(severity: str) -> Severity:
    if severity not in {"warn", "fail"}:
        raise ValueError("Invalid severity: expected 'warn' or 'fail'.")
    return severity


def _parse_expiry(value: str | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(
                f"Invalid expiry date: {value!r}. Expected ISO format YYYY-MM-DD."
            ) from exc
    raise ValueError(
        f"Invalid expiry date: {value!r}. Expected None, datetime.date, or ISO string."
    )


def _caller_file() -> str | None:
    frame = inspect.currentframe()
    try:
        if frame is None or frame.f_back is None:
            return None
        return str(Path(frame.f_back.f_code.co_filename).resolve())
    finally:
        del frame


def _caller_line() -> int | None:
    frame = inspect.currentframe()
    try:
        if frame is None or frame.f_back is None:
            return None
        return frame.f_back.f_lineno
    finally:
        del frame
