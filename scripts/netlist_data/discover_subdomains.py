"""Passive subdomain discovery for approved user-submitted domains.

Uses Certificate Transparency search (crt.sh). Results are candidates, not proof
that a hostname is currently active or controlled by the submitted service.
Existing discoveries are retained when the upstream source is unavailable.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .normalize import normalize_domain
from .seed_import import load_user_submissions

CT_URL = "https://crt.sh/?q=%25.{domain}&output=json"
TIMEOUT_SECONDS = 25
MAX_RESPONSE_BYTES = 20 * 1024 * 1024
MAX_NAMES_PER_ROOT = 5000
RETRIES = 3


def _within_root(candidate: str, root: str) -> bool:
    return candidate == root or candidate.endswith("." + root)


def query_certificate_transparency(root: str) -> set[str]:
    url = CT_URL.format(domain=quote(root, safe=".-"))
    request = Request(url, headers={"User-Agent": "NetList-subdomain-discovery/1.0"})
    last_error: Exception | None = None
    for attempt in range(RETRIES):
        try:
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ValueError("CT response exceeded size limit")
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, list):
                raise ValueError("CT response is not a JSON array")
            found: set[str] = set()
            for item in payload:
                if not isinstance(item, dict):
                    continue
                for raw_name in str(item.get("name_value", "")).splitlines():
                    name = raw_name.strip().lower()
                    if name.startswith("*."):
                        name = name[2:]
                    domain = normalize_domain(name)
                    if domain and _within_root(domain, root):
                        found.add(domain)
                        if len(found) >= MAX_NAMES_PER_ROOT:
                            return found
            return found
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            if attempt + 1 < RETRIES:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"CT lookup failed for {root}: {last_error}")


def discover(repo_root: Path) -> dict:
    root = Path(repo_root)
    path = root / "state" / "discovered_subdomains.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    previous: dict[str, dict] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for item in data.get("domains", []):
                if isinstance(item, dict) and item.get("root_domain") and item.get("domain"):
                    previous[item["root_domain"] + "|" + item["domain"]] = item
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            raise RuntimeError("Existing discovered_subdomains.json is unreadable; refusing to overwrite")

    submissions = load_user_submissions(root)
    roots = sorted({next(iter(record["domains"])) for record in submissions})
    discovered_roots = set()
    failures = []
    for domain in roots:
        try:
            names = query_certificate_transparency(domain)
            discovered_roots.add(domain)
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            # Store only discovered descendants. The submitted root is already in the catalogue.
            for name in names:
                if name == domain:
                    continue
                key = domain + "|" + name
                previous[key] = {
                    "root_domain": domain,
                    "domain": name,
                    "source": "crt.sh",
                    "discovered_at": now,
                    "status": "candidate_unverified",
                }
        except RuntimeError as exc:
            failures.append(str(exc))

    # A source outage must not erase earlier results. Existing records are additive.
    payload = {
        "schema_version": 1,
        "source": "Certificate Transparency via crt.sh",
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "roots_checked": len(discovered_roots),
        "roots_failed": failures,
        "domains": [previous[key] for key in sorted(previous)],
    }
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)
    return {
        "submitted_roots": len(roots),
        "roots_checked": len(discovered_roots),
        "roots_failed": len(failures),
        "discovered_candidates": len(previous),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(discover(Path(args.repo_root)), ensure_ascii=False, sort_keys=True))
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Subdomain discovery failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
