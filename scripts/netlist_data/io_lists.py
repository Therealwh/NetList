"""Списки NetList: UTF-8, LF, сортировка, дедупликация, строки '#' — комментарии."""
from __future__ import annotations

from pathlib import Path

LIST_FILES = ("domains.txt", "ipv4.txt", "ipv6.txt", "cidrv4.txt", "cidrv6.txt")


def read_list(path: str | Path) -> list[str]:
    path = Path(path)
    if not path.exists():
        return []
    return [
        stripped
        for line in path.read_text(encoding="utf-8").splitlines()
        if (stripped := line.strip()) and not stripped.startswith("#")
    ]


def write_list(
    path: str | Path, entries: list[str], comments: list[str] | None = None
) -> None:
    """Атомарная запись отсортированного уникального списка."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {text}" for text in (comments or [])]
    lines.extend(sorted(set(entries)))
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)
