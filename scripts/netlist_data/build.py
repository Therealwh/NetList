"""Сборка опубликованных списков и catalog.json из state/registry.json."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .io_lists import write_list
from .seed_import import Service, load_registry, load_user_submissions, primary_domain, slugify

NOTICE = (
    "Кандидаты для проверки: наличие домена в списке не подтверждает блокировку, "
    "доступность или принадлежность IP сервису."
)


def content_signature(catalog: dict) -> str:
    """Отпечаток контента без generated_at — для коммита только при изменениях."""
    payload = {k: v for k, v in catalog.items() if k != "generated_at"}
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _read_existing(root: Path) -> dict:
    path = root / "catalog.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def build_all(repo_root: Path) -> dict:
    root = Path(repo_root)
    registry: dict[str, Service] = load_registry(root / "state" / "registry.json")

    # Пользовательские кандидаты загружаются на каждой сборке, а не только при ручном import.
    # Источник истины — sources/user_submissions/*.json, которые добавляются через GitHub API.
    known_categories = {category for service in registry.values() for category in service.categories}
    for record in load_user_submissions(root, known_categories=known_categories):
        domain = next(iter(record["domains"]))
        existing = next((service for service in registry.values() if domain in service.domains), None)
        if existing is not None:
            existing.categories |= record["categories"]
            existing.datasets.add("user")
            existing.counts[domain] = existing.counts.get(domain, 0) + 1
            continue
        base_slug = slugify(record["name"]) or slugify(domain) or "user-domain"
        slug = base_slug
        suffix = 2
        while slug in registry and domain not in registry[slug].domains:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        service = registry.get(slug)
        if service is None:
            service = Service(name=record["name"], slug=slug)
            registry[slug] = service
        service.domains.add(domain)
        service.categories |= record["categories"]
        service.datasets.add("user")
        service.counts[domain] = service.counts.get(domain, 0) + 1

    for slug, service in sorted(registry.items()):
        write_list(
            root / "services" / slug / "domains.txt",
            service.domains,
            comments=[f"NetList seed candidates: {service.name}", NOTICE],
        )

    by_category: dict[str, set[str]] = {}
    for service in registry.values():
        for category in service.categories:
            by_category.setdefault(category, set()).update(service.domains)
    for category, domains in sorted(by_category.items()):
        write_list(
            root / "collections" / category / "domains.txt",
            domains,
            comments=[f"NetList collection: {category}", NOTICE],
        )

    all_domains: set[str] = set()
    for service in registry.values():
        all_domains.update(service.domains)
    # Human-readable grouped combined domain list. Repeated values across service
    # groups are intentional when a domain is associated with more than one service.
    common_path = root / "common" / "domains.txt"
    common_path.parent.mkdir(parents=True, exist_ok=True)
    grouped_lines = [
        "# NetList combined domains — grouped by service",
        f"# {NOTICE}",
        "# A domain may appear in more than one service group when the catalog links it to multiple services.",
        "",
    ]
    for service in sorted(registry.values(), key=lambda item: (item.name.casefold(), item.slug)):
        grouped_lines.append(f"# Service — {service.name}")
        grouped_lines.extend(sorted(service.domains))
        grouped_lines.append("")
    common_tmp = common_path.with_name("domains.txt.tmp")
    common_tmp.write_text("\n".join(grouped_lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    common_tmp.replace(common_path)

    catalog = {
        "schema_version": 1,
        "dataset": "netlist",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "notice": NOTICE,
        "counts": {
            "services": len(registry),
            "categories": len(by_category),
            "domains": len(all_domains),
        },
        "categories": [
            {
                "id": category,
                "services_count": sum(
                    1 for s in registry.values() if category in s.categories
                ),
                "domains_count": len(by_category[category]),
            }
            for category in sorted(by_category)
        ],
        "services": [
            {
                "name": s.name,
                "slug": s.slug,
                "primary_domain": primary_domain(s),
                "domains": sorted(s.domains),
                "domain_count": len(s.domains),
                "categories": sorted(s.categories),
                "datasets": sorted(s.datasets),
                "seed_status": "candidate_unverified",
            }
            for s in (registry[k] for k in sorted(registry))
        ],
    }
    previous = _read_existing(root)
    if previous and content_signature(catalog) == content_signature(previous):
        catalog["generated_at"] = previous.get(
            "generated_at", catalog["generated_at"]
        )
    path = root / "catalog.json"
    tmp = path.with_name("catalog.json.tmp")
    tmp.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    tmp.replace(path)
    return catalog
