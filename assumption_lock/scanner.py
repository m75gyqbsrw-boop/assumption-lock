from __future__ import annotations

import ast
from pathlib import Path

from assumption_lock.model import ScannedAssumption


def scan_paths(paths: list[str]) -> list[ScannedAssumption]:
    results: list[ScannedAssumption] = []
    for root in sorted(Path(path).resolve() for path in paths):
        if root.is_file():
            if root.suffix == ".py":
                results.extend(scan_file(root))
            continue
        for file_path in sorted(root.rglob("*.py")):
            results.extend(scan_file(file_path))
    return results


def scan_file(path: str | Path) -> list[ScannedAssumption]:
    file_path = Path(path).resolve()
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    visitor = _AssumeCallVisitor(file_path)
    visitor.visit(tree)
    return visitor.results


class _AssumeCallVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.results: list[ScannedAssumption] = []

    def visit_Call(self, node: ast.Call) -> None:
        if _is_assume_call(node.func):
            name = _literal_name(node)
            if name is not None:
                self.results.append(
                    ScannedAssumption(
                        name=name,
                        file=str(self.file_path),
                        line=node.lineno,
                    )
                )
        self.generic_visit(node)


def _is_assume_call(node: ast.expr) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "assume"
    if isinstance(node, ast.Attribute) and node.attr == "assume":
        return isinstance(node.value, ast.Name) and node.value.id == "assumption_lock"
    return False


def _literal_name(node: ast.Call) -> str | None:
    if not node.args:
        return None
    first_arg = node.args[0]
    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
        return first_arg.value
    return None
