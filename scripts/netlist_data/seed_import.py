"""Импорт seed-каталогов в реестр сервисов NetList.

Источник истины — catalog.json датасета: в папках seed слаги кириллических
имён схлопнулись ('service', '1', '2'), а имена в JSON сохранены. Слаги
генерируются заново. Сервис центричен: один сервис, несколько категорий.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .normalize import normalize_domain, slugify


@dataclass
class Service:
    name: str
    slug: str
    domains: set[str] = field(default_factory=set)
    categories: set[str] = field(default_factory=set)
    datasets: set[str] = field(default_factory=set)
    counts: dict[str, int] = field(default_factory=dict)  # домен -> число упоминаний


def load_seed_catalog(seed_root: Path, dataset: str) -> list[dict]:
    """Читает seed_root/<dataset>/catalog.json, нормализует домены, битые отбрасывает."""
    path = Path(seed_root) / dataset / "catalog.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    records: list[dict] = []
    for category in data["categories"]:
        for service in category["services"]:
            clean = {
                d for d in (normalize_domain(x) for x in service["domains"])
                if d is not None
            }
            if not clean:
                continue
            records.append({
                "name": service["name"].strip(),
                "categories": {category["id"]},
                "domains": clean,
                "dataset": dataset,
            })
    return records


def build_registry(records: list[dict]) -> dict[str, Service]:
    """Сливает записи по сгенерированному слагу.

    Одинаковый слаг с пересечением доменов (или из другого датасета/категории)
    — один сервис. Разные сервисы с одним слагом (нет пересечения) получают
    суффикс '-2'. Слаги seed игнорируются полностью.
    """
    registry: dict[str, Service] = {}
    for record in records:
        slug = slugify(record["name"])
        service = registry.get(slug)
        if service is not None and not service.domains & record["domains"]:
            slug = f"{slug}-2"
            service = registry.get(slug)
            if service is not None and not service.domains & record["domains"]:
                raise ValueError(f"unresolvable slug collision: {record['name']!r}")
        if service is None:
            service = Service(name=record["name"], slug=slug)
            registry[slug] = service
        service.domains |= record["domains"]
        service.categories |= record["categories"]
        service.datasets.add(record["dataset"])
        for domain in record["domains"]:
            service.counts[domain] = service.counts.get(domain, 0) + 1
    return registry


def primary_domain(service: Service) -> str:
    """Самый частый домен, при равенстве — лексикографически меньший."""
    return min(service.counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]


def save_registry(repo_root: Path, registry: dict[str, Service]) -> None:
    path = Path(repo_root) / "state" / "registry.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"services": [
        {
            "name": s.name, "slug": s.slug,
            "domains": sorted(s.domains),
            "categories": sorted(s.categories),
            "datasets": sorted(s.datasets),
            "counts": dict(sorted(s.counts.items())),
        }
        for s in (registry[k] for k in sorted(registry))
    ]}
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def load_registry(path: Path) -> dict[str, Service]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        item["slug"]: Service(
            name=item["name"], slug=item["slug"],
            domains=set(item["domains"]),
            categories=set(item["categories"]),
            datasets=set(item["datasets"]),
            counts=dict(item.get("counts", {})),
        )
        for item in data["services"]
    }
