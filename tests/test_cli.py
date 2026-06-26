from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from assumption_lock.cli import main
from assumption_lock.registry import clear_registry


@pytest.fixture(autouse=True)
def reset_registry() -> None:
    clear_registry()


def test_warn_failures_do_not_cause_cli_exit_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module_name = _write_module(
        tmp_path,
        "warn_assumptions",
        'assume("payments.stripe_webhook_latency", severity="warn")\n',
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    exit_code = main(["check", "--module", module_name])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "WARNING: payments.stripe_webhook_latency - Missing owner" in output


def test_fail_failures_cause_cli_exit_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module_name = _write_module(
        tmp_path,
        "fail_assumptions",
        'assume("legacy.cache_contract", owner="platform", expires="2026-06-01", severity="fail")\n',
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    exit_code = main(["check", "--module", module_name])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "FAILED: legacy.cache_contract - Expired on 2026-06-01" in output


def test_report_outputs_markdown_and_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module_name = _write_module(
        tmp_path,
        "report_assumptions",
        'assume("users.table_under_1m_rows", owner="platform", expires="2026-12-31", severity="fail")\n',
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    markdown_exit_code = main(["report", "--module", module_name, "--format", "markdown"])
    markdown_output = capsys.readouterr().out
    json_exit_code = main(["report", "--module", module_name, "--format", "json"])
    json_output = capsys.readouterr().out

    assert markdown_exit_code == 0
    assert "# Assumption Register" in markdown_output
    assert json_exit_code == 0
    assert json.loads(json_output)[0]["name"] == "users.table_under_1m_rows"


def test_inventory_outputs_summary_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module_name = _write_module(
        tmp_path,
        "inventory_assumptions",
        'assume("users.table_under_1m_rows", owner="platform", expires="2026-12-31", severity="fail")\n',
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    exit_code = main(["inventory", "--module", module_name, "--format", "json"])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert exit_code == 0
    assert payload["summary"]["total"] == 1
    assert payload["assumptions"][0]["name"] == "users.table_under_1m_rows"


def test_scan_uses_ast_without_importing_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "app"
    target.mkdir()
    assumptions_file = target / "assumptions.py"
    assumptions_file.write_text(
        "\n".join(
            [
                "from assumption_lock import assume",
                "raise RuntimeError('should not import')",
                'assume("users.table_under_1m_rows")',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["scan", str(target)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "FOUND: users.table_under_1m_rows (app/assumptions.py:3)" in output


def _write_module(tmp_path: Path, module_name: str, body: str) -> str:
    module_path = tmp_path / f"{module_name}.py"
    module_path.write_text(
        "\n".join(
            [
                "from assumption_lock import assume",
                "",
                body.rstrip(),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    sys.modules.pop(module_name, None)
    return module_name
