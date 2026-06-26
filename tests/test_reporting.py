from __future__ import annotations

from datetime import date

from assumption_lock.model import Assumption, CheckResult
from assumption_lock.reporting import (
    build_inventory_summary,
    format_check_result,
    render_inventory_json_report,
    render_json_report,
    render_markdown_report,
)


def test_markdown_report_renders_expected_columns() -> None:
    assumptions = [
        Assumption(
            name="users.table_under_1m_rows",
            owner="platform",
            expires=date(2026, 12, 31),
            evidence="capacity-plan-2026",
            severity="fail",
            that=None,
            file="/repo/app/assumptions.py",
            line=12,
        )
    ]

    report = render_markdown_report(assumptions, cwd="/repo")

    assert "| users.table_under_1m_rows | platform | 2026-12-31 | fail | capacity-plan-2026 | app/assumptions.py:12 |" in report


def test_json_report_is_machine_readable() -> None:
    assumptions = [
        Assumption(
            name="users.table_under_1m_rows",
            owner="platform",
            expires=date(2026, 12, 31),
            evidence=None,
            severity="warn",
            that=lambda: True,
            file="/repo/app/assumptions.py",
            line=12,
        )
    ]

    report = render_json_report(assumptions, cwd="/repo")

    assert '"name": "users.table_under_1m_rows"' in report
    assert '"has_predicate": true' in report


def test_check_result_format_matches_cli_style() -> None:
    result = CheckResult(
        name="legacy.cache_contract",
        status="failed",
        message="Expired on 2026-06-01",
        severity="fail",
        file="/repo/app/assumptions.py",
        line=18,
    )

    assert (
        format_check_result(result, cwd="/repo")
        == "FAILED: legacy.cache_contract - Expired on 2026-06-01 (app/assumptions.py:18)"
    )


def test_inventory_summary_counts_metadata() -> None:
    assumptions = [
        Assumption(
            name="users.table_under_1m_rows",
            owner="platform",
            expires=date(2026, 1, 15),
            evidence=None,
            severity="fail",
            that=lambda: True,
            file=None,
            line=None,
        ),
        Assumption(
            name="payments.cache_contract",
            owner=None,
            expires=date(2025, 12, 31),
            evidence=None,
            severity="warn",
            that=None,
            file=None,
            line=None,
        ),
    ]

    summary = build_inventory_summary(assumptions, today=date(2026, 1, 1))

    assert summary.total == 2
    assert summary.unique_owners == 1
    assert summary.missing_owner == 1
    assert summary.expired == 1
    assert summary.expiring_soon == 1
    assert summary.with_predicate == 1
    assert summary.severity_warn == 1
    assert summary.severity_fail == 1


def test_markdown_report_includes_inventory_summary() -> None:
    assumptions = [
        Assumption(
            name="users.table_under_1m_rows",
            owner="platform",
            expires=date(2026, 12, 31),
            evidence="capacity-plan-2026",
            severity="fail",
            that=None,
            file="/repo/app/assumptions.py",
            line=12,
        )
    ]

    report = render_markdown_report(assumptions, cwd="/repo")

    assert "## Inventory Summary" in report
    assert "- Total assumptions: 1" in report


def test_inventory_json_report_has_summary_and_assumptions() -> None:
    assumptions = [
        Assumption(
            name="users.table_under_1m_rows",
            owner="platform",
            expires=date(2026, 12, 31),
            evidence="capacity-plan-2026",
            severity="fail",
            that=lambda: True,
            file="/repo/app/assumptions.py",
            line=12,
        )
    ]

    report = render_inventory_json_report(assumptions, cwd="/repo")
    payload = __import__("json").loads(report)

    assert payload["summary"]["total"] == 1
    assert payload["assumptions"][0]["name"] == "users.table_under_1m_rows"
