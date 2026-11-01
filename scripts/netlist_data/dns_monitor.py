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
            last_good = addresses if status in {"ok", "no_records"} and addresses else list((old.get(key, {}) or {}).get("last_good_addresses", []))
            if status == "no_records":
                # Empty answers are recorded as observations, but the previous good
                # snapshot remains visible for diagnosis instead of being discarded.
                last_good = list(old.get("last_good_" + key, []))
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
            if new_state["status"] in {"ok", "no_records"} and isinstance(old_state, dict) and "status" in old_state:
                old_observed = old_state.get("last_good_addresses", []) if old_state.get("status") == "error" else old_state.get("addresses", [])
                if sorted(old_observed or []) != new_state["addresses"]:
                    changed.append(key)
        history = list(old.get("history", [])) if isinstance(old, dict) else []
        event = {
            "checked_at": timestamp,
            "ipv4_status": current["ipv4"]["status"],
            "ipv6_status": current["ipv6"]["status"],
            "ipv4_count": len(current["ipv4"]["addresses"]),
            "ipv6_count": len(current["ipv6"]["addresses"]),
            "changed": changed,
        }
        if not history or history[-1] != event:
            history.append(event)
        entry = {
            "services": owners[domain],
            "checked_at": timestamp,
            "ipv4": current["ipv4"],
            "ipv6": current["ipv6"],
            "changed": changed,
            "history": history[-HISTORY_LIMIT:],
        }
        return domain, entry

    with ThreadPoolExecutor(max_workers=DNS_WORKERS) as pool:
        for domain, entry in pool.map(inspect, domains):
            results[domain] = entry

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
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(previous_path)
    return payload


def main() -> int:
    result = monitor_catalog(Path("."))
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
