"""Импорт seed-каталогов в реестр сервисов NetList.

Источник истины — catalog.json датасета: в папках seed слаги кириллических
имён схлопнулись ('service', '1', '2'), а имена в JSON сохранены. Слаги
генерируются заново. Сервис центричен: один сервис, несколько категорий.
"""
from __future__ import annotations

import json
import re
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
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_user_submissions(repo_root: Path, known_categories: set[str] | None = None) -> list[dict]:
    """Читает sources/user_submissions/*.json — подтверждённые заявки пользователей
    (ТЗ §8.3: публикация только через штатную сборку; заявки не теряются при пересборке).

    Категории фильтруются по каталогу; без известной категории запись попадает
    в пользовательскую коллекцию. Источник данных помечается как "user".
    """
    directory = Path(repo_root) / "sources" / "user_submissions"
    if not directory.is_dir():
        return []
    records: list[dict] = []
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        domain = normalize_domain(str(data.get("domain", "")))
        if domain is None:
            continue
        categories = set()
        for raw in (data.get("categories") or []):
            category = str(raw).strip().lower()
            if re.fullmatch(r"[a-z0-9-]{1,60}", category) and (known_categories is None or category in known_categories):
                categories.add(category)
        records.append({
            "name": str(data.get("name") or domain)[:100],
            "categories": categories or {"user_collections"},
            "domains": {domain},
            "dataset": "user",
        })
    return records


def apply_domain_overrides(repo_root: Path, registry: dict[str, Service]) -> int:
    """Apply curated, provenance-carrying additions on every build and DNS run.

    The overlay is additive: it never removes seed/user domains. A missing service
    is an error so catalog renames cannot silently discard curated additions.
    """
    path = Path(repo_root) / "sources" / "seed" / "domain-overrides.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"sources": []}
    by_name: dict[str, list[Service]] = {}
    for service in registry.values():
        by_name.setdefault(service.name.casefold(), []).append(service)
    added = 0
    for item in data.get("sources", []):
        service_slug = str(item.get("service_slug", "")).strip()
        name = str(item.get("service", "")).strip()
        if service_slug:
            service = registry.get(service_slug)
            if service is None:
                raise ValueError(f"domain override service slug {service_slug!r} is missing")
        else:
            matches = by_name.get(name.casefold(), [])
            if len(matches) != 1:
                raise ValueError(
                    f"domain override service {name!r} matched {len(matches)} registry entries"
                )
            service = matches[0]
        for raw in item.get("domains", []):
            domain = normalize_domain(str(raw))
            if domain is None:
                raise ValueError(f"invalid override domain for {name!r}: {raw!r}")
            if domain not in service.domains:
                service.domains.add(domain)
                service.counts[domain] = service.counts.get(domain, 0) + 1
                added += 1
    # Full upstream geosite files are checked out by the daily GitHub Actions workflow.
    # Only literal domain:/full: rules are imported; regexp/keyword/include rules are
    # deliberately skipped because they are not concrete domains and may be broad.
    geosite_dir = Path(repo_root) / "sources" / "upstream" / "domain-list-community" / "data"
    if geosite_dir.is_dir():
        for slug, service in registry.items():
            source_path = geosite_dir / slug
            if not source_path.is_file():
                continue
            try:
                lines = source_path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeError):
                continue
            imported_for_service = 0
            for raw_line in lines:
                line = raw_line.partition("#")[0].strip()
                if not line:
                    continue
                rule, separator, value = line.partition(":")
                if not separator or rule not in {"domain", "full"}:
                    continue
                candidate = value.strip().split(maxsplit=1)[0] if value.strip() else ""
                domain = normalize_domain(candidate)
                if domain is None:
                    continue
                if domain not in service.domains:
                    service.domains.add(domain)
                    service.counts[domain] = service.counts.get(domain, 0) + 1
                    added += 1
                imported_for_service += 1
            if imported_for_service:
                service.datasets.add("v2fly-domain-list-community")
    return added


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
