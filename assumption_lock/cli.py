from __future__ import annotations

import argparse
import importlib
import sys

from assumption_lock.config import load_policy_config
from assumption_lock.checks import check_all
from assumption_lock.registry import all_assumptions, clear_registry
from assumption_lock.reporting import (
    InventoryFilters,
    format_check_result,
    render_inventory_markdown_report,
    render_inventory_json_report,
    render_json_report,
    render_markdown_report,
    render_scan_results,
)
from assumption_lock.scanner import scan_paths


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "check":
        return _run_check(args.module, args.config)
    if args.command == "scan":
        return _run_scan(args.paths)
    if args.command == "report":
        return _run_report(args.module, args.format, args.config)
    if args.command == "inventory":
        return _run_inventory(args.module, args.format, args.config, args)
    parser.error(f"Unknown command: {args.command}")
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="assumption-lock")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--module", action="append", required=True)
    check_parser.add_argument("--config")

    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("paths", nargs="+")

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--module", action="append", required=True)
    report_parser.add_argument("--format", choices=("markdown", "json"), required=True)
    report_parser.add_argument("--config")

    inventory_parser = subparsers.add_parser("inventory")
    inventory_parser.add_argument("--module", action="append", required=True)
    inventory_parser.add_argument("--format", choices=("markdown", "json"), required=True)
    inventory_parser.add_argument("--config")
    inventory_parser.add_argument("--owner")
    inventory_parser.add_argument("--severity", choices=("warn", "fail"))
    inventory_parser.add_argument("--status", choices=("active", "expired", "expiring_soon"))
    inventory_parser.add_argument("--has-predicate", action="store_true")
    inventory_parser.add_argument("--group-by", choices=("owner", "severity", "status"))

    return parser


def _run_check(modules: list[str], config_path: str | None) -> int:
    config = load_policy_config(config_path)
    _load_modules(modules)
    results = check_all(config=config)
    for result in results:
        print(format_check_result(result))
    return 1 if any(result.status == "failed" and result.severity == "fail" for result in results) else 0


def _run_scan(paths: list[str]) -> int:
    results = scan_paths(paths)
    output = render_scan_results(results)
    if output:
        print(output)
    return 0


def _run_report(modules: list[str], report_format: str, config_path: str | None) -> int:
    config = load_policy_config(config_path)
    _load_modules(modules)
    assumptions = all_assumptions()
    if report_format == "markdown":
        print(render_markdown_report(assumptions, expiring_within_days=config.expiring_within_days))
    else:
        print(render_json_report(assumptions))
    return 0


def _run_inventory(
    modules: list[str],
    report_format: str,
    config_path: str | None,
    args: argparse.Namespace | None = None,
) -> int:
    config = load_policy_config(config_path)
    _load_modules(modules)
    assumptions = all_assumptions()
    filters = InventoryFilters(
        owner=getattr(args, "owner", None),
        severity=getattr(args, "severity", None),
        status=getattr(args, "status", None),
        has_predicate=True if getattr(args, "has_predicate", False) else None,
    )
    group_by = getattr(args, "group_by", None)
    if report_format == "markdown":
        print(
            render_inventory_markdown_report(
                assumptions,
                expiring_within_days=config.expiring_within_days,
                filters=filters,
                group_by=group_by,
            )
        )
    else:
        print(
            render_inventory_json_report(
                assumptions,
                expiring_within_days=config.expiring_within_days,
                filters=filters,
                group_by=group_by,
            )
        )
    return 0


def _load_modules(modules: list[str]) -> None:
    clear_registry()
    for module_name in modules:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)


if __name__ == "__main__":
    raise SystemExit(main())
