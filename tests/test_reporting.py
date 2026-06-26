from __future__ import annotations

from datetime import date

from assumption_lock.model import Assumption, CheckResult
from assumption_lock.reporting import (
    format_check_result,
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
