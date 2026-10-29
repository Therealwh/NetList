"""Единая система логотипов NetList (ТЗ deasing §15).

GitHub-репозиторий данных — единственный источник истины: assets/logos/<slug>.svg
+ assets/logos/manifest.json + assets/logos/sources.json (конфиг кандидатов).

Команды:
    python -m scripts.netlist_data logos build     # скачать новых по sources.json, собрать манифест
    python -m scripts.netlist_data logos discover  # найти сервисы без логотипа, попробовать кандидатов
    python -m scripts.netlist_data logos check     # валидация манифеста/файлов (для CI)

Безопасность (§15.3): SVG считается недоверенным до проверки — отклоняются скрипты,
обработчики событий, foreignObject, внешние ссылки javascript:/http(s)://, размер >100 КБ;
обязательны <svg> и viewBox. Хорошие файлы не перезаписываются без нового валидного
содержимого; неоднозначные кандидаты попадают в manifest.pending, а не в файлы.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT_NAME = "assets/logos"
CDN = "https://cdn.jsdelivr.net/npm/simple-icons@15/icons/{slug}.svg"
MAX_SIZE = 100_000

_UNSAFE_RE = re.compile(rb"<script|<foreignObject|on\w+\s*=|javascript:", re.IGNORECASE)
_EXTERNAL_HREF_RE = re.compile(rb'href\s*=\s*["\']https?:', re.IGNORECASE)
_PATH_RE = re.compile(r"^[a-z0-9][a-z0-9-]*\.svg$")


def logos_dir(repo_root: Path) -> Path:
    return Path(repo_root) / "assets" / "logos"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate_svg(body: bytes) -> tuple[bool, str]:
    if len(body) > MAX_SIZE:
        return False, "слишком большой"
    if b"<svg" not in body or b"viewBox" not in body:
        return False, "нет <svg> или viewBox"
    if _UNSAFE_RE.search(body) or _EXTERNAL_HREF_RE.search(body):
        return False, "небезопасное содержимое"
    try:
        body.decode("utf-8")
    except UnicodeDecodeError:
        return False, "не UTF-8"
    return True, ""


def sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def fetch_cdn(slug: str) -> bytes | None:
    try:
        with urllib.request.urlopen(CDN.format(slug=slug), timeout=15) as resp:
            if resp.status != 200:
                return None
            return resp.read()
    except Exception:
        return None


def load_sources(logos_path: Path) -> dict:
    path = logos_path / "sources.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_sources(logos_path: Path, sources: dict) -> None:
    (logos_path / "sources.json").write_text(
        json.dumps(sources, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def auto_candidates(service_slug: str, name: str) -> list[str]:
    """Детерминированные кандидаты-слаги Simple Icons для нового сервиса."""
    base = service_slug.lower()
    candidates = [base, base.replace("-", "")]
    latin = re.sub(r"[^a-z0-9]", "", name.lower())
    if latin and latin not in candidates:
        candidates.append(latin)
    return [c for c in candidates if c][:3]


def build(repo_root: Path, discover: bool = False) -> dict:
    """Собирает манифест; при discover — ищет логотипы для сервисов без файла."""
    root = Path(repo_root)
    logos_path = logos_dir(root)
    logos_path.mkdir(parents=True, exist_ok=True)
    sources = load_sources(logos_path)

    catalog_path = root / "catalog.json"
    services: list[dict] = []
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        services = catalog.get("services", [])

    known_files = {p.name for p in logos_path.glob("*.svg")}
    manifest_entries: dict[str, dict] = {}
    pending: list[dict] = []
    added: list[str] = []

    for service in services:
        sid = service["slug"]
        entry_src = sources.get(sid) or {}
        candidates = entry_src.get("candidates") or auto_candidates(sid, service.get("name", ""))
        file_name = f"{sid}.svg"
        file_path = logos_path / file_name

        if file_name in known_files:
            body = file_path.read_bytes()
            ok, reason = validate_svg(body)
            if not ok:
                pending.append({"service_id": sid, "reason": f"файл не прошёл проверку: {reason}"})
                continue
            manifest_entries[sid] = {
                "service_id": sid,
                "name": service.get("name", sid),
                "primary_domain": service.get("primary_domain", ""),
                "file": file_name,
                "source": entry_src.get("source", "simple-icons"),
                "license": entry_src.get("license", "CC0"),
                "checked_at": now_iso(),
                "sha256": sha256(body),
            }
            continue

        # файла нет: пробуем кандидатов; первый валидный становится логотипом
        got = None
        for candidate in candidates:
            if not re.fullmatch(r"[a-z0-9-]{1,60}", candidate or ""):
                continue
            body = fetch_cdn(candidate)
            if body is None:
                continue
            ok, _ = validate_svg(body)
            if ok:
                got = candidate
                file_path.write_bytes(body)
                known_files.add(file_name)
                added.append(sid)
                break
        if got:
            sources[sid] = {"candidates": [got], "source": "simple-icons", "license": "CC0"}
            manifest_entries[sid] = {
                "service_id": sid,
                "name": service.get("name", sid),
                "primary_domain": service.get("primary_domain", ""),
                "file": file_name,
                "source": "simple-icons",
                "license": "CC0",
                "checked_at": now_iso(),
                "sha256": sha256((logos_path / file_name).read_bytes()),
            }
        else:
            # неоднозначно/не найдено: в список ручной проверки, случайный файл не качаем
            pending.append({"service_id": sid, "primary_domain": service.get("primary_domain", ""),
                            "tried": candidates, "reason": "не найден в Simple Icons"})

    manifest = {
        "version": 1,
        "generated_at": now_iso(),
        "source": "netlist-data",
        "logos": dict(sorted(manifest_entries.items())),
        "pending": pending,
    }
    (logos_path / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    save_sources(logos_path, sources)
    return {
        "logos": len(manifest_entries),
        "added": added,
        "pending": len(pending),
        "manifest": logos_path / "manifest.json",
    }


def check(repo_root: Path) -> list[str]:
    """Валидатор (§15.4): битые пути, отсутствующие/дублирующиеся файлы, небезопасный SVG, sha256."""
    root = Path(repo_root)
    logos_path = logos_dir(root)
    problems: list[str] = []
    path = logos_path / "manifest.json"
    if not path.exists():
        return ["manifest.json отсутствует"]
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"manifest.json: невалидный JSON: {e}"]

    seen_files: dict[str, str] = {}
    for sid, entry in manifest.get("logos", {}).items():
        file_name = str(entry.get("file", ""))
        if not _PATH_RE.fullmatch(file_name):
            problems.append(f"{sid}: недопустимый путь {file_name!r}")
            continue
        if file_name in seen_files:
            problems.append(f"{sid}: дублирование файла с {seen_files[file_name]}")
            continue
        seen_files[file_name] = sid
        file_path = logos_path / file_name
        if sid != file_name[: -4]:  # без суффикса ".svg"
            problems.append(f"{sid}: имя файла не совпадает с ID сервиса")
            continue
        if not file_path.is_file():
            problems.append(f"{sid}: файл {file_name} отсутствует")
            continue
        body = file_path.read_bytes()
        ok, reason = validate_svg(body)
        if not ok:
            problems.append(f"{sid}: {reason}")
        if entry.get("sha256") and sha256(body) != entry["sha256"]:
            problems.append(f"{sid}: sha256 не совпадает")
    return sorted(problems)


def main(argv: list[str]) -> int:
    repo_root = Path(__file__).resolve().parents[2]
    command = argv[1] if len(argv) > 1 else "check"
    if command == "build":
        result = build(repo_root, discover=False)
        print(json.dumps({k: v for k, v in result.items() if k != "manifest"}, ensure_ascii=False))
        problems = check(repo_root)
        for problem in problems:
            print(f"LOGOS PROBLEM: {problem}", file=sys.stderr)
        return 1 if problems else 0
    if command == "discover":
        result = build(repo_root, discover=True)
        print(json.dumps({k: v for k, v in result.items() if k != "manifest"}, ensure_ascii=False))
        problems = check(repo_root)
        for problem in problems:
            print(f"LOGOS PROBLEM: {problem}", file=sys.stderr)
        return 1 if problems else 0
    if command == "check":
        problems = check(repo_root)
        for problem in problems:
            print(f"LOGOS PROBLEM: {problem}", file=sys.stderr)
        print(f"logos: проблем {len(problems)}")
        return 1 if problems else 0
    print("неизвестная команда; используйте build | discover | check", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
