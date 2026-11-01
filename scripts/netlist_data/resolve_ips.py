"""Generate DNS-derived IP lists grouped by service and domain.

Common files are human-readable: each domain is introduced by a comment such
as '# YouTube — youtube.com', followed by its resolved IPs. Shared CDN answers
may appear under multiple domains; consumers can deduplicate when needed.
"""
from __future__ import annotations

import ipaddress
import re
from concurrent.futures import ThreadPoolExecutor
import socket
import sys
from pathlib import Path

from .io_lists import read_list
from .seed_import import apply_domain_overrides, load_registry, load_user_submissions
from .normalize import normalize_domain

NON_PUBLIC_NETWORKS = (ipaddress.ip_network("100.0.0.0/8"),)
DNS_WORKERS = 32


def resolve_domain(domain: str) -> tuple[set[str], set[str]]:
    v4: set[str] = set()
    v6: set[str] = set()
    try:
        records = socket.getaddrinfo(domain, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
    except (OSError, UnicodeError):
        return v4, v6
    for record in records:
        try:
            address = ipaddress.ip_address(record[4][0].split("%", 1)[0])
        except ValueError:
            continue
        if not address.is_global or any(
            address.version == network.version and address in network
            for network in NON_PUBLIC_NETWORKS
        ):
            continue
        (v4 if address.version == 4 else v6).add(str(address))
    return v4, v6


def write_grouped_list(path: Path, groups: list[tuple[str, set[str]]], comments: list[str] | None = None) -> None:
    """Atomically write labelled groups without sorting away group boundaries."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {comment}" for comment in (comments or [])]
    for label, entries in groups:
        lines.append(f"# {label}")
        clean_entries = sorted(set(entries))
        lines.extend(clean_entries if clean_entries else ["# (no public DNS addresses found)"])
        lines.append("")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)


def generate(repo_root: Path) -> dict[str, int]:
    root = Path(repo_root)
    registry = load_registry(root / "state" / "registry.json")
    apply_domain_overrides(root, registry)

    # Keep DNS generation in sync with build.py: user-submitted domains are
    # stored separately from the seed registry and must be resolved as well.
    known_categories = {category for service in registry.values() for category in service.categories}
    for record in load_user_submissions(root, known_categories=known_categories):
        domain = next(iter(record["domains"]))
        existing = next((service for service in registry.values() if domain in service.domains), None)
        if existing is not None:
            existing.categories |= record["categories"]
            existing.datasets.add("user")
            existing.counts[domain] = existing.counts.get(domain, 0) + 1
            continue
        base_slug = re.sub(r"[^a-z0-9]+", "-", record["name"].lower()).strip("-") or "user-domain"
        slug = base_slug
        suffix = 2
        while slug in registry and domain not in registry[slug].domains:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        service = registry.get(slug)
        if service is None:
            from .seed_import import Service
            service = Service(name=record["name"], slug=slug)
            registry[slug] = service
        service.domains.add(domain)
        service.categories |= record["categories"]
        service.datasets.add("user")
        service.counts[domain] = service.counts.get(domain, 0) + 1

    # Also resolve passive CT discoveries attached to submitted roots.
    discoveries_path = root / "state" / "discovered_subdomains.json"
    if discoveries_path.exists():
        import json
        discovery_data = json.loads(discoveries_path.read_text(encoding="utf-8"))
        for item in discovery_data.get("domains", []):
            root_domain = normalize_domain(str(item.get("root_domain", "")))
            candidate = normalize_domain(str(item.get("domain", "")))
            if not root_domain or not candidate or candidate == root_domain:
                continue
            service = next((s for s in registry.values() if root_domain in s.domains), None)
            if service is not None and candidate.endswith("." + root_domain):
                service.domains.add(candidate)
                service.counts.setdefault(candidate, 1)
                service.datasets.add("crt.sh-certificate-transparency")

    # Resolve each unique domain once, with bounded concurrency. The same CDN
    # hostname may belong to multiple services; caching avoids repeated DNS work.
    unique_domains = sorted({domain for service in registry.values() for domain in service.domains})
    with ThreadPoolExecutor(max_workers=DNS_WORKERS) as executor:
        resolved_by_domain = dict(zip(unique_domains, executor.map(resolve_domain, unique_domains)))

    all_v4: set[str] = set()
    all_v6: set[str] = set()
    common_groups: dict[str, list[tuple[str, set[str]]]] = {
        name: [] for name in ("ipv4", "ipv6", "cidrv4", "cidrv6")
    }
    resolved_services = stale_services = 0

    for slug, service in sorted(registry.items()):
        service_v4: set[str] = set()
        service_v6: set[str] = set()
        service_groups: dict[str, list[tuple[str, set[str]]]] = {
            name: [] for name in ("ipv4", "ipv6", "cidrv4", "cidrv6")
        }
        for domain in sorted(service.domains):
            v4, v6 = resolved_by_domain.get(domain, (set(), set()))
            service_v4.update(v4)
            service_v6.update(v6)
            label = f"{service.name} — {domain}"
            groups = {
                "ipv4": v4,
                "ipv6": v6,
                "cidrv4": {f"{address}/32" for address in v4},
                "cidrv6": {f"{address}/128" for address in v6},
            }
            for kind, entries in groups.items():
                service_groups[kind].append((label, entries))
                common_groups[kind].append((label, entries))

        service_dir = root / "services" / slug
        old_v4 = set(read_list(service_dir / "ipv4.txt"))
        old_v6 = set(read_list(service_dir / "ipv6.txt"))
        if service_v4 or service_v6:
            resolved_services += 1
        else:
            service_v4, service_v6 = old_v4, old_v6
            if service_v4 or service_v6:
                stale_services += 1
                label = f"{service.name} — last known snapshot (DNS unavailable)"
                groups = {
                    "ipv4": service_v4,
                    "ipv6": service_v6,
                    "cidrv4": {f"{address}/32" for address in service_v4},
                    "cidrv6": {f"{address}/128" for address in service_v6},
                }
                for kind, entries in groups.items():
                    service_groups[kind] = [(label, entries)]
                    common_groups[kind].append((label, entries))

        headers = [
            f"DNS-derived IP snapshot for {service.name} ({slug})",
            "Groups are labelled by domain; IPs may be shared by CDNs/hosting providers.",
            "DNS answers change and do not prove exclusive service ownership.",
        ]
        write_grouped_list(service_dir / "ipv4.txt", service_groups["ipv4"], headers)
        write_grouped_list(service_dir / "ipv6.txt", service_groups["ipv6"], headers)
        write_grouped_list(service_dir / "cidrv4.txt", service_groups["cidrv4"], ["Exact IPv4 host routes (/32); not service-owned ranges."])
        write_grouped_list(service_dir / "cidrv6.txt", service_groups["cidrv6"], ["Exact IPv6 host routes (/128); not service-owned ranges."])
        all_v4.update(service_v4)
        all_v6.update(service_v6)

    common_headers = [
        "Grouped by service and domain for readability; an IP may appear in multiple groups.",
        "DNS answers may be shared by CDNs/hosting providers and do not prove exclusive ownership.",
    ]
    write_grouped_list(root / "common" / "ipv4.txt", common_groups["ipv4"], common_headers)
    write_grouped_list(root / "common" / "ipv6.txt", common_groups["ipv6"], common_headers)
    write_grouped_list(root / "common" / "cidrv4.txt", common_groups["cidrv4"], ["Exact IPv4 host routes (/32), grouped by source domain; not service-owned ranges."])
    write_grouped_list(root / "common" / "cidrv6.txt", common_groups["cidrv6"], ["Exact IPv6 host routes (/128), grouped by source domain; not service-owned ranges."])

    if not all_v4 and not all_v6:
        raise RuntimeError("DNS produced no IP addresses and no previous IP snapshot exists")
    return {
        "services_total": len(registry),
        "services_resolved": resolved_services,
        "services_using_last_known_snapshot": stale_services,
        "ipv4": len(all_v4),
        "ipv6": len(all_v6),
        "cidrv4": len(all_v4),
        "cidrv6": len(all_v6),
    }


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    root = Path(args[0]) if args else Path(".")
    try:
        import json
        print(json.dumps(generate(root), ensure_ascii=False, sort_keys=True))
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"IP list generation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
