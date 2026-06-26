from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from assumption_lock.model import Assumption, CheckResult, ScannedAssumption


def format_check_result(result: CheckResult, *, cwd: str | None = None) -> str:
    prefix = _result_prefix(result)
    location = _format_location(result.file, result.line, cwd=cwd)
    if location:
        return f"{prefix}: {result.name} - {result.message} ({location})"
    return f"{prefix}: {result.name} - {result.message}"


def render_markdown_report(
    assumptions: list[Assumption],
    *,
    cwd: str | None = None,
) -> str:
    lines = [
        "# Assumption Register",
        "",
        "| Name | Owner | Expires | Severity | Evidence | Location |",
        "|---|---|---:|---|---|---|",
    ]
    for assumption in sorted(assumptions, key=lambda item: item.name):
        lines.append(
            "| {name} | {owner} | {expires} | {severity} | {evidence} | {location} |".format(
                name=assumption.name,
                owner=assumption.owner or "",
                expires=assumption.expires.isoformat() if assumption.expires else "",
                severity=assumption.severity,
                evidence=assumption.evidence or "",
                location=_format_location(assumption.file, assumption.line, cwd=cwd),
            )
        )
    return "\n".join(lines)


def render_json_report(assumptions: list[Assumption], *, cwd: str | None = None) -> str:
    payload = [
        {
            "name": assumption.name,
            "owner": assumption.owner,
            "expires": assumption.expires.isoformat() if assumption.expires else None,
            "severity": assumption.severity,
            "evidence": assumption.evidence,
            "file": _display_file(assumption.file, cwd=cwd),
            "line": assumption.line,
            "has_predicate": assumption.that is not None,
        }
        for assumption in sorted(assumptions, key=lambda item: item.name)
    ]
    return json.dumps(payload, indent=2)


def render_scan_results(results: list[ScannedAssumption], *, cwd: str | None = None) -> str:
    lines: list[str] = []
    for result in sorted(results, key=lambda item: (item.file, item.line, item.name or "")):
        location = _format_location(result.file, result.line, cwd=cwd)
        name = result.name if result.name is not None else "<unknown>"
        lines.append(f"FOUND: {name} ({location})")
    return "\n".join(lines)


def _result_prefix(result: CheckResult) -> str:
    if result.status == "passed":
        return "PASSED"
    if result.severity == "warn":
        return "WARNING"
    return "FAILED"


def _format_location(file: str | None, line: int | None, cwd: str | None = None) -> str:
    display_file = _display_file(file, cwd=cwd)
    if display_file is None:
        return ""
    if line is None:
        return display_file
    return f"{display_file}:{line}"


def _display_file(file: str | None, cwd: str | None = None) -> str | None:
    if file is None:
        return None
    file_path = Path(file)
    if not file_path.is_absolute():
        return str(file_path)

    base_path = Path(cwd).resolve() if cwd is not None else Path.cwd().resolve()
    try:
        return str(file_path.resolve().relative_to(base_path))
    except ValueError:
        return str(file_path.resolve())
