"""Daily per-domain DNS health snapshots for the NetList catalog."""
from __future__ import annotations

import ipaddress
import json
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

DNS_WORKERS = 32
HISTORY_LIMIT = 30


def check_family(domain: str, family: int) -> dict:
    """Return an explicit DNS state; distinguish authoritative absence from resolver errors."""
    version = 4 if family == socket.AF_INET else 6
    try:
        records = socket.getaddrinfo(domain, None, family=family, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        no_name = getattr(socket, "EAI_NONAME", -2)
        no_data = getattr(socket, "EAI_NODATA", no_name)
        state = "no_records" if exc.errno in {no_name, no_data} else "error"
        return {"status": state, "addresses": [], "error": None if state == "no_records" else str(exc)[:240]}
    except (OSError, UnicodeError) as exc:
        return {"status": "error", "addresses": [], "error": str(exc)[:240]}

    addresses = set()
    for record in records:
        try:
            address = ipaddress.ip_address(record[4][0].split("%", 1)[0])
        except (IndexError, TypeError, ValueError):
            continue
        if address.version == version and address.is_global:
            addresses.add(str(address))
    return {"status": "ok" if addresses else "no_records", "addresses": sorted(addresses), "error": None}


def monitor_catalog(
    repo_root: Path,
    family_checker: Callable[[str, int], dict] = check_family,
    checked_at: str | None = None,
) -> dict:
    root = Path(repo_root)
    catalog_path = root / "catalog.json"
    if not catalog_path.is_file():
        raise RuntimeError("catalog.json is missing; build the catalog before DNS monitoring")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    previous_path = root / "state" / "dns_monitor.json"
    try:
        previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else {}
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        previous = {}
    previous_domains = previous.get("domains", {}) if isinstance(previous, dict) else {}
    history_path = root / "state" / "dns_history.json"
    try:
        history_data = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else {}
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        history_data = {}
    change_events = list(history_data.get("events", [])) if isinstance(history_data, dict) else []

    owners: dict[str, list[dict]] = {}
    for service in catalog.get("services", []):
        slug = str(service.get("slug", ""))
        name = str(service.get("name", slug))
        for domain in service.get("domains", []):
            if isinstance(domain, str) and domain:
                owners.setdefault(domain, []).append({"slug": slug, "name": name})

    domains = sorted(owners)
    timestamp = checked_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    results: dict[str, dict] = {}

    def inspect(domain: str) -> tuple[str, dict]:
        old = previous_domains.get(domain, {}) if isinstance(previous_domains, dict) else {}
        current = {}
        for key, family in (("ipv4", socket.AF_INET), ("ipv6", socket.AF_INET6)):
            observed = family_checker(domain, family)
            status = observed.get("status", "error")
            addresses = sorted(set(observed.get("addresses", [])))
            if status not in {"ok", "no_records", "error"}:
                status = "error"
            old_family = old.get(key, {}) if isinstance(old, dict) else {}
            last_good = list(old_family.get("last_good_addresses", [])) if isinstance(old_family, dict) else []
            if not last_good and isinstance(old_family, dict) and old_family.get("status") == "ok":
                last_good = list(old_family.get("addresses", []))
            if status == "ok" and addresses:
                last_good = addresses
            current[key] = {
                "status": status,
                "addresses": addresses,
                "last_good_addresses": last_good,
                "error": str(observed.get("error") or "")[:240] or None,
            }

        changed = []
        for key in ("ipv4", "ipv6"):
            old_state = old.get(key, {}) if isinstance(old, dict) else {}
            new_state = current[key]
            if new_state["status"] == "ok" and new_state["addresses"] and isinstance(old_state, dict) and "status" in old_state:
                old_observed = old_state.get("last_good_addresses", [])
                if not old_observed and old_state.get("status") == "ok":
                    old_observed = old_state.get("addresses", [])
                if sorted(old_observed or []) != new_state["addresses"]:
                    changed.append(key)
        # Хранится только актуальное состояние; прошлые проверки удаляются.
        # События изменений ведутся отдельно в state/dns_history.json (bounded).
        entry = {
            "services": owners[domain],
            "checked_at": timestamp,
            "ipv4": current["ipv4"],
            "ipv6": current["ipv6"],
            "changed": changed,
        }
        return domain, entry

    with ThreadPoolExecutor(max_workers=DNS_WORKERS) as pool:
        for domain, entry in pool.map(inspect, domains):
            results[domain] = entry

    # Build an append-only, bounded event log. DNS errors and empty answers never
    # imply address removal; removals are recorded only after a successful non-empty
    # answer for that address family. Catalog additions/removals are tracked separately.
    old_names = set(previous_domains) if isinstance(previous_domains, dict) else set()
    new_names = set(results)
    def add_event(kind: str, domain: str, service_refs: list[dict], family: str | None = None, address: str | None = None) -> None:
        event = {"id": f"{timestamp}|{kind}|{domain}|{family or ''}|{address or ''}", "at": timestamp,
                 "type": kind, "domain": domain, "services": service_refs}
        if family: event["family"] = family
        if address: event["address"] = address
        if not any(isinstance(item, dict) and item.get("id") == event["id"] for item in change_events):
            change_events.append(event)

    if old_names:
        for domain in sorted(new_names - old_names):
            add_event("domain_added", domain, owners[domain])
    for domain in sorted(old_names - new_names):
        old_item = previous_domains.get(domain, {}) if isinstance(previous_domains, dict) else {}
        refs = old_item.get("services", []) if isinstance(old_item, dict) else []
        add_event("domain_removed", domain, refs if isinstance(refs, list) else [])

    for domain, item in results.items():
        old_item = previous_domains.get(domain, {}) if isinstance(previous_domains, dict) else {}
        for family in ("ipv4", "ipv6"):
            now = item[family]
            before = old_item.get(family, {}) if isinstance(old_item, dict) else {}
            if now["status"] != "ok" or not now["addresses"]:
                continue
            previous_good = before.get("last_good_addresses", []) if isinstance(before, dict) else []
            if not previous_good and isinstance(before, dict) and before.get("status") == "ok":
                previous_good = before.get("addresses", [])
            old_set, new_set = set(previous_good or []), set(now["addresses"])
            old_was_observed = isinstance(before, dict) and before.get("status") in {"ok", "no_records"}
            for address in sorted(new_set - old_set):
                if domain in old_names and (old_set or old_was_observed):
                    add_event("ip_added", domain, item["services"], family, address)
            for address in sorted(old_set - new_set):
                add_event("ip_removed", domain, item["services"], family, address)

    # Keep one year of events, capped defensively for shared-hosting consumers.
    change_events = change_events[-10000:]
    history_payload = {"schema_version": 1, "updated_at": timestamp, "events": change_events}
    history_tmp = history_path.with_name(history_path.name + ".tmp")
    history_tmp.write_text(json.dumps(history_payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    history_tmp.replace(history_path)

    # Компактная сводка для главной страницы сайта: агрегаты по сервисам без детальных доменов.
    service_stats: dict[str, dict] = {}
    for domain, item in results.items():
        for ref in item.get("services", []):
            slug = str(ref.get("slug", ""))
            if not slug:
                continue
            stat = service_stats.setdefault(slug, {
                "checked_domains": 0, "has_error": False, "has_change": False, "ipv4": {}, "ipv6": {},
            })
            stat["checked_domains"] += 1
            if item.get("changed"):
                stat["has_change"] = True
            for family in ("ipv4", "ipv6"):
                record = item[family]
                if record.get("status") == "error":
                    stat["has_error"] = True
                for address in record.get("addresses", []):
                    stat[family][address] = True
    for stat in service_stats.values():
        stat["ipv4"] = sorted(stat["ipv4"])
        stat["ipv6"] = sorted(stat["ipv6"])
        stat["ipv4_count"] = len(stat["ipv4"])
        stat["ipv6_count"] = len(stat["ipv6"])

    ok = sum(1 for item in results.values() if item["ipv4"]["status"] == "ok" or item["ipv6"]["status"] == "ok")
    errors = sum(1 for item in results.values() if item["ipv4"]["status"] == "error" or item["ipv6"]["status"] == "error")
    no_records = sum(1 for item in results.values() if item["ipv4"]["status"] == "no_records" and item["ipv6"]["status"] == "no_records")
    changed = sum(1 for item in results.values() if item["changed"])
    payload = {
        "schema_version": 1,
        "checked_at": timestamp,
        "source_generated_at": catalog.get("generated_at"),
        "summary": {
            "domains_total": len(results),
            "domains_with_records": ok,
            "domains_with_errors": errors,
            "domains_without_records": no_records,
            "domains_changed": changed,
        },
        "domains": results,
    }
    previous_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = previous_path.with_name(previous_path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary.replace(previous_path)

    summary_path = previous_path.with_name("dns_monitor_summary.json")
    summary_payload = {
        "schema_version": 1,
        "checked_at": timestamp,
        "summary": payload["summary"],
        "services": dict(sorted(service_stats.items())),
    }
    summary_tmp = summary_path.with_name(summary_path.name + ".tmp")
    summary_tmp.write_text(json.dumps(summary_payload, ensure_ascii=False, separators=(",", ":")) + '\\n', encoding="utf-8")
    summary_tmp.replace(summary_path)
    return payload


def main() -> int:
    result = monitor_catalog(Path("."))
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
