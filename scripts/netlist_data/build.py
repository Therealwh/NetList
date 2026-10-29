"""Сборка опубликованных списков и catalog.json из state/registry.json."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .io_lists import write_list
from .seed_import import Service, load_registry, primary_domain

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
    write_list(
        root / "common" / "domains.txt",
        all_domains,
        comments=["NetList combined domains", NOTICE],
    )

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
