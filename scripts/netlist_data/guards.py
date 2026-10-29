"""Защита опубликованных данных: пустая сборка, массовое удаление, усохшие сервисы."""
from __future__ import annotations

import json
from pathlib import Path

DROP_RATIO = 0.5        # сервис усох, если потерял больше половины записей
TOTAL_DROP_RATIO = 0.2  # сборка не публикуется при падении общего числа >20%
MIN_SUSPICIOUS = 5      # сервисы меньше этого размера не считаются подозрительными


def _load_previous(repo_root: Path) -> dict:
    path = Path(repo_root) / "state" / "last_good.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def check_against_previous(repo_root: Path, catalog: dict) -> list[str]:
    """Список проблем; непустой список запрещает публикацию сборки."""
    previous = _load_previous(repo_root)
    if not previous:
        return []
    problems: list[str] = []
    prev_total = previous.get("counts", {}).get("domains", 0)
    new_total = catalog["counts"]["domains"]
    if new_total == 0:
        problems.append("build produced 0 domains; refusing to publish")
        return problems
    if prev_total and new_total < prev_total * (1 - TOTAL_DROP_RATIO):
        problems.append(
            f"total domains dropped {prev_total} -> {new_total} "
            f"(>{int(TOTAL_DROP_RATIO * 100)}%)"
        )
    prev_services = previous.get("services", {})
    for service in catalog.get("services", []):
        before = prev_services.get(service["slug"], {}).get("domain_count")
        after = service["domain_count"]
        if before is None:
            continue
        if before >= MIN_SUSPICIOUS and after == 0:
            problems.append(f"service {service['slug']} lost all {before} domains")
        elif before and after < before * DROP_RATIO:
            problems.append(
                f"service {service['slug']} shrank {before} -> {after} domains"
            )
    return problems


def save_last_good(repo_root: Path, catalog: dict) -> None:
    path = Path(repo_root) / "state" / "last_good.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "counts": catalog["counts"],
        "services": {
            s["slug"]: {"domain_count": s["domain_count"]}
            for s in catalog.get("services", [])
        },
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
