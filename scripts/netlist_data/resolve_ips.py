"""Генерация актуальных IP-снимков из DNS доменов NetList.

IPv4/IPv6 — адреса, полученные через системный DNS-резолвер CI.
CIDR — точные маршруты хостов (/32 и /128), а не предполагаемые сети сервиса.
При полном сбое DNS для сервиса сохраняются прошлые файлы, чтобы не публиковать пустоту.
"""
from __future__ import annotations

import ipaddress
import socket
import sys
from pathlib import Path

from .io_lists import read_list, write_list
from .seed_import import load_registry

# RFC 6598 shared address space: not globally routable despite platform/version
# differences in ipaddress.is_global behavior.
NON_PUBLIC_NETWORKS = (ipaddress.ip_network("100.64.0.0/10"),)


def resolve_domain(domain: str) -> tuple[set[str], set[str]]:
    v4: set[str] = set()
    v6: set[str] = set()
    try:
        records = socket.getaddrinfo(
            domain, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM
        )
    except (OSError, UnicodeError):
        return v4, v6

    for record in records:
        try:
            address = ipaddress.ip_address(record[4][0].split("%", 1)[0])
        except ValueError:
            continue
        # Public routing lists must not include private, local, reserved or
        # otherwise non-global addresses.
        if not address.is_global or any(
            address.version == network.version and address in network
            for network in NON_PUBLIC_NETWORKS
        ):
            continue
        if address.version == 4:
            v4.add(str(address))
        else:
            v6.add(str(address))
    return v4, v6


def generate(repo_root: Path) -> dict[str, int]:
    root = Path(repo_root)
    registry = load_registry(root / "state" / "registry.json")
    all_v4: set[str] = set()
    all_v6: set[str] = set()
    resolved_services = 0
    stale_services = 0

    for slug, service in sorted(registry.items()):
        v4: set[str] = set()
        v6: set[str] = set()
        for domain in sorted(service.domains):
            domain_v4, domain_v6 = resolve_domain(domain)
            v4.update(domain_v4)
            v6.update(domain_v6)

        service_dir = root / "services" / slug
        old_v4 = set(read_list(service_dir / "ipv4.txt"))
        old_v6 = set(read_list(service_dir / "ipv6.txt"))
        if v4 or v6:
            resolved_services += 1
        else:
            # Don't turn transient DNS/network failure into destructive empty
            # output. Previous values remain clearly marked as last-known.
            v4, v6 = old_v4, old_v6
            if v4 or v6:
                stale_services += 1

        write_list(
            service_dir / "ipv4.txt",
            sorted(v4),
            comments=[
                f"NetList DNS snapshot for {service.name}",
                "Only globally routable IPv4 answers observed during this run.",
                "Addresses may be shared, CDN-backed, or change over time.",
            ],
        )
        write_list(
            service_dir / "ipv6.txt",
            sorted(v6),
            comments=[
                f"NetList DNS snapshot for {service.name}",
                "Only globally routable IPv6 answers observed during this run.",
                "Addresses may be shared, CDN-backed, or change over time.",
            ],
        )
        write_list(
            service_dir / "cidrv4.txt",
            [f"{address}/32" for address in v4],
            comments=["Exact host routes derived from current/last-known IPv4 answers; not service-owned ranges."],
        )
        write_list(
            service_dir / "cidrv6.txt",
            [f"{address}/128" for address in v6],
            comments=["Exact host routes derived from current/last-known IPv6 answers; not service-owned ranges."],
        )
        all_v4.update(v4)
        all_v6.update(v6)

    write_list(root / "common" / "ipv4.txt", sorted(all_v4), comments=[
        "Unique globally routable IPv4 DNS answers across NetList services.",
        "May include shared hosting/CDN addresses; not proof of service ownership.",
    ])
    write_list(root / "common" / "ipv6.txt", sorted(all_v6), comments=[
        "Unique globally routable IPv6 DNS answers across NetList services.",
        "May include shared hosting/CDN addresses; not proof of service ownership.",
    ])
    write_list(root / "common" / "cidrv4.txt", [f"{address}/32" for address in all_v4])
    write_list(root / "common" / "cidrv6.txt", [f"{address}/128" for address in all_v6])

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
