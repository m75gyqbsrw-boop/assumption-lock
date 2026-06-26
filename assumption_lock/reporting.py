from __future__ import annotations

import json
from dataclasses import dataclass
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, Literal

from assumption_lock.model import Assumption, CheckResult, ScannedAssumption


@dataclass(frozen=True)
class InventorySummary:
    total: int
    unique_owners: int
    missing_owner: int
    expired: int
    expiring_soon: int
    with_predicate: int
    severity_warn: int
    severity_fail: int


InventoryGroupBy = Literal["owner", "severity", "status"]
InventoryStatus = Literal["active", "expired", "expiring_soon"]


@dataclass(frozen=True)
class InventoryFilters:
    owner: str | None = None
    severity: str | None = None
    status: InventoryStatus | None = None
    has_predicate: bool | None = None


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
    expiring_within_days: int = 30,
) -> str:
    summary = build_inventory_summary(assumptions, expiring_within_days=expiring_within_days)
    lines = [
        "# Assumption Register",
        "",
        "## Inventory Summary",
        "",
        f"- Total assumptions: {summary.total}",
        f"- Unique owners: {summary.unique_owners}",
        f"- Missing owner: {summary.missing_owner}",
        f"- Expired: {summary.expired}",
        f"- Expiring soon: {summary.expiring_soon}",
        f"- With predicate: {summary.with_predicate}",
        f"- Severity warn: {summary.severity_warn}",
        f"- Severity fail: {summary.severity_fail}",
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


def render_inventory_markdown_report(
    assumptions: list[Assumption],
    *,
    cwd: str | None = None,
    today: date | None = None,
    expiring_within_days: int = 30,
    filters: InventoryFilters | None = None,
    group_by: InventoryGroupBy | None = None,
) -> str:
    filtered_assumptions = filter_inventory_assumptions(
        assumptions,
        today=today,
        expiring_within_days=expiring_within_days,
        filters=filters,
    )
    summary = build_inventory_summary(filtered_assumptions, today=today, expiring_within_days=expiring_within_days)
    lines = [
        "# Assumption Inventory",
        "",
        "## Inventory Summary",
        "",
        f"- Total assumptions: {summary.total}",
        f"- Unique owners: {summary.unique_owners}",
        f"- Missing owner: {summary.missing_owner}",
        f"- Expired: {summary.expired}",
        f"- Expiring soon: {summary.expiring_soon}",
        f"- With predicate: {summary.with_predicate}",
        f"- Severity warn: {summary.severity_warn}",
        f"- Severity fail: {summary.severity_fail}",
        "",
    ]

    if group_by is None:
        lines.extend(_render_inventory_table(filtered_assumptions, cwd=cwd))
        return "\n".join(lines)

    groups = group_inventory_assumptions(
        filtered_assumptions,
        group_by=group_by,
        today=today,
        expiring_within_days=expiring_within_days,
    )
    for group_label, items in groups:
        lines.extend(
            [
                f"## {group_label}",
                "",
            ]
        )
        lines.extend(_render_inventory_table(items, cwd=cwd))
        lines.append("")
    return "\n".join(lines).rstrip()


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


def render_inventory_json_report(
    assumptions: list[Assumption],
    *,
    cwd: str | None = None,
    today: date | None = None,
    expiring_within_days: int = 30,
    filters: InventoryFilters | None = None,
    group_by: InventoryGroupBy | None = None,
) -> str:
    filtered_assumptions = filter_inventory_assumptions(
        assumptions,
        today=today,
        expiring_within_days=expiring_within_days,
        filters=filters,
    )
    summary = build_inventory_summary(
        filtered_assumptions,
        today=today,
        expiring_within_days=expiring_within_days,
    )
    payload = {
        "summary": {
            "total": summary.total,
            "unique_owners": summary.unique_owners,
            "missing_owner": summary.missing_owner,
            "expired": summary.expired,
            "expiring_soon": summary.expiring_soon,
            "with_predicate": summary.with_predicate,
            "severity_warn": summary.severity_warn,
            "severity_fail": summary.severity_fail,
        },
        "assumptions": [
            _inventory_payload_item(assumption, cwd=cwd, today=today, expiring_within_days=expiring_within_days)
            for assumption in sorted(filtered_assumptions, key=lambda item: item.name)
        ],
    }
    if group_by is not None:
        payload["groups"] = [
            {
                "group_by": group_by,
                "value": group_label,
                "assumptions": [
                    _inventory_payload_item(
                        assumption,
                        cwd=cwd,
                        today=today,
                        expiring_within_days=expiring_within_days,
                    )
                    for assumption in items
                ],
            }
            for group_label, items in group_inventory_assumptions(
                filtered_assumptions,
                group_by=group_by,
                today=today,
                expiring_within_days=expiring_within_days,
            )
        ]
    return json.dumps(payload, indent=2)


def filter_inventory_assumptions(
    assumptions: Iterable[Assumption],
    *,
    today: date | None = None,
    expiring_within_days: int = 30,
    filters: InventoryFilters | None = None,
) -> list[Assumption]:
    active_filters = filters or InventoryFilters()
    check_date = today or date.today()
    result: list[Assumption] = []

    for assumption in assumptions:
        if active_filters.owner is not None and (assumption.owner or "") != active_filters.owner:
            continue
        if active_filters.severity is not None and assumption.severity != active_filters.severity:
            continue
        if active_filters.has_predicate is not None and (assumption.that is not None) != active_filters.has_predicate:
            continue
        if active_filters.status is not None and _inventory_status(
            assumption, today=check_date, expiring_within_days=expiring_within_days
        ) != active_filters.status:
            continue
        result.append(assumption)

    return sorted(result, key=lambda item: item.name)


def group_inventory_assumptions(
    assumptions: Iterable[Assumption],
    *,
    group_by: InventoryGroupBy,
    today: date | None = None,
    expiring_within_days: int = 30,
) -> list[tuple[str, list[Assumption]]]:
    check_date = today or date.today()
    grouped: dict[str, list[Assumption]] = {}

    for assumption in assumptions:
        group_value = _inventory_group_value(
            assumption,
            group_by=group_by,
            today=check_date,
            expiring_within_days=expiring_within_days,
        )
        grouped.setdefault(group_value, []).append(assumption)

    return [(group_label, sorted(items, key=lambda item: item.name)) for group_label, items in sorted(grouped.items())]


def build_inventory_summary(
    assumptions: Iterable[Assumption],
    *,
    today: date | None = None,
    expiring_within_days: int = 30,
) -> InventorySummary:
    check_date = today or date.today()
    unique_owners: set[str] = set()
    missing_owner = 0
    expired = 0
    expiring_soon = 0
    with_predicate = 0
    severity_warn = 0
    severity_fail = 0
    total = 0

    for assumption in assumptions:
        total += 1
        if assumption.owner and assumption.owner.strip():
            unique_owners.add(assumption.owner.strip())
        else:
            missing_owner += 1

        if assumption.expires is not None:
            if assumption.expires < check_date:
                expired += 1
            elif assumption.expires <= check_date + timedelta(days=expiring_within_days):
                expiring_soon += 1

        if assumption.that is not None:
            with_predicate += 1

        if assumption.severity == "warn":
            severity_warn += 1
        else:
            severity_fail += 1

    return InventorySummary(
        total=total,
        unique_owners=len(unique_owners),
        missing_owner=missing_owner,
        expired=expired,
        expiring_soon=expiring_soon,
        with_predicate=with_predicate,
        severity_warn=severity_warn,
        severity_fail=severity_fail,
    )


def _render_inventory_table(assumptions: Iterable[Assumption], *, cwd: str | None = None) -> list[str]:
    lines = [
        "| Name | Owner | Expires | Severity | Evidence | Status | Location |",
        "|---|---|---:|---|---|---|---|",
    ]
    for assumption in sorted(assumptions, key=lambda item: item.name):
        lines.append(
            "| {name} | {owner} | {expires} | {severity} | {evidence} | {status} | {location} |".format(
                name=assumption.name,
                owner=assumption.owner or "",
                expires=assumption.expires.isoformat() if assumption.expires else "",
                severity=assumption.severity,
                evidence=assumption.evidence or "",
                status=_inventory_status(assumption),
                location=_format_location(assumption.file, assumption.line, cwd=cwd),
            )
        )
    return lines


def _inventory_status(
    assumption: Assumption,
    *,
    today: date | None = None,
    expiring_within_days: int = 30,
) -> InventoryStatus:
    check_date = today or date.today()
    if assumption.expires is not None:
        if assumption.expires < check_date:
            return "expired"
        if assumption.expires <= check_date + timedelta(days=expiring_within_days):
            return "expiring_soon"
    return "active"


def _inventory_group_value(
    assumption: Assumption,
    *,
    group_by: InventoryGroupBy,
    today: date,
    expiring_within_days: int,
) -> str:
    if group_by == "owner":
        return assumption.owner.strip() if assumption.owner and assumption.owner.strip() else "<missing owner>"
    if group_by == "severity":
        return assumption.severity
    return _inventory_status(assumption, today=today, expiring_within_days=expiring_within_days)


def _inventory_payload_item(
    assumption: Assumption,
    *,
    cwd: str | None = None,
    today: date | None = None,
    expiring_within_days: int = 30,
) -> dict[str, object]:
    return {
        "name": assumption.name,
        "owner": assumption.owner,
        "expires": assumption.expires.isoformat() if assumption.expires else None,
        "severity": assumption.severity,
        "evidence": assumption.evidence,
        "file": _display_file(assumption.file, cwd=cwd),
        "line": assumption.line,
        "has_predicate": assumption.that is not None,
        "status": _inventory_status(
            assumption,
            today=today,
            expiring_within_days=expiring_within_days,
        ),
    }


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
