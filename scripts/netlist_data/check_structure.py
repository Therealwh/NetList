"""Репозиторий данных — только публичные данные и код сборки."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED_TOP_LEVEL = {
    "services", "common", "collections", "sources", "schemas",
    "scripts", "tests", "state", "assets", ".github", ".gitignore", ".gitattributes",
    "README_RU.md", "catalog.json",
}
FORBIDDEN_RE = re.compile(
    r"\.(php|html?|css|js|mjs|env|sqlite3?|db|bak|log|exe|dll)$"
    r"|(^|/)(vendor|node_modules|templates?|public|var|logs?|backups?)(/|$)"
    r"|(^|/)\.env"
    r"|(^|/)(prompts?|agent-private|\.agent|\.prompts?)(/|$)"
    r"|(^|/)[^/]*(prompt|reasoning|agent[-_]?notes|worklog)[^/]*\.(md|txt|json|ya?ml)$",
    re.IGNORECASE,
)


def violations(repo_root: Path) -> list[str]:
    root = Path(repo_root)
    found: list[str] = []
    for path in root.rglob("*"):
        if path.is_dir() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        top = relative.split("/", 1)[0]
        if top not in ALLOWED_TOP_LEVEL:
            found.append(f"unexpected top-level entry: {relative}")
        elif FORBIDDEN_RE.search(relative):
            found.append(f"forbidden file: {relative}")
    return sorted(found)


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[2]
    found = violations(root)
    for item in found:
        print(f"STRUCTURE VIOLATION: {item}", file=sys.stderr)
    print(f"checked {root}; violations: {len(found)}")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
