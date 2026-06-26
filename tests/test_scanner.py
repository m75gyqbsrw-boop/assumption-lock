from __future__ import annotations

from pathlib import Path

from assumption_lock.scanner import scan_file, scan_paths


def test_static_scanner_finds_simple_assume_calls(tmp_path: Path) -> None:
    target = tmp_path / "assumptions.py"
    target.write_text(
        "\n".join(
            [
                "from assumption_lock import assume",
                "",
                'assume("users.table_under_1m_rows")',
                'assumption_lock.assume("payments.stripe_webhook_latency")',
            ]
        ),
        encoding="utf-8",
    )

    results = scan_file(target)

    assert [result.name for result in results] == [
        "users.table_under_1m_rows",
        "payments.stripe_webhook_latency",
    ]


def test_static_scanner_does_not_import_application_code(tmp_path: Path) -> None:
    marker = tmp_path / "imported.txt"
    target = tmp_path / "dangerous.py"
    target.write_text(
        "\n".join(
            [
                "from pathlib import Path",
                "Path(__file__).with_name('imported.txt').write_text('imported', encoding='utf-8')",
                "",
                'assume("safe.assumption")',
            ]
        ),
        encoding="utf-8",
    )

    results = scan_paths([str(tmp_path)])

    assert [result.name for result in results] == ["safe.assumption"]
    assert not marker.exists()
